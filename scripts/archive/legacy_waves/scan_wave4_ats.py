import urllib.request
import json
import ssl
import re
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

with open('data/all_existing_urls.json') as f:
    existing = json.load(f)
existing_urls = set(existing['urls'])

found = []

# Greenhouse candidate slugs
gh_slugs = [
    ('Glean', 'gleanworkplace'),
    ('Glean', 'glean'),
    ('Moveworks', 'moveworks'),
    ('Observe.ai', 'observeai'),
    ('Postman', 'postman'),
    ('Arista Networks', 'aristanetworks'),
    ('Snowflake', 'snowflake'),
    ('Twilio', 'twilio'),
    ('Elastic', 'elastic'),
    ('MongoDB', 'mongodb'),
    ('Okta', 'okta'),
    ('Sprinklr', 'sprinklr'),
    ('Groww', 'groww'),
    ('Swiggy', 'swiggy'),
    ('Zepto', 'zepto'),
    ('Nutanix', 'nutanix'),
    ('NetApp', 'netapp'),
    ('Palo Alto Networks', 'paloaltonetworks'),
    ('Cloudflare', 'cloudflare'),
    ('Databricks', 'databricks'),
    ('Coinbase', 'coinbase'),
    ('Thoughtworks', 'thoughtworks'),
    ('InMobi', 'inmobi'),
    ('Glance', 'glance'),
    ('Graviton Research Capital', 'gravitonresearchcapital')
]

def check_gh(item):
    name, slug = item
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
                
                loc_lower = loc.lower()
                is_india = any(k in loc_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india:
                    continue
                    
                t_lower = title.lower()
                is_senior = any(k in t_lower for k in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director', 'manager', 'head', 'architect', 'ii', '2', '3', 'iii', 'iv', '4'])
                if is_senior:
                    continue
                    
                is_fresher_fit = any(k in t_lower for k in [
                    'intern', 'graduate', 'fresher', 'trainee', 'campus', 'entry', 'junior', 'associate', 
                    'engineer 1', 'engineer i', 'sde 1', 'sde i', 'analyst', 'developer', 'software engineer'
                ])
                
                if is_fresher_fit:
                    clean_u = j_url.lower().rstrip('/')
                    if clean_u not in existing_urls:
                        found.append({
                            'source': 'greenhouse',
                            'company': name,
                            'title': title,
                            'location': loc,
                            'url': j_url,
                            'content': content[:300]
                        })
    except Exception as e:
        pass

# Lever candidate slugs
lever_slugs = [
    ('Zepto', 'zeptonow'),
    ('Zepto', 'zepto'),
    ('Swiggy', 'swiggy'),
    ('Delhivery', 'delhivery'),
    ('Urban Company', 'urbancompany'),
    ('Pine Labs', 'pinelabs'),
    ('Shiprocket', 'shiprocket'),
    ('Lenskart', 'lenskart'),
    ('Spinny', 'spinny'),
    ('MakeMyTrip', 'makemytrip'),
    ('Cred', 'cred'),
    ('Meesho', 'meesho'),
    ('Paytm', 'paytm')
]

def check_lever(item):
    name, slug = item
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
                is_senior = any(k in t_lower for k in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director', 'manager', 'head', 'architect', 'ii', '2', '3', 'iii', 'iv', '4'])
                if is_senior:
                    continue
                    
                is_fresher_fit = any(k in t_lower for k in [
                    'intern', 'graduate', 'fresher', 'trainee', 'campus', 'entry', 'junior', 'associate', 
                    'engineer 1', 'engineer i', 'sde 1', 'sde i', 'analyst', 'developer', 'software engineer'
                ])
                
                if is_fresher_fit:
                    clean_u = j_url.lower().rstrip('/')
                    if clean_u not in existing_urls:
                        found.append({
                            'source': 'lever',
                            'company': name,
                            'title': title,
                            'location': loc or 'India',
                            'url': j_url,
                            'content': desc[:300]
                        })
    except Exception as e:
        pass

# Ashby candidate slugs
ashby_slugs = [
    ('Glean', 'glean'),
    ('Mistral AI', 'mistral'),
    ('Sarvam AI', 'sarvam'),
    ('Level AI', 'level-ai'),
    ('Atlys', 'atlys'),
    ('Atlan', 'atlan'),
    ('Composio', 'composio'),
    ('Krutrim', 'krutrim'),
    ('PhysicsWallah', 'physicswallah'),
    ('Aiprise', 'aiprise'),
    ('Avoca', 'avoca')
]

def check_ashby(item):
    name, slug = item
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
                is_senior = any(k in t_lower for k in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director', 'manager', 'head', 'architect', 'ii', '2', '3', 'iii', 'iv', '4'])
                if is_senior:
                    continue
                    
                is_fresher_fit = any(k in t_lower for k in [
                    'intern', 'graduate', 'fresher', 'trainee', 'campus', 'entry', 'junior', 'associate', 
                    'engineer 1', 'engineer i', 'sde 1', 'sde i', 'analyst', 'developer', 'software engineer', 'resident'
                ])
                
                if is_fresher_fit:
                    clean_u = j_url.lower().rstrip('/')
                    if clean_u not in existing_urls:
                        found.append({
                            'source': 'ashby',
                            'company': name,
                            'title': title,
                            'location': loc or 'India',
                            'url': j_url,
                            'content': ''
                        })
    except Exception as e:
        pass

print("Starting parallel scanning of Wave 4 ATS endpoints...")
with ThreadPoolExecutor(max_workers=10) as ex:
    ex.map(check_gh, gh_slugs)
    ex.map(check_lever, lever_slugs)
    ex.map(check_ashby, ashby_slugs)

print(f"Total Wave 4 candidate postings found: {len(found)}")
with open('data/raw_wave4_ats_jobs.json', 'w') as f:
    json.dump(found, f, indent=2)
