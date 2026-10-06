import urllib.request
import json

targets = [
    ("crowdstrike", "wd5", "crowdstrikecareers"),
    ("paypal", "wd1", "jobs"),
    ("adobe", "wd5", "external_experienced"),
    ("citi", "wd5", "2")
]

for tenant, wd_num, site in targets:
    url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    payload = json.dumps({"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "India"}).encode('utf-8')
    # If bad request with searchText, use empty payload or loop pages
    req = urllib.request.Request(url, data=b"{}", headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            facets = data.get('facets', [])
            total = data.get('total', 0)
            print(f"=== {tenant.upper()} (Total {total}) ===")
            # Look for location facets to find India facet id
            india_facet = None
            for f in facets:
                if f.get('facetParameter') == 'locationHierarchy1' or f.get('facetParameter') == 'locations' or 'location' in f.get('facetParameter', '').lower():
                    for v in f.get('values', []):
                        if 'india' in v.get('descriptor', '').lower() or 'bengaluru' in v.get('descriptor', '').lower() or 'pune' in v.get('descriptor', '').lower():
                            print(f"   Location facet: {f.get('facetParameter')} = {v.get('id')} ({v.get('descriptor')}) [{v.get('count')}]")
    except Exception as e:
        print(f"Error {tenant}: {e}")
