import json
import re
import time
import ssl
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Load candidates from both sources:
# 1. Harvested LinkedIn cards
with open('data/scratch_harvested_cards.json') as f:
    cards = json.load(f)

# 2. ATS matches from Ashby/Greenhouse/Lever
with open('data/scratch_wave9_raw_matches.json') as f:
    ats_matches = json.load(f)

print(f"Loaded {len(cards)} LinkedIn cards and {len(ats_matches)} ATS postings.")

# Target priority companies (Tier-1 Tech, Global Capability Centers, Top High-Growth Startups, Quant Funds)
priority_companies = [
    'bain', 'nk securities', 'quadeye', 'united airlines', 'american express',
    'thales', 'mykaarma', 'siemens energy', 'safe security', 'atlys', 'xenonstack',
    'exl', 'pwc', 'ibm', 'infosys', 'accenture', 'plane', 'cursor', 'ema',
    'avoca', 'cartesia', 'bolna', 'cognition', 'purestorage', 'squarepoint',
    'single store', 'aiprise', 'saaf ai', 'atlan', 'together ai', 'delhivery',
    'shadowfax', 'cars24', 'spinny', 'urban company', 'zomato', 'blinkit', 'zepto',
    'groww', 'paytm', 'incred', 'slice', 'cred', 'meesho', 'postman', 'browserstack'
]

# Tech keywords that MUST be in title
required_tech = [
    'software', 'engineer', 'developer', 'backend', 'data', 'python',
    'machine learning', 'ml', 'ai', 'trainee', 'get', 'sde', 'qa', 'sdet'
]

# Hard reject title words
reject_titles = [
    'intern', 'internship', 'summer', 'winter', 'senior', 'sr', 'lead',
    'manager', 'director', 'principal', 'staff', 'ii', 'iii', '2', '3', '4',
    'sales', 'marketing', 'hr', 'recruiter', 'business development',
    'product management', 'operations', 'customer support', 'bpo', 'telecaller',
    'civil', 'mechanical site', 'php developer', 'wordpress'
]

filtered_candidates = []

# Process ATS roles first
for a in ats_matches:
    c_lower = a.get('company', '').lower()
    t_lower = a.get('title', '').lower()
    if any(re.search(r'\b' + re.escape(w) + r'\b', t_lower) for w in reject_titles):
        continue
    filtered_candidates.append({
        'company': a.get('company'),
        'title': a.get('title'),
        'location': a.get('location'),
        'url': a.get('url'),
        'source': f"Direct ATS ({a.get('platform')})",
        'is_ats': True
    })

# Process LinkedIn cards
for c in cards:
    comp = c.get('company', '')
    title = c.get('title', '')
    loc = c.get('location', '')
    url = c.get('url', '')

    c_lower = comp.lower()
    t_lower = title.lower()
    loc_lower = loc.lower()

    if any(re.search(r'\b' + re.escape(w) + r'\b', t_lower) for w in reject_titles):
        continue

    if not any(k in t_lower for k in required_tech):
        continue

    # Priority score
    priority = 0
    if any(p in c_lower for p in priority_companies):
        priority += 10
    if any(ncr in loc_lower for ncr in ['noida', 'gurgaon', 'gurugram', 'delhi']):
        priority += 5
    if any(k in t_lower for k in ['python', 'backend', 'data', 'ml', 'ai']):
        priority += 3
    if any(k in t_lower for k in ['graduate', 'trainee', 'get', 'entry', 'junior', 'associate']):
        priority += 3

    c['priority'] = priority
    c['is_ats'] = False
    c['source'] = 'Public Requisition (LinkedIn Guest)'
    filtered_candidates.append(c)

filtered_candidates.sort(key=lambda x: x.get('priority', 0), reverse=True)
print(f"Total candidate roles shortlisted for deep JD scraping: {len(filtered_candidates)}")

# Take top 80 for deep scraping
to_scrape = filtered_candidates[:80]
with open('data/scratch_candidates_to_scrape.json', 'w') as f:
    json.dump(to_scrape, f, indent=2)

print("Saved top candidates to data/scratch_candidates_to_scrape.json")
