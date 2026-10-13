import json, re

with open('data/wave13_verified_pure_tech.json') as f:
    roles = json.load(f)

# Disqualify Staff / Level 4 or non-fit titles if any
disqualify = ['staff software engineer', 'python / django']

curated = []
seen_urls = set()
seen_comp_title = set()

for r in roles:
    comp = r['company'].strip()
    title = r['title'].strip()
    url = r['url'].strip()
    loc = r['location'].strip()
    t_lower = title.lower()

    if any(dk in t_lower for dk in disqualify):
        continue

    clean_url = url.split('?')[0].lower().rstrip('/')
    if clean_url in seen_urls:
        continue

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
    curated.append(r)

print(f"Total curated Wave 13 roles: {len(curated)}")

# Sort by tech fit: prioritize .NET, Azure, Node, Distributed Systems, Java/Spring
def sort_fit(r):
    tech = r['tech_stack'].lower()
    score = r['score']
    if '.net' in tech or 'c#' in tech or 'azure' in tech:
        score += 8
    if 'node' in tech or 'microservices' in tech or 'distributed systems' in tech:
        score += 5
    return score

curated.sort(key=sort_fit, reverse=True)

# Select 31 pure engineering roles
w13_final = curated[:31]

for i, r in enumerate(w13_final, 1):
    print(f"{i:2d}. [{r['company']}] {r['title']} | {r['location']} | {r['tech_stack']}")

with open('data/wave13_final_curated.json', 'w') as f:
    json.dump(w13_final, f, indent=2)

print("Saved to data/wave13_final_curated.json")
