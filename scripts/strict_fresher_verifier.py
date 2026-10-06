import urllib.request
import urllib.parse
import ssl
import json
import re
import html
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

# 1. Load candidates
with open('data/promising_fresher_cards.json') as f:
    linkedin_cards = json.load(f)

with open('data/fresher_ats_cards.json') as f:
    ats_cards = json.load(f)

# Also load existing deduplication set
with open('data/all_existing_urls.json') as f:
    existing_meta = json.load(f)
existing_urls = set(existing_meta.get('urls', []))

# Filter candidates: India only, exclude foreign locations
def is_india_loc(loc):
    l = loc.lower()
    return any(k in l for k in ['india', 'noida', 'gurgaon', 'gurugram', 'delhi', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'mumbai', 'remote']) and not any(k in l for k in ['california', 'united states', 'san jose', 'london', 'singapore', 'ca', 'ny', 'austin', 'seattle'])

india_linkedin = [c for c in linkedin_cards if is_india_loc(c.get('location', ''))]
print(f"India LinkedIn cards: {len(india_linkedin)}")
print(f"ATS cards: {len(ats_cards)}")

# Take top priority candidates to deep-verify
top_candidates = []

# Add ATS candidates first (highly reliable direct applications)
for ac in ats_cards:
    top_candidates.append({
        'company': ac['company'],
        'title': ac['title'],
        'location': ac['location'],
        'url': ac['url'],
        'source': ac['source']
    })

# Add top LinkedIn candidates
for lc in india_linkedin[:50]:
    top_candidates.append({
        'company': lc['company'],
        'title': lc['title'],
        'location': lc['location'],
        'url': lc['url'],
        'source': 'LinkedIn'
    })

print(f"Total candidates queued for deep verification: {len(top_candidates)}")

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)

verified_roles = []
rejected_roles = []

hard_exp_patterns = [
    r'\b([2-9]|\d{2,})\+?\s*(?:to\s*\d+\s*)?years?\b',
    r'\b([2-9]|\d{2,})\s*[\u2013\u2014]\s*\d+\s*years?\b',
    r'\bminimum\s+([2-9]|\d{2,})\s+years?\b',
    r'\bat\s+least\s+([2-9]|\d{2,})\s+years?\b'
]

fresher_signals = [
    r'\bintern\b', r'\binternship\b', r'\bgraduate\s+engineer\s+trainee\b',
    r'\bget\b', r'\b0.?2\s*years?\b', r'\b0.?1\s*years?\b', r'\b0\s*years?\b',
    r'\b2026\b', r'\bfresh(?:er|ers)\b', r'\bcampus\b', r'\bcollege\b',
    r'\buniversity\b', r'\bentry.?level\b', r'\bno\s+prior\s+experience\b'
]

def score_role(company, title, location, jd_text):
    score = 0
    t = (title + ' ' + jd_text).lower()
    loc = location.lower()
    
    # Role alignment (30 pts)
    if any(k in t for k in ['backend', 'software engineer', 'sde', 'python developer']):
        score += 30
    elif any(k in t for k in ['data engineer', 'ml engineer', 'ai engineer', 'machine learning']):
        score += 26
    elif any(k in t for k in ['graduate engineer trainee', 'get', 'qa', 'sdet']):
        score += 22
    else:
        score += 15

    # Experience level fit (20 pts)
    if any(k in t for k in ['2026 batch', '0-1 year', '0-2 year', '0 year', 'no experience required']):
        score += 20
    elif any(k in t for k in ['intern', 'internship', 'graduate trainee', 'campus']):
        score += 18
    elif 'junior' in t or 'entry level' in t:
        score += 15

    # Tech stack fit (20 pts)
    stack_pts = 0
    if 'python' in t: stack_pts += 7
    if any(k in t for k in ['fastapi', 'flask', 'django', 'rest api']): stack_pts += 5
    if any(k in t for k in ['sql', 'postgres', 'postgresql', 'database']): stack_pts += 3
    if any(k in t for k in ['redis', 'celery', 'kafka', 'message queue']): stack_pts += 3
    if any(k in t for k in ['nlp', 'bert', 'machine learning', 'pytorch', 'tensorflow', 'llm']): stack_pts += 4
    score += min(20, stack_pts)

    # Location fit (10 pts)
    if any(k in loc for k in ['noida', 'gurgaon', 'gurugram', 'delhi', 'ncr']):
        score += 10
    elif any(k in loc for k in ['remote']):
        score += 9
    elif any(k in loc for k in ['bengaluru', 'bangalore']):
        score += 7
    else:
        score += 6

    # Brand / Salary likelihood (15 pts)
    comp_lower = company.lower()
    if any(tc in comp_lower for tc in ['tower research', 'rubrik', 'stripe', 'squarepoint', 'zomato', 'blinkit', 'cars24', 'adobe', 'goldman sachs', 'amazon', 'google', 'microsoft']):
        score += 15
    elif any(tc in comp_lower for tc in ['greyorange', 'pwc', 'paytm', 'incred', 'cred', 'swiggy', 'slice', 'meesho', 'postman']):
        score += 12
    else:
        score += 9

    # Freshness & Confidence (5 pts)
    score += 5
    return min(99, score)

try:
    for idx, c in enumerate(top_candidates):
        url = c['url']
        company = c['company']
        title = c['title']
        loc = c['location']
        src = c['source']
        
        print(f"\n[{idx+1}/{len(top_candidates)}] Verifying: {company} - {title} ({loc})")
        
        # Scrape page
        text = ""
        try:
            if src == 'LinkedIn':
                driver.get(url)
                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Check if job is closed
                closed_alert = soup.find('div', class_='closed-job__alert')
                if closed_alert or "no longer accepting applications" in driver.page_source.lower():
                    print("   -> ❌ REJECTED: Job is closed / no longer accepting applications.")
                    rejected_roles.append({**c, 'reason': 'Closed on LinkedIn'})
                    continue
                
                # Extract JD
                desc_div = soup.find('div', class_='show-more-less-html__markup') or soup.find('div', class_='description__text')
                if desc_div:
                    text = desc_div.get_text(separator=' ', strip=True)
                else:
                    text = soup.get_text(separator=' ', strip=True)
            else:
                # Direct HTTP for ATS
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                    raw = r.read().decode('utf-8', errors='ignore')
                    text = re.sub(r'<[^>]+>', ' ', raw)
                    text = re.sub(r'\s+', ' ', text)
        except Exception as e:
            print(f"   -> ❌ Error fetching JD: {e}")
            rejected_roles.append({**c, 'reason': f"Fetch error: {e}"})
            continue

        clean_text = text.lower()
        
        # Verify Experience
        hard_reject = False
        reject_reason = ""
        for pat in hard_exp_patterns:
            m = re.search(pat, clean_text)
            if m:
                # check context to ensure it's a requirement
                start = max(0, m.start()-50)
                end = min(len(clean_text), m.end()+80)
                snip = clean_text[start:end]
                # Ignore if it mentions "0-2 years" or "0-3 years"
                if re.search(r'\b0\s*[\u2013\u2014\-to]\s*[1-3]\s*years?\b', snip):
                    continue
                if any(w in snip for w in ['experience', 'work', 'background', 'minimum', 'required', 'qualification', 'must have']):
                    hard_reject = True
                    reject_reason = f"Requires experience: '{m.group()}' in context: ...{snip}..."
                    break
        
        if hard_reject:
            print(f"   -> ❌ REJECTED: {reject_reason}")
            rejected_roles.append({**c, 'reason': reject_reason})
            continue
            
        # Check fresher signals
        fresher_found = any(re.search(f, clean_text) for f in fresher_signals) or any(f in title.lower() for f in ['intern', 'trainee', 'get', 'junior', 'graduate'])
        
        if not fresher_found:
            print("   -> ❌ REJECTED: No explicit fresher / intern / 0 YOE signal in JD.")
            rejected_roles.append({**c, 'reason': 'No explicit 0 YOE / intern / fresher signal in JD'})
            continue
            
        # Role is VERIFIED ELIGIBLE!
        score = score_role(company, title, loc, clean_text)
        print(f"   -> ✅ VERIFIED FRESHER-ELIGIBLE! Match Score: {score}/100")
        
        verified_roles.append({
            **c,
            'match_score': score,
            'jd_snippet': text[:400].replace('\n', ' ')
        })

finally:
    driver.quit()

print(f"\n=== VERIFICATION SUMMARY ===")
print(f"Total Eligible: {len(verified_roles)}")
print(f"Total Rejected: {len(rejected_roles)}")

with open('data/verified_fresh_roles_w5.json', 'w') as f:
    json.dump(verified_roles, f, indent=2)

with open('data/rejected_fresh_roles_w5.json', 'w') as f:
    json.dump(rejected_roles, f, indent=2)
