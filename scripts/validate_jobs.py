#!/usr/bin/env python3
"""Strict Validator for Vrinda Job Records.

Enforces schema compliance, direct source URLs, verified statuses,
authentic job IDs (internal: prefixes), source type integrity,
link status classification, 7-component fit scoring, and salary research evidence.
Supports both the repaired final schema (config/job.schema.json) and legacy datasets.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Fields required for repaired schema (config/job.schema.json)
REQUIRED_REPAIRED = {
    "company",
    "title",
    "location",
    "original_source_url",
    "canonical_source_url",
    "link_status",
    "source_url_is_direct",
    "source_type",
    "verification_status",
    "needs_verification",
    "checked_at",
    "verification_reason",
    "salary_status",
    "salary_fit",
    "role_fit_score",
    "experience_or_batch_fit_score",
    "skill_fit_score",
    "location_fit_score",
    "source_evidence_score",
    "salary_fit_score",
    "freshness_score",
    "overall_match_score",
    "match_label",
    "status",
}

# Legacy required fields
REQUIRED_LEGACY = {
    "company",
    "title",
    "location",
    "source_url",
    "source_type",
    "retrieved_at",
    "match_label",
    "match_score",
    "status",
    "needs_verification",
}

# Intermediate 5-stage required fields
REQUIRED_INTERMEDIATE = {
    "company",
    "title",
    "location",
    "source_url",
    "source_url_is_direct",
    "source_type",
    "retrieved_at",
    "verification_status",
    "match_label",
    "match_score",
    "role_match_score",
    "experience_fit_score",
    "skill_fit_score",
    "location_fit_score",
    "salary_fit",
    "evidence_quality",
    "status",
    "needs_verification",
    "last_verified_at",
}

ALLOWED_SOURCE_TYPES = {
    "official_career_page",
    "official_job_board",
    "public_job_post",
    "third_party",
}

ALLOWED_STATUSES = {
    "new",
    "needs_review",
    "shortlisted",
    "rejected",
    "closed",
    "applied_by_user",
}

ALLOWED_VERIFICATION_STATUSES = {
    "verified",
    "lead",
    "stale",
    "closed",
    "stale_or_closed",
    "not_eligible",
    "not_relevant",
    "blocked_manual_review",
    "blocked_manual_check",
    "browser_manual_check",
    "rejected",
}

ALLOWED_SALARY_STATUSES = {
    "confirmed_published",
    "estimated_market",
    "confirmed",
    "estimated",
    "unknown",
    "not_applicable",
}

ALLOWED_SALARY_FITS = {
    "confirmed",
    "estimated",
    "unknown",
    "below_target",
    "estimated_above_target",
    "estimated_below_target",
    "published_above_target",
}

ALLOWED_LINK_STATUSES = {
    "active_exact",
    "active_canonical_redirect",
    "generic_portal",
    "dead_404",
    "gone_410",
    "blocked_403",
    "browser_manual_check",
    "connection_failed",
    "expired_or_closed",
    "unknown",
}

ALLOWED_EVIDENCE_QUALITIES = {
    "high",
    "medium",
    "low",
}

ALLOWED_MATCH_LABELS = {
    "strong_match",
    "potential_match",
    "stretch",
    "exclude",
}

THIRD_PARTY_DOMAINS = {
    "instahyre.com",
    "naukri.com",
    "cutshort.io",
    "wellfound.com",
    "hirist.com",
    "hirist.tech",
    "indeed.com",
    "efinancialcareers.com",
    "simplyhired.co.in",
    "jobaaj.com",
}

GENERIC_PATH_PATTERN = re.compile(
    r"^(/careers/?|/jobs/?|/page/careers/?|/join-us/?|/open-roles/?|/company/careers/?|/positions/?|/cmp/[^/]+/jobs/?)$",
    re.IGNORECASE,
)

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){2,}$")


def is_synthetic_job_id(job_id: str) -> bool:
    """Detect if a job ID appears to be an invented human/agent slug instead of an employer ID."""
    jid = str(job_id).strip()
    if jid.startswith("internal:"):
        return False
    if re.match(r"^(R|JR|REQ|P|JOB|DEV|GOOG|SR|BCN)?[0-9A-Z_-]+$", jid, re.IGNORECASE):
        if SLUG_PATTERN.match(jid):
            return True
        return False
    return True


def key_for(job: dict) -> tuple[str, str, str, str]:
    def norm(value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().lower())

    return (
        norm(job.get("company")),
        norm(job.get("title")),
        norm(job.get("location")),
        norm(job.get("job_id")),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", default="data/jobs_vrinda_repaired_final.json")
    parser.add_argument("--legacy", action="store_true", help="Validate against legacy schema")
    args = parser.parse_args()
    path = Path(args.jobs)

    try:
        jobs = json.loads(path.read_text())
    except Exception as exc:
        print(f"ERROR: could not read {path}: {exc}")
        return 2

    if not isinstance(jobs, list):
        print("ERROR: jobs file must contain a JSON array")
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    seen: set[tuple[str, str, str, str]] = set()

    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            errors.append(f"#{index}: record is not an object")
            continue

        c_name = job.get("company", "Unknown")
        title = job.get("title", "Unknown")
        label = f"#{index} [{c_name} - {title}]"

        # Determine schema profile
        is_repaired = "overall_match_score" in job and "canonical_source_url" in job
        is_intermediate = "role_match_score" in job and not is_repaired

        # 1. Required fields
        if args.legacy:
            req_fields = REQUIRED_LEGACY
        elif is_repaired:
            req_fields = REQUIRED_REPAIRED
        elif is_intermediate:
            req_fields = REQUIRED_INTERMEDIATE
        else:
            req_fields = REQUIRED_LEGACY

        missing = sorted(req_fields - job.keys())
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")

        if args.legacy:
            if job.get("source_type") not in ALLOWED_SOURCE_TYPES:
                errors.append(f"{label}: invalid source_type")
            if job.get("status") not in ALLOWED_STATUSES:
                errors.append(f"{label}: invalid status")
            if not isinstance(job.get("match_score"), int) or not 0 <= job.get("match_score", -1) <= 100:
                errors.append(f"{label}: match_score must be an integer from 0 to 100")
            key = key_for(job)
            if key in seen:
                errors.append(f"{label}: duplicate key")
            seen.add(key)
            continue

        # 2. Enum field validations
        if job.get("source_type") not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{label}: invalid source_type '{job.get('source_type')}'")
        if job.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{label}: invalid status '{job.get('status')}'")
        if job.get("verification_status") not in ALLOWED_VERIFICATION_STATUSES:
            errors.append(f"{label}: invalid verification_status '{job.get('verification_status')}'")
        if job.get("salary_status") and job.get("salary_status") not in ALLOWED_SALARY_STATUSES:
            errors.append(f"{label}: invalid salary_status '{job.get('salary_status')}'")
        if job.get("salary_fit") not in ALLOWED_SALARY_FITS:
            errors.append(f"{label}: invalid salary_fit '{job.get('salary_fit')}'")
        if job.get("evidence_quality") and job.get("evidence_quality") not in ALLOWED_EVIDENCE_QUALITIES:
            errors.append(f"{label}: invalid evidence_quality '{job.get('evidence_quality')}'")
        if job.get("match_label") not in ALLOWED_MATCH_LABELS:
            errors.append(f"{label}: invalid match_label '{job.get('match_label')}'")
        if job.get("link_status") and job.get("link_status") not in ALLOWED_LINK_STATUSES:
            errors.append(f"{label}: invalid link_status '{job.get('link_status')}'")

        # 3. Numeric scores & component audit
        if is_repaired:
            score_components = [
                ("role_fit_score", 25),
                ("experience_or_batch_fit_score", 20),
                ("skill_fit_score", 20),
                ("location_fit_score", 10),
                ("source_evidence_score", 5),
                ("salary_fit_score", 15),
                ("freshness_score", 5),
            ]
            computed_sum = 0
            for skey, smax in score_components:
                sval = job.get(skey)
                if not isinstance(sval, int) or not (0 <= sval <= smax):
                    errors.append(f"{label}: {skey} must be an integer between 0 and {smax}")
                else:
                    computed_sum += sval

            overall = job.get("overall_match_score")
            if not isinstance(overall, int) or not (0 <= overall <= 100):
                errors.append(f"{label}: overall_match_score must be an integer between 0 and 100")
            elif overall != computed_sum:
                errors.append(f"{label}: overall_match_score ({overall}) does not equal sum of 7 components ({computed_sum})")
        else:
            for score_key, max_score in [
                ("match_score", 100),
                ("role_match_score", 30),
                ("experience_fit_score", 20),
                ("skill_fit_score", 20),
                ("location_fit_score", 10),
            ]:
                val = job.get(score_key)
                if not isinstance(val, int) or not 0 <= val <= max_score:
                    errors.append(f"{label}: {score_key} must be an integer between 0 and {max_score}")

        # 4. Source URL Checks
        check_urls = [job.get("canonical_source_url") or job.get("source_url")]
        for u in check_urls:
            if not u:
                continue
            parsed = urlparse(str(u).strip())
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append(f"{label}: URL '{u}' is not a valid HTTP(S) URL")

            netloc_lower = parsed.netloc.lower()
            path_lower = parsed.path.lower()

            # Check LinkedIn forbidden routes
            if "linkedin.com" in netloc_lower:
                if "/in/" in path_lower or "/search/results/people" in path_lower:
                    errors.append(f"{label}: LinkedIn profile/people-search URL is prohibited: '{u}'")

            # Check third-party marked official
            is_third_party_domain = any(domain in netloc_lower for domain in THIRD_PARTY_DOMAINS)
            if is_third_party_domain and job.get("source_type") != "third_party":
                errors.append(
                    f"{label}: URL is on third-party aggregator '{parsed.netloc}' but source_type is '{job.get('source_type')}' (must be 'third_party')"
                )

            # Check generic career URLs
            is_generic_url = bool(GENERIC_PATH_PATTERN.match(path_lower)) or path_lower in {"", "/"}
            if is_generic_url or job.get("link_status") == "generic_portal":
                if job.get("source_url_is_direct") is True:
                    errors.append(f"{label}: generic career URL '{u}' cannot have source_url_is_direct=true")
                if job.get("verification_status") == "verified":
                    errors.append(f"{label}: generic career URL '{u}' cannot have verification_status=verified (must be 'lead')")

        if job.get("source_url_is_direct") is False and job.get("verification_status") == "verified":
            errors.append(f"{label}: cannot be verification_status='verified' when source_url_is_direct=false")

        # Page-level evidence is required for an active exact/verified record.
        # A direct-looking URL, API result, or LinkedIn card is discovery only.
        if job.get("link_status") == "active_exact" or job.get("verification_status") == "verified":
            required_evidence = {
                "actual_http_status": job.get("actual_http_status", job.get("http_status")),
                "application_form_visible": job.get("application_form_visible"),
                "page_title_actual": job.get("page_title_actual", job.get("page_title")),
                "page_company_actual": job.get("page_company_actual"),
                "page_location_actual": job.get("page_location_actual"),
                "page_job_id_actual": job.get("page_job_id_actual"),
            }
            missing_evidence = [k for k, v in required_evidence.items() if v in (None, "", False)]
            if missing_evidence:
                errors.append(f"{label}: active/verified record lacks page evidence: {', '.join(missing_evidence)}")
            if required_evidence["actual_http_status"] != 200:
                errors.append(f"{label}: active/verified record must have actual HTTP 200")
            if job.get("needs_verification") is True:
                errors.append(f"{label}: active/verified record cannot still have needs_verification=true")
            if job.get("source_type") == "third_party":
                errors.append(f"{label}: third-party discovery cannot be counted as verified active without canonical employer evidence")

        # 5. Job ID Checks
        job_id = job.get("job_id")
        if job_id is not None:
            jid_str = str(job_id).strip()
            if is_synthetic_job_id(jid_str):
                errors.append(
                    f"{label}: invented/slug job_id '{jid_str}' must be prefixed with 'internal:' (e.g. 'internal:{jid_str}')"
                )

        # 6. Salary & Salary Estimate Checks
        m_estimate = job.get("market_salary_estimate") or job.get("salary_estimate")
        if m_estimate is not None:
            if not isinstance(m_estimate, dict):
                errors.append(f"{label}: market_salary_estimate must be an object or null")

        # 7. Strong Match Constraint Checks
        if job.get("match_label") == "strong_match":
            if job.get("verification_status") != "verified":
                errors.append(
                    f"{label}: cannot be labelled 'strong_match' when verification_status is '{job.get('verification_status')}' (must be 'verified')"
                )
            if job.get("salary_fit") in {"below_target", "estimated_below_target"}:
                errors.append(f"{label}: cannot be labelled 'strong_match' when salary_fit is below target")

        # 8. Needs verification consistency
        if job.get("source_type") == "third_party" and not job.get("needs_verification"):
            warnings.append(f"{label}: third-party source should normally have needs_verification=true")
        if job.get("verification_status") == "lead" and not job.get("needs_verification"):
            errors.append(f"{label}: verification_status='lead' must have needs_verification=true")

        # 9. Deduplication check
        key = key_for(job)
        if key in seen:
            errors.append(f"{label}: duplicate company/title/location/job_id key")
        seen.add(key)

    print("=" * 60)
    print(f"Strict Validator Report for: {path}")
    print(f"Total Records Evaluated: {len(jobs)}")
    print(f"Validation Errors: {len(errors)}")
    print(f"Validation Warnings: {len(warnings)}")
    print("=" * 60)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if not errors and not warnings:
        print("ALL CHECKS PASSED: Zero errors, zero warnings.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
