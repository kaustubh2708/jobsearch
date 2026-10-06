import json
import re
import time
import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Load raw cards
with open('data/raw_entry_level_cards.json') as f:
    cards = json.load(f)

print(f"Total raw entry-level cards to filter: {len(cards)}")

# Target companies to prioritize
top_tier_companies = [
    'amazon', 'google', 'microsoft', 'adobe', 'cisco', 'oracle', 'sap',
    'servicenow', 'salesforce', 'atlassian', 'intuit', 'uber', 'flipkart',
    'swiggy', 'zomato', 'blinkit', 'zepto', 'urban company', 'paytm', 'cars24',
    'incred', 'slice', 'cred', 'meesho', 'postman', 'browserstack', 'inmobi',
    'rubrik', 'stripe', 'goldman sachs', 'morgan stanley', 'd. e. shaw',
    'tower research', 'squarepoint', 'graviton', 'hpe', 'hewlett packard',
    'boeing', 'airtel', 'info edge', 'naukri', 'physicswallah', 'groww',
    'jupiter', 'navi', 'sprinklr', 'optum', 'barclays', 'bny mellon',
    'wells fargo', 'american express', 'deloitte', 'pwc', 'kpmg', 'ey',
    'wadhwani', 'greyorange', 'ingersoll rand', 'prismagic', 'tecnod8',
    'together ai', 'atlan', 'atlys', 'sarvam', 'clevertap', 'juspay'
]

# Tech keywords that MUST be in title
required_tech_keywords = [
    'software', 'engineer', 'developer', 'backend', 'data', 'python',
    'machine learning', 'ml', 'ai', 'trainee', 'get', 'sde'
]

# Hard reject keywords in title
hard_reject_title = [
    'intern', 'internship', 'summer', 'winter', 'senior', 'sr', 'lead',
    'manager', 'director', 'principal', 'staff', 'ii', 'iii', '2', '3', '4',
    'sales', 'marketing', 'hr', 'recruiter', 'business development',
    'product management', 'operations', 'customer support', 'bpo', 'telecaller',
    'graphic', 'ui/ux', 'civil', 'mechanical site'
]

filtered_priority = []
for c in cards:
    t = c.get('title', '').lower()
    comp = c.get('company', '').lower()
    loc = c.get('location', '').lower()
    
    # Must not have reject words
    if any(re.search(r'\b' + re.escape(w) + r'\b', t) for w in hard_reject_title):
        continue
        
    # Must have tech keyword
    if not any(k in t for k in required_tech_keywords):
        continue
        
    # Must be in India
    is_india = any(k in loc for k in ['india', 'noida', 'gurgaon', 'gurugram', 'delhi', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'mumbai', 'remote'])
    is_foreign = any(k in loc for k in ['united states', 'california', 'ca', 'ny', 'london', 'singapore', 'germany', 'canada'])
    if not is_india or is_foreign:
        continue
        
    priority = 0
    if any(tc in comp for tc in top_tier_companies):
        priority += 4
    if any(k in loc for k in ['noida', 'gurgaon', 'gurugram', 'delhi']):
        priority += 3
    if 'python' in t or 'backend' in t or 'data' in t or 'ml' in t or 'ai' in t:
        priority += 2
    if 'trainee' in t or 'get' in t or 'graduate' in t or 'engineer i' in t:
        priority += 2
        
    c['priority_score'] = priority
    filtered_priority.append(c)

filtered_priority.sort(key=lambda x: x['priority_score'], reverse=True)
print(f"Filtered promising candidates for live verification: {len(filtered_priority)}")

# Deep verify top 40 candidates using Selenium
candidates_to_verify = filtered_priority[:40]

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)

verified_clean_roles = []
rejected_roles = []

# Hard reject patterns for experience: 3+ years, 4+ years, etc.
high_exp_patterns = [
    r'\b([3-9]|\d{2,})\+?\s*(?:to\s*\d+\s*)?years?\b',
    r'\b([3-9]|\d{2,})\s*[\u2013\u2014]\s*\d+\s*years?\b',
    r'\bminimum\s+([3-9]|\d{2,})\s+years?\b',
    r'\bat\s+least\s+([3-9]|\d{2,})\s+years?\b'
]

# Explicit 0-1, 0-2, 0 YOE signals
entry_signals = [
    r'\b0\s*[\u2013\u2014\-to]\s*[1-2]\s*years?\b',
    r'\b0\s*years?\b',
    r'\b0.?1\s*years?\b',
    r'\b0.?2\s*years?\b',
    r'\b(?:freshers?|freshly\s+graduated?|new\s+grad|entry.?level)\b',
    r'\b(?:graduate\s+engineer\s+trainee|get)\b',
    r'\b(?:2025|2026)\s*batch\b',
    r'\bno\s+prior\s+experience\b',
    r'\b1\s*year\s+or\s+less\b'
]

def score_fte_role(company, title, loc, text):
    score = 0
    t = (title + ' ' + text).lower()
    l = loc.lower()
    
    # Role alignment (30 pts)
    if any(k in t for k in ['backend', 'software engineer', 'sde', 'python developer']):
        score += 30
    elif any(k in t for k in ['data engineer', 'ml engineer', 'ai engineer', 'machine learning']):
        score += 26
    elif any(k in t for k in ['graduate engineer trainee', 'get']):
        score += 22
    else:
        score += 15

    # Experience level fit (20 pts)
    if any(k in t for k in ['0-1 year', '0-2 year', '0 year', 'freshers welcome', 'no experience required', '2026']):
        score += 20
    elif any(k in t for k in ['graduate trainee', 'get', 'entry level', 'junior']):
        score += 18
    else:
        score += 14

    # Tech stack fit (20 pts)
    stack_pts = 0
    if 'python' in t: stack_pts += 7
    if any(k in t for k in ['fastapi', 'flask', 'django', 'rest api']): stack_pts += 5
    if any(k in t for k in ['sql', 'postgres', 'postgresql', 'database']): stack_pts += 3
    if any(k in t for k in ['redis', 'celery', 'kafka', 'message queue']): stack_pts += 3
    if any(k in t for k in ['nlp', 'bert', 'machine learning', 'pytorch', 'tensorflow', 'llm']): stack_pts += 4
    score += min(20, stack_pts)

    # Location fit (10 pts)
    if any(k in l for k in ['noida', 'gurgaon', 'gurugram', 'delhi', 'ncr']):
        score += 10
    elif 'remote' in l:
        score += 9
    elif any(k in l for k in ['bengaluru', 'bangalore']):
        score += 7
    else:
        score += 6

    # Brand / Salary likelihood (15 pts)
    comp_l = company.lower()
    if any(tc in comp_l for tc in ['amazon', 'google', 'microsoft', 'adobe', 'cisco', 'goldman sachs', 'tower research', 'hpe', 'urban company', 'zepto']):
        score += 15
    elif any(tc in comp_l for tc in ['greyorange', 'paytm', 'incred', 'cred', 'swiggy', 'postman', 'cars24']):
        score += 12
    else:
        score += 9

    score += 5
    return min(98, score)

try:
    for idx, c in enumerate(candidates_to_verify):
        url = c['url']
        company = c['company']
        title = c['title']
        loc = c['location']
        
        print(f"\n[{idx+1}/{len(candidates_to_verify)}] Verifying: {company} - {title} ({loc})")
        
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Check closed
            if "no longer accepting applications" in driver.page_source.lower() or soup.find('div', class_='closed-job__alert'):
                print("   -> ❌ REJECTED: Closed on LinkedIn")
                rejected_roles.append({**c, 'reason': 'Closed on LinkedIn'})
                continue
                
            desc_div = soup.find('div', class_='show-more-less-html__markup') or soup.find('div', class_='description__text')
            text = desc_div.get_text(separator=' ', strip=True) if desc_div else soup.get_text(separator=' ', strip=True)
        except Exception as e:
            print(f"   -> ❌ Error fetching JD: {e}")
            rejected_roles.append({**c, 'reason': f"Fetch error: {e}"})
            continue

        clean_text = text.lower()
        
        # Hard check for 3+ YOE
        hard_reject = False
        reject_reason = ""
        for pat in high_exp_patterns:
            m = re.search(pat, clean_text)
            if m:
                start = max(0, m.start()-50)
                end = min(len(clean_text), m.end()+80)
                snip = clean_text[start:end]
                if re.search(r'\b0\s*[\u2013\u2014\-to]\s*[1-2]\s*years?\b', snip):
                    continue
                if any(w in snip for w in ['experience', 'work', 'background', 'minimum', 'required', 'qualification', 'must have']):
                    hard_reject = True
                    reject_reason = f"Requires 3+ YOE: '{m.group()}' in context: ...{snip}..."
                    break
        
        if hard_reject:
            print(f"   -> ❌ REJECTED: {reject_reason}")
            rejected_roles.append({**c, 'reason': reject_reason})
            continue

        # Check if intern role slipped in
        if 'intern' in clean_text[:300] and 'intern' in title.lower():
            print("   -> ❌ REJECTED: Internship role (Full-time only required)")
            rejected_roles.append({**c, 'reason': 'Internship role'})
            continue
            
        # Check explicit 0-1, 0-2, or entry level signal
        has_entry = any(re.search(pat, clean_text) for pat in entry_signals) or any(re.search(pat, title.lower()) for pat in [r'\bentry\b', r'\bjunior\b', r'\btrainee\b', r'\bget\b', r'\bgraduate\b', r'\bengineer\s+i\b', r'\bsde\s*1\b'])
        
        if not has_entry:
            print("   -> ❌ REJECTED: No explicit 0-1 / 0-2 YOE or entry level signal in JD")
            rejected_roles.append({**c, 'reason': 'No explicit 0-1 / 0-2 YOE signal in JD'})
            continue

        # Check skill alignment (Must have at least one of: Python, Backend, Data, ML, SQL, APIs, Systems)
        has_skill = any(k in clean_text for k in ['python', 'backend', 'data', 'sql', 'database', 'api', 'machine learning', 'ml', 'ai', 'systems', 'cloud', 'c++'])
        if not has_skill:
            print("   -> ❌ REJECTED: Lacks technical skill alignment with Vaanya")
            rejected_roles.append({**c, 'reason': 'No technical skill alignment'})
            continue

        # Role is VERIFIED ELIGIBLE!
        score = score_fte_role(company, title, loc, clean_text)
        print(f"   -> ✅ VERIFIED 0-1/0-2 YOE FULL-TIME ROLE! Match Score: {score}/100")
        
        verified_clean_roles.append({
            **c,
            'match_score': score,
            'jd_snippet': text[:400].replace('\n', ' ')
        })

finally:
    driver.quit()

print(f"\n=== VERIFICATION RESULTS ===")
print(f"Total Eligible Full-Time 0-1 / 0-2 YOE roles: {len(verified_clean_roles)}")
print(f"Total Rejected: {len(rejected_roles)}")

with open('data/verified_entry_level_fte.json', 'w') as f:
    json.dump(verified_clean_roles, f, indent=2)

with open('data/rejected_entry_level_fte.json', 'w') as f:
    json.dump(rejected_roles, f, indent=2)
