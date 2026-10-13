import json, re

# Load all candidate pools
with open('data/fresh_verified_swe_harvest.json') as f:
    fresh_swe = json.load(f)

with open('data/wave12_pure_engineering_verified.json') as f:
    audited_eng = json.load(f)

with open('data/wave12_bulletproof_roles.json') as f:
    bulletproof = json.load(f)

# Paused companies
paused = {'amazon', 'sarvam', 'sarvam ai', 'mongodb', 'microsoft'}

# Disqualifiers: strictly NO support, field, solutions architect, sales, trainee, etc.
disqualifiers = [
    'field engineer', 'solutions architect', 'product support', 'gtm engineer',
    'customer reliability', 'support engineer', 'sales engineer', 'network engineer',
    'business analyst', 'marketing', 'trainee', 'türkiye', 'cursor'
]

# Seen URLs deduplication against historical waves (Waves 1-11)
with open('data/vrinda_all_seen_urls.json') as f:
    dedup = json.load(f)
seen_urls = set(dedup.get('seen_urls', []))

all_roles = fresh_swe + audited_eng + bulletproof

final_curated = []
seen_current = set()
seen_comp_title = set()

for r in all_roles:
    comp = r['company'].strip()
    title = r['title'].strip()
    url = r['url'].strip()
    loc = r['location'].strip()
    t_lower = title.lower()

    if comp.lower() in paused:
        continue

    # Disqualify non-core tech / support
    if any(dk in t_lower for dk in disqualifiers):
        continue

    # Disqualify pure python titles per dynamic search switch
    if 'python developer' in t_lower or 'sr python' in t_lower or 'python engineer' in t_lower:
        continue

    # Reject Staff / Level 4 if over-senior
    if 'staff' in t_lower or 'principal' in t_lower or 'director' in t_lower or 'lead' in t_lower:
        continue

    # Require authentic software / backend / fullstack / cloud developer titles
    if not any(k in t_lower for k in ['developer', 'software engineer', 'backend', 'sde', 'swe', 'full stack', 'fullstack', 'platform engineer', 'devops', 'cloud engineer']):
        continue

    clean_url = url.split('?')[0].lower().rstrip('/')
    if clean_url in seen_urls or clean_url in seen_current:
        continue

    # Disambiguate duplicate comp+title
    key = (comp.lower(), title.lower())
    if key in seen_comp_title:
        if r.get('id'):
            title = f"{title} (Req {r['id']})"
            r['title'] = title
            key = (comp.lower(), title.lower())
        else:
            continue

    seen_current.add(clean_url)
    seen_comp_title.add(key)
    final_curated.append(r)

print(f"Total pure engineering roles curated: {len(final_curated)}")

# Prioritize by tech stack fit: .NET, Azure, Node.js, TypeScript, Microservices, Distributed Systems
def sort_fit(r):
    tech = r['tech_stack'].lower()
    loc = r['location'].lower()
    score = r['score']
    if '.net' in tech or 'c#' in tech or 'azure' in tech:
        score += 8
    if 'node' in tech or 'typescript' in tech or 'distributed systems' in tech:
        score += 5
    if 'gurugram' in loc or 'gurgaon' in loc or 'noida' in loc:
        score += 4
    return score

final_curated.sort(key=sort_fit, reverse=True)

final_32 = final_curated[:32]
print(f"\nFinal {len(final_32)} Pure Engineering Roles for Wave 12:")
for i, r in enumerate(final_32, 1):
    print(f"{i:2d}. [{r['company']}] {r['title']} | {r['location']} | Stack: {r['tech_stack']}")

with open('data/wave12_final_pure_tech_32.json', 'w') as f:
    json.dump(final_32, f, indent=2)

print("Saved to data/wave12_final_pure_tech_32.json")
