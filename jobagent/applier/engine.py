"""The apply worker.

Polls for jobs you've marked Approved, applies to them one at a time with
human-ish pacing, and records exactly what happened — including a screenshot
of every submission, so you always have proof of what was sent.
"""
from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlmodel import select

from ..config import EVIDENCE_DIR, load_config
from ..db import (Application, AppStatus, Job, JobStatus, get_session,
                  log as dblog, utcnow)
from ..llm import get_llm
from ..resume_parser import get_or_build
from . import generic, linkedin, naukri
from .browser import browser_page
from .forms import AnswerResolver, bank_store

log = logging.getLogger("jobagent.applier")

COVER_SYSTEM = """You write short, specific cover letters for a candidate applying to Indian tech roles.
No flattery, no "I am writing to express my interest", no adjectives the candidate hasn't earned.
Concrete evidence only, drawn from the facts given. British/Indian English. Never invent anything."""

COVER_PROMPT = """Write a cover letter for this application.

CANDIDATE
{facts}

Strongest achievements:
{achievements}

JOB
{title} at {company}
{description}

Requirements: 150-200 words. Four short paragraphs at most.
Para 1: what the candidate does now and why this specific role fits.
Para 2: the single most relevant achievement, with its number.
Para 3: one concrete tie to what this company is building.
Para 4: one line close.
Plain text. No markdown, no placeholders, no "[Your Name]"."""


def generate_cover_letter(profile: Dict[str, Any], job: Job, facts: str) -> str:
    try:
        return get_llm().chat(
            COVER_SYSTEM,
            COVER_PROMPT.format(
                facts=facts[:3000],
                achievements="\n".join(f"- {a}" for a in (profile.get("achievements") or [])[:6]),
                title=job.title, company=job.company,
                description=(job.description or "")[:4000],
            ),
            temperature=0.4,
        ).strip()
    except Exception as e:  # noqa: BLE001
        log.warning("cover letter generation failed: %s", e)
        return ""


def applied_today() -> int:
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).replace(tzinfo=None)
    with get_session() as s:
        rows = s.exec(
            select(Application).where(Application.submitted_at != None)  # noqa: E711
            .where(Application.submitted_at >= since)
        ).all()
    return len(rows)


def queue_approved() -> int:
    """Create Application rows for anything newly approved."""
    n = 0
    with get_session() as s:
        approved = s.exec(select(Job).where(Job.status == JobStatus.APPROVED.value)).all()
        existing = {a.job_id for a in s.exec(select(Application)).all()}
        for j in approved:
            if j.id in existing:
                continue
            s.add(Application(job_id=j.id, status=AppStatus.QUEUED.value))
            n += 1
        if n:
            s.commit()
    return n


def _pick_handler(job: Job):
    ats = (job.ats or "").lower()
    src = (job.source or "").lower()
    if ats == "linkedin" or src == "linkedin":
        return "linkedin_easy_apply", linkedin.apply
    if ats == "naukri" or src == "naukri":
        return "naukri", naukri.apply
    return (ats or "generic"), generic.apply


def apply_to_job(job: Job, app: Application, profile: Dict[str, Any],
                 page, cfg) -> Dict[str, Any]:
    facts_resolver = AnswerResolver(profile, job.title, job.company, cfg=cfg)

    cover = app.cover_letter
    if cfg.apply.generate_cover_letter and not cover:
        cover = generate_cover_letter(profile, job, facts_resolver.facts)
    resolver = AnswerResolver(profile, job.title, job.company, cover_letter=cover, cfg=cfg)

    method, handler = _pick_handler(job)
    resume_pdf = cfg.resume_pdf

    log.info("Applying: %s @ %s  [%s]", job.title, job.company, method)
    try:
        res = handler(page, job, resolver, resume_pdf, cfg.apply.auto_submit)
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "status": "failed", "error": f"{type(e).__name__}: {e}"}

    # LinkedIn job with no Easy Apply -> chase the external ATS link
    if res.get("status") in ("not_easy_apply", "external"):
        target = res.get("external_url") or job.apply_url or job.url
        if target and target != job.url:
            job_copy = Job(**{**job.model_dump(), "apply_url": target})
            try:
                res = generic.apply(page, job_copy, resolver, resume_pdf, cfg.apply.auto_submit)
                method = "external_ats"
            except Exception as e:  # noqa: BLE001
                res = {"ok": False, "status": "failed", "error": str(e)}

    res["method"] = method
    res["cover_letter"] = cover
    res["answers"] = resolver.used
    res["pending"] = res.get("pending") or resolver.unresolved

    if cfg.apply.screenshot_evidence:
        try:
            p = EVIDENCE_DIR / f"job{job.id}_{datetime.now():%Y%m%d_%H%M%S}.png"
            page.screenshot(path=str(p), full_page=True)
            res["evidence_path"] = str(p)
        except Exception:
            pass
    return res


def _persist(app_id: int, job_id: int, res: Dict[str, Any]) -> None:
    with get_session() as s:
        app = s.get(Application, app_id)
        job = s.get(Job, job_id)
        if not app:
            return
        app.attempts += 1
        app.updated_at = utcnow()
        app.method = res.get("method", "")
        app.cover_letter = res.get("cover_letter", "") or app.cover_letter
        app.answers = json.dumps(res.get("answers", {}), default=str)
        app.pending_questions = json.dumps(res.get("pending", []), default=str)
        app.evidence_path = res.get("evidence_path", "") or app.evidence_path
        app.error = res.get("error", "") or ""
        app.external_url = res.get("external_url", "") or app.external_url

        st = res.get("status")
        if res.get("ok") or st in ("applied", "already_applied"):
            app.status = AppStatus.APPLIED.value
            app.submitted_at = app.submitted_at or utcnow()
            if job:
                job.status = JobStatus.APPROVED.value
        elif st == "needs_input":
            app.status = AppStatus.NEEDS_INPUT.value
        elif st in ("ready_not_submitted", "uncertain"):
            app.status = AppStatus.NEEDS_INPUT.value
            app.notes = (app.notes or "") + f"\n[{utcnow():%Y-%m-%d %H:%M}] {st}: verify manually"
        else:
            app.status = (AppStatus.FAILED.value if app.attempts >= 3
                          else AppStatus.QUEUED.value)
        s.add(app)
        if job:
            s.add(job)
        s.commit()


def run_apply_batch(limit: Optional[int] = None, progress=None) -> Dict[str, Any]:
    cfg = load_config(reload=True)
    queue_approved()

    cap = cfg.apply.daily_apply_cap - applied_today()
    if cap <= 0:
        msg = f"Daily apply cap of {cfg.apply.daily_apply_cap} already reached."
        dblog("apply", msg)
        return {"applied": 0, "skipped": 0, "message": msg}

    with get_session() as s:
        pend = s.exec(
            select(Application)
            .where(Application.status.in_([AppStatus.QUEUED.value, AppStatus.APPLYING.value]))
            .order_by(Application.created_at)
        ).all()
        pend = pend[: (limit or cap)]
        jobs = {a.id: s.get(Job, a.job_id) for a in pend}
        pend_data = [(a.id, a.job_id) for a in pend]

    if not pend_data:
        return {"applied": 0, "skipped": 0, "message": "Nothing approved and waiting."}

    profile = get_or_build().data()
    ok_count, fail_count = 0, 0

    with browser_page(headless=cfg.apply.headless) as page:
        for idx, (app_id, job_id) in enumerate(pend_data):
            with get_session() as s:
                app = s.get(Application, app_id)
                job = s.get(Job, job_id)
                if not app or not job:
                    continue
                app.status = AppStatus.APPLYING.value
                s.add(app)
                s.commit()
                s.refresh(app)
                s.refresh(job)
                app_snapshot, job_snapshot = app, job

            if progress:
                progress(f"Applying to {job_snapshot.title} @ {job_snapshot.company}")

            res = apply_to_job(job_snapshot, app_snapshot, profile, page, cfg)
            _persist(app_id, job_id, res)

            if res.get("ok"):
                ok_count += 1
                dblog("apply", f"Applied: {job_snapshot.title} @ {job_snapshot.company}",
                      method=res.get("method"), job_id=job_id)
            else:
                fail_count += 1
                dblog("warn", f"Did not complete: {job_snapshot.title} @ {job_snapshot.company} "
                              f"({res.get('status')}) {res.get('error','')}", job_id=job_id)

            if idx < len(pend_data) - 1:
                lo, hi = (cfg.apply.delay_between_s + [45, 120])[:2]
                delay = random.uniform(float(lo), float(hi))
                log.info("Pausing %.0fs before the next application", delay)
                time.sleep(delay)

    summary = {"applied": ok_count, "skipped": fail_count,
               "message": f"{ok_count} submitted, {fail_count} need attention"}
    dblog("apply", summary["message"], **summary)
    return summary


def answer_pending(app_id: int, answers: Dict[str, str]) -> None:
    """You answered the questions the agent got stuck on; remember them and requeue."""
    for q, a in answers.items():
        if a:
            bank_store(q, a, confirmed=True)
    with get_session() as s:
        app = s.get(Application, app_id)
        if app:
            app.status = AppStatus.QUEUED.value
            app.pending_questions = "[]"
            app.updated_at = utcnow()
            s.add(app)
            s.commit()
