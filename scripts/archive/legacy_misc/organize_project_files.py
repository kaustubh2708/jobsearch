#!/usr/bin/env python3
"""Project Organization and Archive Script.

Safely categorizes, archives, and organizes intermediate crawls, raw batches,
debugging dumps, and scratch test scripts for both Vaanya and Vrinda,
leaving ONLY the pristine, canonical, unerring production files in data/.

Non-negotiable constraint:
data/jobs_vrinda_discovery_wave2_verified.xlsx must remain untouched and byte-identical (MD5: 603645d035fb7282ec948b11e493d9b5).
"""

import os
import shutil
import hashlib
from pathlib import Path

ROOT = Path("/Users/kaustubhsingh/Developer/job_search_agent 2")
DATA_DIR = ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"

VRINDA_CANONICAL_FILE = DATA_DIR / "jobs_vrinda_discovery_wave2_verified.xlsx"
EXPECTED_VRINDA_MD5 = "603645d035fb7282ec948b11e493d9b5"

# 1. Verify Vrinda master MD5 before starting
def verify_vrinda_checksum():
    assert VRINDA_CANONICAL_FILE.exists(), "Vrinda canonical master missing!"
    with open(VRINDA_CANONICAL_FILE, "rb") as f:
        digest = hashlib.md5(f.read()).hexdigest()
    assert digest == EXPECTED_VRINDA_MD5, f"Vrinda checksum mismatch! Got {digest}, expected {EXPECTED_VRINDA_MD5}"
    print(f"Verified Vrinda canonical master MD5: {digest}")

verify_vrinda_checksum()

# 2. Define canonical files to remain in data/
CANONICAL_PRODUCTION_FILES = {
    "Job Search.xlsx",
    "jobs_vrinda_discovery_wave2_verified.xlsx",
    "jobs_vaanya_discovery_wave2_verified.xlsx",
    "companies.xlsx",
    "jobs.json",
    "all_existing_urls.json",
    "last_run.md",
    "archive",  # The archive directory itself
}

# 3. Create target archive directories
archive_dirs = {
    "vrinda": ARCHIVE_DIR / "vrinda",
    "vaanya": ARCHIVE_DIR / "vaanya",
    "crawls": ARCHIVE_DIR / "crawls_and_scrapes",
    "repair": ARCHIVE_DIR / "system_repair_and_duplicates",
    "scratch_tests": ROOT / "scripts" / "scratch_tests",
}

for d in archive_dirs.values():
    d.mkdir(parents=True, exist_ok=True)

# 4. Map files to archive
VRINDA_ARCHIVE = [
    "archive_vrinda_wave2_backup",
    "batches_vrinda_claude",
    "jobs_vrinda_claude_raw_batches.xlsx",
    "jobs_vrinda_portfolio_20260930.json",
    "jobs_vrinda_portfolio_20260930.xlsx",
    "jobs_vrinda_portfolio_20260930.xlsx.inspect.ndjson",
    "dead_links_vrinda_portfolio_20260930.json",
    "review_queue_vrinda_portfolio_20260930.json",
    "last_run_vrinda_portfolio_20260930.md",
    "progress_vrinda_claude.md",
]

VAANYA_ARCHIVE = [
    "vaanya_data_archive",
    "batches_vaanya_claude",
    "jobs_vaanya_claude.json",
    "dead_links_vaanya_claude.json",
    "hiring_drives_vaanya_claude.json",
    "last_run_vaanya_claude.md",
    "progress_vaanya_claude.md",
    "jobs_vaanya_incremental_20260930.json",
    "jobs_vaanya_incremental_20260930_v2.json",
    "jobs_vaanya_portfolio_20260930.json",
    "jobs_vaanya_portfolio_20260930.xlsx",
    "jobs_vaanya_portfolio_20260930.xlsx.inspect.ndjson",
    "dead_links_vaanya_portfolio_20260930.json",
    "review_queue_vaanya_portfolio_20260930.json",
    "last_run_vaanya_portfolio_20260930.md",
    "vaanya_new_additions_20260930.json",
    "last_run_vaanya_new_additions_20260930.md",
    "analyzed_vaanya_roles.json",
]

CRAWLS_ARCHIVE = [
    "raw_data_eng_cards.json",
    "raw_entry_level_cards.json",
    "raw_new_ats_jobs.json",
    "raw_wave4_ats_jobs.json",
    "raw_workday_roles.json",
    "entry_level_ats_roles.json",
    "fresher_ats_cards.json",
    "fresher_linkedin_cards.json",
    "promising_fresher_cards.json",
    "fresh_2026_candidates.json",
    "wave4_crawled_cards.json",
    "wave4_detailed_jobs.json",
    "wave4_linkedin_recruiter_discovery_report.json",
    "wave4_recruiters_found.json",
    "deep_scan_wave4.json",
    "curated_wave4_verified.json",
    "verified_wave4_additions.json",
    "verified_fresh_roles_w5.json",
    "rejected_fresh_roles_w5.json",
    "verified_entry_level_fte.json",
    "rejected_entry_level_fte.json",
    "verified_data_eng_fte.json",
    "verified_wave5_additions.json",
    "verified_new_sheet_additions.json",
    "linkedin_crawled_cards.json",
    "linkedin_detailed_discovered.json",
    "linkedin_recruiter_discovery_report.json",
    "qualified_linkedin_leads.json",
    "ranked_active_jobs.json",
    "ranked_active_jobs_v2.json",
    "audit_companies_links_final.json",
    "checked_job_links.json",
    "detailed_audited_links.json",
    "existing_job_links_set.json",
    "extracted_job_links.json",
    "jd_eligibility_check.json",
]

REPAIR_ARCHIVE = [
    "Companies(1).xlsx",
    "jobs_pre_repair_20260929.json",
    "jobs_repaired.json",
    "jobs_repaired.xlsx",
    "jobs_repaired.xlsx.inspect.ndjson",
    "last_run_repaired.md",
    "ANTIGRAVITY_MANIFEST.md",
    "ANTIGRAVITY_MIGRATION_REPORT.md",
]

ROOT_SCRATCH_TESTS = [
    "parse_jobs.py",
    "parse_workday.py",
    "scan_jiostar.py",
    "scan_workday_jobs.py",
    "test_atlassian.py",
    "test_ats.py",
    "test_sr.py",
    "test_sr2.py",
    "test_workday.py",
    "test_workday2.py",
]

def move_items(items, target_dir, src_base=DATA_DIR):
    for item in items:
        src = src_base / item
        dst = target_dir / item
        if src.exists():
            print(f"Moving {src.name} -> {target_dir.relative_to(ROOT)}/")
            shutil.move(str(src), str(dst))
        else:
            print(f"Notice: {src} not found, skipping.")

print("\n--- Moving Vrinda Intermediate / Wave Archives ---")
move_items(VRINDA_ARCHIVE, archive_dirs["vrinda"])

print("\n--- Moving Vaanya Intermediate / Wave Archives ---")
move_items(VAANYA_ARCHIVE, archive_dirs["vaanya"])

print("\n--- Moving Crawls, Scrapes, and Intermediate Card Batches ---")
move_items(CRAWLS_ARCHIVE, archive_dirs["crawls"])

print("\n--- Moving System Repair, Duplicates, and Reports ---")
move_items(REPAIR_ARCHIVE, archive_dirs["repair"])

print("\n--- Moving Root Scratch Scripts to scripts/scratch_tests/ ---")
move_items(ROOT_SCRATCH_TESTS, archive_dirs["scratch_tests"], src_base=ROOT)

# Remove .DS_Store if present in data
ds_store = DATA_DIR / ".DS_Store"
if ds_store.exists():
    ds_store.unlink()

# Final Checks
verify_vrinda_checksum()

remaining_in_data = set(os.listdir(DATA_DIR)) - {".DS_Store"}
print(f"\nRemaining items in data/ ({len(remaining_in_data)}):")
for f in sorted(remaining_in_data):
    print(f" [CANONICAL] {f}")

unexpected = remaining_in_data - CANONICAL_PRODUCTION_FILES
if unexpected:
    print(f"\nWARNING: Unexpected remaining files in data/: {unexpected}")
else:
    print("\nSUCCESS: data/ contains ONLY clean, canonical, unerring files!")
