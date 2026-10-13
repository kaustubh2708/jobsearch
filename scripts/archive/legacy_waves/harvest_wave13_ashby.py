import urllib.request, json, ssl, time, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('data/master_history_dedup_wave13.json') as f:
    dedup = json.load(f)
history_companies = {c.lower().strip() for c in dedup['companies']}

ashby_orgs = [
    'linear', 'warp', 'vanta', 'retool', 'synthesia', 'descript', 'harvey',
    'snyk', 'glean', 'cohere', 'mistral', 'together', 'groq', 'perplexity',
    'supabase', 'hex', 'deepgram', 'tome', 'dust', 'pave', 'magic', 'atlan',
    'cursor', 'anyscale', 'elevenlabs', 'postman'
]

ashby_results = []
for org in ashby_orgs:
    if org in history_companies or org in ['amazon', 'sarvam ai', 'mongodb']:
        continue
    url = f'https://api.ashbyhq.com/posting-api/job-board/{org}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for j in data.get('jobs', []):
                title = j.get('title', '')
                loc = (j.get('locationName') or '').lower()
                sec_locs = [str(x).lower() for x in (j.get('secondaryLocations') or [])]
                all_locs = loc + ' ' + ' '.join(sec_locs)

                if not any(k in all_locs for k in ['india', 'bengaluru', 'bangalore', 'noida', 'gurgaon', 'hyderabad', 'pune', 'remote']):
                    continue

                tl = title.lower()
                if any(w in tl for w in ['senior', 'sr.', 'principal', 'staff', 'lead', 'manager', 'director', 'intern', 'apprentice', 'trainee', 'head']):
                    continue

                if not any(w in tl for w in ['engineer', 'developer', 'sde', 'qa', 'analyst', 'systems', 'cloud']):
                    continue

                ashby_results.append({
                    'company': org.capitalize(),
                    'title': title,
                    'location': j.get('locationName') or 'India / Remote',
                    'url': j.get('jobUrl'),
                    'desc_html': j.get('descriptionHtml', ''),
                    'source': 'Ashby'
                })
    except:
        pass

print(f"Total Ashby candidates harvested: {len(ashby_results)}")
with open('data/wave13_ashby_raw.json', 'w') as f:
    json.dump(ashby_results, f, indent=2)
