import urllib.request
import json

workdays = [
    ("adobe", "wd5", "external_campus"),
    ("adobe", "wd5", "external_experienced"),
    ("crowdstrike", "wd5", "crowdstrike"),
    ("paypal", "wd1", "PayPal-Jobs"),
    ("citi", "wd5", "2")
]

for tenant, wd_num, site in workdays:
    url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    payload = json.dumps({
        "appliedFacets": {},
        "limit": 20,
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
            print(f"Workday {tenant} ({site}): total {total}")
            for it in items:
                title = it.get('title', '')
                ext_url = "https://" + tenant + "." + wd_num + ".myworkdayjobs.com/en-US/" + site + it.get('externalPath', '')
                loc = it.get('locationsText', '')
                bullet = it.get('bulletFields', [])
                print(f"  - {title} | {loc} | {bullet} | {ext_url}")
    except Exception as e:
        print(f"Workday {tenant} ({site}) error: {e}")
