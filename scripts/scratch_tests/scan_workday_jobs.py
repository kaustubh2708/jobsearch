import urllib.request
import json
import time

targets = [
    ("crowdstrike", "wd5", "crowdstrikecareers"),
    ("paypal", "wd1", "jobs"),
    ("adobe", "wd5", "external_experienced"),
    ("citi", "wd5", "2")
]

for tenant, wd_num, site in targets:
    print(f"\n=================== {tenant.upper()} ===================")
    url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    offset = 0
    limit = 20
    india_jobs = []
    
    while True:
        payload = json.dumps({"limit": limit, "offset": offset, "searchText": "India"}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                postings = data.get('jobPostings', [])
                total = data.get('total', 0)
                if not postings:
                    break
                for p in postings:
                    title = p.get('title', '')
                    loc = p.get('locationsText', '')
                    req_id = p.get('bulletFields', [''])[0] if p.get('bulletFields') else ''
                    path = p.get('externalPath', '')
                    full_url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/en-US/{site}{path}"
                    india_jobs.append((req_id, title, loc, full_url))
                offset += limit
                if offset >= total or offset >= 100: # cap at 100 for search
                    break
        except Exception as e:
            print(f"Error {tenant} at offset {offset}: {e}")
            break
            
    print(f"Found {len(india_jobs)} India search matches in {tenant}:")
    for req_id, title, loc, full_url in india_jobs:
        if any(k in title.lower() for k in ['software', 'engineer', 'developer', 'intern', 'graduate', 'associate', 'data', 'analyst', 'qa', 'apprentice']):
            print(f"  * [{req_id}] {title} | {loc} | {full_url}")
