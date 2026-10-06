"""Extract conservative LinkedIn posting-age and closure signals.

LinkedIn often exposes only relative text such as ``Posted 18 days ago``.
The exact posting date is therefore optional.  We preserve the observed text,
calculate an approximate age, and never infer that an old post is closed.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any


def extract_linkedin_freshness(text: str | None, observed_at: datetime | None = None) -> dict[str, Any]:
    raw = " ".join((text or "").split())
    low = raw.lower()
    observed = observed_at or datetime.now(timezone.utc)
    closed = any(x in low for x in (
        "no longer accepting applications", "job is closed", "job is no longer available",
        "position has been filled", "position is no longer available", "applications are closed",
    ))

    exact = re.search(r"(?:posted|date posted|published)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", low)
    age = re.search(r"(?:posted|reposted|published)?\s*(\d+)\s*(day|days|week|weeks|month|months|year|years)\s+ago", low)
    observed_text = None
    posted_at = None
    age_days = None
    if exact:
        observed_text = exact.group(0)
        posted_at = exact.group(1)
        age_days = max(0, (observed.date() - datetime.strptime(posted_at, "%Y-%m-%d").date()).days)
    elif age:
        observed_text = age.group(0)
        n = int(age.group(1)); unit = age.group(2)
        if unit.startswith("day"): age_days = n
        elif unit.startswith("week"): age_days = n * 7
        elif unit.startswith("month"): age_days = n * 30
        else: age_days = n * 365
        posted_at = (observed - timedelta(days=age_days)).date().isoformat()

    if closed:
        age_flag = "closed_signal"
        open_status = "closed"
    elif age_days is None:
        age_flag = "age_unknown"
        open_status = "unknown_age"
    elif age_days > 30:
        age_flag = "older_than_1_month"
        open_status = "active_older_than_30d"
    else:
        age_flag = "within_1_month"
        open_status = "active_recent"

    return {
        "linkedin_posted_at": posted_at,
        "linkedin_age_days": age_days,
        "linkedin_age_flag": age_flag,
        "linkedin_open_status": open_status,
        "linkedin_age_source_text": observed_text,
        "linkedin_age_checked_at": observed.isoformat(),
    }
