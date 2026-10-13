import json, urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

with open('data/wave12_curated_india_roles.json') as f:
    roles = json.load(f)

print(f"Loaded {len(roles)} curated roles for Wave 12.")

reject_titles = ['devices - türkiye', 'sales engineer', 'product support engineer iii-1', 'network engineer', 'business analyst']
paused_companies = {'amazon', 'sarvam', 'sarvam ai', 'mongodb', 'microsoft'}

clean_roles = []
seen_urls = set()
seen_comp_title = set()

# Deduplication against global seen
with open('data/vrinda_all_seen_urls.json') as f:
    dedup = json.load(f)
seen_urls.update(dedup.get('seen_urls', []))

for r in roles:
    url = r['url']
    comp = r['company'].strip()
    title = r['title'].strip()
    loc = r['location'].strip()
    t_lower = title.lower()

    if comp.lower() in paused_companies:
        continue

    if any(rk in t_lower for rk in reject_titles):
        continue

    clean_url = url.split('?')[0].lower().rstrip('/')
    if clean_url in seen_urls:
        continue

    # Disambiguate duplicate company + title
    key = (comp.lower(), title.lower())
    if key in seen_comp_title:
        if r.get('id'):
            title = f"{title} (Req {r['id']})"
            r['title'] = title
            key = (comp.lower(), title.lower())
        else:
            continue

    # Test HTTP 200
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            if resp.getcode() == 200:
                clean_roles.append(r)
                seen_urls.add(clean_url)
                seen_comp_title.add(key)
                print(f"[{len(clean_roles)}] 200 OK: {comp} - {title}")
                if len(clean_roles) >= 32:
                    break
    except Exception as e:
        print(f"Skipping {comp} ({e})")

print(f"\nFinal bulletproof roles selected for Wave 12: {len(clean_roles)}")
with open('data/wave12_bulletproof_roles.json', 'w') as f:
    json.dump(clean_roles, f, indent=2)
print("Saved to data/wave12_bulletproof_roles.json")
