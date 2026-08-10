"""Common shape every job source normalises into."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional

log = logging.getLogger("jobagent.sources")


@dataclass
class RawJob:
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    apply_url: str = ""
    description: str = ""
    source: str = ""
    ats: str = "unknown"
    is_remote: bool = False
    salary_text: str = ""
    salary_min_lpa: Optional[float] = None
    salary_max_lpa: Optional[float] = None
    posted_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def is_fresh(self, hours: int) -> bool:
        """No posted_at = we keep it; boards lie about dates more than they omit them."""
        if not self.posted_at:
            return True
        pa = self.posted_at
        if pa.tzinfo is None:
            pa = pa.replace(tzinfo=timezone.utc)
        return pa >= datetime.now(timezone.utc) - timedelta(hours=hours)


# --------------------------------------------------------------------------- #

_LPA = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac|l\b)", re.I)
_LPA_SINGLE = re.compile(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)", re.I)
_RANGE_NUM = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]{5,})\s*(?:-|–|to)\s*(?:₹|rs\.?|inr)?\s*([\d,]{5,})", re.I)


def parse_salary_lpa(text: str):
    """Best-effort INR salary -> (min_lpa, max_lpa). Indian boards are messy."""
    if not text:
        return None, None
    t = text.replace(",", ",")
    m = _LPA.search(t)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = _RANGE_NUM.search(t)
    if m:
        lo = float(m.group(1).replace(",", ""))
        hi = float(m.group(2).replace(",", ""))
        # heuristics: monthly vs annual
        if lo < 500_000:
            lo, hi = lo * 12, hi * 12
        return round(lo / 100_000, 1), round(hi / 100_000, 1)
    m = _LPA_SINGLE.search(t)
    if m:
        v = float(m.group(1))
        return v, v
    return None, None


def detect_ats(url: str) -> str:
    u = (url or "").lower()
    for key, name in (
        ("greenhouse.io", "greenhouse"),
        ("lever.co", "lever"),
        ("ashbyhq.com", "ashby"),
        ("myworkdayjobs.com", "workday"),
        ("workday.com", "workday"),
        ("smartrecruiters.com", "smartrecruiters"),
        ("icims.com", "icims"),
        ("taleo.net", "taleo"),
        ("successfactors", "successfactors"),
        ("linkedin.com", "linkedin"),
        ("naukri.com", "naukri"),
        ("indeed.com", "indeed"),
        ("wellfound.com", "wellfound"),
        ("angel.co", "wellfound"),
        ("instahyre.com", "instahyre"),
        ("keka.com", "keka"),
        ("darwinbox", "darwinbox"),
        ("zohorecruit", "zoho"),
        ("freshteam", "freshteam"),
    ):
        if key in u:
            return name
    return "unknown"


def clean(s: Optional[str]) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(s))
    s = re.sub(r"&nbsp;?", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()
