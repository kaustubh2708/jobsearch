"""India-specific boards that JobSpy doesn't cover.

These hit the same JSON endpoints the sites' own React frontends use. They are
inherently more fragile than the ATS APIs — if a site changes its internals a
source here goes quiet rather than crashing the run. Everything degrades
gracefully and the pipeline carries on with the sources that still work.

  Instahyre   curated Indian tech roles, strong product-company coverage
  Foundit     ex-Monster India, huge volume across Indian enterprises
  Cutshort    Indian startup roles
  Wellfound   startup roles, India filter (Playwright, see wellfound.py)
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from .base import RawJob, clean, detect_ats, parse_salary_lpa

log = logging.getLogger("jobagent.sources.india")
TIMEOUT = 25
UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
}


def _days_ago(n) -> datetime | None:
    try:
        return datetime.now(timezone.utc) - timedelta(days=float(n))
    except Exception:
        return None


# --------------------------------------------------------------------------- #

def instahyre(query: str, limit: int = 30) -> List[RawJob]:
    """Instahyre's public job-search endpoint."""
    out: List[RawJob] = []
    try:
        r = httpx.get(
            "https://www.instahyre.com/api/v1/job_search",
            params={"job_type": "-1", "limit": min(limit, 40), "offset": 0, "keyword": query},
            headers={**UA, "Referer": "https://www.instahyre.com/search-jobs/"},
            timeout=TIMEOUT, follow_redirects=True,
        )
        r.raise_for_status()
        for j in (r.json().get("objects") or [])[:limit]:
            emp = j.get("employer") or {}
            slug = j.get("public_url") or j.get("id")
            url = f"https://www.instahyre.com/job/{slug}" if slug else "https://www.instahyre.com"
            desc = clean(j.get("job_description") or j.get("description") or "")
            lo, hi = j.get("min_salary"), j.get("max_salary")
            out.append(RawJob(
                title=clean(j.get("title")),
                company=clean(emp.get("company_name") or emp.get("name")),
                location=clean(", ".join(l.get("name", "") for l in (j.get("locations") or []) if isinstance(l, dict))
                               or j.get("location", "")),
                url=url, apply_url=url, description=desc,
                source="instahyre", ats="instahyre",
                salary_min_lpa=float(lo) if lo else None,
                salary_max_lpa=float(hi) if hi else None,
                posted_at=_days_ago(j.get("days_ago") or 0),
            ))
    except Exception as e:  # noqa: BLE001
        log.debug("instahyre: %s", e)
    return out


def foundit(query: str, location: str = "india", limit: int = 30) -> List[RawJob]:
    """Foundit (formerly Monster India) — very large Indian job index."""
    out: List[RawJob] = []
    try:
        r = httpx.get(
            "https://www.foundit.in/middleware/jobsearch",
            params={"start": 0, "limit": min(limit, 40), "query": query,
                    "locations": location, "sort": 1, "days": 7},
            headers={**UA, "Referer": "https://www.foundit.in/"},
            timeout=TIMEOUT, follow_redirects=True,
        )
        r.raise_for_status()
        data = r.json()
        jobs = (data.get("jobSearchResponse") or {}).get("data") or data.get("data") or []
        for j in jobs[:limit]:
            url = j.get("jobUrl") or j.get("seoJdUrl") or ""
            if url and not url.startswith("http"):
                url = "https://www.foundit.in" + url
            sal = clean(str(j.get("salary") or j.get("minimumSalary") or ""))
            lo, hi = parse_salary_lpa(sal)
            out.append(RawJob(
                title=clean(j.get("title")), company=clean(j.get("companyName")),
                location=clean(", ".join(j.get("locations", [])) if isinstance(j.get("locations"), list)
                               else str(j.get("location", ""))),
                url=url, apply_url=url,
                description=clean(j.get("jobDescription") or j.get("description") or j.get("summary") or ""),
                source="foundit", ats=detect_ats(url), salary_text=sal,
                salary_min_lpa=lo, salary_max_lpa=hi,
                posted_at=_days_ago(j.get("postedOnDays") or j.get("daysOld") or 0),
            ))
    except Exception as e:  # noqa: BLE001
        log.debug("foundit: %s", e)
    return out


def cutshort(query: str, limit: int = 25) -> List[RawJob]:
    """Cutshort public job listing feed — Indian startup roles."""
    out: List[RawJob] = []
    try:
        r = httpx.get("https://cutshort.io/api/v2/jobs/search",
                      params={"q": query, "limit": min(limit, 30), "location": "India"},
                      headers={**UA, "Referer": "https://cutshort.io/jobs"},
                      timeout=TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        payload = r.json()
        jobs = payload.get("jobs") or payload.get("data") or payload.get("results") or []
        for j in jobs[:limit]:
            url = j.get("url") or j.get("permalink") or ""
            if url and not url.startswith("http"):
                url = "https://cutshort.io" + url
            lo, hi = parse_salary_lpa(str(j.get("salary", "")))
            out.append(RawJob(
                title=clean(j.get("title") or j.get("role")),
                company=clean(j.get("company_name") or (j.get("company") or {}).get("name")),
                location=clean(j.get("location") or "India"),
                url=url, apply_url=url,
                description=clean(j.get("description") or ""),
                source="cutshort", ats="cutshort",
                salary_min_lpa=lo, salary_max_lpa=hi,
            ))
    except Exception as e:  # noqa: BLE001
        log.debug("cutshort: %s", e)
    return out


REGISTRY = {"instahyre": instahyre, "foundit": foundit, "cutshort": cutshort}


def scrape_all(queries: List[str], enabled: List[str], per_source: int = 25) -> List[RawJob]:
    out: List[RawJob] = []
    for name in enabled:
        fn = REGISTRY.get(name)
        if not fn:
            continue
        for q in queries[:5]:
            jobs = fn(q, per_source)
            if jobs:
                log.info("[%s] '%s' -> %d", name, q, len(jobs))
            out.extend(jobs)
    return out
