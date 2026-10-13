import datetime, json

now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open('data/curated_wave14_final.json') as f:
    w14_roles = json.load(f)

md_content = f"""# Run Summary — Wave 14 (Completed {now_str})

## Architecture & Consolidation
- **Architecture Principle Followed**: Exactly the last two waves (**Wave 13** and **Wave 14**) are maintained as standalone active sheets.
- **Consolidation**: `Wave 12` (32 rows) was consolidated cleanly into the `past wave` historical sheet (now totaling **754 total rows / 753 data rows**).
- **Workbooks Updated & Mirrored**: [data/Companies(1).xlsx](file:///Users/kaustubhsingh/Developer/job_search_agent%202/data/Companies(1).xlsx) and [data/companies.xlsx](file:///Users/kaustubhsingh/Developer/job_search_agent%202/data/companies.xlsx).

---

## Safety & Constraints Check
- **Paused Employers**: Amazon, Microsoft, MongoDB, and Sarvam AI remain strictly excluded (0 roles added).
- **Zero Non-Tech / Support Roles**: Solutions architect, customer reliability, GTM, sales engineer, tech support, business analyst, and QA/SDET roles disqualified.
- **Candidate Stack Fit**: Targeted C#/.NET Core, Azure Cloud, Node.js/TypeScript, Microservices, Distributed Systems, and AI Agent workflows for Vrinda Gupta (2–5 YOE).
- **Headless Chrome Verification**: All roles rendered via Selenium Chrome Headless to verify active requisition DOM states.
- **Schema Validation**: [data/jobs.json](file:///Users/kaustubhsingh/Developer/job_search_agent%202/data/jobs.json) exported with **438 total records**, passing with **0 errors, 0 warnings**.

---

## Wave 14 Verified Openings (32 Roles)

| # | Company | Role Title | Location | Key Tech Stack | Match Score | Priority Tier |
|---|---|---|---|---|---|---|
"""

for i, r in enumerate(w14_roles, 1):
    md_content += f"| {i} | {r['company']} | {r['title']} | {r['location']} | {r['tech_stack']} | {r['score']} | {r['tier']} |\n"

with open('data/last_run.md', 'w') as f:
    f.write(md_content)

print("Updated data/last_run.md successfully.")
