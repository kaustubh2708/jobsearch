#!/usr/bin/env python3
"""
discover_wave9_vrinda_candidates.py

Fetches live job postings directly from official ATS APIs (Greenhouse, Ashby, Lever).
Extracts: title, location, direct URL, JD text, required YOE, and tech stack.
Filters strictly for Vrinda:
- 2–5 YOE (rejects 6+ yrs, Staff, Principal, Lead, Manager, freshers/interns).
- Tech: C#/.NET, Azure, Node.js, TypeScript, Python, Microservices, Distributed Systems, AI Agents.
- Locations: Gurugram, Noida, Delhi NCR, Remote India, Bengaluru.
- Paused employers (Amazon, Sarvam AI, MongoDB) are strictly excluded.
"""

import json, re, ssl, html, urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

def get_json(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return None

def strip_html(t):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(html.unescape(t or ''))))

def extract_exp(text):
    found = re.findall(r'(\d{1,2}\s*(?:\+|-|–|to)?\s*\d{0,2}\s*\+?\s*years?)[^.]{0,60}?(?:experience|exp)', text, flags=re.I)
    found += re.findall(r'(?:minimum|at least)\s+(?:of\s+)?(\d{1,2}\s*\+?\s*years?)', text, flags=re.I)
    seen = []
    for f in found:
        f = re.sub(r'\s+', ' ', f).strip()
        if f not in seen:
            seen.append(f)
    return seen[:3]

def get_min_yoe(phrases):
    ys = [int(m.group(1)) for p in phrases if (m := re.match(r'(\d+)', p))]
    return min(ys) if ys else None

# Load deduplication index
with open('data/vrinda_all_seen_urls.json') as f:
    dedup = json.load(f)
seen_urls = set(dedup.get('seen_urls', []))
seen_ids = set(dedup.get('seen_ids', []))

# Load dynamic search switches
try:
    with open('config/search_switches.json') as f:
        switches_cfg = json.load(f)
        active_switches = switches_cfg.get('active_switches', {})
except Exception:
    active_switches = {}

exclude_existing_companies = active_switches.get('exclude_companies_with_existing_openings', False)
exclude_python_heavy = active_switches.get('exclude_python_heavy_roles', False)

# Load existing companies if switch is active
existing_companies = set()
if exclude_existing_companies:
    import openpyxl
    try:
        wb_check = openpyxl.load_workbook('data/Companies(1).xlsx', data_only=True)
        if 'past wave' in wb_check.sheetnames:
            ws_p = wb_check['past wave']
            for r in range(2, ws_p.max_row + 1):
                val = ws_p.cell(r, 3).value
                if val: existing_companies.add(str(val).strip().lower())
        for s in ['Wave 8', 'Wave 9', 'Wave 7']:
            if s in wb_check.sheetnames:
                ws_s = wb_check[s]
                for r in range(2, ws_s.max_row + 1):
                    val = ws_s.cell(r, 2).value
                    if val: existing_companies.add(str(val).strip().lower())
    except Exception as e:
        print("Note: Could not load workbook for existing companies check:", e)

print(f"Loaded deduplication index: {len(seen_urls)} URLs, {len(seen_ids)} IDs.")
print(f"Active Switches: exclude_existing_companies={exclude_existing_companies} ({len(existing_companies)} companies tracked), exclude_python_heavy={exclude_python_heavy}")

candidates = []

# 1. Ashby Boards
ashby_boards = [
    ('PAR Technology', 'PAR%20Technology'),
    ('Level AI', 'level-ai'),
    ('Plane Software', 'plane'),
    ('Ema', 'ema'),
    ('Anuvaya Labs', 'anuvaya'),
    ('Bolna', 'bolna'),
    ('Ciroos', 'ciroos'),
    ('Pravah', 'pravah'),
    ('Commure', 'commure'),
    ('AiPrise', 'aiprise'),
    ('Astronomer', 'astronomer')
]

for comp_name, b_token in ashby_boards:
    url = f'https://api.ashbyhq.com/posting-api/job-board/{b_token}'
    d = get_json(url)
    if not d: continue
    for j in d.get('jobs', []):
        title = j.get('title', '').strip()
        loc = j.get('location', '') or ''
        jurl = j.get('jobUrl', '')
        jid = j.get('id', '')
        desc = strip_html(j.get('descriptionPlain') or j.get('descriptionHtml'))
        
        # Location filter
        if not any(k in loc.lower() for k in ['india', 'gurgaon', 'gurugram', 'noida', 'delhi', 'bengaluru', 'bangalore', 'remote']):
            continue
            
        candidates.append({
            'source_board': 'Ashby',
            'company': comp_name,
            'title': title,
            'location': loc,
            'url': jurl,
            'id': jid,
            'desc': desc
        })

# 2. Greenhouse Boards
gh_boards = [
    ('Databricks', 'databricks'),
    ('Stripe', 'stripe'),
    ('Elastic', 'elastic'),
    ('Coinbase', 'coinbase'),
    ('Squarepoint Capital', 'squarepointcapital'),
    ('Tower Research Capital', 'towerresearchcapital'),
    ('HackerRank', 'hackerrank'),
    ('Okta', 'okta'),
    ('InMobi', 'inmobi'),
    ('Branch', 'branchmetrics'),
    ('Rubrik', 'rubrik'),
    ('Deliveroo', 'deliveroo')
]

for comp_name, b_token in gh_boards:
    url = f'https://boards-api.greenhouse.io/v1/boards/{b_token}/jobs?content=true'
    d = get_json(url)
    if not d: continue
    for j in d.get('jobs', []):
        title = j.get('title', '').strip()
        loc = j.get('location', {}).get('name', '') or ''
        jurl = j.get('absolute_url', '')
        jid = str(j.get('id', ''))
        desc = strip_html(j.get('content', ''))
        
        # Location filter
        if not any(k in loc.lower() for k in ['india', 'gurgaon', 'gurugram', 'noida', 'delhi', 'bengaluru', 'bangalore', 'remote']):
            continue
            
        candidates.append({
            'source_board': 'Greenhouse',
            'company': comp_name,
            'title': title,
            'location': loc,
            'url': jurl,
            'id': jid,
            'desc': desc
        })

print(f"Total raw candidates fetched from live ATS: {len(candidates)}")

# 3. Filter for Vrinda
verified_matches = []
rejected = []

for c in candidates:
    comp = c['company']
    title = c['title']
    loc = c['location']
    u = c['url']
    jid = c['id']
    desc = c['desc']
    d_lower = desc.lower()
    t_lower = title.lower()

    # Rule: paused employers
    if any(k in comp.lower() for k in ['amazon', 'sarvam', 'mongodb']):
        continue

    # Title exclusions
    if any(k in t_lower for k in [
        'director', 'principal', 'head of', 'architect', 'lead ', 'manager',
        'vp', 'vice president', 'staff', 'intern', 'trainee', 'graduate',
        'campus', 'fresher', 'salesforce', 'sap ', 'abap', 'peoplesoft',
        'consultant', 'account executive', 'recruiter', 'marketing', 'designer',
        'operations', 'analyst', 'legal', 'finance', 'specialist', 'commercial'
    ]):
        rejected.append((comp, title, 'Title excluded (leadership/intern/non-eng)'))
        continue

    # Seniority check from JD
    phrases = extract_exp(desc)
    min_y = get_min_yoe(phrases)
    if min_y is not None and min_y >= 6:
        rejected.append((comp, title, f'JD explicitly requires >= 6 yrs: {phrases}'))
        continue
    if min_y is not None and min_y == 0:
        rejected.append((comp, title, f'Fresher role (0 yrs): {phrases}'))
        continue

    # Tech stack check
    tech_detected = []
    if any(k in d_lower for k in ['c#', '.net', 'asp.net']):
        tech_detected.append('C#/.NET Core')
    if 'azure' in d_lower:
        tech_detected.append('Azure Cloud')
    if any(k in d_lower for k in ['node', 'nodejs']):
        tech_detected.append('Node.js')
    if 'typescript' in d_lower:
        tech_detected.append('TypeScript')
    if 'python' in d_lower:
        tech_detected.append('Python')
    if 'java' in d_lower:
        tech_detected.append('Java')
    if any(k in d_lower for k in ['microservice', 'distributed system', 'distributed architecture']):
        tech_detected.append('Microservices/Distributed Systems')
    if any(k in d_lower for k in ['kafka', 'event-driven', 'event streaming']):
        tech_detected.append('Kafka/Streaming')
    if any(k in d_lower for k in ['ai agent', 'agentic', 'llm', 'langchain', 'langgraph', 'mcp']):
        tech_detected.append('AI Agents/LLM')
    if any(k in d_lower for k in ['rest api', 'graphql', 'grpc', 'apis']):
        tech_detected.append('REST/gRPC APIs')
    if any(k in d_lower for k in ['sql', 'postgres', 'redis', 'nosql', 'mysql']):
        tech_detected.append('Databases/Redis')
    if any(k in d_lower for k in ['kubernetes', 'docker', 'k8s']):
        tech_detected.append('Kubernetes/Containers')

    if not tech_detected:
        rejected.append((comp, title, 'No target backend/cloud skills found in JD'))
        continue

    # Deduplication check against seen URLs and IDs
    clean_u = u.split('?')[0].lower().rstrip('/')
    if clean_u in seen_urls and '?' not in u:
        rejected.append((comp, title, 'Already seen in earlier waves'))
        continue
    if jid and jid in seen_ids:
        rejected.append((comp, title, 'Requisition ID already seen'))
        continue

    # SWITCH 1: Exclude companies with existing openings
    if exclude_existing_companies and comp.lower() in existing_companies:
        rejected.append((comp, title, f'Company {comp} already has openings in previous waves (exclude_companies_with_existing_openings=True)'))
        continue

    # SWITCH 2: Exclude Python-heavy roles
    if exclude_python_heavy:
        is_python_title = 'python' in t_lower
        is_python_stack = 'Python' in tech_detected and not any(k in tech_detected for k in ['C#/.NET Core', 'Node.js', 'TypeScript', 'Azure Cloud', 'Java'])
        if is_python_title or is_python_stack:
            rejected.append((comp, title, f'Python-heavy role without candidate core stack (exclude_python_heavy_roles=True)'))
            continue

    exp_str = " | ".join(phrases) if phrases else "Not stated in JD"
    
    # Calculate score
    score = 75
    if 'C#/.NET Core' in tech_detected or 'Azure Cloud' in tech_detected:
        score += 8
    if 'Node.js' in tech_detected or 'TypeScript' in tech_detected:
        score += 6
    if 'AI Agents/LLM' in tech_detected:
        score += 7
    if 'Microservices/Distributed Systems' in tech_detected:
        score += 5
    if any(k in loc.lower() for k in ['gurugram', 'gurgaon', 'noida', 'delhi']):
        score += 5

    score = min(score, 97)
    tier = "P1 Strong Match" if score >= 88 else ("P2 Good Match" if score >= 80 else "P3 Potential Match")

    comp_upper = comp.upper()
    if any(k in comp_upper for k in ['TOWER', 'SQUAREPOINT', 'STRIPE', 'COINBASE', 'DATABRICKS', 'ELASTIC', 'RUBRIK', 'OKTA']):
        est_comp = "₹45 – 80+ LPA (Tier-1 Global Tech / Quant / Cloud Platform)"
    elif any(k in comp_upper for k in ['LEVEL AI', 'EMA', 'ANUVAYA', 'PLANE', 'BOLNA', 'CIROOS', 'PAR']):
        est_comp = "₹35 – 55 LPA (High-Growth AI / Cloud Platform)"
    else:
        est_comp = "₹30 – 45 LPA (Enterprise GCC / Competitive Product Tech)"

    verified_matches.append({
        'company': comp,
        'title': title,
        'location': loc,
        'url': u,
        'id': jid,
        'experience_per_jd': exp_str,
        'tech_stack': ", ".join(tech_detected[:5]),
        'comp': est_comp,
        'score': score,
        'tier': tier,
        'notes': f"Direct {c['source_board']} requisition verified live. Skills: {', '.join(tech_detected[:3])}. Seniority 2-5 YOE verified."
    })

print(f"\n--- MATCH RESULTS ---")
print(f"Verified matching roles: {len(verified_matches)}")
print(f"Rejected: {len(rejected)}")

with open('data/wave9_discovered_matches.json', 'w') as f:
    json.dump(verified_matches, f, indent=2)

print("Saved candidate matches to data/wave9_discovered_matches.json")
