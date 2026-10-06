import json
import re
import html
import openpyxl

# Load seen URLs
seen_urls = set()
with open('data/all_existing_urls.json') as f:
    for u in json.load(f):
        seen_urls.add(u.strip().lower().rstrip('/'))

wb = openpyxl.load_workbook('data/Job Search.xlsx', data_only=True)
for sname in wb.sheetnames:
    ws = wb[sname]
    for row in ws.iter_rows(values_only=True):
        for cell in row:
            if cell and isinstance(cell, str) and cell.startswith('http'):
                seen_urls.add(cell.strip().lower().rstrip('/'))

with open('data/scratch_raw_ats_jobs.json') as f:
    raw_jobs = json.load(f)

print(f"Total raw jobs to inspect: {len(raw_jobs)}")

# Excluded employers per rules
paused_employers = {'amazon', 'sarvam', 'sarvam ai', 'mongodb'}

# Exclude non-tech or high seniority or internships
reject_title_words = [
    r'\bintern\b', r'\binternship\b', r'\bsummer\b', r'\bwinter\b', r'\bco-op\b', r'\bcoop\b',
    r'\bsenior\b', r'\bsr\.?\b', r'\blead\b', r'\bprincipal\b', r'\bstaff\b',
    r'\bii\b', r'\biii\b', r'\biv\b', r'\b2\b', r'\b3\b', r'\b4\b', r'\b5\b',
    r'\bmanager\b', r'\bdirector\b', r'\bvp\b', r'\bhead\b',
    r'\brecruiter\b', r'\btalent\b', r'\bhr\b', r'\bsales\b', r'\bmarketing\b',
    r'\boperations\b', r'\baccountant\b', r'\blegal\b', r'\bexecutive\b'
]

tech_title_words = [
    r'\bsoftware\b', r'\bsde\b', r'\bengineer\b', r'\bdeveloper\b',
    r'\bbackend\b', r'\bdata\b', r'\bml\b', r'\bmachine\s+learning\b',
    r'\bai\b', r'\bqa\b', r'\bsdet\b', r'\btest\b', r'\bpython\b',
    r'\bfull\s*stack\b', r'\bfrontend\b', r'\bplatform\b', r'\bcloud\b',
    r'\bsystems\b', r'\bgraduate\b', r'\btrainee\b', r'\bget\b'
]

india_locations = [
    'india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida',
    'delhi', 'hyderabad', 'pune', 'mumbai', 'chennai', 'remote'
]

candidates = []

for j in raw_jobs:
    comp = j.get('company', '').lower()
    if any(p in comp for p in paused_employers):
        continue

    title = j.get('title', '').strip()
    loc = j.get('location', '').strip()
    url = j.get('url', '').strip()
    content = j.get('content', '')

    clean_url = url.lower().rstrip('/')
    if clean_url in seen_urls:
        continue

    # Location check
    loc_lower = loc.lower()
    if not any(loc_token in loc_lower for loc_token in india_locations):
        # Some remote roles might have "Remote" without explicit India, check if content mentions India
        if 'remote' in loc_lower and ('india' in content.lower() or 'in' in loc_lower):
            pass
        else:
            continue

    # Title checks
    t_lower = title.lower()
    if any(re.search(pat, t_lower) for pat in reject_title_words):
        continue

    if not any(re.search(pat, t_lower) for pat in tech_title_words):
        continue

    # Check content for 2+ YOE or 3+ YOE strict gates
    content_lower = content.lower()
    if content_lower:
        # Check strict 3+ / 4+ / 5+ YOE
        if re.search(r'\b([3-9]|\d{2,})\+?\s*(?:to\s*\d+\s*)?years?\b', content_lower):
            continue
        if re.search(r'\b([3-9]|\d{2,})\s*[\u2013\u2014]\s*\d+\s*years?\b', content_lower):
            continue
        
        # Check for strict 2+ years minimum requirements
        # If it says 'minimum 2 years' or 'at least 2 years' or '2+ years of experience', exclude from fresher
        if re.search(r'\b(?:minimum|at least|min\.?)\s*2\+?\s*years?\b', content_lower):
            continue
        if re.search(r'\b2\+?\s*years\s+of\s+(?:relevant\s+)?experience\b', content_lower) and not ('0-2' in content_lower or '0 to 2' in content_lower):
            continue

    candidates.append({
        'company': j.get('company'),
        'title': title,
        'location': loc,
        'url': url,
        'platform': j.get('platform'),
        'id': j.get('id'),
        'content_snip': content[:500] if content else ''
    })

print(f"Total eligible candidate postings after strict filtering: {len(candidates)}")
with open('data/scratch_filtered_wave9_candidates.json', 'w') as f:
    json.dump(candidates, f, indent=2)

for c in candidates[:30]:
    print(f"[{c['platform']}] {c['company']} | {c['title']} | {c['location']} | {c['url']}")
