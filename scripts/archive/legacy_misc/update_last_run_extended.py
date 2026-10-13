import datetime, json, openpyxl

now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open('data/curated_wave13_extended_final.json') as f:
    added_roles = json.load(f)

md_content = f"""# Run Summary — Wave 13 Extended (Completed {now_str})

## Overview
- **Candidate Target**: Vrinda Gupta (~3 YOE at Microsoft; C#/.NET Core, Azure Cloud, Node.js/TypeScript, Microservices, Distributed Systems, AI Agent workflows).
- **Execution Mode**: **Wave 13 Extended** (retained all existing Wave 13 data and appended 35 fresh verified pure engineering rows directly into the `Wave 13` sheet).
- **Total Rows in `Wave 13`**: **66 engineering roles** (31 initial + 35 newly verified).
- **Workbooks Updated**: Both `data/Companies(1).xlsx` and `data/companies.xlsx`.
- **Validation**: Schema validated via `scripts/validate_jobs.py --jobs data/jobs.json` with **0 errors and 0 warnings** across **406 total active records**.

---

## Strict Constraints & Safety Followed
- **Permanently Paused Employers**: Amazon, Microsoft, MongoDB, and Sarvam AI excluded (0 roles added).
- **Strict Title & Role Filtering**: No non-tech, support, sales engineer, customer reliability, GTM, solutions architect, or QA/testing roles. Strictly pure software engineering / backend / cloud / distributed systems tracks.
- **Verification Engine**: Verified live via headless Chrome DOM rendering (checking actual page body text for absence of closed indicators and confirming live apply buttons).
- **Compensation Floor**: Tier-1 Tech / High-Growth Product benchmark (≥ ₹35 LPA).

---

## Newly Appended Roles (Sample of 35 Roles in Wave 13 Extension)

| # | Company | Role Title | Location | Key Tech Stack | Match Score |
|---|---|---|---|---|---|
"""

for i, r in enumerate(added_roles, 32):
    md_content += f"| {i} | {r['company']} | {r['title']} | {r['location']} | {r['tech_stack']} | {r['score']} |\n"

with open('data/last_run.md', 'w') as f:
    f.write(md_content)

print("Updated data/last_run.md successfully.")
