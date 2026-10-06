import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from linkedin_freshness import extract_linkedin_freshness

with open('data/linkedin_detailed_discovered.json') as f:
    jobs = json.load(f)

print(f"Total jobs to evaluate: {len(jobs)}")

parsed_roles = []

for j in jobs:
    if j.get('is_closed'):
        continue

    title = j['title']
    company = j['company']
    loc = j['location']
    job_id = j['job_id']
    url = j['url']
    recruiter = j.get('recruiter')
    desc = j.get('description_snippet', '')
    desc_lower = desc.lower()

    # Experience parsing
    # Look for patterns like "X-Y years", "X+ years", "at least X years"
    exp_snippets = j.get('experience_snippets', [])
    exp_text = " ".join(exp_snippets)
    
    # Try finding min/max exp in text
    exp_found = None
    min_exp = None
    max_exp = None
    
    # Check for direct range e.g. 2-5, 3-5, 2 to 4, 3+ etc
    m_range = re.search(r'(\d+)\s*(?:-|–|to)\s*(\d+)\s*years?', desc, re.IGNORECASE)
    if m_range:
        min_exp = int(m_range.group(1))
        max_exp = int(m_range.group(2))
        exp_found = f"{min_exp}–{max_exp} years"
    else:
        m_plus = re.search(r'(\d+)\+?\s*years?(?:\s+of)?\s+experience', desc, re.IGNORECASE)
        if m_plus:
            min_exp = int(m_plus.group(1))
            max_exp = min_exp + 3
            exp_found = f"{min_exp}+ years"

    # Reject 6+ years or lead/staff/principal
    if min_exp and min_exp >= 6:
        continue
    if max_exp and max_exp > 8 and min_exp and min_exp >= 5:
        continue

    # Tech stack extraction
    techs = []
    if re.search(r'\bc#\b|\b\.net\b|\bdotnet\b', desc_lower):
        techs.append("C#/.NET Core")
    if re.search(r'\bazure\b', desc_lower):
        techs.append("Azure")
    if re.search(r'\baws\b', desc_lower):
        techs.append("AWS")
    if re.search(r'\bnode(?:\.js)?\b|\btypescript\b', desc_lower):
        techs.append("Node.js/TypeScript")
    if re.search(r'\bpython\b', desc_lower):
        techs.append("Python")
    if re.search(r'\bjava\b|\bspring(?:\s+boot)?\b', desc_lower):
        techs.append("Java/Spring Boot")
    if re.search(r'\bgo\b|\bgolang\b', desc_lower):
        techs.append("Golang")
    if re.search(r'\bc\+\+\b', desc_lower):
        techs.append("C++")
    if re.search(r'\bmicroservices\b', desc_lower):
        techs.append("Microservices")
    if re.search(r'\bkafka\b|\brabbitmq\b|\bevent[- ]driven\b', desc_lower):
        techs.append("Kafka/Event-Driven")
    if re.search(r'\bdistributed systems\b|\bhigh availability\b|\bscalab', desc_lower):
        techs.append("Distributed Systems")
    if re.search(r'\bgenai\b|\bai agent\b|\bagentic\b|\bllm\b', desc_lower):
        techs.append("AI Agents/LLMs")
    if re.search(r'\bsql\b|\bpostgres\b|\bmongo(?:db)?\b|\bredis\b', desc_lower):
        techs.append("Databases (SQL/NoSQL/Redis)")

    # Seniority & Compensation likelihood
    # Target >= 35 LPA
    # Top tier MNCs / funded startups / fintechs / trading firms have very high compensation likelihood
    comp_likelihood = "Competitive (Market ~25–35 LPA)"
    tier1_firms = ["Tower Research Capital", "Amazon", "MongoDB", "Adobe", "Payoneer", "Cadence", "Atlys", "Statiq", "Syfe", "Leena AI", "ixigo", "PW (PhysicsWallah)", "Deloitte", "Optum India"]
    if any(tf.lower() in company.lower() for tf in ["Tower Research Capital", "MongoDB", "Amazon", "Adobe", "Atlys", "Syfe"]):
        comp_likelihood = "Very High (Target >= 40–70+ LPA base)"
    elif any(tf.lower() in company.lower() for tf in tier1_firms):
        comp_likelihood = "High (Target >= 32–45 LPA base)"

    hiring_route = "LinkedIn Direct Apply / Public ATS"
    if recruiter:
        # Clean up recruiter name/title
        rec_clean = " ".join(recruiter.split())
        hiring_route = f"Direct Recruiter InMail / Application: {rec_clean}"

    parsed_roles.append({
        'company': company,
        'title': title,
        'location': loc,
        'url': url,
        'job_id': job_id,
        # Never invent a 2–5-year requirement from the title. Unknown remains
        # unknown and is sent for manual JD verification.
        'experience_required': exp_found or "experience_unknown",
        'min_exp': min_exp,
        'max_exp': max_exp,
        'tech_stack': techs,
        'recruiter_route': hiring_route,
        'compensation_likelihood': comp_likelihood,
        'raw_recruiter': recruiter
        ,**{k: j.get(k) for k in (
            'linkedin_posted_at', 'linkedin_age_days', 'linkedin_age_flag',
            'linkedin_open_status', 'linkedin_age_source_text',
            'linkedin_age_checked_at'
        )}
    })

print(f"Qualified target leads: {len(parsed_roles)}")
with open('data/qualified_linkedin_leads.json', 'w') as f:
    json.dump(parsed_roles, f, indent=2)

for r in parsed_roles[:15]:
    print(f"[{r['job_id']}] {r['title']} @ {r['company']} ({r['location']})")
    print(f"   Exp: {r['experience_required']} | Tech: {', '.join(r['tech_stack'])}")
    print(f"   Route: {r['recruiter_route'][:80]}...")
    print(f"   Comp: {r['compensation_likelihood']}")
    print()
