import urllib.request, json, ssl, time, re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('data/master_history_dedup_wave13.json') as f:
    dedup = json.load(f)
history_companies = {c.lower().strip() for c in dedup['companies']}
history_urls = {u.strip() for u in dedup['urls']}

print(f"Master deduplication baseline: {len(history_companies)} companies, {len(history_urls)} URLs")

# 1. Harvest fresh Greenhouse boards
gh_boards = [
    'airtable', 'benchling', 'cohere', 'dbtlabs', 'ramp', 'retool',
    'snyk', 'vanta', 'warp', 'deepgram', 'mistral', 'together',
    'postman', 'browserstack', 'inmobi', 'swiggy', 'clevertap', 'hasura',
    'chargebee', 'druva', 'innovaccer', 'couchbase', 'yugabyte', 'confluent',
    'tibco', 'canonical', 'qualys', 'rapid7', 'cyberark', 'sailpoint',
    'pingidentity', 'docusign', 'box', 'dropbox', 'samsara', 'toast', 'verkada',
    'cloudflare', 'palantir', 'snowflake', 'nutanix', 'informatica',
    'synopsys', 'cadence', 'marvell', 'arm', 'siemens', 'nxp', 'mathworks',
    'akamai', 'splunk', 'netapp', 'citrix', 'teradata', 'veritas', 'commvault',
    'cohesity', 'purestorage', 'tanium', 'crowdstrike', 'sentinelone', 'fortinet',
    'paloaltonetworks', 'zscaler', 'fastly', 'checkpoint', 'proofpoint'
]

gh_results = []
for b in gh_boards:
    if b in history_companies or b in ['amazon', 'sarvam ai', 'mongodb']:
        continue
    url = f'https://boards-api.greenhouse.io/v1/boards/{b}/jobs?content=true'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            jobs = data.get('jobs', [])
            for j in jobs:
                loc = (j.get('location', {}).get('name') or '').lower()
                title = j.get('title', '')
                tl = title.lower()

                # India location check
                if not any(k in loc for k in ['india', 'bengaluru', 'bangalore', 'noida', 'gurgaon', 'gurugram', 'hyderabad', 'pune', 'mumbai', 'remote']):
                    continue

                # Exclude senior / intern
                if any(w in tl for w in ['senior', 'sr.', 'principal', 'staff', 'lead', 'manager', 'director', 'intern', 'apprentice', 'trainee', 'head']):
                    continue

                # Must be tech
                if not any(w in tl for w in ['engineer', 'developer', 'sde', 'qa', 'analyst', 'systems', 'cloud', 'software', 'technology']):
                    continue

                gh_results.append({
                    'company': b.capitalize(),
                    'title': title,
                    'location': j.get('location', {}).get('name'),
                    'url': j.get('absolute_url'),
                    'desc_html': j.get('content', ''),
                    'source': 'Greenhouse'
                })
    except:
        pass

print(f"Total Greenhouse candidates harvested: {len(gh_results)}")
with open('data/wave13_gh_raw.json', 'w') as f:
    json.dump(gh_results, f, indent=2)
