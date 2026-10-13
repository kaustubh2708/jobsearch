import urllib.request
import ssl
import json
import re
import html

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*'
}

with open('data/all_existing_urls.json') as f:
    existing_meta = json.load(f)
seen_urls = set(existing_meta.get('urls', []))

greenhouse_boards = [
    'rubrik', 'stripe', 'towerresearchcapital', 'squarepointcapital',
    'postman', 'browserstack', 'inmobi', 'swiggy', 'sharechat',
    'urbancompany', 'cars24', 'physicswallah', 'sliceit', 'cred',
    'meesho', 'nutanix', 'aristanetworks', 'datadog', 'elastic',
    'couchbase', 'cloudera', 'purestorage', 'hashicorp', 'cloudflare',
    'roblox', 'snowflake', 'cohere', 'anthropic', 'gleanwork'
]

lever_boards = [
    'paytm', 'zomato', 'blinkit', 'zepto', 'incred', 'jupiter',
    'navi', 'fi-money', 'clevertap', 'urbanpiper', 'simpl', 'kuku-fm',
    'groww', 'razorpay'
]

ashby_boards = [
    'atlys', 'sarvam', 'avoca', 'forma-ai', 'atlan', 'aiprise',
    'together-ai', 'plane', 'squadstack', 'mercury', 'cursor'
]

# Strict engineering title match
tech_keywords = [
    r'\bsoftware\b', r'\bdeveloper\b', r'\bengineer\b', r'\bbackend\b',
    r'\bdata\b', r'\bmachine\s+learning\b', r'\bml\b', r'\bai\b',
    r'\bpython\b', r'\bqa\b', r'\bsdet\b', r'\btest\b', r'\bsystems\b',
    r'\bfull\s*stack\b', r'\binfra\b', r'\bquant\b', r'\bresearcher\b'
]

# Explicit fresher / intern marker
fresher_markers = [
    r'\bintern\b', r'\binternship\b', r'\bgraduate\b', r'\btrainee\b',
    r'\bget\b', r'\bcampus\b', r'\bearly\s+career\b', r'\buniversity\b',
    r'\bjunior\b', r'\bapprentice\b', r'\b2026\b'
]

non_tech = [
    'talent acquisition', 'recruiter', 'hr', 'sales', 'marketing',
    'business development', 'growth', 'creative', 'communications',
    'finance', 'accounting', 'fulfillment', 'content', 'legal',
    'operations', 'specialist', 'investigations'
]

def is_valid_tech_fresher(title):
    t = title.lower()
    if any(nt in t for nt in non_tech):
        return False
    has_tech = any(re.search(k, t) for k in tech_keywords)
    has_fresher = any(re.search(f, t) for f in fresher_markers)
    return has_tech and has_fresher

results = []

print("Scanning Greenhouse...")
for slug in greenhouse_boards:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            data = json.loads(r.read())
            for j in data.get('jobs', []):
                title = j.get('title', '')
                loc = j.get('location', {}).get('name', '')
                abs_url = j.get('absolute_url', '')
                
                loc_lower = loc.lower()
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india:
                    continue
                    
                if is_valid_tech_fresher(title):
                    content = html.unescape(re.sub(r'<[^>]+>', ' ', j.get('content', ''))).lower()
                    # Check for 2+ YOE
                    has_exp = re.search(r'\b([2-9]|\d{2,})\+?\s*(?:to\s*\d+\s*)?years?\b', content)
                    has_exp_en = re.search(r'\b([2-9]|\d{2,})\s*[\u2013\u2014]\s*\d+\s*years?\b', content)
                    
                    if not has_exp and not has_exp_en:
                        if abs_url.lower() not in seen_urls:
                            results.append({
                                'company': slug.capitalize(),
                                'title': title,
                                'location': loc,
                                'url': abs_url,
                                'source': 'Greenhouse'
                            })
                            print(f"  [GH MATCH] {slug}: {title} ({loc})")
    except:
        pass

print("\nScanning Lever...")
for slug in lever_boards:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            jobs = json.loads(r.read())
            for j in jobs:
                title = j.get('text', '')
                loc = j.get('categories', {}).get('location', '')
                h_url = j.get('hostedUrl', '')
                
                loc_lower = loc.lower() if loc else ''
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india:
                    continue
                    
                if is_valid_tech_fresher(title):
                    desc = html.unescape(j.get('descriptionPlain', '') + ' ' + j.get('additionalPlain', '')).lower()
                    has_exp = re.search(r'\b([2-9]|\d{2,})\+?\s*(?:to\s*\d+\s*)?years?\b', desc)
                    has_exp_en = re.search(r'\b([2-9]|\d{2,})\s*[\u2013\u2014]\s*\d+\s*years?\b', desc)
                    
                    if not has_exp and not has_exp_en:
                        if h_url.lower() not in seen_urls:
                            results.append({
                                'company': slug.capitalize(),
                                'title': title,
                                'location': loc,
                                'url': h_url,
                                'source': 'Lever'
                            })
                            print(f"  [LEVER MATCH] {slug}: {title} ({loc})")
    except:
        pass

print("\nScanning Ashby...")
for slug in ashby_boards:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            data = json.loads(r.read())
            for j in data.get('jobs', []):
                title = j.get('title', '')
                loc = j.get('location', '')
                jid = j.get('id', '')
                h_url = f"https://jobs.ashbyhq.com/{slug}/{jid}"
                
                loc_lower = loc.lower() if loc else ''
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india:
                    continue
                    
                if is_valid_tech_fresher(title):
                    if h_url.lower() not in seen_urls:
                        results.append({
                            'company': slug.capitalize(),
                            'title': title,
                            'location': loc,
                            'url': h_url,
                            'source': 'Ashby'
                        })
                        print(f"  [ASHBY MATCH] {slug}: {title} ({loc})")
    except:
        pass

with open('data/fresher_ats_cards.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nTotal verified fresher ATS roles found: {len(results)}")
