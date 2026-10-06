import urllib.request, json, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

# Ashby endpoints
ashby_companies = [
    ('Supabase', 'supabase'),
    ('Ramp', 'ramp'),
    ('Retool', 'retool'),
    ('Brex', 'brex'),
    ('Linear', 'linear'),
    ('Vellum', 'vellum'),
    ('Braintrust', 'braintrust'),
    ('Decagon', 'decagon'),
    ('Cursor', 'cursor'),
    ('Sourcegraph', 'sourcegraph'),
    ('PostHog', 'posthog'),
    ('Railway', 'railway'),
    ('Render', 'render'),
    ('Neon', 'neon'),
    ('Turso', 'turso'),
    ('Encore', 'encore'),
    ('Together AI', 'together-ai'),
    ('Cartesia', 'cartesia'),
    ('Bolna', 'bolna'),
    ('Ema', 'ema'),
    ('Level AI', 'level-ai'),
    ('Plane', 'plane'),
    ('LlamaIndex', 'llamaindex'),
    ('LangChain', 'langchain')
]

print("Scanning Ashby job boards...")
for comp, token in ashby_companies:
    try:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            data = json.loads(r.read().decode('utf-8'))
            jobs = data.get('jobs', [])
            india_jobs = []
            for j in jobs:
                loc = (j.get('location') or '').lower()
                sec_locs = [str(l).lower() for l in j.get('secondaryLocations', [])]
                all_locs = loc + ' ' + ' '.join(sec_locs)
                if any(x in all_locs for x in ['india', 'gurgaon', 'gurugram', 'noida', 'delhi', 'bengaluru', 'bangalore', 'remote']):
                    india_jobs.append(j['title'])
            if india_jobs:
                print(f"[{comp}] ({len(jobs)} total jobs, {len(india_jobs)} India/Remote): {india_jobs[:3]}")
    except Exception as e:
        pass

# Greenhouse endpoints
gh_companies = [
    ('Grafana Labs', 'grafanalabs'),
    ('Temporal', 'temporal'),
    ('Databricks', 'databricks'),
    ('Stripe', 'stripe'),
    ('Elastic', 'elastic'),
    ('Coinbase', 'coinbase'),
    ('Cloudflare', 'cloudflare'),
    ('GitLab', 'gitlab'),
    ('HackerRank', 'hackerrank'),
    ('Atlan', 'atlan'),
    ('BrowserStack', 'browserstack'),
    ('SimCorp', 'simcorp'),
    ('Keysight Technologies', 'keysighttechnologies'),
    ('Honeywell', 'honeywell'),
    ('3Pillar Global', '3pillarglobal'),
    ('UKG', 'ukg'),
    ('Siemens Energy', 'siemensenergy'),
    ('NatWest Group', 'natwest'),
    ('Fidelity International', 'fidelityinternational'),
    ('Squarepoint Capital', 'squarepointcapital'),
    ('Tower Research Capital', 'towerresearchcapital'),
    ('Deliveroo', 'deliveroo'),
    ('Rubrik', 'rubrik'),
    ('Brex', 'brex'),
    ('Carta', 'carta'),
    ('Plaid', 'plaid'),
    ('Robinhood', 'robinhood'),
    ('Samsara', 'samsara'),
    ('Chainalysis', 'chainalysis'),
    ('Chime', 'chime'),
    ('Gusto', 'gusto'),
    ('Rippling', 'rippling')
]

print("\nScanning Greenhouse job boards...")
for comp, token in gh_companies:
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            data = json.loads(r.read().decode('utf-8'))
            jobs = data.get('jobs', [])
            india_jobs = []
            for j in jobs:
                loc = (j.get('location', {}).get('name') or '').lower()
                if any(x in loc for x in ['india', 'gurgaon', 'gurugram', 'noida', 'delhi', 'bengaluru', 'bangalore', 'remote']):
                    india_jobs.append(j['title'])
            if india_jobs:
                print(f"[{comp}] ({len(jobs)} total jobs, {len(india_jobs)} India/Remote): {india_jobs[:3]}")
    except Exception as e:
        pass
