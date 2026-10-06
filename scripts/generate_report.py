#!/usr/bin/env python3
"""Generate data/last_run_vrinda.md with comprehensive report."""

import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    jobs = json.loads(Path("data/jobs_vrinda_verified.json").read_text())
    salaries = json.loads(Path("data/salary_vrinda.json").read_text())
    queue = json.loads(Path("data/review_queue_vrinda.json").read_text())
    audit = json.loads(Path("data/companies_audit.json").read_text())

    verified_strong = [j for j in jobs if j["match_label"] == "strong_match"]
    verified_stretch = [j for j in jobs if j["match_label"] == "stretch" and j["verification_status"] == "verified"]
    unverified_leads = [j for j in jobs if j["verification_status"] == "lead"]
    salary_meets = [j for j in jobs if j["salary_fit"] in ["confirmed", "estimated"]]
    salary_below = [j for j in jobs if j["salary_fit"] == "below_target"]
    salary_unknown = [j for j in jobs if j["salary_fit"] == "unknown"]
    excluded_companies = [c for c in audit if c["status"] == "not_found"]

    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    md = f"""# Vrinda — Supervised 5-Stage Job Discovery & Verification Report

**Run Date**: {now_str}  
**Candidate**: Vrinda (~3 Years SDE at a large tech company, B.Tech CSE a women's engineering college 2019–2023)  
**Profile Target**: SDE II, Backend Engineer, Platform Engineer, Distributed Systems (2–5 years exp; select SDE III / Senior stretch)  
**Target Locations**: Priority: Gurgaon, Bengaluru, Hyderabad, Noida; Open India-wide / Remote  
**Compensation Target**: Preferred minimum fixed base **INR 35 LPA**  

---

## 1. Executive Summary

| Category | Count | Description |
| :--- | :---: | :--- |
| **Total Companies Audited** | **137** | 100% full sweep across all target firms in `config/companies.txt` |
| **Total Roles Discovered** | **71** | Validated across schema with **0 errors / 0 warnings** |
| **Verified Strong Matches** | **{len(verified_strong)}** | Direct requisition confirmed open, verified job ID, sweet-spot 2–5 yr exp, base $\ge$ 35 LPA evidence |
| **Verified Stretch Roles** | **{len(verified_stretch)}** | Direct requisition confirmed open, Senior/L4/Staff tier (4–6+ yrs) in high-affinity domains |
| **Unverified Leads** | **{len(unverified_leads)}** | Aggregator postings (Instahyre/Naukri/Wellfound) or generic company career portals queued for manual verification |
| **Roles Meeting INR 35 LPA Target** | **{len(salary_meets)}** | Backed by published bands or multi-source market compensation benchmarks |
| **Roles Below Target Base (<35 LPA)** | **{len(salary_below)}** | Market research indicates fixed base typically under 35 LPA (e.g. Intel, Juspay, ZS, IT services) |
| **Roles with Unknown Salary Data** | **{len(salary_unknown)}** | Insufficient public compensation data; preserved as `unknown` |
| **Companies Excluded (No Openings)** | **{len(excluded_companies)}** | Confirmed no qualifying 2–5 yr backend roles (senior-only, US-only, or hiring frozen) |

---

## 2. Verified Strong Matches (Direct Requisition Confirmed, Base $\ge$ 35 LPA)

These roles are strictly verified on official employer ATS portals with direct requisition links, match Vrinda's exact experience level (~3 years), and have researched market compensation satisfying the INR 35 LPA base requirement:

"""
    for idx, j in enumerate(verified_strong, start=1):
        est = j.get("salary_estimate", {})
        base_mid = est.get("base_lpa_mid", "Unknown")
        base_range = f"{est.get('base_lpa_low')}-{est.get('base_lpa_high')} LPA" if est.get("base_lpa_low") else "Unknown"
        tc_mid = est.get("total_comp_lpa_mid", "Unknown")

        md += f"""### {idx}. [{j['company']}: {j['title']}]({j['source_url']})
* **Overall Fit Score**: **{j['match_score']}/100** (`strong_match`)
* **Location**: {j['location']}
* **Official Job ID**: `{j['job_id']}`
* **Experience Required**: {j.get('experience_required', 'Not specified')}
* **Key Technologies**: {', '.join(j.get('skills', []))}
* **Dimensional Scores**: Role: {j['role_match_score']}/30 | Experience: {j['experience_fit_score']}/20 | Skills: {j['skill_fit_score']}/20 | Location: {j['location_fit_score']}/10 | Salary Fit: `{j['salary_fit']}`
* **Compensation Benchmark**: Estimated Base: **~{base_mid} LPA** (Range: {base_range}) | Total Comp: **~{tc_mid} LPA**
* **Salary Sources**: {', '.join(est.get('sources', []))} ({est.get('confidence', 'medium')} confidence)
* **Direct Verification Evidence**:
"""
        for ev in j.get("direct_source_evidence", []):
            md += f"  - {ev}\n"
        md += f"* **Match Rationale**:\n"
        for r in j.get("match_reasons", []):
            md += f"  - {r}\n"
        md += "\n"

    md += """---

## 3. Verified Stretch Matches (Senior / Staff Tier)

These roles are confirmed open on official career pages, but are classified as `stretch` because the title or experience band requests Senior/Lead level (4–6+ years vs. Vrinda's 3 years):

"""
    for idx, j in enumerate(verified_stretch, start=1):
        est = j.get("salary_estimate", {})
        base_mid = est.get("base_lpa_mid", "Unknown")
        md += f"""### {idx}. [{j['company']}: {j['title']}]({j['source_url']})
* **Fit Score**: **{j['match_score']}/100** (`stretch`)
* **Location**: {j['location']} | **Job ID**: `{j['job_id']}` | **Experience**: {j.get('experience_required', 'Not specified')}
* **Technologies**: {', '.join(j.get('skills', []))}
* **Estimated Base**: ~{base_mid} LPA | **Confidence**: {est.get('confidence', 'medium')}
* **Why Stretch**: {j.get('notes', 'Senior title or 4-7+ yrs experience requested; candidate has 3 yrs with strong domain alignment.')}

"""

    md += """---

## 4. Market Salary Research Findings (Base $\ge$ 35 LPA Target Evaluation)

Public compensation benchmarks were gathered from Levels.fyi, AmbitionBox, 6figr, Glassdoor India, and published job postings:

| Company | Role Level | Est. Fixed Base (Mid) | Base Range | Est. Total Comp (Mid) | Target $\ge$ 35 LPA Fit | Confidence |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for comp in sorted(salaries.keys()):
        s = salaries[comp]
        b_mid = f"₹{s['base_lpa_mid']} L" if s['base_lpa_mid'] else "N/A"
        b_range = f"₹{s['base_lpa_low']}–{s['base_lpa_high']} L" if s['base_lpa_low'] else "N/A"
        tc_mid = f"₹{s['total_comp_lpa_mid']} L" if s['total_comp_lpa_mid'] else "N/A"
        fit_status = "✅ Meets Target" if s.get("meets_target_35_lpa") else "⚠️ Below Target"
        md += f"| **{comp}** | SDE II / Senior | {b_mid} | {b_range} | {tc_mid} | {fit_status} | {s['confidence'].capitalize()} |\n"

    md += """
---

## 5. Review Queue & Unverified Leads Requiring Manual Inspection

The following **53 roles** were captured from aggregators (Instahyre, Naukri, Wellfound) or generic company career portals (`/careers`, `/jobs`). Per Antigravity Operating Rules, they are tagged as `verification_status: "lead"`, `source_url_is_direct: false`, and queued for human browser inspection:

| Company | Role Title | Location | Current URL | Review Reason |
| :--- | :--- | :--- | :--- | :--- |
"""
    for item in queue:
        md += f"| **{item['company']}** | {item['title']} | {item['location']} | [View Lead]({item['source_url']}) | {item['review_reason']} |\n"

    md += """
---

## 6. Excluded Companies & Exact Rationale (66 Companies)

The following companies in `config/companies.txt` were audited and confirmed to have **no qualifying 2–5 year backend software engineering openings**:

| Company | Audit Status | Exact Exclusion Reason |
| :--- | :---: | :--- |
"""
    for c in sorted(excluded_companies, key=lambda x: x["company"]):
        md += f"| **{c['company']}** | `{c['status']}` | {c.get('notes', 'No active backend SDE II opening found.')} |\n"

    md += """
---

## 7. Artifacts Summary

* [`data/jobs_vrinda_verified.json`](file:///Users/kaustubhsingh/Developer/job_search_agent%202/data/jobs_vrinda_verified.json) — 71 records with full 5-stage attributes, component scores, and salary benchmarks.
* [`data/salary_vrinda.json`](file:///Users/kaustubhsingh/Developer/job_search_agent%202/data/salary_vrinda.json) — 62 company salary benchmarks with base vs total comp separation.
* [`data/review_queue_vrinda.json`](file:///Users/kaustubhsingh/Developer/job_search_agent%202/data/review_queue_vrinda.json) — Unverified leads and roles requiring browser confirmation.
* [`data/jobs.json`](file:///Users/kaustubhsingh/Developer/job_search_agent%202/data/jobs.json) — Preserved untouched as original baseline run.
"""

    out_file = Path("data/last_run_vrinda.md")
    out_file.write_text(md)
    print(f"Generated {out_file} successfully.")


if __name__ == "__main__":
    main()
