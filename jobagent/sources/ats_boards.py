"""Company career portals via their public ATS JSON APIs.

Greenhouse, Lever and Ashby all expose official, documented, unauthenticated
endpoints. No scraping, no rate limits worth worrying about, no ban risk, and
the descriptions are complete — these are the highest-signal jobs in the whole
pipeline. Add company slugs to `sources.ats_boards` in config.yaml.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

import httpx

from .base import RawJob, clean, parse_salary_lpa

log = logging.getLogger("jobagent.sources.ats")

TIMEOUT = 25


def _ts(v) -> datetime | None:
    if not v:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v / 1000 if v > 1e11 else v, tz=timezone.utc)
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception:
        return None


def greenhouse(slug: str) -> List[RawJob]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    out: List[RawJob] = []
    try:
        r = httpx.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        for j in r.json().get("jobs", []):
            desc = clean(j.get("content", ""))
            lo, hi = parse_salary_lpa(desc[:2000])
            out.append(RawJob(
                title=clean(j.get("title")),
                company=slug.replace("-", " ").title(),
                location=clean((j.get("location") or {}).get("name", "")),
                url=j.get("absolute_url", ""),
                apply_url=j.get("absolute_url", ""),
                description=desc,
                source="greenhouse",
                ats="greenhouse",
                is_remote="remote" in ((j.get("location") or {}).get("name", "") or "").lower(),
                salary_min_lpa=lo, salary_max_lpa=hi,
                posted_at=_ts(j.get("updated_at") or j.get("first_published")),
            ))
    except Exception as e:  # noqa: BLE001
        log.debug("greenhouse/%s: %s", slug, e)
    return out


def lever(slug: str) -> List[RawJob]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    out: List[RawJob] = []
    try:
        r = httpx.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        for j in r.json():
            cats = j.get("categories") or {}
            desc = clean(j.get("descriptionPlain") or j.get("description", ""))
            for li in j.get("lists", []) or []:
                desc += "\n\n" + clean(li.get("text", "")) + "\n" + clean(li.get("content", ""))
            lo, hi = parse_salary_lpa(desc[:2000])
            out.append(RawJob(
                title=clean(j.get("text")),
                company=slug.replace("-", " ").title(),
                location=clean(cats.get("location", "")),
                url=j.get("hostedUrl", ""),
                apply_url=j.get("applyUrl") or j.get("hostedUrl", ""),
                description=desc,
                source="lever",
                ats="lever",
                is_remote="remote" in (cats.get("location", "") or "").lower(),
                salary_min_lpa=lo, salary_max_lpa=hi,
                posted_at=_ts(j.get("createdAt")),
                tags=[cats.get("team", ""), cats.get("commitment", "")],
            ))
    except Exception as e:  # noqa: BLE001
        log.debug("lever/%s: %s", slug, e)
    return out


def ashby(slug: str) -> List[RawJob]:
    url = "https://api.ashbyhq.com/posting-api/job-board/" + slug
    out: List[RawJob] = []
    try:
        r = httpx.get(url, params={"includeCompensation": "true"}, timeout=TIMEOUT)
        r.raise_for_status()
        for j in r.json().get("jobs", []):
            desc = clean(j.get("descriptionPlain") or j.get("descriptionHtml", ""))
            comp = j.get("compensation") or {}
            sal_text = clean(str(comp.get("compensationTierSummary", "")))
            lo, hi = parse_salary_lpa(sal_text or desc[:2000])
            out.append(RawJob(
                title=clean(j.get("title")),
                company=clean(j.get("organizationName") or slug.replace("-", " ").title()),
                location=clean(j.get("location", "")),
                url=j.get("jobUrl", ""),
                apply_url=j.get("applyUrl") or j.get("jobUrl", ""),
                description=desc,
                source="ashby",
                ats="ashby",
                is_remote=bool(j.get("isRemote")),
                salary_text=sal_text,
                salary_min_lpa=lo, salary_max_lpa=hi,
                posted_at=_ts(j.get("publishedAt")),
                tags=[j.get("department", ""), j.get("employmentType", "")],
            ))
    except Exception as e:  # noqa: BLE001
        log.debug("ashby/%s: %s", slug, e)
    return out


PROVIDERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}


def scrape_all(board_cfg: dict) -> List[RawJob]:
    out: List[RawJob] = []
    for provider, slugs in (board_cfg or {}).items():
        fn = PROVIDERS.get(provider)
        if not fn or not isinstance(slugs, list):
            continue
        for slug in slugs:
            jobs = fn(str(slug))
            if jobs:
                log.info("[%s/%s] -> %d", provider, slug, len(jobs))
            out.extend(jobs)
    return out
