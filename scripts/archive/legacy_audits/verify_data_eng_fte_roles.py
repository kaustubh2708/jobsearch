import json
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

with open('data/raw_data_eng_cards.json') as f:
    cards = json.load(f)

print(f"Total raw Data Engineering cards: {len(cards)}")

# Target companies to prioritize
priority_companies = [
    'amazon', 'google', 'microsoft', 'oracle', 'salesforce', 'cisco',
    'american express', 'amex', 'optum', 'unitedhealth', 'ey', 'pwc',
    'deloitte', 'kpmg', 'bny mellon', 'barclays', 'wells fargo', 'paytm',
    'incred', 'slice', 'cred', 'swiggy', 'zomato', 'blinkit', 'zepto',
    'cars24', 'urban company', 'airtel', 'info edge', 'naukri', 'physicswallah',
    'groww', 'jupiter', 'navi', 'sprinklr', 'atlan', 'clevertap', 'postman',
    'hpe', 'boeing', 'honeywell', 'siemens', 'sap', 'wadhwani', 'greyorange',
    'synopsys', 'cadence', 'intuit', 'flipkart', 'meesho', 'tower research'
]

hard_reject_titles = [
    'intern', 'internship', 'summer', 'winter', 'senior', 'sr', 'lead',
    'manager', 'director', 'principal', 'staff', 'ii', 'iii', '2', '3', '4',
    'sales', 'marketing', 'hr', 'recruiter', 'business development'
]

filtered = []
for c in cards:
    t = c.get('title', '').lower()
    comp = c.get('company', '').lower()
    loc = c.get('location', '').lower()
    
    if any(re.search(r'\b' + re.escape(w) + r'\b', t) for w in hard_reject_titles):
        continue
        
    is_india = any(k in loc for k in ['india', 'noida', 'gurgaon', 'gurugram', 'delhi', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'mumbai', 'remote'])
    is_foreign = any(k in loc for k in ['united states', 'california', 'ca', 'ny', 'london', 'singapore'])
    if not is_india or is_foreign:
        continue
        
    priority = 0
    if any(pc in comp for pc in priority_companies):
        priority += 4
    if any(k in loc for k in ['noida', 'gurgaon', 'gurugram', 'delhi']):
        priority += 3
    if 'associate' in t or 'junior' in t or 'trainee' in t or 'engineer i' in t:
        priority += 2
        
    c['priority_score'] = priority
    filtered.append(c)

filtered.sort(key=lambda x: x['priority_score'], reverse=True)
print(f"Filtered promising DE candidates: {len(filtered)}")

top_de_candidates = filtered[:35]

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)

verified_de_roles = []
rejected_de_roles = []

high_exp_patterns = [
    r'\b([3-9]|\d{2,})\+?\s*(?:to\s*\d+\s*)?years?\b',
    r'\b([3-9]|\d{2,})\s*[\u2013\u2014]\s*\d+\s*years?\b',
    r'\bminimum\s+([3-9]|\d{2,})\s+years?\b',
    r'\bat\s+least\s+([3-9]|\d{2,})\s+years?\b'
]

entry_signals = [
    r'\b0\s*[\u2013\u2014\-to]\s*[1-2]\s*years?\b',
    r'\b0\s*years?\b',
    r'\b0.?1\s*years?\b',
    r'\b0.?2\s*years?\b',
    r'\b(?:freshers?|new\s+grad|entry.?level)\b',
    r'\b(?:graduate\s+engineer\s+trainee|get)\b',
    r'\b(?:2025|2026)\s*batch\b',
    r'\bno\s+prior\s+experience\b',
    r'\b1\s*year\s+or\s+less\b'
]

def score_de_role(comp, title, loc, text):
    score = 0
    t = (title + ' ' + text).lower()
    l = loc.lower()
    
    # Role alignment (30 pts)
    if 'data engineer' in t:
        score += 30
    elif any(k in t for k in ['etl', 'data pipeline', 'analytics engineer', 'sql developer']):
        score += 26
    else:
        score += 20
        
    # Experience fit (20 pts)
    if any(k in t for k in ['0-1 year', '0-2 year', '0 year', 'freshers welcome']):
        score += 20
    elif any(k in t for k in ['junior', 'associate', 'entry level', 'graduate']):
        score += 17
    else:
        score += 14
        
    # Stack fit (20 pts)
    stack_pts = 0
    if 'python' in t: stack_pts += 7
    if any(k in t for k in ['sql', 'postgres', 'postgresql', 'mysql']): stack_pts += 5
    if any(k in t for k in ['spark', 'pyspark', 'etl', 'pipeline', 'kafka']): stack_pts += 4
    if any(k in t for k in ['aws', 's3', 'redshift', 'snowflake', 'bigquery', 'cloud']): stack_pts += 4
    score += min(20, stack_pts)
    
    # Location (10 pts)
    if any(k in l for k in ['noida', 'gurgaon', 'gurugram', 'delhi', 'ncr']):
        score += 10
    elif 'remote' in l:
        score += 9
    elif any(k in l for k in ['bengaluru', 'bangalore']):
        score += 7
    else:
        score += 6
        
    # Brand / Salary likelihood (15 pts)
    comp_l = comp.lower()
    if any(tc in comp_l for tc in ['amazon', 'google', 'microsoft', 'american express', 'optum', 'oracle', 'salesforce', 'cisco', 'hpe']):
        score += 15
    elif any(tc in comp_l for tc in ['ey', 'pwc', 'deloitte', 'kpmg', 'paytm', 'incred', 'swiggy', 'zepto']):
        score += 12
    else:
        score += 9
        
    score += 5
    return min(98, score)

try:
    for idx, c in enumerate(top_de_candidates):
        url = c['url']
        comp = c['company']
        title = c['title']
        loc = c['location']
        
        print(f"\n[{idx+1}/{len(top_de_candidates)}] Verifying: {comp} - {title} ({loc})")
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            if "no longer accepting applications" in driver.page_source.lower() or soup.find('div', class_='closed-job__alert'):
                print("   -> ❌ REJECTED: Closed on LinkedIn")
                rejected_de_roles.append({**c, 'reason': 'Closed on LinkedIn'})
                continue
                
            desc_div = soup.find('div', class_='show-more-less-html__markup') or soup.find('div', class_='description__text')
            text = desc_div.get_text(separator=' ', strip=True) if desc_div else soup.get_text(separator=' ', strip=True)
        except Exception as e:
            print(f"   -> ❌ Fetch error: {e}")
            rejected_de_roles.append({**c, 'reason': f"Fetch error: {e}"})
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
            rejected_de_roles.append({**c, 'reason': reject_reason})
            continue
            
        if 'intern' in clean_text[:300] and 'intern' in title.lower():
            print("   -> ❌ REJECTED: Internship role")
            rejected_de_roles.append({**c, 'reason': 'Internship role'})
            continue
            
        has_entry = any(re.search(pat, clean_text) for pat in entry_signals) or any(re.search(pat, title.lower()) for pat in [r'\bentry\b', r'\bjunior\b', r'\bassociate\b', r'\btrainee\b', r'\bget\b', r'\bgraduate\b', r'\bengineer\s+i\b'])
        if not has_entry:
            print("   -> ❌ REJECTED: No explicit 0-1 / 0-2 YOE or entry level signal in JD")
            rejected_de_roles.append({**c, 'reason': 'No explicit 0-1 / 0-2 YOE signal in JD'})
            continue
            
        score = score_de_role(comp, title, loc, clean_text)
        print(f"   -> ✅ VERIFIED FULL-TIME DATA ENGINEER ROLE! Match Score: {score}/100")
        verified_de_roles.append({
            **c,
            'match_score': score,
            'jd_snippet': text[:400].replace('\n', ' ')
        })
finally:
    driver.quit()

print(f"\n=== DATA ENGINEERING VERIFICATION RESULTS ===")
print(f"Total Eligible Full-Time 0-1 / 0-2 YOE DE roles: {len(verified_de_roles)}")
print(f"Total Rejected: {len(rejected_de_roles)}")

with open('data/verified_data_eng_fte.json', 'w') as f:
    json.dump(verified_de_roles, f, indent=2)
