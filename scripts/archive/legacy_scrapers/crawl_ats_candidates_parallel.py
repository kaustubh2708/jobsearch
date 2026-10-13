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

# Boards to crawl
greenhouse_boards = [
    'rubrik', 'stripe', 'towerresearchcapital', 'squarepointcapital',
    'postman', 'browserstack', 'inmobi', 'swiggy', 'sharechat',
    'urbancompany', 'cars24', 'physicswallah', 'sliceit', 'cred',
    'meesho', 'nutanix', 'aristanetworks', 'datadog', 'elastic',
    'couchbase', 'cloudera', 'purestorage', 'hashicorp', 'cloudflare',
    'roblox', 'snowflake', 'gleanwork', 'okta', 'thoughtworks',
    'fivetran', 'gitlab', 'carta', 'verkada', 'plaid', 'brex',
    'samsara', 'confluent', 'airtable', 'figma', 'grafana', 'sentinelone',
    'vanta', 'ramp', 'scale', 'benchling', 'instabase', 'cohesity',
    'branch', 'dbtlabs', 'ripple', 'lucidsoftware', 'braintrust',
    'decagon', 'hubspot', 'canonical', 'paloaltonetworks'
]

lever_boards = [
    'paytm', 'zomato', 'blinkit', 'zepto', 'incred', 'jupiter',
    'navi', 'fi-money', 'clevertap', 'urbanpiper', 'simpl', 'kuku-fm',
    'groww', 'razorpay', 'bharatpe', 'pocketfm', 'khatabook',
    'classplus', 'apna', 'porter', 'rebelfoods', 'cuemath',
    'leapfinance', 'loco', 'spinny', 'atlys'
]

ashby_boards = [
    'atlys', 'avoca', 'forma-ai', 'atlan', 'aiprise',
    'together-ai', 'plane', 'squadstack', 'mercury', 'cursor',
    'warp', 'hex', 'pylon', 'linear', 'retool', 'modal',
    'langchain', 'tavily', 'perplexity', 'ema', 'anuvaya',
    'bolna', 'cartesia', 'elevenlabs', 'vapi', 'recrew', 'deel'
]

smartrecruiters_companies = [
    'Visa', 'PublicisSapient', 'Informatica', 'BoschGroup', 'AveryDennison',
    'Skechers', 'Square', 'Twitter'
]

def fetch_greenhouse(slug):
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
    except Exception:
        return []

def fetch_lever(slug):
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
    except Exception:
        return []

def fetch_ashby(slug):
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
    except Exception:
        return []

def fetch_smartrecruiters(comp):
    url = f"https://api.smartrecruiters.com/v1/companies/{comp}/postings"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=3.5) as r:
            data = json.loads(r.read())
            jobs = []
            for j in data.get('content', []):
                loc = j.get('location', {}).get('city', '') + ', ' + j.get('location', {}).get('country', '')
                jid = j.get('id', '')
                jobs.append({
                    'platform': 'SmartRecruiters',
                    'company': comp,
                    'title': j.get('name', ''),
                    'location': loc,
                    'url': f"https://jobs.smartrecruiters.com/{comp}/{jid}",
                    'content': '',
                    'id': jid
                })
            return jobs
    except Exception:
        return []

all_jobs = []
with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
    gh_futures = {executor.submit(fetch_greenhouse, s): s for s in greenhouse_boards}
    lever_futures = {executor.submit(fetch_lever, s): s for s in lever_boards}
    ashby_futures = {executor.submit(fetch_ashby, s): s for s in ashby_boards}
    sr_futures = {executor.submit(fetch_smartrecruiters, s): s for s in smartrecruiters_companies}

    for f in concurrent.futures.as_completed(list(gh_futures.keys()) + list(lever_futures.keys()) + list(ashby_futures.keys()) + list(sr_futures.keys())):
        try:
            res = f.result()
            if res:
                all_jobs.extend(res)
        except Exception:
            pass

print(f"Total raw postings scraped across all platforms: {len(all_jobs)}")
with open('data/scratch_raw_ats_jobs.json', 'w') as f:
    json.dump(all_jobs, f, indent=2)
