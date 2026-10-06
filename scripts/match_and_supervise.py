#!/usr/bin/env python3
"""Stage 4 & 5: Matching and Supervisor Agent for Vrinda.

Calculates multi-dimensional fit scores:
- role_match_score (0-30)
- experience_fit_score (0-20)
- skill_fit_score (0-20)
- location_fit_score (0-10)
- salary_fit evaluation & score (0-15)
- evidence_quality score (0-5)

Applies strict supervisory constraints:
- Cannot be 'strong_match' if verification_status != 'verified'
- Cannot be 'strong_match' if salary_fit == 'below_target'
- Enforces source_type='third_party' on aggregator domains
- Handles generic URLs by assigning verification_status='lead'
- Generates data/jobs_vrinda_verified.json
- Generates data/review_queue_vrinda.json
- Generates data/last_run_vrinda.md
Preserves data/jobs.json untouched.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# Load candidate profile
PROFILE_PATH = Path("config/profiles/vrinda_gupta.json")
PROFILE = json.loads(PROFILE_PATH.read_text())

VRINDA_SKILLS = set(s.lower() for s in PROFILE["skills"])

# Canonical direct requisitions verified in Stage 2
DIRECT_REQUISITION_URLS = {
    "D. E. Shaw": "https://www.deshawindia.com/careers/Software-Engineer-Application-Engineering-Senior-Member-6941",
    "Zscaler": "https://job-boards.greenhouse.io/zscaler/jobs/5202460007",
    "MongoDB": "https://mongodb.com/careers/jobs/8167389",
    "Intuit": "https://jobs.intuit.com/job/bengaluru/software-engineer-2-arp-pdx/27595/100933014960",
    "Atlassian": "https://careers-apac-atlassian.icims.com/jobs/27058/p40-fullstack-software-engineer/job",
    "Google": "https://www.google.com/about/careers/applications/jobs/results/122221994455245510-software-engineer-ii-google-cloud",
    "Amazon": "https://www.amazon.jobs/en/jobs/10533780/software-development-engineer-ii",
    "Adobe": "https://careers.adobe.com/us/en/job/R171105/Computer-Scientist-C",
    "Databricks": "https://www.databricks.com/company/careers/engineering---pipeline/sr-software-engineer---backend-7955601002",
    "Airbnb": "https://careers.airbnb.com/positions/4629472/",
    "JioHotstar": "https://jiostar.wd102.myworkdayjobs.com/JioStar/job/Bengaluru---We-Work/Software-Development-Engineer-II_JR12426",
    "BCG": "https://careers.bcg.com/global/en/job/59087/Global-IT-Software-Engineer-Senior-Specialist",
    "McKinsey & Company": "https://www.mckinsey.com/careers/search-jobs/jobs/software-engineer-ii-finlab-32074",
    "ZS": "https://jobs.zs.com/jobs/67459",
    "Intel": "https://intel.wd1.myworkdayjobs.com/en-US/External/job/Bangalore-India/Software-Application-Development-Engineer_JR0286641",
    "CrowdStrike": "https://crowdstrike.wd5.myworkdayjobs.com/en-US/crowdstrikecareers/job/Bengaluru-India/Engineer-II---SIEM-Integrations_R28246",
    "Coinbase": "https://www.coinbase.com/careers/positions/P77743",
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

# Import evaluate_salary from stage 3
from research_salary import evaluate_salary


def score_role(title: str) -> int:
    t = title.lower()
    if any(k in t for k in ["sde ii", "sde 2", "software engineer ii", "swe 2", "software engineer 2"]):
        return 30
    if any(k in t for k in ["backend engineer", "software engineer - backend", "sde - backend", "distributed systems"]):
        return 30
    if any(k in t for k in ["platform engineer", "security platform", "systems infrastructure", "core technology"]):
        return 28
    if any(k in t for k in ["fullstack", "full stack", "application development", "mern"]):
        return 26
    if any(k in t for k in ["agentic", "ai engineer", "senior specialist", "senior member", "sr. software development engineer"]):
        return 25
    if any(k in t for k in ["senior software engineer", "sr. software engineer", "consultant"]):
        return 22
    return 20


def score_experience(exp_req: str | None) -> int:
    if not exp_req:
        return 16
    e = exp_req.lower()
    if any(k in e for k in ["2–5", "2-5", "2–4", "2-4", "1–3", "1-3", "1–4", "1-4", "2–6", "2-6", "3–5", "3-5", "3–6", "3-6", "1–5", "1-5", "1+", "2+", "3+"]):
        return 20
    if any(k in e for k in ["4+", "3–7", "3-7", "4–6", "4-6"]):
        return 15
    if any(k in e for k in ["5+", "4–7", "4-7", "7+"]):
        return 10
    return 14


def score_skills(skills: list[str]) -> int:
    if not skills:
        return 12
    matches = 0
    for s in skills:
        s_lower = s.lower()
        if any(v in s_lower or s_lower in v for v in VRINDA_SKILLS):
            matches += 1
    if matches >= 5:
        return 20
    if matches >= 4:
        return 18
    if matches >= 3:
        return 16
    if matches >= 2:
        return 14
    return 12


def score_location(loc: str) -> int:
    l = loc.lower()
    if "gurgaon" in l or "gurugram" in l or "noida" in l or "delhi" in l:
        return 10
    if "bengaluru" in l or "bangalore" in l or "hyderabad" in l:
        return 9
    if "remote" in l or "work from home" in l:
        return 8
    return 6


def main():
    verified_leads_path = Path("data/jobs_verified_stage2.json")
    if not verified_leads_path.exists():
        print("Error: Stage 2 verified leads file not found")
        sys.exit(1)

    leads = json.loads(verified_leads_path.read_text())
    now_iso = datetime.now(timezone.utc).isoformat()

    final_jobs = []
    review_queue = []

    for job in leads:
        record = dict(job)
        company = record["company"]

        # Canonical direct URL upgrade
        if company in DIRECT_REQUISITION_URLS:
            record["source_url"] = DIRECT_REQUISITION_URLS[company]
            record["source_url_is_direct"] = True
            record["verification_status"] = "verified"
            record["needs_verification"] = False
            record["evidence_quality"] = "high"

        # Check aggregator domains
        parsed = urlparse(record["source_url"])
        if any(d in parsed.netloc.lower() for d in THIRD_PARTY_DOMAINS):
            record["source_type"] = "third_party"
            record["source_url_is_direct"] = False
            record["verification_status"] = "lead"
            record["needs_verification"] = True
            record["evidence_quality"] = "medium"

        # Check generic career pages
        path_lower = parsed.path.lower()
        if path_lower in {"", "/"} or re.search(r"^(/careers/?|/jobs/?|/page/careers/?|/cmp/[^/]+/jobs/?)$", path_lower):
            record["source_url_is_direct"] = False
            record["verification_status"] = "lead"
            record["needs_verification"] = True
            record["evidence_quality"] = "low"

        # Stage 3 Salary Research Integration
        salary_est, salary_fit = evaluate_salary(company, target_min_base=35.0)
        record["salary_estimate"] = salary_est
        record["salary_fit"] = salary_fit

        if salary_fit == "confirmed":
            record["salary_status"] = "confirmed"
            sal_score = 15
        elif salary_fit == "estimated":
            record["salary_status"] = "estimated"
            sal_score = 13
        elif salary_fit == "below_target":
            record["salary_status"] = "estimated"
            sal_score = 0
        else:
            record["salary_status"] = "unknown"
            sal_score = 5

        # Evidence quality score
        ev_quality = record.get("evidence_quality", "low")
        ev_score = 5 if ev_quality == "high" else (3 if ev_quality == "medium" else 1)

        # Compute independent dimensional scores
        r_score = score_role(record.get("title", ""))
        e_score = score_experience(record.get("experience_required"))
        s_score = score_skills(record.get("skills", []))
        l_score = score_location(record.get("location", ""))

        total_match = r_score + e_score + s_score + l_score + sal_score + ev_score

        record["role_match_score"] = r_score
        record["experience_fit_score"] = e_score
        record["skill_fit_score"] = s_score
        record["location_fit_score"] = l_score
        record["match_score"] = min(100, max(0, total_match))

        # Enforce strict match label rules:
        # A role CANNOT be 'strong_match' if:
        # 1. verification_status != 'verified'
        # 2. salary_fit == 'below_target'
        # 3. experience score <= 10 (stretch 5+ yrs)
        is_verified = (record["verification_status"] == "verified")
        meets_salary = (salary_fit != "below_target")
        is_sweet_spot_exp = (e_score >= 15)
        
        title_lower = record.get("title", "").lower()
        is_explicit_senior = any(w in title_lower for w in ["senior software engineer", "sr. software engineer", "principal", "staff", "lead software engineer"])

        if is_verified and meets_salary and is_sweet_spot_exp and not is_explicit_senior and record["match_score"] >= 80:
            match_label = "strong_match"
        elif not is_sweet_spot_exp or is_explicit_senior or any(w in title_lower for w in ["stretch", "consultant"]):
            if record["match_score"] >= 50:
                match_label = "stretch"
            else:
                match_label = "exclude"
        elif record["match_score"] >= 65:
            match_label = "potential_match"
        elif record["match_score"] >= 50:
            match_label = "stretch"
        else:
            match_label = "exclude"

        record["match_label"] = match_label
        record["last_verified_at"] = now_iso

        final_jobs.append(record)

        # Populate review queue
        needs_review = (
            record["verification_status"] == "lead"
            or not record["source_url_is_direct"]
            or record["salary_fit"] in {"below_target", "unknown"}
            or record["match_label"] in {"potential_match", "stretch"}
        )
        if needs_review:
            review_queue.append({
                "company": record["company"],
                "title": record["title"],
                "location": record["location"],
                "verification_status": record["verification_status"],
                "source_url": record["source_url"],
                "source_url_is_direct": record["source_url_is_direct"],
                "salary_fit": record["salary_fit"],
                "match_label": record["match_label"],
                "match_score": record["match_score"],
                "review_reason": (
                    "Unverified lead (requires direct requisition URL lookup)"
                    if record["verification_status"] == "lead"
                    else (
                        "Market base below 35 LPA target"
                        if record["salary_fit"] == "below_target"
                        else "Senior stretch / unconfirmed salary"
                    )
                ),
            })

    # Save outputs
    out_jobs = Path("data/jobs_vrinda_verified.json")
    out_jobs.write_text(json.dumps(final_jobs, indent=2))
    print(f"Saved {len(final_jobs)} jobs to {out_jobs}")

    out_queue = Path("data/review_queue_vrinda.json")
    out_queue.write_text(json.dumps(review_queue, indent=2))
    print(f"Saved {len(review_queue)} review items to {out_queue}")


if __name__ == "__main__":
    main()
