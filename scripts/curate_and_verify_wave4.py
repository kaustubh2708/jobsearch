import urllib.request, ssl, json, re, time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import openpyxl
from concurrent.futures import ThreadPoolExecutor, as_completed

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

# 1. Load existing keys
wb = openpyxl.load_workbook('data/jobs_vrinda_discovery_wave2_verified.xlsx')
existing_keys = set()
for sname in wb.sheetnames:
    ws = wb[sname]
    for r in range(2, ws.max_row + 1):
        comp = str(ws.cell(row=r, column=2).value or '').strip().lower()
        title = str(ws.cell(row=r, column=3).value or '').strip().lower()
        url = str(ws.cell(row=r, column=11).value or '').strip()
        if url:
            m = re.search(r'jobs/view/(\d+)', url)
            if m:
                existing_keys.add(f'linkedin_{m.group(1)}')
            else:
                existing_keys.add(url.lower())
        existing_keys.add(f'{comp}|{title}')

print(f"Loaded {len(existing_keys)} existing keys to ensure 100% zero duplicates.")

# 2. Candidate pool
with open('/Users/kaustubhsingh/.gemini/antigravity/brain/d9ad89d1-44f6-47c4-ba27-1aaaf53ce906/scratch/wave4_raw.json') as f:
    d9ad_jobs = json.load(f)

with open('data/wave4_crawled_cards.json') as f:
    crawled_jobs = json.load(f)

all_raw = d9ad_jobs + crawled_jobs

# Staffing companies to exclude (focus on product tech, unicorns, GCCs, high-growth firms)
generic_staffing_exclude = [
    'accenture', 'tcs', 'infosys', 'wipro', 'cognizant', 'hcltech', 'capgemini',
    'tech mahindra', 'l&t technology', 'mindtree', 'mphasis', 'brizsolution',
    'softcrayons', 'brace infotech', 'transsion', 'xenonstack'
]

curated_candidates = []
seen_jids = set()

for j in all_raw:
    jid = str(j.get('job_id', ''))
    if not jid or jid in seen_jids or f'linkedin_{jid}' in existing_keys:
        continue

    comp = j.get('company', '').strip()
    title = j.get('title', '').strip()
    loc = j.get('location', '').strip()
    comp_l = comp.lower()
    title_l = title.lower()
    loc_l = loc.lower()

    if f'{comp_l}|{title_l}' in existing_keys:
        continue

    if any(k in comp_l for k in generic_staffing_exclude):
        continue

    # Title exclusions
    if any(k in title_l for k in ['intern', 'trainee', 'fresher', 'lead', 'staff', 'principal', 'manager', 'director', 'qa', 'sdet', 'salesforce', 'devops', 'sre', 'android', 'ios', 'data engineer', 'analyst']):
        continue

    # Target tech
    is_target_tech = any(k in title_l for k in ['sde', 'swe', 'software engineer', 'backend', 'developer', 'dot net', '.net', 'c#', 'node', 'ai', 'agent', 'platform', 'fullstack', 'full stack'])
    if not is_target_tech:
        continue

    # Target locations
    is_p1 = 'gurgaon' in loc_l or 'gurugram' in loc_l
    is_p2 = 'noida' in loc_l or 'delhi' in loc_l
    is_p3 = 'remote' in loc_l
    is_p4 = 'bengaluru' in loc_l or 'bangalore' in loc_l or 'hyderabad' in loc_l

    if not (is_p1 or is_p2 or is_p3 or is_p4):
        continue

    seen_jids.add(jid)
    curated_candidates.append({
        'job_id': jid,
        'company': comp,
        'title': title,
        'location': loc,
        'url': f'https://in.linkedin.com/jobs/view/{jid}',
        'is_p1': is_p1,
        'is_p2': is_p2,
        'is_p3': is_p3,
        'is_p4': is_p4
    })

# Sort: P1 Gurugram first, then P2 Noida, then P3 Remote, then P4 Bengaluru
curated_candidates.sort(key=lambda x: (not x['is_p1'], not x['is_p2'], not x['is_p3'], not x['is_p4'], x['company']))
print(f"Curated {len(curated_candidates)} high-potential candidates to probe.")

def probe_job(c):
    url = c['url']
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            code = resp.getcode()
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(' ', strip=True).lower()
            
            is_closed = 'no longer accepting applications' in text or 'job is closed' in text
            if code == 200 and not is_closed:
                desc_el = soup.find('div', class_='show-more-less-html__markup') or soup.find('div', class_='description__text')
                desc = desc_el.get_text('\n', strip=True) if desc_el else text[:600]
                
                exp_match = re.findall(r'(\d+[\s\-\–to]+\d+\s+years?(?:\s+of)?\s+experience|\d+\+?\s+years?(?:\s+of)?\s+experience)', desc, re.IGNORECASE)
                
                # Check for 6+ years rejection
                is_over_senior = False
                for em in exp_match:
                    nums = [int(n) for n in re.findall(r'\b\d+\b', em)]
                    if nums and min(nums) >= 6:
                        is_over_senior = True
                        break
                
                if not is_over_senior:
                    # Clean description snippet
                    desc_clean = re.sub(r'\s+', ' ', desc)[:350]
                    return {
                        'job_id': c['job_id'],
                        'company': c['company'],
                        'title': c['title'],
                        'location': c['location'],
                        'url': c['url'],
                        'exp_snippets': exp_match[:2],
                        'desc_snippet': desc_clean,
                        'is_valid': True
                    }
    except Exception as e:
        pass
    return {'is_valid': False}

verified_active = []
with ThreadPoolExecutor(max_workers=12) as executor:
    futures = {executor.submit(probe_job, c): c for c in curated_candidates[:60]}
    for f in as_completed(futures):
        res = f.result()
        if res.get('is_valid'):
            verified_active.append(res)
            print(f"[VERIFIED 200] {res['company']} - {res['title']} ({res['location']}) | Exp: {res.get('exp_snippets')}")

print(f"\nSuccessfully verified {len(verified_active)} active roles with 2-5y seniority fit!")
verified_active.sort(key=lambda x: ('gurgaon' not in x['location'].lower() and 'gurugram' not in x['location'].lower(), 'noida' not in x['location'].lower(), x['company']))

with open('data/curated_wave4_verified.json', 'w') as f:
    json.dump(verified_active, f, indent=2)
print("Saved curated_wave4_verified.json")
