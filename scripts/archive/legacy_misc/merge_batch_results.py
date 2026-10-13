#!/usr/bin/env python3
"""Helper script to merge new job listings and company audit statuses."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

REQUIRED = {
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-file", required=True, help="JSON file with batch results")
    args = parser.parse_args()

    batch_path = Path(args.batch_file)
    if not batch_path.exists():
        print(f"Error: {batch_path} not found")
        sys.exit(1)

    batch = json.loads(batch_path.read_text())
    # batch should have: {"new_jobs": [...], "company_updates": [...]}

    jobs_path = Path("data/jobs.json")
    jobs = json.loads(jobs_path.read_text()) if jobs_path.exists() else []

    audit_path = Path("data/companies_audit.json")
    audit_list = json.loads(audit_path.read_text()) if audit_path.exists() else []
    audit_map = {c["company"]: c for c in audit_list}

    # Existing jobs set by key (company, title, location, job_id)
    seen_jobs = {
        (
            str(j.get("company", "")).strip().lower(),
            str(j.get("title", "")).strip().lower(),
            str(j.get("location", "")).strip().lower(),
            str(j.get("job_id", "")).strip().lower(),
        )
        for j in jobs
    }

    added_jobs_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for job in batch.get("new_jobs", []):
        key = (
            str(job.get("company", "")).strip().lower(),
            str(job.get("title", "")).strip().lower(),
            str(job.get("location", "")).strip().lower(),
            str(job.get("job_id", "")).strip().lower(),
        )
        if key in seen_jobs:
            print(f"Skipping duplicate: {key}")
            continue

        # Fill defaults
        job.setdefault("job_id", None)
        job.setdefault("experience_required", None)
        job.setdefault("skills", [])
        job.setdefault("posted_at", None)
        job.setdefault("deadline", None)
        job.setdefault("salary_base_lpa", None)
        job.setdefault("salary_status", "unknown")
        job.setdefault("status", "new")
        job.setdefault("retrieved_at", now_iso)
        job.setdefault("last_verified_at", now_iso)
        job.setdefault("notes", "")

        # Source verification
        if job.get("source_type") == "third_party":
            job["needs_verification"] = True
        else:
            job.setdefault("needs_verification", False)

        # Basic check
        missing = REQUIRED - job.keys()
        if missing:
            print(f"Error: Missing fields {missing} in job {job.get('title')}")
            continue

        jobs.append(job)
        seen_jobs.add(key)
        added_jobs_count += 1

        # Update company audit status
        c_name = job["company"]
        if c_name in audit_map:
            audit_map[c_name]["status"] = "openings_found"
            audit_map[c_name]["openings_count"] = audit_map[c_name].get("openings_count", 0) + 1
            audit_map[c_name]["last_audited_at"] = now_iso
            sources = set(audit_map[c_name].get("checked_sources", []))
            sources.add(job["source_type"])
            audit_map[c_name]["checked_sources"] = list(sources)
            audit_map[c_name]["notes"] = f"Found matching opening: {job['title']} in {job['location']}."

    # Process company updates (e.g. not_found)
    updated_companies_count = 0
    for update in batch.get("company_updates", []):
        c_name = update["company"]
        status = update.get("status", "not_found")
        notes = update.get("notes", "No matching 2-5 yr backend/SDE openings found.")
        sources = update.get("checked_sources", ["official_career_page", "linkedin_jobs", "instahyre"])

        if c_name in audit_map:
            # If we already found openings for it, keep openings_found
            if audit_map[c_name]["status"] != "openings_found":
                audit_map[c_name]["status"] = status
                audit_map[c_name]["notes"] = notes
                audit_map[c_name]["checked_sources"] = sources
                audit_map[c_name]["last_audited_at"] = now_iso
                updated_companies_count += 1

    # Save
    jobs_path.write_text(json.dumps(jobs, indent=2))
    audit_path.write_text(json.dumps(list(audit_map.values()), indent=2))

    print(f"Successfully added {added_jobs_count} new job(s). Total jobs now: {len(jobs)}")
    print(f"Updated {updated_companies_count} company status records.")


if __name__ == "__main__":
    main()
