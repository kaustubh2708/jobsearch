import urllib.request
import ssl
import json
import re
import html
import concurrent.futures

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*'
}

# Paused companies
EXCLUDED_COMPANIES = {'amazon', 'sarvam', 'sarvam ai', 'mongodb'}

# Expanded Greenhouse boards
greenhouse_slugs = [
    'rubrik', 'stripe', 'towerresearchcapital', 'squarepointcapital',
    'postman', 'browserstack', 'inmobi', 'swiggy', 'sharechat',
    'urbancompany', 'cars24', 'physicswallah', 'sliceit', 'cred',
    'meesho', 'nutanix', 'aristanetworks', 'datadog', 'elastic',
    'couchbase', 'cloudera', 'purestorage', 'hashicorp', 'cloudflare',
    'snowflake', 'gleanwork', 'okta', 'thoughtworks', 'fivetran',
    'gitlab', 'carta', 'verkada', 'plaid', 'brex', 'samsara',
    'confluent', 'airtable', 'figma', 'grafana', 'sentinelone',
    'vanta', 'ramp', 'scale', 'benchling', 'instabase', 'cohesity',
    'branch', 'dbtlabs', 'ripple', 'lucidsoftware', 'braintrust',
    'decagon', 'hubspot', 'canonical', 'paloaltonetworks', 'tanium',
    'sumologic', 'appdynamics', 'chime', 'affirm', 'doordash', 'lyft',
    'coinbase', 'robinhood', 'gusto', 'databricks', 'rippling',
    'flexport', 'toast', 'checkr', 'snyk', 'harness', 'pagerduty',
    'segment', 'amplitude', 'launchdarkly', 'mural', 'miro', 'notion',
    'airtel', 'clevertap', 'paypayneobank', 'quora', 'hackerrank',
    'airmeet', 'whatfix', 'signeasy', 'chargebee', 'freshworks',
    'hasura', 'jupiter', 'dunzo', 'oyorooms', 'cultfit', 'lenskart',
    'nykaa', 'shiprocket', 'shadowfax', 'delhivery', 'spinny'
]

# Expanded Lever slugs
lever_slugs = [
    'paytm', 'zomato', 'blinkit', 'zepto', 'incred', 'jupiter',
    'navi', 'fi-money', 'clevertap', 'urbanpiper', 'simpl', 'kuku-fm',
    'groww', 'razorpay', 'bharatpe', 'pocketfm', 'khatabook',
    'classplus', 'apna', 'porter', 'rebelfoods', 'cuemath',
    'leapfinance', 'loco', 'spinny', 'atlys', 'swiggy', 'dunzo',
    'cred', 'curefit', 'bounce', 'rapido', 'headout', 'treebo',
    'cleartax', 'smallcase', 'indmoney', 'scripbox', 'jar', 'famapp',
    'fampay', 'onecode', 'rupeek', 'cashfree', 'setu', 'progcap'
]

# Expanded Ashby slugs
ashby_slugs = [
    'atlys', 'avoca', 'forma-ai', 'atlan', 'aiprise',
    'together-ai', 'plane', 'squadstack', 'mercury', 'cursor',
    'warp', 'hex', 'pylon', 'linear', 'retool', 'modal',
    'langchain', 'tavily', 'perplexity', 'ema', 'anuvaya',
    'bolna', 'cartesia', 'elevenlabs', 'vapi', 'recrew', 'deel',
    'saaf-ai', 'synthesia', 'replicate', 'resend', 'clay',
    'vantage', 'incidentio', 'basehub', 'dub', 'speakeasy',
    'dust', 'mistral', 'midjourney', 'runwayml', 'cognition',
    'harvey', 'suno', 'luma', 'ideogram', 'pika', 'poe'
]

def fetch_gh(slug):
    if slug in EXCLUDED_COMPANIES:
        return []
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3.5) as r:
            data = json.loads(r.read())
            jobs = []
            for j in data.get('jobs', []):
                jobs.append({
                    'platform': 'Greenhouse',
                    'company': slug,
                    'title': j.get('title', ''),
                    'location': j.get('location', {}).get('name', ''),
                    'url': j.get('absolute_url', ''),
                    'content': html.unescape(re.sub(r'<[^>]+>', ' ', j.get('content', ''))),
                    'id': str(j.get('id', ''))
                })
            return jobs
    except:
        return []

def fetch_lever(slug):
    if slug in EXCLUDED_COMPANIES:
        return []
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3.5) as r:
            data = json.loads(r.read())
            jobs = []
            for j in data:
                loc = j.get('categories', {}).get('location', '')
                jobs.append({
                    'platform': 'Lever',
                    'company': slug,
                    'title': j.get('text', ''),
                    'location': loc,
                    'url': j.get('hostedUrl', ''),
                    'content': html.unescape(j.get('descriptionPlain', '') + ' ' + j.get('additionalPlain', '')),
                    'id': str(j.get('id', ''))
                })
            return jobs
    except:
        return []

def fetch_ashby(slug):
    if slug in EXCLUDED_COMPANIES:
        return []
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3.5) as r:
            data = json.loads(r.read())
            jobs = []
            for j in data.get('jobs', []):
                jid = j.get('id', '')
                jobs.append({
                    'platform': 'Ashby',
                    'company': slug,
                    'title': j.get('title', ''),
                    'location': j.get('location', ''),
                    'url': f"https://jobs.ashbyhq.com/{slug}/{jid}",
                    'content': '',
                    'id': jid
                })
            return jobs
    except:
        return []

all_jobs = []
with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
    futs = []
    for s in greenhouse_slugs:
        futs.append(ex.submit(fetch_gh, s))
    for s in lever_slugs:
        futs.append(ex.submit(fetch_lever, s))
    for s in ashby_slugs:
        futs.append(ex.submit(fetch_ashby, s))

    for f in concurrent.futures.as_completed(futs):
        try:
            r = f.result()
            if r:
                all_jobs.extend(r)
        except:
            pass

print(f"Total postings collected: {len(all_jobs)}")
with open('data/scratch_raw_comprehensive_ats.json', 'w') as f:
    json.dump(all_jobs, f, indent=2)
