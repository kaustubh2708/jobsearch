#!/usr/bin/env python3
"""Repair the current master dataset without fabricating evidence."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from eligibility_rules import parse_experience_requirement
from linkedin_freshness import extract_linkedin_freshness

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
INPUT = DATA / "jobs.json"
AUDIT = DATA / "audit_companies_links_final.json"
LINKEDIN = DATA / "linkedin_detailed_discovered.json"
OUTPUT = DATA / "jobs_repaired.json"
REPORT = DATA / "last_run_repaired.md"


def canon(url: str | None) -> str:
    return (url or "").strip().rstrip("/")


def extract_job_id(url: str, skills: list[str]) -> str | None:
    for value in skills or []:
        s = str(value).strip()
        if re.fullmatch(r"[0-9]{5,}", s) or re.fullmatch(r"[A-Za-z]{1,5}\d{4,}", s) or re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{20,}", s, re.I):
            return s
    for pattern in (r"/jobs/view/(\d+)", r"/jobs/(\d+)", r"gh_jid=(\d+)", r"_([A-Z]{0,4}\d{5,})(?:[/?#]|$)"):
        match = re.search(pattern, url or "", re.I)
        if match:
            return match.group(1)
    return None


def is_generic(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/").lower()
    return path in {"", "/jobs", "/careers", "/search", "/jobs/search"}


def source_type(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "linkedin.com" in host:
        return "public_job_post"
    if any(x in host for x in ("indeed.com", "naukri.com", "instahyre.com", "wellfound.com")):
        return "third_party"
    return "official_career_page"


def main() -> None:
    rows = json.loads(INPUT.read_text())
    audit_rows = json.loads(AUDIT.read_text()) if AUDIT.exists() else []
    linkedin_rows = json.loads(LINKEDIN.read_text()) if LINKEDIN.exists() else []
    audit_by_url = {}
    for row in audit_rows:
        for key in ("url", "final_url"):
            if row.get(key):
                audit_by_url[canon(row[key])] = row
    linkedin_by_id = {str(x.get("job_id")): x for x in linkedin_rows if x.get("job_id")}
    now = datetime.now(timezone.utc).isoformat()
    repaired = []
    counters = {"audited_active": 0, "downgraded_unverified": 0, "deduped": 0}

    for original in rows:
        j = dict(original)
        url = canon(j.get("canonical_source_url") or j.get("original_source_url") or j.get("source_url"))
        j["original_source_url"] = j.get("original_source_url") or url
        j["canonical_source_url"] = url
        j["source_url"] = url
        j["source_url_original"] = j.get("source_url_original") or j["original_source_url"]
        j["source_url_canonical"] = url
        j["source_type"] = source_type(url)
        j["source_url_is_direct"] = not is_generic(url)

        skills = j.get("skills") if isinstance(j.get("skills"), list) else []
        jid = j.get("job_id") or extract_job_id(url, skills)
        if jid is None:
            jid = "internal:discovery:" + hashlib.sha1((j.get("company", "") + "|" + url).encode()).hexdigest()[:12]
        j["job_id"] = str(jid)
        if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{20,}", j["job_id"], re.I):
            j["job_id"] = "internal:" + j["job_id"]
        if skills and len(skills) == 1 and str(skills[0]) == str(jid):
            j["skills"] = []

        # Repair the known parser column shift: a discovery strategy was stored
        # as location and the real location was stored as experience text.
        if str(j.get("location", "")).lower().startswith("strategy "):
            actual_location = str(j.get("experience_required") or "").strip()
            j["location"] = actual_location or "India / location unknown"
            j["experience_required"] = "experience_unknown"
        exp_text = str(j.get("experience_required") or "")
        if exp_text.lower().startswith("strategy "):
            exp_text = "experience_unknown"
        parsed = parse_experience_requirement(exp_text + " " + str(j.get("verification_reason") or ""))
        j["experience_required"] = exp_text
        j["experience_min_years_detected"] = parsed["min_years"]
        j["experience_max_years_detected"] = parsed["max_years"]

        lid = extract_job_id(url, [])
        lrow = linkedin_by_id.get(str(lid)) if lid else None
        if lrow:
            for key in ("linkedin_posted_at", "linkedin_age_days", "linkedin_age_flag", "linkedin_open_status", "linkedin_age_source_text", "linkedin_age_checked_at"):
                j[key] = lrow.get(key)
        else:
            j.update(extract_linkedin_freshness(j.get("notes", ""), datetime.now(timezone.utc)))

        ar = audit_by_url.get(url)
        if ar and ar.get("http_status") == 200 and ar.get("is_active") is True:
            audited_final = canon(ar.get("final_url") or ar.get("url"))
            # A LinkedIn/aggregator discovery can become an official record
            # only after the audit resolves it to the employer/ATS page.
            j["source_type"] = source_type(audited_final)
            j["source_url_is_direct"] = True
            j.update({
                "http_status": 200,
                "actual_http_status": 200,
                "application_form_visible": True,
                "page_title_actual": ar.get("title"),
                "page_company_actual": ar.get("company"),
                "page_location_actual": ar.get("location"),
                "page_job_id_actual": str(ar.get("job_id") or j["job_id"]),
                "final_url_after_redirect": audited_final,
                "checked_at": now,
                "live_check_method": "independent_company_link_audit",
                "verification_status": "verified",
                "link_status": "active_exact",
                "needs_verification": False,
                "verification_reason": ar.get("reason") or "Independent page-level audit returned HTTP 200 and an active application route.",
            })
            counters["audited_active"] += 1
        else:
            j["verification_status"] = "lead"
            j["needs_verification"] = True
            j["link_status"] = "generic_portal" if is_generic(url) else "unknown"
            j["http_status"] = None
            j["actual_http_status"] = None
            j["application_form_visible"] = None
            j["verification_reason"] = "Discovered URL retained, but no matching independent page-level evidence was found."
            counters["downgraded_unverified"] += 1

        if j.get("match_label") == "strong_match" and j.get("verification_status") != "verified":
            j["match_label"] = "potential_match" if (j.get("overall_match_score") or 0) >= 65 else "stretch"
        j["last_verified_at"] = now if j.get("verification_status") == "verified" else j.get("last_verified_at") or ""
        j["checked_at"] = j.get("checked_at") or now
        j["status"] = j.get("status") or "new"
        if not j.get("salary_sources") and not j.get("market_salary_estimate") and not j.get("employer_published_salary"):
            j["salary_status"] = "unknown"
            j["salary_fit"] = "unknown"
        repaired.append(j)

    selected = {}
    for j in repaired:
        key = canon(j.get("canonical_source_url")) or (j.get("company", "") + "|" + j.get("job_id", ""))
        old = selected.get(key)
        rank = (j.get("verification_status") == "verified", bool(j.get("job_id")))
        old_rank = (old.get("verification_status") == "verified", bool(old.get("job_id"))) if old else (-1, -1)
        if old is not None:
            counters["deduped"] += 1
        if old is None or rank > old_rank:
            selected[key] = j
    repaired = list(selected.values())
    OUTPUT.write_text(json.dumps(repaired, indent=2, ensure_ascii=False))
    REPORT.write_text(
        f"# Repaired current job-search dataset\n\nGenerated: {now}\n\n"
        f"- Input records: {len(rows)}\n- Output records: {len(repaired)}\n"
        f"- Independently audited active records retained: {counters['audited_active']}\n"
        f"- Unverified discoveries downgraded to leads: {counters['downgraded_unverified']}\n"
        f"- Duplicate records removed by canonical URL: {counters['deduped']}\n\n"
        "Only records with independent page-level evidence remain `verified` / `active_exact`.\n"
        "Third-party and LinkedIn discoveries remain leads until verified on the employer or ATS page.\n"
    )
    print(json.dumps({"input": len(rows), "output": len(repaired), **counters}, indent=2))


if __name__ == "__main__":
    main()
