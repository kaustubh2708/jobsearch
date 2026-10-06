import urllib.request
import json
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0'}

# Load existing URLs to avoid any duplicates
with open('data/existing_job_links_set.json') as f:
    existing = json.load(f)
existing_urls = set(existing['urls'])

new_jobs = []

# 1. Check Greenhouse boards
gh_boards = [
    ('Graviton Research Capital', 'gravitonresearchcapital'),
    ('Glance', 'glance'),
    ('InMobi', 'inmobi'),
    ('Groww', 'groww'),
    ('Thoughtworks', 'thoughtworks'),
    ('Slice', 'slice'),
    ('Instawork', 'instawork'),
    ('Rubrik', 'rubrik'),
    ('NK Securities', 'nksecuritiesresearch'),
    ('AlphaGrep', 'alphagrepsecurities'),
    ('Coinbase', 'coinbase'),
    ('Bitwarden', 'bitwarden')
]

for company_name, slug in gh_boards:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read())
            jobs = data.get('jobs', [])
            for j in jobs:
                title = j.get('title', '')
                loc = j.get('location', {}).get('name', '')
                j_url = j.get('absolute_url', '')
                content = j.get('content', '')
                
                # Check location
                loc_lower = loc.lower()
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india:
                    continue
                
                # Check title relevance for fresher / early career / intern
                t_lower = title.lower()
                is_senior = any(k in t_lower for k in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director', 'manager', 'head', 'architect', 'ii', '2', '3', 'iii'])
                if is_senior:
                    continue
                    
                is_fresher_candidate = any(k in t_lower for k in [
                    'intern', 'graduate', 'fresher', 'trainee', 'campus', 'entry', 'junior', 'associate', 
                    'engineer 1', 'engineer i', 'sde 1', 'sde i', 'analyst', 'developer'
                ]) or ('software engineer' in t_lower and not is_senior)
                
                if is_fresher_candidate:
                    if j_url.lower().rstrip('/') not in existing_urls:
                        new_jobs.append({
                            'source': 'greenhouse',
                            'company': company_name,
                            'title': title,
                            'location': loc,
                            'url': j_url,
                            'content': content[:500]
                        })
    except Exception as e:
        pass

# 2. Check Lever boards
lever_boards = [
    ('Meesho', 'meesho'),
    ('Paytm', 'paytm'),
    ('Cred', 'cred'),
    ('Epifi', 'epifi')
]

for company_name, slug in lever_boards:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            jobs = json.loads(r.read())
            for j in jobs:
                title = j.get('text', '')
                loc = j.get('categories', {}).get('location', '')
                j_url = j.get('hostedUrl', '')
                desc = j.get('descriptionPlain', '')
                
                loc_lower = loc.lower()
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india and loc:
                    continue
                    
                t_lower = title.lower()
                is_senior = any(k in t_lower for k in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director', 'manager', 'head', 'architect', 'ii', '2', '3', 'iii'])
                if is_senior:
                    continue
                    
                is_fresher_candidate = any(k in t_lower for k in [
                    'intern', 'graduate', 'fresher', 'trainee', 'campus', 'entry', 'junior', 'associate', 
                    'engineer 1', 'engineer i', 'sde 1', 'sde i', 'analyst', 'developer'
                ]) or ('software engineer' in t_lower and not is_senior)
                
                if is_fresher_candidate:
                    if j_url.lower().rstrip('/') not in existing_urls:
                        new_jobs.append({
                            'source': 'lever',
                            'company': company_name,
                            'title': title,
                            'location': loc or 'India',
                            'url': j_url,
                            'content': desc[:500]
                        })
    except Exception as e:
        pass

# 3. Check Ashby boards
ashby_boards = [
    ('Atlys', 'atlys'),
    ('Atlan', 'atlan'),
    ('Level AI', 'level-ai'),
    ('Sarvam AI', 'sarvam'),
    ('Composio', 'composio'),
    ('Plane', 'plane'),
    ('PlayPower Labs', 'playpowerlabs'),
    ('Aiprise', 'aiprise'),
    ('Avoca', 'avoca')
]

for company_name, slug in ashby_boards:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read())
            jobs = data.get('jobs', [])
            for j in jobs:
                title = j.get('title', '')
                loc = j.get('location', '')
                jid = j.get('id', '')
                j_url = f"https://jobs.ashbyhq.com/{slug}/{jid}"
                
                loc_lower = str(loc).lower()
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india and loc:
                    continue
                    
                t_lower = title.lower()
                is_senior = any(k in t_lower for k in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director', 'manager', 'head', 'architect', 'ii', '2', '3', 'iii'])
                if is_senior:
                    continue
                    
                is_fresher_candidate = any(k in t_lower for k in [
                    'intern', 'graduate', 'fresher', 'trainee', 'campus', 'entry', 'junior', 'associate', 
                    'engineer 1', 'engineer i', 'sde 1', 'sde i', 'analyst', 'developer', 'resident'
                ]) or ('engineer' in t_lower and not is_senior)
                
                if is_fresher_candidate:
                    if j_url.lower().rstrip('/') not in existing_urls:
                        new_jobs.append({
                            'source': 'ashby',
                            'company': company_name,
                            'title': title,
                            'location': loc or 'India / Remote',
                            'url': j_url,
                            'content': ''
                        })
    except Exception as e:
        pass

print(f'Total candidates found across ATS boards: {len(new_jobs)}')
with open('data/raw_new_ats_jobs.json', 'w') as f:
    json.dump(new_jobs, f, indent=2)
