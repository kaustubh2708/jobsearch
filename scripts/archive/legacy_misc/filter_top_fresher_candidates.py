import json
import re

with open('data/fresher_linkedin_cards.json') as f:
    cards = json.load(f)

print(f"Total raw LinkedIn cards: {len(cards)}")

# Target company priority or reputable tech firms
reputable_companies = [
    'zomato', 'blinkit', 'cars24', 'urban company', 'paytm', 'tower research',
    'adobe', 'american express', 'amex', 'amazon', 'google', 'microsoft',
    'uber', 'flipkart', 'swiggy', 'zepto', 'incred', 'slice', 'cred',
    'phonepe', 'meesho', 'postman', 'browserstack', 'inmobi', 'rubrik',
    'stripe', 'salesforce', 'atlassian', 'goldman sachs', 'morgan stanley',
    'd. e. shaw', 'de shaw', 'cisco', 'intel', 'amd', 'qualcomm', 'oracle',
    'sap', 'servicenow', 'siemens', 'honeywell', 'pitney bowes', 'wadhwani',
    'together ai', 'hpe', 'hewlett packard', 'boeing', 'airtel', 'info edge',
    'naukri', 'physicswallah', 'groww', 'jupiter', 'navi', 'fi money',
    'sprinklr', 'optum', 'unitedhealth', 'barclays', 'bny mellon', 'wells fargo',
    'deloitte', 'pwc', 'kpmg', 'ey', 'bain', 'mckinsey', 'hacker earth',
    'hackerrank', 'juspay', 'clevertap', 'atlan', 'atlys', 'sarvam',
    'formac', 'forma.ai', 'squarepoint', 'quadeye', 'graviton', 'jumptrading'
]

# Tech keywords in title
tech_title_patterns = [
    r'\bsoftware\b', r'\bdeveloper\b', r'\bengineer\b', r'\bbackend\b',
    r'\bdata\b', r'\bmachine\s+learning\b', r'\bml\b', r'\bai\b',
    r'\bpython\b', r'\bqa\b', r'\bsdet\b', r'\btrainee\b', r'\bget\b',
    r'\bintern\b', r'\bgraduate\b'
]

# Excluded keywords
reject_title = [
    'talent acquisition', 'recruiter', 'hr', 'marketing', 'sales',
    'business development', 'content', 'telecaller', 'graphic', 'ui/ux',
    'civil', 'mechanical', 'electrical site', 'construction', 'accounting',
    'finance intern', 'customer support', 'bpo', 'operations executive'
]

filtered = []
for c in cards:
    title = c.get('title', '').lower()
    comp = c.get('company', '').lower()
    loc = c.get('location', '').lower()
    
    # Exclude non-tech
    if any(r in title for r in reject_title):
        continue
    
    # Must have tech keyword
    if not any(re.search(pat, title) for pat in tech_title_patterns):
        continue
        
    # Check if company is reputable or title has strong early career marker
    is_top_company = any(tc in comp for tc in reputable_companies)
    is_strong_role = any(k in title for k in ['intern', 'graduate engineer trainee', 'get', 'junior', 'early career', 'fresher'])
    
    priority = 0
    if is_top_company:
        priority += 3
    if 'noida' in loc or 'gurgaon' in loc or 'gurugram' in loc or 'delhi' in loc:
        priority += 2
    if 'python' in title or 'backend' in title or 'ml' in title or 'ai' in title:
        priority += 2
    if 'intern' in title or 'trainee' in title or 'graduate' in title:
        priority += 1

    c['priority_score'] = priority
    c['is_top_company'] = is_top_company
    filtered.append(c)

filtered.sort(key=lambda x: x['priority_score'], reverse=True)
print(f"Filtered promising tech early-career cards: {len(filtered)}")

with open('data/promising_fresher_cards.json', 'w') as f:
    json.dump(filtered, f, indent=2)

print("\n--- Top 20 Candidates by Priority ---")
for f in filtered[:25]:
    print(f"[{f['priority_score']} pts] {f['company'][:25]} | {f['title'][:35]} | {f['location'][:20]}")
