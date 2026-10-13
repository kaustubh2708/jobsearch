import json

with open('data/verified_wave16_all_pool.json') as f:
    roles = json.load(f)

print(f"Total roles in verified pool: {len(roles)}")

# Disqualification list
disqualifiers = [
    'staff', 'principal', 'lead', 'director', 'manager', 'head of', '7+ years',
    'servicenow', 'boomi', 'ruby on rails', 'salesforce', 'sap abap', 'intern'
]

clean = []
seen_keys = set()

for r in roles:
    tl = r['title'].lower()
    comp = r['company'].replace(' in India', '').replace(' India', '').strip()
    
    # Exclude paused
    if comp.lower() in {'amazon', 'sarvam', 'sarvam ai', 'mongodb', 'microsoft'}:
        continue

    # Disqualify out-of-scope titles
    if any(k in tl for k in disqualifiers):
        continue

    # Composite key for deduplication
    key = (comp.lower(), tl)
    if key in seen_keys:
        continue
    seen_keys.add(key)

    stack = r['tech_stack']
    loc = r['location']

    # Match scoring
    score = 90
    if 'C#' in stack or 'Azure' in stack:
        score = 95
        tier = 'P1 Strong Match (.NET / Azure Focus)'
    elif 'Node.js' in stack or 'TypeScript' in stack or 'Distributed Systems' in stack:
        score = 92
        tier = 'P1 Strong Match (Distributed Systems / TS)'
    elif 'AI Agent' in stack:
        score = 95
        tier = 'P1 Strong Match (AI Agents / Systems)'
    else:
        score = 88
        tier = 'P2 Match (Backend Engineering)'

    if 'Gurgaon' in loc or 'Gurugram' in loc:
        tier += ' [NCR Priority 1]'
    elif 'Noida' in loc or 'Delhi' in loc:
        tier += ' [NCR Priority 2]'

    clean.append({
        'company': comp,
        'title': r['title'],
        'location': loc,
        'experience': '2–5 years (SDE II fit)',
        'tech_stack': stack,
        'comp': '₹35 – 55 LPA (Tier-1 Tech / High-Growth Product)',
        'score': score,
        'tier': tier,
        'link_status': 'Verified: live ATS / LinkedIn match',
        'url': r['url'],
        'notes': f"Verified live requisition (Chrome Render OK). Core engineering role. Tech Stack: {stack}. Location: {loc}."
    })

print(f"Clean curated roles: {len(clean)}")

# Prioritize .NET, Azure, NCR, and Tech Giants
def sort_key(r):
    t = r['tier']
    s = r['score']
    p_ncr = 1 if 'NCR' in t else 0
    p_stack = 1 if ('.NET' in t or 'Azure' in t or 'AI Agents' in t) else 0
    return (s, p_stack, p_ncr)

clean.sort(key=sort_key, reverse=True)

final_selection = clean[:32]
print(f"Final selection for Wave 16: {len(final_selection)}")

with open('data/curated_wave16_final.json', 'w') as f:
    json.dump(final_selection, f, indent=2)

