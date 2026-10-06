import json, urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

with open('data/wave11_curated_india_roles.json') as f:
    all_curated = json.load(f)

with open('data/wave11_final_verified_roles.json') as f:
    current_final = json.load(f)

# Find all roles that pass strict HTTP 200 within 5 seconds
bulletproof = []
seen_urls = set()
seen_comp_title = set()

for r in current_final + all_curated:
    url = r['url']
    comp = r['company'].strip()
    title = r['title'].strip()
    
    if url in seen_urls:
        continue

    # Clean / disambiguate
    key = (comp.lower(), title.lower())
    if key in seen_comp_title:
        if r.get('id'):
            title = f"{title} (Req {r['id']})"
            r['title'] = title
            key = (comp.lower(), title.lower())
        else:
            continue

    # Probe HTTP 200
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            if resp.getcode() == 200:
                bulletproof.append(r)
                seen_urls.add(url)
                seen_comp_title.add(key)
                print(f"[{len(bulletproof)}] 200 OK: {comp} - {title}")
                if len(bulletproof) >= 32:
                    break
    except Exception as e:
        print(f"Skipping {comp} ({e})")

print(f"\nFinal bulletproof roles selected: {len(bulletproof)}")
with open('data/wave11_bulletproof_roles.json', 'w') as f:
    json.dump(bulletproof, f, indent=2)
print("Saved to data/wave11_bulletproof_roles.json")
