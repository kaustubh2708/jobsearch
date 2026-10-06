import json, re

with open('data/wave11_curated_india_roles.json') as f:
    roles = json.load(f)

print(f"Total input roles: {len(roles)}")

# We want 32 top roles for Wave 11.
# Let's filter out any duplicates by (company, title)
# And prioritize:
# 1. C#/.NET Core, Azure Cloud
# 2. Node.js, TypeScript, AI Agents / LLMs
# 3. High quality employers in Gurugram, Noida, Delhi NCR, and Tier-1 Remote/Bengaluru
# Exclude low-quality agency/consultancy roles if better product/GCC roles exist.

clean_roles = []
seen_comp_title = set()
seen_urls = set()

# Disqualify agencies or non-fit titles if needed
reject_titles = ['devices - türkiye', 'sales engineer', 'product support engineer iii-1', 'network engineer']

for r in roles:
    comp = r['company'].strip()
    title = r['title'].strip()
    url = r['url'].strip()
    loc = r['location'].strip()
    t_lower = title.lower()

    if any(rk in t_lower for rk in reject_titles):
        continue

    # Disambiguate duplicate company + title by appending req ID to title if necessary
    key = (comp.lower(), title.lower())
    if key in seen_comp_title:
        if r.get('id'):
            title = f"{title} (Req {r['id']})"
            r['title'] = title
            key = (comp.lower(), title.lower())
        else:
            continue

    if url in seen_urls:
        continue

    seen_comp_title.add(key)
    seen_urls.add(url)
    clean_roles.append(r)

print(f"Cleaned unique roles: {len(clean_roles)}")

# Prioritize by tech fit and location fit
def sort_key(r):
    tech = r['tech_stack'].lower()
    loc = r['location'].lower()
    score = r['score']
    # boost .NET / Azure
    if '.net' in tech or 'azure' in tech:
        score += 10
    if 'node' in tech or 'typescript' in tech or 'ai agent' in tech:
        score += 5
    if 'gurugram' in loc or 'gurgaon' in loc or 'noida' in loc:
        score += 5
    return score

clean_roles.sort(key=sort_key, reverse=True)

# Select top 32 roles
wave11_final = clean_roles[:32]
print(f"Selected {len(wave11_final)} final roles for Wave 11.")

for i, r in enumerate(wave11_final, 1):
    print(f"{i:2d}. [{r['company']}] {r['title']} | {r['location']} | Stack: {r['tech_stack']} | Score: {r['score']}")

with open('data/wave11_final_verified_roles.json', 'w') as f:
    json.dump(wave11_final, f, indent=2)

print("Saved to data/wave11_final_verified_roles.json")
