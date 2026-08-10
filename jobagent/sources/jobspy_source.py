"""LinkedIn / Indeed / Naukri / Google Jobs / Glassdoor via python-jobspy.

JobSpy handles the rotating-header, rate-limit and pagination misery for us.
We keep concurrency low and add jitter because LinkedIn and Naukri both
throttle aggressively.
"""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone
from typing import List

import pandas as pd  # noqa: F401  (jobspy dependency, imported for type clarity)

from .base import RawJob, clean, detect_ats, parse_salary_lpa

log = logging.getLogger("jobagent.sources.jobspy")

# jobspy site keys
SITE_MAP = {
    "linkedin": "linkedin",
    "indeed": "indeed",
    "naukri": "naukri",
    "google": "google",
    "glassdoor": "glassdoor",
}


def _to_dt(v):
    if v is None:
        return None
    try:
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(str(v)).replace(tzinfo=timezone.utc)
    except Exception:
        try:
            import pandas as pd

            ts = pd.to_datetime(v, errors="coerce")
            if ts is None or pd.isna(ts):
                return None
            return ts.to_pydatetime().replace(tzinfo=timezone.utc)
        except Exception:
            return None


def scrape(
    site: str,
    query: str,
    location: str,
    hours_old: int = 168,
    limit: int = 40,
    country: str = "India",
    remote_ok: bool = True,
) -> List[RawJob]:
    site_key = SITE_MAP.get(site)
    if not site_key:
        return []
    try:
        from jobspy import scrape_jobs
    except ImportError:
        log.error("python-jobspy not installed — run ./install.sh")
        return []

    kwargs = dict(
        site_name=[site_key],
        search_term=query,
        location=location,
        results_wanted=limit,
        hours_old=hours_old,
        country_indeed=country,
        description_format="markdown",
        verbose=0,
    )
    # LinkedIn descriptions are opt-in and slow, but we need them to score well.
    if site_key == "linkedin":
        kwargs["linkedin_fetch_description"] = True
    if site_key == "google":
        # Google Jobs works off a natural-language string, not term+location.
        kwargs["google_search_term"] = f"{query} jobs near {location} since last week"

    try:
        df = scrape_jobs(**kwargs)
    except Exception as e:  # noqa: BLE001
        log.warning("[%s] '%s' @ %s failed: %s", site, query, location, e)
        return []

    if df is None or len(df) == 0:
        return []

    out: List[RawJob] = []
    for _, r in df.iterrows():
        g = lambda k, d="": (r[k] if k in df.columns and r.get(k) is not None and str(r.get(k)) != "nan" else d)  # noqa: E731
        url = str(g("job_url") or "")
        apply_url = str(g("job_url_direct") or "") or url
        sal_bits = [str(g("min_amount", "")), str(g("max_amount", "")), str(g("interval", "")), str(g("currency", ""))]
        sal_text = " ".join(b for b in sal_bits if b and b != "nan").strip()
        lo, hi = parse_salary_lpa(sal_text)
        if lo is None:
            lo, hi = parse_salary_lpa(str(g("description", ""))[:1500])

        out.append(
            RawJob(
                title=clean(str(g("title"))),
                company=clean(str(g("company"))),
                location=clean(str(g("location"))) or location,
                url=url,
                apply_url=apply_url,
                description=clean(str(g("description"))),
                source=site,
                ats=detect_ats(apply_url or url),
                is_remote=bool(g("is_remote", False)),
                salary_text=sal_text,
                salary_min_lpa=lo,
                salary_max_lpa=hi,
                posted_at=_to_dt(g("date_posted")),
            )
        )
    log.info("[%s] '%s' @ %s -> %d", site, query, location, len(out))
    time.sleep(random.uniform(2.0, 5.0))  # be a good citizen
    return out
