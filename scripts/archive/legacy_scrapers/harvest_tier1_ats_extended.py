import urllib.request, json, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

with open('data/raw_wave13_extended_leads.json') as f:
    existing_leads = json.load(f)

existing_urls = {item['url'].lower().rstrip('/') for item in existing_leads}

# Greenhouse boards of top tech giants & unicorns
gh_boards = [
    'postman', 'browserstack', 'inmobi', 'swiggy', 'clevertap', 'hasura',
    'chargebee', 'druva', 'innovaccer', 'couchbase', 'yugabyte', 'confluent',
    'docusign', 'cloudflare', 'snowflake', 'nutanix', 'qualys', 'sailpoint',
    'samsara', 'verkada', 'uber', 'atlassian', 'stripe', 'affirm', 'databricks'
]

ats_leads = []

for b in gh_boards:
    url = f'https://boards-api.greenhouse.io/v1/boards/{b}/jobs?content=true'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for j in data.get('jobs', []):
                title = j.get('title', '')
                loc = (j.get('location', {}).get('name') or '').lower()
                tl = title.lower()

                # India check
                if not any(k in loc for k in ['india', 'bengaluru', 'bangalore', 'noida', 'gurgaon', 'gurugram', 'hyderabad', 'pune', 'delhi', 'remote']):
                    continue

                # Exclude staff/director/manager/intern
                if any(w in tl for w in ['senior', 'sr.', 'principal', 'staff', 'lead', 'manager', 'director', 'intern', 'apprentice', 'head']):
                    continue

                # Must be core engineering
                if not any(w in tl for w in ['engineer', 'developer', 'sde', 'backend', 'cloud', 'systems']):
                    continue

                abs_url = j.get('absolute_url', '')
                if abs_url.lower().rstrip('/') in existing_urls:
                    continue

                ats_leads.append({
                    'company': b.capitalize(),
                    'title': title,
                    'location': j.get('location', {}).get('name') or 'India',
                    'url': abs_url,
                    'job_id': str(j.get('id')),
                    'desc_html': j.get('content', '')
                })
    except Exception as e:
        pass

print(f"Discovered {len(ats_leads)} active tier-1 Greenhouse roles.")

# Ashby boards
ashby_boards = [
    'linear', 'warp', 'vanta', 'retool', 'synthesia', 'descript', 'harvey',
    'snyk', 'glean', 'cohere', 'mistral', 'together', 'groq', 'perplexity',
    'supabase', 'hex', 'deepgram', 'dust', 'atlan', 'anyscale'
]

for org in ashby_boards:
    url = f'https://api.ashbyhq.com/posting-api/job-board/{org}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for j in data.get('jobs', []):
                title = j.get('title', '')
                loc = (j.get('locationName') or '').lower()
                sec_locs = [str(x).lower() for x in (j.get('secondaryLocations') or [])]
                all_locs = loc + ' ' + ' '.join(sec_locs)
                if not any(k in all_locs for k in ['india', 'bengaluru', 'bangalore', 'noida', 'gurgaon', 'hyderabad', 'pune', 'delhi', 'remote']):
                    continue
                tl = title.lower()
                if any(w in tl for w in ['senior', 'sr.', 'principal', 'staff', 'lead', 'manager', 'director', 'intern', 'apprentice', 'head']):
                    continue
                if not any(w in tl for w in ['engineer', 'developer', 'sde', 'backend']):
                    continue
                job_url = j.get('jobUrl', '')
                if job_url.lower().rstrip('/') in existing_urls:
                    continue
                ats_leads.append({
                    'company': org.capitalize(),
                    'title': title,
                    'location': j.get('locationName') or 'India / Remote',
                    'url': job_url,
                    'job_id': str(j.get('id')),
                    'desc_html': j.get('descriptionHtml', '')
                })
    except Exception as e:
        pass

print(f"Total ATS leads discovered: {len(ats_leads)}")
with open('data/raw_ats_wave13_extended.json', 'w') as f:
    json.dump(ats_leads, f, indent=2)

