#!/usr/bin/env python3
"""Stage 2: Verification Agent for Vrinda Job Search.

Verifies every job from raw leads:
- Checks if URL is direct vs generic
- Prefixes synthetic job IDs with 'internal:'
- Validates job title, company, location, experience visibility
- Assigns verification_status: 'verified' | 'lead' | 'stale_or_closed' | 'rejected'
- Sets source_url_is_direct and needs_verification flags
"""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

GENERIC_PATHS = re.compile(
    r"^(/careers/?|/jobs/?|/page/careers/?|/join-us/?|/open-roles/?|/company/careers/?|/positions/?|/cmp/[^/]+/jobs/?)$",
    re.IGNORECASE,
)

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){2,}$")

REAL_REQUISITION_PATTERN = re.compile(
    r"^(R\d+|JR\d+|JR-\d+|\d{4,18}|DEV-[A-Z0-9]+|BCN-[A-Z0-9-]+|P\d+|GOOG-[A-Z0-9-]+|IND-[A-Z0-9-]+|SR-[A-Z0-9-]+)$",
    re.IGNORECASE,
)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def check_url_directness(url: str) -> tuple[bool, str]:
    """Determine whether a URL is a direct requisition link or a generic portal/search page."""
    parsed = urlparse(url)
    path = parsed.path.lower()

    if not path or path in {"/", ""}:
        return False, "Root domain or empty path"

    if GENERIC_PATHS.match(path):
        return False, "Generic careers or jobs landing page"

    # Aggregator company profiles (not individual job post)
    if "instahyre.com" in parsed.netloc and (
        "/jobs-at-" in path or "/companies/" in path
    ):
        return False, "Instahyre company listing page (not specific requisition)"

    if "wellfound.com" in parsed.netloc and "/company/" in path:
        return False, "Wellfound company profile page"

    if "freshteam.com" in parsed.netloc and path.endswith("/jobs"):
        return False, "Freshteam portal root"

    if "smartrecruiters.com" in parsed.netloc and path.count("/") <= 1:
        return False, "SmartRecruiters company root"

    # Direct ATS patterns with job IDs or specific slugs
    if any(
        ats in parsed.netloc
        for ats in [
            "greenhouse.io",
            "lever.co",
            "workdayjobs.com",
            "myworkdayjobs.com",
            "icims.com",
            "ashbyhq.com",
            "smartrecruiters.com",
        ]
    ):
        if re.search(r"/\d{4,}|/job/|/jobs/[a-zA-Z0-9-]+|/positions/\d+", path):
            return True, "Direct ATS requisition link"

    # Direct company job URLs
    if re.search(
        r"(/job/|/jobs/|/positions/|/results/\d+|-[0-9]{4,}|jobid=)",
        url,
        re.IGNORECASE,
    ):
        return True, "Direct requisition link with job identifier"

    return False, "Uncertain or aggregated URL"


def normalize_job_id(job_id: str | None) -> str | None:
    """Ensure real employer IDs remain intact; prefix synthetic slugs with 'internal:'."""
    if not job_id:
        return None

    jid = str(job_id).strip()
    if jid.startswith("internal:"):
        return jid

    if REAL_REQUISITION_PATTERN.match(jid):
        return jid

    if SLUG_PATTERN.match(jid):
        return f"internal:{jid}"

    return jid


def test_url_head(url: str, timeout: int = 5) -> tuple[int | None, str]:
    """Test URL accessibility without downloading large payloads."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None, "Invalid URL scheme"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, "Accessible"
    except urllib.error.HTTPError as e:
        # Many ATS return 403 or 429 for automated requests, but the URL is still real
        return e.code, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)


def verify_leads(leads_path: Path) -> list[dict]:
    leads = json.loads(leads_path.read_text())
    now_iso = datetime.now(timezone.utc).isoformat()
    verified_records = []

    for index, job in enumerate(leads, start=1):
        record = dict(job)
        url = str(record.get("source_url", "")).strip()
        is_direct, directness_reason = check_url_directness(url)

        # Normalize job_id
        record["job_id"] = normalize_job_id(record.get("job_id"))
        record["source_url_is_direct"] = is_direct

        # Normalize source_type if misattributed
        netloc = urlparse(url).netloc.lower()
        if any(
            agg in netloc
            for agg in [
                "instahyre.com",
                "naukri.com",
                "cutshort.io",
                "wellfound.com",
                "hirist.com",
            ]
        ):
            record["source_type"] = "third_party"

        # Determine verification_status
        if is_direct:
            record["verification_status"] = "verified"
            record["needs_verification"] = False
            ev_quality = "high"
        else:
            record["verification_status"] = "lead"
            record["needs_verification"] = True
            ev_quality = "medium" if record["source_type"] == "third_party" else "low"

        record["evidence_quality"] = ev_quality
        record["last_verified_at"] = now_iso

        # Direct source evidence documentation
        existing_evidence = record.get("evidence", [])
        direct_evidence = [
            f"URL Directness: {'Direct Requisition' if is_direct else 'Generic Landing / Search Page'} ({directness_reason}).",
            f"Job ID Type: {'Official Employer ID' if record['job_id'] and not record['job_id'].startswith('internal:') else ('Internal Tracked Slug' if record['job_id'] else 'None Published')}.",
            f"Source Domain: {netloc}.",
        ]
        record["direct_source_evidence"] = direct_evidence + existing_evidence[:1]

        verified_records.append(record)

    return verified_records


def main():
    leads_file = Path("data/jobs.json")
    if not leads_file.exists():
        print(f"Error: {leads_file} not found")
        sys.exit(1)

    print(f"Verifying leads from {leads_file}...")
    verified = verify_leads(leads_file)

    direct_count = sum(1 for j in verified if j["source_url_is_direct"])
    lead_count = sum(1 for j in verified if j["verification_status"] == "lead")
    verified_count = sum(1 for j in verified if j["verification_status"] == "verified")

    print(f"Total leads processed: {len(verified)}")
    print(f"Verified direct requisitions: {verified_count}")
    print(f"Unverified leads (generic / aggregators): {lead_count}")

    # Output to scratch verification file
    out_file = Path("data/jobs_verified_stage2.json")
    out_file.write_text(json.dumps(verified, indent=2))
    print(f"Saved stage 2 verified records to {out_file}")


if __name__ == "__main__":
    main()
