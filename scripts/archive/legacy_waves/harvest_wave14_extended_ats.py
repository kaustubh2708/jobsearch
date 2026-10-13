import urllib.request, json, ssl, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

paused = {'amazon', 'microsoft', 'mongodb', 'sarvam ai'}

# Greenhouse boards
gh_boards = [
    'datadog', 'confluent', 'canonical', 'qualys', 'rapid7', 'docusign',
    'box', 'dropbox', 'samsara', 'toast', 'cloudflare', 'palantir',
    'snowflake', 'nutanix', 'siemens', 'akamai', 'splunk', 'purestorage',
    'crowdstrike', 'zscaler', 'elastic', 'gitlab', 'pagerduty', 'twilio',
    'rubrik', 'cohere', 'couchbase', 'fivetran', 'airbyte', 'postman', 'uber'
]

ats_jobs = []

for b in gh_boards:
    if b in paused: continue
    url = f"https://boards-api.greenhouse.io/v1/boards/{b}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for j in data.get('jobs', []):
                loc = (j.get('location', {}).get('name') or '').lower()
                title = j.get('title', '')
                tl = title.lower()

                if not any(k in loc for k in ['india', 'bengaluru', 'bangalore', 'noida', 'gurgaon', 'gurugram', 'hyderabad', 'pune', 'mumbai', 'remote']):
                    continue
                if any(w in tl for w in ['senior', 'sr.', 'principal', 'staff', 'lead', 'manager', 'director', 'intern', 'apprentice', 'trainee', 'head']):
                    continue
                if not any(w in tl for w in ['engineer', 'developer', 'sde', 'qa', 'analyst', 'systems', 'cloud', 'software', 'technology']):
                    continue

                ats_jobs.append({
                    'company': b.capitalize(),
                    'title': title,
                    'location': j.get('location', {}).get('name'),
                    'url': j.get('absolute_url'),
                    'desc_html': j.get('content', ''),
                    'source': 'Greenhouse'
                })
    except:
        pass

print(f"Harvested {len(ats_jobs)} official ATS candidates.")
with open('data/wave14_extended_raw_ats.json', 'w') as f:
    json.dump(ats_jobs, f, indent=2)

