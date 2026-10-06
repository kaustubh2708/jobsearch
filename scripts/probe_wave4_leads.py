import urllib.request, ssl, json, re, time
from bs4 import BeautifulSoup
import openpyxl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

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

# Load all candidate leads
with open('/Users/kaustubhsingh/.gemini/antigravity/brain/d9ad89d1-44f6-47c4-ba27-1aaaf53ce906/scratch/wave4_raw.json') as f:
    d9ad_jobs = json.load(f)

with open('data/wave4_crawled_cards.json') as f:
    crawled_jobs = json.load(f)

all_jobs = d9ad_jobs + crawled_jobs

candidate_list = []
seen_jids = set()

for j in all_jobs:
    jid = str(j.get('job_id', ''))
    if not jid or jid in seen_jids or f'linkedin_{jid}' in existing_keys:
        continue
    seen_jids.add(jid)

    title = j.get('title', '').strip()
    title_l = title.lower()
    comp = j.get('company', '').strip()
    loc = j.get('location', '').strip()
    loc_l = loc.lower()

    if f'{comp.lower()}|{title.lower()}' in existing_keys:
        continue

    # Filter out CRM, support, intern, etc.
    if any(k in title_l for k in ['intern', 'trainee', 'fresher', 'lead', 'staff', 'principal', 'manager', 'director', 'qa', 'sdet', 'salesforce', 'devops', 'sre', 'android', 'ios', 'data engineer', 'analyst']):
        continue

    # Priority target keywords
    is_target_tech = any(k in title_l for k in ['sde', 'swe', 'software engineer', 'backend', 'developer', 'dot net', '.net', 'c#', 'node', 'ai', 'agent', 'platform'])
    if not is_target_tech:
        continue

    # Priority locations
    is_p1 = 'gurgaon' in loc_l or 'gurugram' in loc_l
    is_p2 = 'noida' in loc_l or 'delhi' in loc_l
    is_p3 = 'remote' in loc_l
    is_p4 = 'bengaluru' in loc_l or 'bangalore' in loc_l

    if not (is_p1 or is_p2 or is_p3 or is_p4):
        continue

    candidate_list.append({
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

# Sort by priority: P1 Gurugram first, then P2 Noida, then P3 Remote, then P4 Bengaluru
candidate_list.sort(key=lambda x: (not x['is_p1'], not x['is_p2'], not x['is_p3'], not x['is_p4'], x['company']))

print(f"Total deduplicated candidates to probe: {len(candidate_list)}")

# Probe top 50
probed = []
for idx, c in enumerate(candidate_list[:50], 1):
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
                # Extract description snippet
                desc_el = soup.find('div', class_='show-more-less-html__markup') or soup.find('div', class_='description__text')
                desc = desc_el.get_text('\n', strip=True) if desc_el else text[:600]
                
                # Check experience
                exp_match = re.findall(r'(\d+[\s\-\–to]+\d+\s+years?(?:\s+of)?\s+experience|\d+\+?\s+years?(?:\s+of)?\s+experience)', desc, re.IGNORECASE)
                
                # Check for 6+ years rejection
                is_over_senior = False
                for em in exp_match:
                    nums = [int(n) for n in re.findall(r'\b\d+\b', em)]
                    if nums and min(nums) >= 6:
                        is_over_senior = True
                        break
                
                if not is_over_senior:
                    c['exp_snippets'] = exp_match[:3]
                    c['desc_snippet'] = desc[:300]
                    probed.append(c)
                    print(f"[ACTIVE 200] #{idx} {c['company']} - {c['title']} ({c['location']}) | Exp: {exp_match[:1]}")
                else:
                    print(f"[OVER-SENIOR REJECT] #{idx} {c['company']} - {c['title']} ({c['location']}) | Exp: {exp_match[:1]}")
            else:
                print(f"[CLOSED] #{idx} {c['company']} - {c['title']}")
    except Exception as e:
        print(f"[ERR] #{idx} {c['company']} - {c['title']} -> {e}")
    time.sleep(0.4)

print(f"\nTotal verified active roles probed: {len(probed)}")
with open('data/wave4_verified_probed.json', 'w') as f:
    json.dump(probed, f, indent=2)
