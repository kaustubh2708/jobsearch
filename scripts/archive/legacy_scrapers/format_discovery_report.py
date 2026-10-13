import json

with open('data/qualified_linkedin_leads.json') as f:
    all_leads = json.load(f)

# Priority ordering
def score_lead(l):
    score = 0
    # Location priority
    loc = l['location'].lower()
    if 'gurgaon' in loc or 'gurugram' in loc:
        score += 50
    elif 'noida' in loc:
        score += 40
    elif 'delhi' in loc:
        score += 35
    elif 'remote' in loc:
        score += 30
    elif 'bengaluru' in loc:
        score += 25

    # Recruiter presence
    if l.get('raw_recruiter'):
        score += 30

    # Tech stack fit
    techs = l.get('tech_stack', [])
    if any(t in ['C#/.NET Core', 'Azure', 'Node.js/TypeScript', 'Microservices', 'Distributed Systems', 'AI Agents/LLMs'] for t in techs):
        score += 20

    # Compensation tier
    if 'Very High' in l.get('compensation_likelihood', ''):
        score += 15
    elif 'High' in l.get('compensation_likelihood', ''):
        score += 10

    return score

all_leads.sort(key=score_lead, reverse=True)

# Select top 20 verified leads across categories
selected = all_leads[:20]

with open('data/linkedin_recruiter_discovery_report.json', 'w') as f:
    json.dump(selected, f, indent=2)

print(f"Top {len(selected)} leads formatted and saved to data/linkedin_recruiter_discovery_report.json")
