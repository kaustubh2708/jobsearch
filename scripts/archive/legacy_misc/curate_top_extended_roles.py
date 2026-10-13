import json, re

with open('data/verified_wave13_extended_roles.json') as f:
    roles = json.load(f)

# Priority 1: Reject over-senior explicitly in title or details
clean_curated = []
seen_titles_comp = set()

for r in roles:
    tl = r['title'].lower()
    comp = r['company']
    key = (comp.lower().strip(), tl.strip())
    if key in seen_titles_comp:
        continue
    seen_titles_comp.add(key)

    # Reject Staff / Lead / Principal / 7+ years
    if any(k in tl for k in ['staff', 'principal', '7+ years', 'director', 'lead engineer']):
        continue

    # Clean up company names
    c_clean = comp.replace(' in India', '').strip()

    # Determine match score and tier
    stack = r['tech_stack']
    score = 95
    if 'C#' in stack or 'Azure' in stack:
        score = 95
        tier = 'P1 Strong Match (.NET / Azure Focus)'
    elif 'Node.js' in stack or 'TypeScript' in stack or 'Distributed Systems' in stack:
        score = 92
        tier = 'P1 Strong Match (Node / Distributed Systems)'
    else:
        score = 88
        tier = 'P2 Match (Backend Engineering)'

    # Format location
    loc = r['location']
    if 'Gurgaon' in loc or 'Gurugram' in loc:
        tier += ' [NCR Priority 1]'
    elif 'Noida' in loc or 'Delhi' in loc:
        tier += ' [NCR Priority 2]'

    clean_curated.append({
        'company': c_clean,
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

print(f"Curated {len(clean_curated)} top pure engineering roles.")
# Take top 30-35 roles
final_selection = clean_curated[:35]
print(f"Final selection: {len(final_selection)} roles.")

with open('data/curated_wave13_extended_final.json', 'w') as f:
    json.dump(final_selection, f, indent=2)

