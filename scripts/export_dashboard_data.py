#!/usr/bin/env python3
"""Export both source workbooks into a read-only JSON payload for the local dashboard."""
from __future__ import annotations

import hashlib
import json
import re
from html import unescape
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value).strip()


def url_for(cell: Any) -> str:
    if cell.hyperlink and cell.hyperlink.target:
        value = cell.hyperlink.target.strip()
        return value if urlsplit(value).scheme.lower() in {"https", "http"} else ""
    value = clean(cell.value)
    match = re.match(r'^=HYPERLINK\("([^\"]+)"', value, re.I)
    value = match.group(1) if match else value
    return value if urlsplit(value).scheme.lower() in {"https", "http"} else ""


def record_id(candidate: str, sheet: str, row: int, company: str, title: str, url: str) -> str:
    raw = "|".join((candidate, sheet, str(row), company.casefold(), title.casefold(), url.casefold()))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def deduplicate_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse repeated workbook views while keeping the richest row and its provenance."""
    by_key: dict[str, dict[str, Any]] = {}
    score = {"Verified wave role": 6, "Job link": 5, "Eligible role": 4,
             "Warm-up lead": 3, "Hiring drive": 2, "Historical / wave role": 1}
    for job in jobs:
        url = job["url"].strip()
        if url:
            key = "url:" + url_key(url)
        else:
            key = "row:" + "|".join((job["company"].casefold(), job["title"].casefold(), job["location"].casefold()))
        if key not in by_key:
            job["source_sheets"] = [job["source_sheet"]]
            by_key[key] = job
            continue
        old = by_key[key]
        sources = list(dict.fromkeys(old.get("source_sheets", []) + [job["source_sheet"]]))
        keep, other = (job, old) if score.get(job["category"], 0) > score.get(old["category"], 0) else (old, job)
        for field in ("location", "status", "experience", "compensation", "notes", "score", "verification"):
            if not keep.get(field) and other.get(field):
                keep[field] = other[field]
        keep["source_sheets"] = sources
        keep["tags"] = list(dict.fromkeys(list(keep.get("tags", [])) + list(other.get("tags", []))))
        if "Rejected" in keep["tags"]:
            keep["status"] = "Closed"  # a rejection recorded on any row of the same role wins
        if not keep.get("appliedAt") and other.get("appliedAt"):
            keep["appliedAt"] = other["appliedAt"]
        by_key[key] = keep
    return list(by_key.values())



# ---------------------------------------------------------------------------
# Status / notes signals. The sheets are hand-edited: statuses and notes live in unnamed columns and
# use free text such as "applied on 30/09" or "message sent for referral on 5/10". Everything below
# turns that text into a canonical stage, an applied date, tags and the user's own note (kept verbatim).
# ---------------------------------------------------------------------------
TODAY = date.today()
NUMERIC_RE = re.compile(r"^\d+(\.\d+)?$")
URL_IN_TEXT = re.compile(r"https?://[^\s<>\"']+", re.I)
EXPERIENCE_RE = re.compile(r"^\s*\d+\s*(\+|[–-]\s*\d+|to\s*\d+)?\s*(years?|yrs?|yoe)\b", re.I)
PLACEHOLDER_RE = re.compile(r"^(no\s+contact\s+yet|none|n/?a|na|nil|tbd|-+|notes?|status|company)$", re.I)
LABEL_RE = re.compile(r"^.{0,40}\b(link|post|requisition|view job|portal)\b\s*[↗]?\s*$|^(view job|linkedin|instahyre)$|^linkedin view \d+$|^(?=\S+$)(?=.*\d)[A-Za-z0-9._/-]{3,24}$", re.I)
PRIORITY_RE = re.compile(r"(priority\s*\d|first priority|second priority|good match)", re.I)
DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\s*/\s*(\d{1,2})(?!\d)")


def find_dates(text: str) -> list[str]:
    out = []
    for d, m in DATE_RE.findall(text):
        day, month = int(d), int(m)
        if not (1 <= day <= 31 and 1 <= month <= 12):
            continue
        try:
            year = TODAY.year
            iso = date(year, month, day)
            if (iso - TODAY).days > 7:  # dd/mm written for a past month of last year
                iso = date(year - 1, month, day)
            out.append(iso.isoformat())
        except ValueError:
            pass
    return out


def classify_status(text: str) -> dict[str, Any] | None:
    """Return {status, appliedAt, tags} for a free-text status, or None when the text is only a note."""
    low = " ".join(text.lower().split())
    dates = find_dates(low)
    tags: list[str] = []
    applied = re.search(r"applied[^0-9]{0,24}(\d{1,2})\s*/\s*(\d{1,2})", low)
    applied_date = find_dates(applied.group(0))[0] if applied and find_dates(applied.group(0)) else (dates[0] if dates else "")
    has_ref = bool(re.search(r"referral|referred|\bref\b|\bref's|ref asked", low))
    if re.search(r"\bno referral\b|without referral", low) and not re.search(r"with referral|via referral", low):
        tags.append("No referral")
    if "reject" in low:
        return {"status": "Closed", "appliedAt": "", "tags": ["Rejected"] + tags}
    if re.search(r"gave oa|online assessment|interview (scheduled|on|round)", low):
        if has_ref:
            tags.append("Referred")
        return {"status": "Interviewing", "appliedAt": applied_date, "tags": ["Assessment / interview"] + tags}
    if re.search(r"\bapplied\b|application (sent|submitted)", low):
        if has_ref and "No referral" not in tags:
            tags.append("Referred")
        return {"status": "Applied", "appliedAt": applied_date, "tags": tags}
    if re.search(r"referred( on|\b)", low) and not re.search(r"ask|message|sent|for referral|need", low):
        return {"status": "Applied", "appliedAt": dates[0] if dates else "", "tags": ["Referred"]}
    if re.search(r"message[d]?\b.*(referral|bhaiya|didi|poonam)|message sent|ref asked|resume sent|e-?mail(ed)? (sent|to)|emailed|cold e-?mails?|sent to hr|\bmessaged\b|text the contact", low):
        return {"status": "Watching", "appliedAt": "", "tags": ["Referral asked"], "outreachAt": dates[0] if dates else ""}
    if re.search(r"no longer active|invalid link|no rel[ae]vant|not relevant|not hiring|position closed|^no$", low):
        return {"status": "Closed", "appliedAt": "", "tags": ["Not available"] if "relevant" not in low else ["Not relevant"]}
    m = re.search(r"closes? on (\d{1,2}/\d{1,2})", low)
    if m:
        d = find_dates(m.group(1))
        if d and d[0] < TODAY.isoformat():
            return {"status": "Closed", "appliedAt": "", "tags": ["Deadline passed " + m.group(1)]}
        return {"status": "Watching", "appliedAt": "", "tags": ["Closes " + m.group(1)]}
    return None


def url_from_cell(cell: Any) -> str:
    link = url_for(cell)
    if link:
        return link
    match = URL_IN_TEXT.search(clean(cell.value))
    return match.group(0).rstrip("),.;") if match else ""


def row_signals(ws: Any, row: int, cols: tuple[int, ...], url_cols: tuple[int, ...]) -> dict[str, Any]:
    """Read one sheet row: first URL, status, applied date, tags, experience and the user's own notes."""
    sig: dict[str, Any] = {"url": "", "status": "", "appliedAt": "", "tags": [], "notes": [], "experience": "", "raw": ""}
    for col in url_cols:
        if not sig["url"]:
            sig["url"] = url_from_cell(ws.cell(row, col))
    for col in cols:
        text = " · ".join(part.strip() for part in cell_text(ws, row, col).splitlines() if part.strip())
        if not text or NUMERIC_RE.match(text) or PLACEHOLDER_RE.match(text):
            continue
        urls = URL_IN_TEXT.findall(text)
        if urls:
            rest = URL_IN_TEXT.sub("", text).strip(" :-·")
            if not sig["url"]:
                sig["url"] = urls[0].rstrip("),.;")
            if rest and not LABEL_RE.match(rest) and len(rest) < 60:
                sig["notes"].append(rest.rstrip(":"))
            continue
        if EXPERIENCE_RE.match(text):
            sig["experience"] = sig["experience"] or text
            continue
        found = classify_status(text)
        if found:
            if not sig["status"] or sig["status"] in ("Watching", "Closed") and found["status"] in ("Applied", "Interviewing"):
                sig["status"] = found["status"]
            sig["appliedAt"] = sig["appliedAt"] or found.get("appliedAt", "")
            sig["tags"].extend(t for t in found["tags"] if t not in sig["tags"])
            sig["raw"] = sig["raw"] or text
            if text.lower().strip() not in ("applied", "rejected", "applied."):
                sig["notes"].append(text)
            continue
        if re.fullmatch(r"(da|ece role)", text.strip(), re.I):
            # The user's shorthand for "not a pure tech role, but close to the candidate's skills".
            sig["tags"].append("Skills-adjacent role")
            sig["notes"].append(f"Marked '{text.strip()}' in your sheet")
            continue
        if PRIORITY_RE.match(text) and len(text) < 48:
            sig["tags"].append(text)
            continue
        if LABEL_RE.match(text):
            continue
        sig["notes"].append(text)
    sig["notes"] = list(dict.fromkeys(sig["notes"]))
    return sig



STATUS_RANK = {"": 0, "Closed": 1, "Watching": 2, "Applied": 3, "Interviewing": 4}


IDENTITY_PARAMS = ("jk", "gh_jid", "jobid", "job_id", "requisitionid", "reqid", "folderid", "id")


def url_key(url: str) -> str:
    """Same idea as the website's job identity: host + path + the query params that name the job."""
    parts = urlsplit(url.strip())
    query = parse_qs(parts.query)
    keep = "&".join(f"{k}={query[k][0]}" for k in IDENTITY_PARAMS if query.get(k) and query[k][0])
    return f"{parts.netloc.lower()}{parts.path.rstrip('/')}" + (f"?{keep}" if keep else "")


def merge_signal(job: dict[str, Any], sig: dict[str, Any]) -> None:
    """Fold a sheet signal into an existing job without losing what is already there."""
    new = sig.get("status", "")
    old = job.get("status", "")
    if new and ("Rejected" in sig.get("tags", []) or STATUS_RANK.get(new, 0) > STATUS_RANK.get(old, 0)):
        job["status"] = new
    if sig.get("appliedAt") and not job.get("appliedAt"):
        job["appliedAt"] = sig["appliedAt"]
    job["tags"] = list(dict.fromkeys(list(job.get("tags", [])) + list(sig.get("tags", []))))
    note = " · ".join(n for n in sig.get("notes", []) if n and n not in (job.get("notes") or ""))
    if note:
        job["notes"] = f"{job['notes']} · {note}" if job.get("notes") else note
    if sig.get("experience") and not job.get("experience"):
        job["experience"] = sig["experience"]


ROLE_WORDS = re.compile(r"engineer|developer|\bsde\b|analyst|software|scientist|manager|intern|trainee|architect|specialist|associate|technical staff", re.I)


def title_from_url(url: str) -> str:
    """Best-effort readable title from a job URL path; falls back to a plain label rather than guessing."""
    for part in reversed([x for x in urlsplit(url).path.split("/") if x]):
        words = re.sub(r"[-_]+", " ", re.sub(r"_(R|JR)[-_]?\d+.*$", "", re.sub(r"^\d+[-_]?", "", part))).strip()
        words = re.sub(r"\s+at\s+\w+(\s+\d+)?$", "", words, flags=re.I)         # '... at Snapmint 446215'
        words = re.sub(r"(\s+(jr|r)?\d+)+$", "", words, flags=re.I).strip()       # trailing ids
        tokens = words.split()
        hexish = sum(bool(re.fullmatch(r"[0-9a-f]{4,}", t, re.I)) for t in tokens)
        if ROLE_WORDS.search(words) and hexish < 2 and len(tokens) >= 2:
            return words.title()
    return ""


def drop_dupes(notes: list[str], title: str) -> str:
    """Join notes, skipping ones that just repeat the role title."""
    t = title.casefold()
    keep = [n for n in notes if n.casefold() not in t and t[:24] not in n.casefold()]
    return " · ".join(keep)



TITLE_CACHE = ROOT / "website" / "data" / "title_cache.json"
GENERIC_TITLE = re.compile(r"^(careers?|jobs?|job details?|job description|apply|search|home|candidate experience|sign in|login|opportunities|open (roles|positions?)|current openings?|all jobs|join us)$", re.I)


def clean_page_title(raw: str, company: str = "") -> str:
    """'Senior Engineer | Acme Careers' -> 'Senior Engineer'. Returns '' if nothing role-like is left."""
    text = re.sub(r"\s+", " ", unescape(raw or "")).strip()
    parts = [p.strip() for p in re.split(r"\s+[|\u2013\u2014-]\s+|\s*\|\s*", text) if p.strip()]
    parts = [p for p in parts if not GENERIC_TITLE.match(p) and not re.search(r"\b(careers?|jobs? at|apply now)\b", p, re.I) and p.casefold() != company.casefold()]
    role = next((p for p in parts if ROLE_WORDS.search(p)), parts[0] if parts else "")
    role = re.sub(r"\s*\(?(req|requisition|job id)[^)]*\)?$", "", role, flags=re.I).strip()
    return role[:120] if len(role) > 5 and not GENERIC_TITLE.match(role) else ""


def fetch_page_title(url: str, company: str = "") -> str:
    """Read the posting's own title (JSON-LD JobPosting, og:title, then <title>). One polite request, 8s timeout."""
    host = urlsplit(url).netloc.lower()
    if host.endswith("linkedin.com"):
        return ""  # LinkedIn listings are only ever read by the user in their own visible session.
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Orbit local job-search dashboard; title lookup)", "Accept": "text/html"})
        with urlopen(req, timeout=8) as resp:
            body = resp.read(300_000).decode("utf-8", "ignore")
    except Exception:
        return ""
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', body, re.S | re.I):
        try:
            data = json.loads(unescape(block).strip())
        except ValueError:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if str(node.get("@type", "")).lower() == "jobposting" and node.get("title"):
                    return clean_page_title(str(node["title"]), company) or str(node["title"]).strip()[:120]
                stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
            elif isinstance(node, list):
                stack.extend(node)
    for pattern in (r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title', r"<title[^>]*>(.*?)</title>"):
        m = re.search(pattern, body, re.S | re.I)
        if m and clean_page_title(m.group(1), company):
            return clean_page_title(m.group(1), company)
    return ""


def enrich_titles(jobs: list[dict[str, Any]]) -> None:
    """Give tracker entries a real job title read from their link (cached, so re-exports stay polite)."""
    try:
        cache = json.loads(TITLE_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    changed = False
    for job in jobs:
        if job.get("category") != "Tracker entry" or not job.get("url"):
            continue
        key = url_key(job["url"])
        if key not in cache:
            cache[key] = fetch_page_title(job["url"], job["company"])
            changed = True
        if cache[key] and not GENERIC_TITLE.match(cache[key]):
            job["title"] = cache[key]
    if changed:
        TITLE_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def all_urls(ws: Any, row: int, cols: tuple[int, ...]) -> list[tuple[str, str]]:
    """Every URL in the given columns, with any label typed in front of it (P1:, without referral:)."""
    found = []
    for col in cols:
        cell = ws.cell(row, col)
        text = clean(cell.value)
        link = url_for(cell)
        urls = URL_IN_TEXT.findall(text)
        if link and link not in urls:
            urls = [link] + urls
        for u in urls[:1]:
            label = URL_IN_TEXT.sub("", text).strip(" :-·\n")
            found.append((u.rstrip("),.;"), label if len(label) < 50 else ""))
    return found


def note_company(companies: list[dict[str, Any]], name: str, sig: dict[str, Any]) -> None:
    """Record a row's status, tags and notes on the company itself (used by the Warm-up tab)."""
    comp = next((c for c in companies if c["name"].casefold() == name.casefold()), None)
    if comp is None:
        comp = {"name": name, "status": "", "contacts": []}
        companies.append(comp)
    comp["tags"] = list(dict.fromkeys(comp.get("tags", []) + sig["tags"]))
    if sig["notes"]:
        comp["notes"] = " · ".join(dict.fromkeys(filter(None, [comp.get("notes", "")] + sig["notes"])))
    if sig["status"] and STATUS_RANK[sig["status"]] >= STATUS_RANK.get(comp.get("tracking", ""), 0):
        comp["tracking"] = sig["status"]
        comp["trackingAt"] = sig.get("appliedAt") or comp.get("trackingAt", "")


def apply_company_tracker(ws: Any, jobs: list[dict[str, Any]], candidate: str,
                          companies: list[dict[str, Any]]) -> None:
    """Company tracker rows carry status text, notes and the links the user applied through."""
    by_url = {url_key(j["url"]): j for j in jobs if j.get("url")}
    comp = {c["name"].casefold(): c for c in companies}
    current = ""
    for r in range(2, ws.max_row + 1):
        name = cell_text(ws, r, 1)
        current = name or current
        if not current:
            continue
        sig = row_signals(ws, r, (2, 4, 6), (4, 6))
        links = all_urls(ws, r, (4, 6))
        if not (sig["status"] or sig["notes"] or sig["tags"] or links):
            continue
        company = comp.get(current.casefold())
        if company is not None:
            for key in ("tags",):
                company[key] = list(dict.fromkeys(company.get(key, []) + sig["tags"]))
            if sig["notes"]:
                company["notes"] = " · ".join(dict.fromkeys(filter(None, [company.get("notes", "")] + sig["notes"])))
            if sig["status"] and STATUS_RANK[sig["status"]] >= STATUS_RANK.get(company.get("tracking", ""), 0):
                company["tracking"] = sig["status"]
                company["trackingAt"] = sig["appliedAt"] or company.get("trackingAt", "")
        targets = []
        for url, label in links or [("", "")]:
            job = by_url.get(url_key(url)) if url else None
            if job is None and (sig["status"] in ("Applied", "Interviewing", "Watching")):
                title = (title_from_url(url) if url else "") or (f"Role at {current.strip().title()}" if url else f"Application at {current.strip().title()}")
                add_job(jobs, candidate, ws, r, current, title, "", url, "", category="Tracker entry")
                job = jobs[-1]
                if url:
                    by_url[url_key(url)] = job
            if job is not None:
                part = dict(sig)
                part["notes"] = list(sig["notes"]) + ([label] if label and label.lower() not in " ".join(sig["notes"]).lower() else [])
                merge_signal(job, part)
                targets.append(job)


def cell_text(ws: Any, row: int, col: int) -> str:
    return clean(ws.cell(row, col).value)


def add_job(out: list[dict[str, Any]], candidate: str, ws: Any, row: int, company: str,
            title: str, location: str = "", url: str = "", status: str = "",
            experience: str = "", compensation: str = "", notes: str = "",
            category: str = "Job", score: str = "", verification: str = "",
            applied_at: str = "", tags: list[str] | None = None) -> None:
    if not company and not title:
        return
    company = company.strip()
    title = title.strip()
    if not company:
        return
    rid = record_id(candidate, ws.title, row, company, title, url)
    out.append({
        "id": rid, "candidate": candidate, "company": company, "title": title or "Company opportunity",
        "location": location, "url": url, "status": status, "experience": experience,
        "compensation": compensation, "notes": notes, "category": category,
        "score": score, "verification": verification, "source_sheet": ws.title,
        "source_row": row, "appliedAt": applied_at, "tags": list(tags or []),
    })


def parse_company_tracker(wb: Any, candidate: str, sheet: str) -> list[dict[str, Any]]:
    ws = wb[sheet]
    companies: dict[str, dict[str, Any]] = {}
    current = ""
    for row in range(2, ws.max_row + 1):
        name = cell_text(ws, row, 1)
        status = cell_text(ws, row, 2)
        contact = cell_text(ws, row, 3)
        if name:
            current = name
            key = name.casefold()
            companies.setdefault(key, {"name": name, "status": "", "contacts": []})
        if not current:
            continue
        item = companies[current.casefold()]
        if status and not item["status"]:
            item["status"] = status
        if contact and contact.casefold() not in {c.casefold() for c in item["contacts"]}:
            item["contacts"].append(contact)
    return list(companies.values())


def parse_contacts_sheet(wb: Any, sheet: str, candidate: str, company_col: int,
                         name_col: int, title_col: int) -> list[dict[str, str]]:
    if sheet not in wb.sheetnames:
        return []
    ws = wb[sheet]
    contacts = []
    for row in range(2, ws.max_row + 1):
        company = cell_text(ws, row, company_col)
        name = cell_text(ws, row, name_col)
        title = cell_text(ws, row, title_col)
        if company or name or title:
            contacts.append({"company": company, "name": name, "title": title, "source_sheet": sheet})
    return contacts


def parse_vaanya(path: Path) -> dict[str, Any]:
    wb = load_workbook(path, data_only=False, read_only=False)
    candidate = "Vaanya"
    companies = parse_company_tracker(wb, candidate, "Tracker") if "Tracker" in wb.sheetnames else []
    contacts = []
    for c in companies:
        contacts.extend({"company": c["name"], "name": n, "title": "", "source_sheet": "Tracker"}
                        for n in c["contacts"])
    jobs: list[dict[str, Any]] = []
    if "Job Links" in wb.sheetnames:
        ws = wb["Job Links"]
        current = ""
        for r in range(2, ws.max_row + 1):
            current = cell_text(ws, r, 1) or current
            title = cell_text(ws, r, 2)
            sig = row_signals(ws, r, (4, 5, 6, 7), (2, 4, 5, 6, 7))
            if not title:
                if jobs and (sig["status"] or sig["notes"] or sig["tags"]):
                    merge_signal(jobs[-1], sig)  # continuation row: attach to the role above
                continue
            add_job(jobs, candidate, ws, r, current, title, cell_text(ws, r, 3),
                    url_for(ws.cell(r, 2)) or sig["url"], sig["status"], experience=sig["experience"],
                    notes=drop_dupes(sig["notes"], title), category="Job link",
                    applied_at=sig["appliedAt"], tags=sig["tags"])
    if "Eligible role" in wb.sheetnames:
        ws = wb["Eligible role"]
        for r in range(2, ws.max_row + 1):
            if not cell_text(ws, r, 2):
                continue
            add_job(jobs, candidate, ws, r, cell_text(ws, r, 1), cell_text(ws, r, 2),
                    cell_text(ws, r, 3), url_for(ws.cell(r, 5)), cell_text(ws, r, 4),
                    category="Eligible role")
    for sheet in ("Wave 9", "Wave 10"):
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        for r in range(2, ws.max_row + 1):
            if not cell_text(ws, r, 3):
                continue
            add_job(jobs, candidate, ws, r, cell_text(ws, r, 2), cell_text(ws, r, 3),
                    cell_text(ws, r, 4), url_for(ws.cell(r, 12)), cell_text(ws, r, 10),
                    cell_text(ws, r, 6), cell_text(ws, r, 8), cell_text(ws, r, 13),
                    "Verified wave role", cell_text(ws, r, 9), cell_text(ws, r, 11))
    if "Fresher Hiring Drives" in wb.sheetnames:
        ws = wb["Fresher Hiring Drives"]
        for r in range(2, ws.max_row + 1):
            if not cell_text(ws, r, 2):
                continue
            window = cell_text(ws, r, 4)
            add_job(jobs, candidate, ws, r, cell_text(ws, r, 1), cell_text(ws, r, 2),
                    cell_text(ws, r, 3), url_for(ws.cell(r, 5)), "",
                    notes="Hiring program / campus drive" + (f" · Application window: {window}" if window else ""),
                    category="Hiring drive")
    jobs = deduplicate_jobs(jobs)
    if not companies:
        seen: set[str] = set()
        for job in jobs:
            key = job["company"].casefold()
            if key not in seen:
                companies.append({"name": job["company"], "status": "", "contacts": []})
                seen.add(key)
    return {"candidate": candidate, "companies": companies, "contacts": contacts, "jobs": jobs}


def parse_vrinda(path: Path) -> dict[str, Any]:
    wb = load_workbook(path, data_only=False, read_only=False)
    candidate = "Vrinda"
    companies = parse_company_tracker(wb, candidate, "Sheet1")
    contacts = parse_contacts_sheet(wb, "Bhaiya contacts", candidate, 1, 2, 3)
    jobs: list[dict[str, Any]] = []
    if "Job Links" in wb.sheetnames:
        ws = wb["Job Links"]
        current = ""
        for r in range(1, ws.max_row + 1):
            current = cell_text(ws, r, 1) or current
            title = cell_text(ws, r, 2)
            if not title:
                continue
            sig = row_signals(ws, r, (4, 5, 6, 7, 8, 9), (5, 4, 6, 7))
            location = cell_text(ws, r, 3)
            if EXPERIENCE_RE.match(location):  # some rows put the experience range where the place goes
                sig["experience"] = sig["experience"] or location
                location = ""
            add_job(jobs, candidate, ws, r, current, title, location,
                    sig["url"], sig["status"], experience=sig["experience"],
                    notes=drop_dupes(sig["notes"], title), category="Job link",
                    applied_at=sig["appliedAt"], tags=sig["tags"])
    if "Warm-up" in wb.sheetnames:
        ws = wb["Warm-up"]
        current = ""
        for r in range(2, ws.max_row + 1):
            company = cell_text(ws, r, 1)
            current = company or current
            title = cell_text(ws, r, 2)
            sig = row_signals(ws, r, (8, 9, 10), (6,))
            referral = cell_text(ws, r, 7)
            if referral and not PLACEHOLDER_RE.match(referral):
                found = classify_status(referral)
                if found:
                    sig["status"] = sig["status"] or found["status"]
                    sig["appliedAt"] = sig["appliedAt"] or found.get("appliedAt", "")
                    sig["tags"] += [t for t in found["tags"] if t not in sig["tags"]]
                    if referral.lower() != "applied":
                        sig["notes"].append(referral)
                elif re.match(r"^active (hiring|careers)$", referral, re.I):
                    sig["tags"].append("Active hiring")
                elif current:
                    contacts.append({"company": current, "name": referral, "title": "Referral contact", "source_sheet": "Warm-up"})
            if current and (sig["status"] or sig["tags"] or sig["notes"]):
                note_company(companies, current, sig)
            if not title:
                if not company and jobs and (sig["status"] or sig["notes"] or sig["tags"]):
                    merge_signal(jobs[-1], sig)  # continuation row: attach to the role above
                elif company and (sig["status"] or sig["notes"]):
                    add_job(jobs, candidate, ws, r, current, "Role not named in your sheet", cell_text(ws, r, 3), sig["url"], sig["status"],
                            notes=drop_dupes(sig["notes"], title), category="Warm-up lead", applied_at=sig["appliedAt"], tags=sig["tags"])
                continue
            add_job(jobs, candidate, ws, r, current, title, cell_text(ws, r, 3), sig["url"], sig["status"],
                    compensation=cell_text(ws, r, 5), notes=drop_dupes(sig["notes"], title), category="Warm-up lead",
                    applied_at=sig["appliedAt"], tags=sig["tags"])
    for sheet, cols in (("past wave", (3,4,5,6,8,9,11,12,13)),
                        ("Wave 8", (2,3,4,5,7,9,10,11,12)),
                        ("Wave 9", (2,3,4,5,7,9,10,11,12))):
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        company_col,title_col,loc_col,exp_col,pay_col,tier_col,verification_col,url_col,notes_col = cols
        for r in range(2, ws.max_row + 1):
            if not cell_text(ws, r, title_col):
                continue
            add_job(jobs, candidate, ws, r, cell_text(ws, r, company_col), cell_text(ws, r, title_col),
                    cell_text(ws, r, loc_col), url_for(ws.cell(r, url_col)), cell_text(ws, r, tier_col),
                    cell_text(ws, r, exp_col), cell_text(ws, r, pay_col), cell_text(ws, r, notes_col),
                    "Historical / wave role", "", cell_text(ws, r, verification_col))
    if "Sheet1" in wb.sheetnames:
        apply_company_tracker(wb["Sheet1"], jobs, candidate, companies)
    enrich_titles(jobs)
    # Company matching joins exact workbook names to the contacts without collecting any network data.
    aliases = {c["name"].casefold(): c for c in companies}
    for contact in contacts:
        k = contact["company"].casefold()
        if k not in aliases:
            companies.append({"name": contact["company"], "status": "", "contacts": []})
            aliases[k] = companies[-1]
        if contact["name"] and contact["name"].casefold() not in {x.casefold() for x in aliases[k]["contacts"]}:
            aliases[k]["contacts"].append(contact["name"])
    jobs = deduplicate_jobs(jobs)
    return {"candidate": candidate, "companies": companies, "contacts": contacts, "jobs": jobs}
