import json, re

# 1. Load previously verified roles from Wave 12 that are strictly core engineering:
with open('data/wave12_bulletproof_roles.json') as f:
    prev_w12 = json.load(f)

# 2. Load newly audited engineering roles:
with open('data/wave12_pure_engineering_verified.json') as f:
    audited_eng = json.load(f)

# Disqualify non-core tech:
# - Field Engineer, Solutions Architect, Product Support, GTM Engineer, Customer Reliability, Sales Engineer, Network Engineer, Business Analyst
disqualifiers = [
    'field engineer', 'solutions architect', 'product support', 'gtm engineer',
    'customer reliability', 'support engineer', 'sales engineer', 'network engineer',
    'business analyst', 'marketing', 'trainee', 'türkiye'
]

# Exclude Python heavy if pure python
# "exclude_python_heavy_roles: true"
# Disqualify roles where title is Python Developer / Sr Python Developer

clean_candidates = []
seen_urls = set()
seen_comp_title = set()

# Deduplication against global seen (Waves 1-11)
with open('data/vrinda_all_seen_urls.json') as f:
    dedup = json.load(f)
seen_urls.update(dedup.get('seen_urls', []))

# Also ensure Microsoft, Amazon, MongoDB, Sarvam AI are excluded
paused = {'amazon', 'sarvam', 'sarvam ai', 'mongodb', 'microsoft'}

all_pool = prev_w12 + audited_eng

for r in all_pool:
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

    # Must be real software engineering title
    if not any(k in t_lower for k in ['developer', 'software engineer', 'backend', 'sde', 'swe', 'full stack', 'fullstack', 'platform engineer', 'devops', 'cloud engineer']):
        continue

    clean_url = url.split('?')[0].lower().rstrip('/')
    if clean_url in seen_urls:
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

    seen_urls.add(clean_url)
    seen_comp_title.add(key)
    clean_candidates.append(r)

print(f"Total clean, pure engineering candidates collected: {len(clean_candidates)}")
for i, r in enumerate(clean_candidates, 1):
    print(f"{i:2d}. [{r['company']}] {r['title']} | {r['location']}")

with open('data/wave12_pure_tech_candidates.json', 'w') as f:
    json.dump(clean_candidates, f, indent=2)
