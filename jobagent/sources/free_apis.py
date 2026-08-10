"""Free, keyless (or free-tier) job APIs — bonus coverage at zero ban risk.

  Remotive      no key   remote tech roles, global (many hire from India)
  RemoteOK      no key   remote roles, good startup coverage
  Arbeitnow     no key   EU/global board, decent remote volume
  Himalayas     no key   remote-first companies
  The Muse      no key   (higher limits with a free key)
  HN Who's Hiring  no key   monthly thread via Algolia — genuinely great signal
  Adzuna        free key  real India coverage, 1000 calls/month free
  Jooble        free key  aggregates Indian boards including Naukri mirrors

Put free keys in a .env file at the repo root:
  ADZUNA_APP_ID=...   ADZUNA_APP_KEY=...   JOOBLE_KEY=...   THEMUSE_KEY=...
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import List

import httpx

from .base import RawJob, clean, detect_ats, parse_salary_lpa

log = logging.getLogger("jobagent.sources.free")
TIMEOUT = 25
UA = {"User-Agent": "LocalJobAgent/1.0 (personal job search assistant)"}


def _iso(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        except Exception:
            return None


# --------------------------------------------------------------------------- #

def remotive(query: str, limit: int = 30) -> List[RawJob]:
    try:
        r = httpx.get("https://remotive.com/api/remote-jobs",
                      params={"search": query, "limit": limit}, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        return [RawJob(
            title=clean(j.get("title")), company=clean(j.get("company_name")),
            location=clean(j.get("candidate_required_location")) or "Remote",
            url=j.get("url", ""), apply_url=j.get("url", ""),
            description=clean(j.get("description")), source="remotive",
            ats=detect_ats(j.get("url", "")), is_remote=True,
            salary_text=clean(j.get("salary")), posted_at=_iso(j.get("publication_date")),
            tags=j.get("tags", []) or [],
        ) for j in r.json().get("jobs", [])[:limit]]
    except Exception as e:  # noqa: BLE001
        log.debug("remotive: %s", e)
        return []


def remoteok(query: str, limit: int = 30) -> List[RawJob]:
    try:
        r = httpx.get("https://remoteok.com/api", headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        rows = [x for x in r.json() if isinstance(x, dict) and x.get("position")]
        toks = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
        out = []
        for j in rows:
            hay = f"{j.get('position','')} {' '.join(j.get('tags',[]) or [])}".lower()
            if toks and not any(t in hay for t in toks):
                continue
            out.append(RawJob(
                title=clean(j.get("position")), company=clean(j.get("company")),
                location=clean(j.get("location")) or "Remote",
                url=j.get("url", ""), apply_url=j.get("apply_url") or j.get("url", ""),
                description=clean(j.get("description")), source="remoteok",
                ats=detect_ats(j.get("apply_url") or j.get("url", "")), is_remote=True,
                salary_text=clean(str(j.get("salary_min") or "")), posted_at=_iso(j.get("date")),
                tags=j.get("tags", []) or [],
            ))
            if len(out) >= limit:
                break
        return out
    except Exception as e:  # noqa: BLE001
        log.debug("remoteok: %s", e)
        return []


def arbeitnow(query: str, limit: int = 25) -> List[RawJob]:
    try:
        r = httpx.get("https://www.arbeitnow.com/api/job-board-api", headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        toks = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
        out = []
        for j in r.json().get("data", []):
            hay = f"{j.get('title','')} {' '.join(j.get('tags',[]) or [])}".lower()
            if toks and not any(t in hay for t in toks):
                continue
            out.append(RawJob(
                title=clean(j.get("title")), company=clean(j.get("company_name")),
                location=clean(j.get("location")), url=j.get("url", ""), apply_url=j.get("url", ""),
                description=clean(j.get("description")), source="arbeitnow",
                ats=detect_ats(j.get("url", "")), is_remote=bool(j.get("remote")),
                posted_at=_iso(j.get("created_at")), tags=j.get("tags", []) or [],
            ))
            if len(out) >= limit:
                break
        return out
    except Exception as e:  # noqa: BLE001
        log.debug("arbeitnow: %s", e)
        return []


def himalayas(query: str, limit: int = 25) -> List[RawJob]:
    try:
        r = httpx.get("https://himalayas.app/jobs/api", params={"limit": limit},
                      headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        toks = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
        out = []
        for j in r.json().get("jobs", []):
            if toks and not any(t in (j.get("title", "") or "").lower() for t in toks):
                continue
            out.append(RawJob(
                title=clean(j.get("title")), company=clean(j.get("companyName")),
                location=", ".join(j.get("locationRestrictions", []) or []) or "Remote",
                url=j.get("applicationLink") or j.get("guid", ""),
                apply_url=j.get("applicationLink", ""),
                description=clean(j.get("description")), source="himalayas",
                ats=detect_ats(j.get("applicationLink", "")), is_remote=True,
                posted_at=_iso(j.get("pubDate")),
            ))
            if len(out) >= limit:
                break
        return out
    except Exception as e:  # noqa: BLE001
        log.debug("himalayas: %s", e)
        return []


def themuse(query: str, limit: int = 25) -> List[RawJob]:
    try:
        params = {"page": 0, "location": "India"}
        if os.getenv("THEMUSE_KEY"):
            params["api_key"] = os.getenv("THEMUSE_KEY")
        r = httpx.get("https://www.themuse.com/api/public/jobs", params=params,
                      headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        toks = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
        out = []
        for j in r.json().get("results", []):
            if toks and not any(t in (j.get("name", "") or "").lower() for t in toks):
                continue
            locs = ", ".join(l.get("name", "") for l in j.get("locations", []) or [])
            url = (j.get("refs") or {}).get("landing_page", "")
            out.append(RawJob(
                title=clean(j.get("name")), company=clean((j.get("company") or {}).get("name")),
                location=clean(locs), url=url, apply_url=url,
                description=clean(j.get("contents")), source="themuse",
                ats=detect_ats(url), is_remote="remote" in locs.lower(),
                posted_at=_iso(j.get("publication_date")),
            ))
            if len(out) >= limit:
                break
        return out
    except Exception as e:  # noqa: BLE001
        log.debug("themuse: %s", e)
        return []


def hn_whos_hiring(query: str, limit: int = 25) -> List[RawJob]:
    """The monthly HN 'Who is hiring?' thread, via Algolia's free search API.
    Low volume, unusually high quality — real engineers posting real roles."""
    try:
        s = httpx.get("https://hn.algolia.com/api/v1/search_by_date",
                      params={"query": "Ask HN: Who is hiring?", "tags": "story", "hitsPerPage": 3},
                      headers=UA, timeout=TIMEOUT)
        s.raise_for_status()
        hits = [h for h in s.json().get("hits", []) if "who is hiring" in (h.get("title", "") or "").lower()]
        if not hits:
            return []
        story_id = hits[0]["objectID"]
        c = httpx.get(f"https://hn.algolia.com/api/v1/items/{story_id}", headers=UA, timeout=TIMEOUT)
        c.raise_for_status()
        toks = [t for t in re.split(r"\W+", query.lower()) if len(t) > 3]
        out = []
        for ch in (c.json().get("children") or []):
            txt = clean(ch.get("text") or "")
            if len(txt) < 120:
                continue
            low = txt.lower()
            if toks and not any(t in low for t in toks):
                continue
            if "india" not in low and "remote" not in low:
                continue
            head = txt.split("\n")[0][:160]
            company = head.split("|")[0].strip()[:80] or "HN post"
            out.append(RawJob(
                title=head[:120], company=company, location="Remote / India",
                url=f"https://news.ycombinator.com/item?id={ch.get('id')}",
                apply_url=f"https://news.ycombinator.com/item?id={ch.get('id')}",
                description=txt, source="hackernews", ats="unknown", is_remote="remote" in low,
                posted_at=_iso(ch.get("created_at")),
            ))
            if len(out) >= limit:
                break
        return out
    except Exception as e:  # noqa: BLE001
        log.debug("hn: %s", e)
        return []


def adzuna(query: str, limit: int = 30, country: str = "in") -> List[RawJob]:
    app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return []
    try:
        r = httpx.get(
            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
            params={"app_id": app_id, "app_key": app_key, "results_per_page": min(limit, 50),
                    "what": query, "max_days_old": 7, "content-type": "application/json"},
            headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        out = []
        for j in r.json().get("results", []):
            lo = j.get("salary_min")
            hi = j.get("salary_max")
            out.append(RawJob(
                title=clean(j.get("title")), company=clean((j.get("company") or {}).get("display_name")),
                location=clean((j.get("location") or {}).get("display_name")),
                url=j.get("redirect_url", ""), apply_url=j.get("redirect_url", ""),
                description=clean(j.get("description")), source="adzuna",
                ats=detect_ats(j.get("redirect_url", "")),
                salary_min_lpa=round(lo / 100000, 1) if lo else None,
                salary_max_lpa=round(hi / 100000, 1) if hi else None,
                posted_at=_iso(j.get("created")),
            ))
        return out
    except Exception as e:  # noqa: BLE001
        log.debug("adzuna: %s", e)
        return []


def jooble(query: str, location: str = "India", limit: int = 30) -> List[RawJob]:
    key = os.getenv("JOOBLE_KEY")
    if not key:
        return []
    try:
        r = httpx.post(f"https://jooble.org/api/{key}",
                       json={"keywords": query, "location": location, "page": 1},
                       headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        out = []
        for j in r.json().get("jobs", [])[:limit]:
            lo, hi = parse_salary_lpa(j.get("salary", "") or "")
            out.append(RawJob(
                title=clean(j.get("title")), company=clean(j.get("company")),
                location=clean(j.get("location")), url=j.get("link", ""), apply_url=j.get("link", ""),
                description=clean(j.get("snippet")), source="jooble",
                ats=detect_ats(j.get("link", "")), salary_text=clean(j.get("salary")),
                salary_min_lpa=lo, salary_max_lpa=hi, posted_at=_iso(j.get("updated")),
            ))
        return out
    except Exception as e:  # noqa: BLE001
        log.debug("jooble: %s", e)
        return []


REGISTRY = {
    "remotive": remotive,
    "remoteok": remoteok,
    "arbeitnow": arbeitnow,
    "himalayas": himalayas,
    "themuse": themuse,
    "hackernews": hn_whos_hiring,
    "adzuna": adzuna,
}


def scrape_all(queries: List[str], enabled: List[str], per_source: int = 25) -> List[RawJob]:
    out: List[RawJob] = []
    for name in enabled:
        fn = REGISTRY.get(name)
        for q in queries[:4]:            # these APIs are broad; a few queries suffice
            if name == "jooble":
                jobs = jooble(q, limit=per_source)
            elif fn:
                jobs = fn(q, per_source)
            else:
                jobs = []
            if jobs:
                log.info("[%s] '%s' -> %d", name, q, len(jobs))
            out.extend(jobs)
    return out
