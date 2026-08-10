"""Daily discovery run: gather -> filter -> dedupe -> score -> persist.

The run stops as soon as it has `target_jobs_per_day` jobs above the score
threshold, so a good day is fast and a bad day keeps digging.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlmodel import select

from .config import load_config
from .db import Job, JobStatus, fingerprint, get_session, log as dblog
from .matcher import Matcher, derive_queries
from .resume_parser import get_or_build
from .sources import ats_boards, free_apis, india_boards, jobspy_source, wellfound
from .sources.base import RawJob

log = logging.getLogger("jobagent.pipeline")

JOBSPY_SITES = ["linkedin", "indeed", "naukri", "google", "glassdoor"]


# --------------------------------------------------------------------------- #
#  Gather
# --------------------------------------------------------------------------- #
def gather(queries: List[str], cfg=None) -> List[RawJob]:
    cfg = cfg or load_config()
    raw: List[RawJob] = []

    # 1. ATS boards first — free, reliable, complete descriptions.
    ats_cfg = cfg.sources.get("ats_boards") or {}
    if ats_cfg.get("enabled"):
        boards = {k: v for k, v in ats_cfg.items() if k != "enabled"}
        raw += ats_boards.scrape_all(boards)

    # 2. Major boards via JobSpy.
    for site in JOBSPY_SITES:
        if not cfg.source_enabled(site):
            continue
        limit = cfg.source_limit(site, 40)
        for q in queries[:6]:
            for loc in cfg.search.locations:
                raw += jobspy_source.scrape(
                    site, q, loc,
                    hours_old=cfg.search.hours_old,
                    limit=max(10, limit // max(1, len(cfg.search.locations))),
                    remote_ok=cfg.search.remote_ok,
                )

    # 3. India-specific boards.
    ib = cfg.sources.get("india_boards") or {}
    if ib.get("enabled"):
        raw += india_boards.scrape_all(queries, ib.get("providers", []), ib.get("max_results", 25))

    # 4. Free public APIs.
    fa = cfg.sources.get("free_apis") or {}
    if fa.get("enabled"):
        raw += free_apis.scrape_all(queries, fa.get("providers", []), fa.get("max_results", 25))

    # 5. Wellfound (Playwright, needs a login).
    if cfg.source_enabled("wellfound"):
        raw += wellfound.scrape(queries, cfg.source_limit("wellfound", 30), headless=True)

    log.info("gathered %d raw postings", len(raw))
    return raw


# --------------------------------------------------------------------------- #
#  Filter + dedupe
# --------------------------------------------------------------------------- #
def hard_filter(jobs: List[RawJob], cfg=None) -> List[RawJob]:
    cfg = cfg or load_config()
    bad_titles = [k.lower() for k in cfg.search.exclude_title_keywords]
    bad_co = [c.lower() for c in cfg.search.exclude_companies]
    out: List[RawJob] = []
    for j in jobs:
        if not j.title or not j.company:
            continue
        t, c = j.title.lower(), j.company.lower()
        if any(k in t for k in bad_titles):
            continue
        if any(k in c for k in bad_co):
            continue
        if not j.is_fresh(cfg.search.hours_old):
            continue
        if cfg.search.min_salary_lpa and j.salary_max_lpa and j.salary_max_lpa < cfg.search.min_salary_lpa:
            continue
        out.append(j)
    return out


def dedupe(jobs: List[RawJob]) -> List[RawJob]:
    """Same role posted on five boards -> keep the one with the best description
    and, where possible, the most directly applyable URL."""
    best: Dict[str, RawJob] = {}
    rank = {"greenhouse": 5, "lever": 5, "ashby": 5, "linkedin": 4, "naukri": 4,
            "instahyre": 3, "wellfound": 3, "foundit": 2, "indeed": 2, "google": 1}
    for j in jobs:
        fp = fingerprint(j.company, j.title, j.location)
        cur = best.get(fp)
        if cur is None:
            best[fp] = j
            continue
        score_new = len(j.description or "") / 500 + rank.get(j.source, 1)
        score_cur = len(cur.description or "") / 500 + rank.get(cur.source, 1)
        if score_new > score_cur:
            j.salary_min_lpa = j.salary_min_lpa or cur.salary_min_lpa
            j.salary_max_lpa = j.salary_max_lpa or cur.salary_max_lpa
            best[fp] = j
    return list(best.values())


def drop_already_seen(jobs: List[RawJob], lookback_days: int = 45) -> List[RawJob]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    with get_session() as s:
        known = {
            r.fingerprint
            for r in s.exec(select(Job).where(Job.discovered_at >= cutoff.replace(tzinfo=None))).all()
        }
    return [j for j in jobs if fingerprint(j.company, j.title, j.location) not in known]


# --------------------------------------------------------------------------- #
#  Run
# --------------------------------------------------------------------------- #
def run_discovery(progress=None, cfg=None) -> Dict[str, Any]:
    cfg = cfg or load_config(reload=True)
    started = datetime.now(timezone.utc)

    def emit(msg: str, **kw):
        log.info(msg)
        dblog("discovery", msg, **kw)
        if progress:
            try:
                progress(msg, kw)
            except Exception:
                pass

    lib = get_or_build()
    profile = lib.data()
    try:
        pemb = json.loads(lib.embedding or "[]")
    except Exception:
        pemb = []

    queries = derive_queries(profile, cfg)
    emit(f"Searching for: {', '.join(queries[:8])}")

    raw = gather(queries, cfg)
    emit(f"Collected {len(raw)} raw postings across all sources")

    jobs = hard_filter(raw, cfg)
    jobs = dedupe(jobs)
    emit(f"{len(jobs)} left after freshness, keyword and duplicate filters")

    jobs = drop_already_seen(jobs)
    emit(f"{len(jobs)} are new (not seen in the last 45 days)")

    # Score most-promising-looking first so we hit the daily target sooner.
    matcher = Matcher(profile, pemb, cfg)
    scored_rows: List[Job] = []
    kept = 0
    max_llm_calls = max(60, cfg.search.max_jobs_per_day * 8)
    llm_calls = 0

    prelim = []
    for j in jobs:
        es = matcher.embed_score(j)
        prelim.append((es, j))
    prelim.sort(key=lambda x: -x[0])
    emit(f"Embedding pre-screen done; {sum(1 for e, _ in prelim if e >= cfg.matching.embed_threshold)} passed")

    with get_session() as s:
        for es, j in prelim:
            if kept >= cfg.search.max_jobs_per_day or llm_calls >= max_llm_calls:
                break
            if es < cfg.matching.embed_threshold and kept >= cfg.search.min_jobs_per_day:
                break

            res = matcher.llm_score(j)
            llm_calls += 1
            status = (JobStatus.PENDING.value if res["score"] >= cfg.matching.llm_min_score
                      else JobStatus.ARCHIVED.value)
            if status == JobStatus.PENDING.value:
                kept += 1

            row = Job(
                fingerprint=fingerprint(j.company, j.title, j.location),
                title=j.title, company=j.company, location=j.location,
                is_remote=j.is_remote, url=j.url, apply_url=j.apply_url or j.url,
                source=j.source, ats=j.ats, description=j.description[:40000],
                salary_text=j.salary_text, salary_min_lpa=j.salary_min_lpa,
                salary_max_lpa=j.salary_max_lpa,
                posted_at=j.posted_at.replace(tzinfo=None) if j.posted_at else None,
                embed_score=round(es, 4),
                score=res["score"], verdict=res["verdict"], reasoning=res["reasoning"],
                matched_skills=json.dumps(res["matched_skills"]),
                missing_skills=json.dumps(res["missing_skills"]),
                red_flags=json.dumps(res["red_flags"]),
                seniority_fit=res["seniority_fit"],
                status=status,
            )
            try:
                s.add(row)
                s.commit()
                s.refresh(row)
                scored_rows.append(row)
            except Exception:
                s.rollback()
                continue

            if kept and kept % 5 == 0:
                emit(f"{kept} matches found so far ({llm_calls} scored)")

    dur = (datetime.now(timezone.utc) - started).total_seconds()
    summary = {
        "raw": len(raw), "new": len(jobs), "scored": llm_calls,
        "matched": kept, "duration_s": round(dur, 1),
        "target": cfg.search.target_jobs_per_day,
    }
    emit(f"Run complete: {kept} jobs waiting for your review "
         f"({llm_calls} scored in {dur/60:.1f} min)", **summary)
    if kept < cfg.search.min_jobs_per_day:
        dblog("warn",
              f"Only {kept} matches today (target {cfg.search.min_jobs_per_day}). "
              f"Consider lowering matching.llm_min_score or widening search.queries.")
    return summary
