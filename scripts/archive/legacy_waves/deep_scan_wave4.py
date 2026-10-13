import urllib.request
import json
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

with open('data/all_existing_urls.json') as f:
    existing = json.load(f)
existing_urls = set(existing['urls'])

results = []

# 1. Check Moveworks on Greenhouse
try:
    url = "https://boards-api.greenhouse.io/v1/boards/moveworks/jobs?content=true"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        data = json.loads(r.read())
        for j in data.get('jobs', []):
            loc = j.get('location', {}).get('name', '')
            t = j.get('title', '')
            u = j.get('absolute_url', '')
            if 'india' in loc.lower() or 'bengaluru' in loc.lower():
                if not any(s in t.lower() for s in ['senior', 'staff', 'lead', 'manager', 'director']):
                    results.append({'company': 'Moveworks', 'title': t, 'location': loc, 'url': u})
except Exception as e:
    pass

# 2. Check Postman on Greenhouse
try:
    url = "https://boards-api.greenhouse.io/v1/boards/postman/jobs?content=true"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        data = json.loads(r.read())
        for j in data.get('jobs', []):
            loc = j.get('location', {}).get('name', '')
            t = j.get('title', '')
            u = j.get('absolute_url', '')
            if 'india' in loc.lower() or 'bengaluru' in loc.lower():
                if not any(s in t.lower() for s in ['senior', 'staff', 'lead', 'manager', 'director']):
                    results.append({'company': 'Postman', 'title': t, 'location': loc, 'url': u})
except Exception as e:
    pass

# 3. Check Arista Networks on Greenhouse
try:
    url = "https://boards-api.greenhouse.io/v1/boards/aristanetworks/jobs?content=true"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        data = json.loads(r.read())
        for j in data.get('jobs', []):
            loc = j.get('location', {}).get('name', '')
            t = j.get('title', '')
            u = j.get('absolute_url', '')
            if 'india' in loc.lower() or 'bengaluru' in loc.lower() or 'pune' in loc.lower():
                if any(k in t.lower() for k in ['software engineer', 'intern', 'graduate', 'associate']):
                    if not any(s in t.lower() for s in ['senior', 'staff', 'lead', 'manager', 'director', 'iii', 'iv']):
                        results.append({'company': 'Arista Networks', 'title': t, 'location': loc, 'url': u})
except Exception as e:
    pass

# 4. Check Databricks on Greenhouse
try:
    url = "https://boards-api.greenhouse.io/v1/boards/databricks/jobs?content=true"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        data = json.loads(r.read())
        for j in data.get('jobs', []):
            loc = j.get('location', {}).get('name', '')
            t = j.get('title', '')
            u = j.get('absolute_url', '')
            if 'india' in loc.lower() or 'bengaluru' in loc.lower():
                if any(k in t.lower() for k in ['intern', 'new grad', 'university', 'associate', 'software engineer i', 'software engineer 1']):
                    results.append({'company': 'Databricks', 'title': t, 'location': loc, 'url': u})
except Exception as e:
    pass

# 5. Check Nutanix on Greenhouse
try:
    url = "https://boards-api.greenhouse.io/v1/boards/nutanix/jobs?content=true"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        data = json.loads(r.read())
        for j in data.get('jobs', []):
            loc = j.get('location', {}).get('name', '')
            t = j.get('title', '')
            u = j.get('absolute_url', '')
            if 'india' in loc.lower() or 'bengaluru' in loc.lower() or 'pune' in loc.lower():
                if any(k in t.lower() for k in ['intern', 'graduate', 'associate', 'mts 1', 'engineer 1']):
                    results.append({'company': 'Nutanix', 'title': t, 'location': loc, 'url': u})
except Exception as e:
    pass

# 6. Check Twilio on Greenhouse
try:
    url = "https://boards-api.greenhouse.io/v1/boards/twilio/jobs?content=true"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        data = json.loads(r.read())
        for j in data.get('jobs', []):
            loc = j.get('location', {}).get('name', '')
            t = j.get('title', '')
            u = j.get('absolute_url', '')
            if 'india' in loc.lower():
                if any(k in t.lower() for k in ['intern', 'associate', 'engineer 1', 'software engineer i', 'analyst']):
                    results.append({'company': 'Twilio', 'title': t, 'location': loc, 'url': u})
except Exception as e:
    pass

# Filter duplicates
unique_results = []
for r in results:
    u = r['url'].lower().rstrip('/')
    if u not in existing_urls:
        unique_results.append(r)

print(f"Deep scan found {len(unique_results)} unique matching roles:")
for r in unique_results:
    print(f"  {r['company']} | {r['title']} | {r['location']} | {r['url']}")

with open('data/deep_scan_wave4.json', 'w') as f:
    json.dump(unique_results, f, indent=2)
