import urllib.request
import json

targets = [
    ("crowdstrike", "wd5", "crowdstrikecareers"),
    ("paypal", "wd1", "jobs")
]

for tenant, wd_num, site in targets:
    url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    payload = json.dumps({
        "appliedFacets": {},
        "limit": 50,
        "offset": 0,
        "searchText": "India"
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            total = data.get('total', 0)
            items = data.get('jobPostings', [])
            print(f"=== Workday {tenant} ({site}): total {total} ===")
            for it in items:
                title = it.get('title', '')
                ext_url = "https://" + tenant + "." + wd_num + ".myworkdayjobs.com/en-US/" + site + it.get('externalPath', '')
                loc = it.get('locationsText', '')
                bullet = it.get('bulletFields', [])
                if any(k in title.lower() for k in ['software', 'engineer', 'developer', 'intern', 'graduate', 'associate', 'data', 'analyst', 'qa']):
                    print(f"  [{bullet[0] if bullet else ''}] {title} | {loc} | {ext_url}")
    except Exception as e:
        print(f"Error {tenant}: {e}")
