# Scripts Directory & Core Tooling

This directory contains the operational scripts and validation tools for maintaining job openings, exporting dashboard data, and synchronizing candidate pipelines.

---

## Active Core Tools

| File | Purpose | Primary Command / Usage |
|---|---|---|
| [`validate_jobs.py`](file:///Users/kaustubhsingh/Developer/job_search_agent%202/scripts/validate_jobs.py) | **Strict Schema & Scoring Validator**: Enforces schema rules, 7-component match scoring, HTTP 200 page evidence, and direct URL constraints. | `python3 scripts/validate_jobs.py --jobs data/jobs.json` |
| [`export_dashboard_data.py`](file:///Users/kaustubhsingh/Developer/job_search_agent%202/scripts/export_dashboard_data.py) | **Web Dashboard Exporter**: Reads workbooks and compiles live JSON payloads for the local Orbit dashboard. | `python3 scripts/export_dashboard_data.py` |
| [`export_and_validate_jobs.py`](file:///Users/kaustubhsingh/Developer/job_search_agent%202/scripts/export_and_validate_jobs.py) | **Workbook to JSON Sync**: Normalizes spreadsheet records into schema-compliant records and invokes validator. | `python3 scripts/export_and_validate_jobs.py` |
| [`eligibility_rules.py`](file:///Users/kaustubhsingh/Developer/job_search_agent%202/scripts/eligibility_rules.py) | **Experience Rules Helper**: Experience parser evaluating years-of-experience ranges and fresher eligibility. | Module import |

---

## Archive Directory Layout (`scripts/archive/`)

Historical wave-specific scrapers, one-off audit scripts, and crawler trials have been categorized into dedicated subdirectories:

- **`scripts/archive/legacy_waves/`**: Historical wave creation, curation, and discovery scripts.
- **`scripts/archive/legacy_audits/`**: One-off audit scripts for past wave link reviews and deep scans.
- **`scripts/archive/legacy_scrapers/`**: Historical crawl scripts, ATS query helpers, and batch harvesters.
- **`scripts/archive/legacy_misc/`**: Miscellaneous one-off conversion and utility scripts.
