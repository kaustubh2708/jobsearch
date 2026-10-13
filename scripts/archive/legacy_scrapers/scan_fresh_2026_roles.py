import urllib.request
import ssl
import json
import re
import html

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*'
}

# Target slugs for Greenhouse boards
greenhouse_slugs = [
    'incred', 'cars24', 'physicswallah', 'postman', 'browserstack',
    'sliceit', 'cred', 'meesho', 'inmobi', 'swiggy', 'sharechat',
    'urbancompany', 'rubrik', 'stripe', 'nutanix', 'aristanetworks',
    'towerresearchcapital', 'squarepointcapital', 'datadog', 'elastic',
    'mongodb', 'okta', 'sprinklr', 'cloudflare', 'roblox', 'snowflake',
    'couchbase', 'cloudera', 'purestorage', 'hashicorp'
]

# Target slugs for Lever boards
lever_slugs = [
    'paytm', 'zomato', 'blinkit', 'zepto', 'incred', 'pocket-fm',
    'jupiter', 'navi', 'fi-money', 'clevertap', 'urbanpiper',
    'simpl', 'kuku-fm', 'groww'
]

# Target slugs for Ashby boards
ashby_slugs = [
    'atlys', 'sarvam', 'avoca', 'forma-ai', 'atlan', 'aiprise',
    'together-ai', 'plane', 'squadstack', 'mercury'
]

# Load already known URLs to deduplicate
with open('data/all_existing_urls.json') as f:
    existing_data = json.load(f)
existing_urls = set(existing_data.get('urls', []))

found_candidates = []

fresher_title_keywords = [
    r'\bintern\b', r'\binternship\b', r'\bgraduate\b', r'\btrainee\b',
    r'\bget\b', r'\bcampus\b', r'\bearly\s+career\b', r'\bcollege\b',
    r'\buniversity\b', r'\bentry\b', r'\bjunior\b', r'\bapprentice\b',
    r'\b2026\b'
]

def is_fresher_title(title):
    t = title.lower()
    return any(re.search(pat, t) for pat in fresher_title_keywords)

print("--- Scanning Greenhouse Boards ---")
for slug in greenhouse_slugs:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
            data = json.loads(r.read())
            jobs = data.get('jobs', [])
            for j in jobs:
                title = j.get('title', '')
                loc = j.get('location', {}).get('name', '')
                abs_url = j.get('absolute_url', '')
                
                # Check India location
                loc_lower = loc.lower()
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india:
                    continue
                
                if is_fresher_title(title):
                    content = html.unescape(re.sub(r'<[^>]+>', ' ', j.get('content', ''))).lower()
                    
                    # Verify no hard 2+ YOE
                    has_exp = re.search(r'\b([2-9]|\d{2,})\+?\s*(?:to\s*\d+\s*)?years?\b', content)
                    has_exp_en = re.search(r'\b([2-9]|\d{2,})\s*[\u2013\u2014]\s*\d+\s*years?\b', content)
                    
                    exp_mention = None
                    if has_exp:
                        exp_mention = has_exp.group()
                    elif has_exp_en:
                        exp_mention = has_exp_en.group()
                        
                    found_candidates.append({
                        'company': slug.capitalize(),
                        'title': title,
                        'location': loc,
                        'url': abs_url,
                        'board': 'greenhouse',
                        'exp_mention': exp_mention,
                        'content_snippet': content[:300]
                    })
                    print(f"  [GH] {slug}: {title} ({loc}) - Exp: {exp_mention}")
    except Exception as e:
        pass

print("\n--- Scanning Lever Boards ---")
for slug in lever_slugs:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
            jobs = json.loads(r.read())
            for j in jobs:
                title = j.get('text', '')
                loc = j.get('categories', {}).get('location', '')
                h_url = j.get('hostedUrl', '')
                
                loc_lower = loc.lower() if loc else ''
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india:
                    continue
                    
                if is_fresher_title(title):
                    desc = html.unescape(j.get('descriptionPlain', '') + ' ' + j.get('additionalPlain', '')).lower()
                    has_exp = re.search(r'\b([2-9]|\d{2,})\+?\s*(?:to\s*\d+\s*)?years?\b', desc)
                    has_exp_en = re.search(r'\b([2-9]|\d{2,})\s*[\u2013\u2014]\s*\d+\s*years?\b', desc)
                    
                    exp_mention = None
                    if has_exp:
                        exp_mention = has_exp.group()
                    elif has_exp_en:
                        exp_mention = has_exp_en.group()
                        
                    found_candidates.append({
                        'company': slug.capitalize(),
                        'title': title,
                        'location': loc,
                        'url': h_url,
                        'board': 'lever',
                        'exp_mention': exp_mention,
                        'content_snippet': desc[:300]
                    })
                    print(f"  [LEVER] {slug}: {title} ({loc}) - Exp: {exp_mention}")
    except Exception as e:
        pass

print("\n--- Scanning Ashby Boards ---")
for slug in ashby_slugs:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
            data = json.loads(r.read())
            jobs = data.get('jobs', [])
            for j in jobs:
                title = j.get('title', '')
                loc = j.get('location', '')
                jid = j.get('id', '')
                h_url = f"https://jobs.ashbyhq.com/{slug}/{jid}"
                
                loc_lower = loc.lower() if loc else ''
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india:
                    continue
                    
                if is_fresher_title(title):
                    found_candidates.append({
                        'company': slug.capitalize(),
                        'title': title,
                        'location': loc,
                        'url': h_url,
                        'board': 'ashby',
                        'exp_mention': None,
                        'content_snippet': ''
                    })
                    print(f"  [ASHBY] {slug}: {title} ({loc})")
    except Exception as e:
        pass

with open('data/fresh_2026_candidates.json', 'w') as f:
    json.dump(found_candidates, f, indent=2)

print(f"\nTotal potential fresher candidates found: {len(found_candidates)}")
