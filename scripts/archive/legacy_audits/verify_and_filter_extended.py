import json, time, re, ssl, urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import openpyxl

# 1. Deduplication baseline
all_seen_urls = set()
all_seen_ids = set()

with open('data/vrinda_all_seen_urls.json') as f:
    d = json.load(f)
    for u in d.get('seen_urls', []):
        all_seen_urls.add(u.strip().lower().rstrip('/'))
    for jid in d.get('seen_ids', []):
        all_seen_ids.add(str(jid).strip().lower())

wb_check = openpyxl.load_workbook('data/Companies(1).xlsx', data_only=False)
for sname in ['past wave', 'Wave 12', 'Wave 13']:
    ws = wb_check[sname]
    url_col = 13 if sname == 'past wave' else 11
    for r in range(2, ws.max_row + 1):
        c = ws.cell(row=r, column=url_col)
        val = c.hyperlink.target if c.hyperlink else c.value
        if val and str(val).strip().startswith('http'):
            all_seen_urls.add(str(val).strip().lower().rstrip('/'))

# 2. Load harvested leads
with open('data/raw_wave13_extended_leads.json') as f:
    li_leads = json.load(f)

with open('data/raw_ats_wave13_extended.json') as f:
    ats_leads = json.load(f)

print(f"Loaded {len(li_leads)} LinkedIn leads and {len(ats_leads)} ATS leads.")

paused = {'amazon', 'sarvam', 'sarvam ai', 'mongodb', 'microsoft'}

# STRICT non-tech / support / over-senior / out-of-scope titles to reject
disqualifiers = [
    'field engineer', 'solutions engineer', 'solutions architect', 'product support',
    'gtm engineer', 'customer reliability', 'support engineer', 'sales engineer',
    'network engineer', 'business analyst', 'marketing', 'trainee', 'türkiye',
    'intern', 'manager', 'lead', 'principal', 'director', 'vp', 'head of',
    'cursor', 'staff software engineer', 'lead engineer', 'associate solutions engineer',
    'senior staff', 'qa engineer', 'test engineer', 'automation engineer',
    'data analyst', 'sdet', 'sr software engineer', 'sr. software engineer',
    'senior software engineer', 'senior engineer', 'sr engineer', 'data engineer',
    'salesforce', 'sap abap', 'security analyst', 'technical account manager'
]

# Strict India location check
def is_india_location(loc_str):
    if not loc_str: return False
    l = loc_str.lower()
    return any(k in l for k in ['india', 'gurgaon', 'gurugram', 'noida', 'delhi', 'ncr', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'mumbai', 'remote - india'])

# Tech stack extraction
def extract_tech_stack(text, title):
    t_low = (text + ' ' + title).lower()
    stacks = []
    if any(k in t_low for k in ['.net', 'c#', 'csharp', 'dotnet', 'asp.net']):
        stacks.append('C#/.NET Core')
    if any(k in t_low for k in ['azure', 'azure functions', 'azure service bus', 'aks']):
        stacks.append('Azure Cloud')
    if any(k in t_low for k in ['node.js', 'nodejs', 'node js', 'express', 'nest.js', 'nestjs']):
        stacks.append('Node.js')
    if any(k in t_low for k in ['typescript', 'ts']):
        stacks.append('TypeScript')
    if any(k in t_low for k in ['kafka', 'distributed systems', 'microservices', 'event-driven']):
        stacks.append('Distributed Systems / Kafka')
    if any(k in t_low for k in ['java', 'spring', 'spring boot', 'springboot']):
        stacks.append('Java/Spring Boot')
    if any(k in t_low for k in ['agentic', 'langgraph', 'langchain', 'llm', 'ai agent', 'rag']):
        stacks.append('AI Agentic Workflows')
    if not stacks:
        stacks = ['Backend Architecture, Distributed Systems, REST/gRPC']
    return ', '.join(stacks)

# 3. Setup Selenium Chrome Headless
options = Options()
options.add_argument('--headless=new')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
driver = webdriver.Chrome(options=options)

verified_roles = []
processed_urls = set()

# Combine leads, prioritize ATS
all_candidate_leads = []
for item in ats_leads:
    item['source'] = 'official_ats'
    all_candidate_leads.append(item)
for item in li_leads:
    item['source'] = 'linkedin_live'
    all_candidate_leads.append(item)

print(f"Filtering and verifying {len(all_candidate_leads)} total candidate leads...")

for item in all_candidate_leads:
    u = item['url']
    c = item['company']
    t = item['title']
    l = item.get('location', '')
    jid = item.get('job_id')
    source = item['source']

    if c.lower() in paused: continue
    if not is_india_location(l): continue

    t_low = t.lower()
    if any(dk in t_low for dk in disqualifiers): continue
    if 'python developer' in t_low or 'python engineer' in t_low: continue

    # Must contain positive engineering indicators
    if not any(ek in t_low for ek in ['software engineer', 'backend', 'developer', 'sde', 'swe', 'full stack', 'cloud engineer', 'systems engineer']):
        continue

    clean_u = u.lower().rstrip('/')
    if clean_u in all_seen_urls or clean_u in processed_urls: continue
    if jid and str(jid).lower() in all_seen_ids: continue

    try:
        driver.get(u)
        time.sleep(1.5)
        body = driver.find_element('tag name', 'body').text
        b_low = body.lower()

        # Check closed indicators
        if any(ci in b_low for ci in ['job does not exist', 'page not found', 'no longer available', 'job has expired', 'this job is closed', 'no longer accepting applications']):
            continue

        # Check experience if mentioned (reject 6+ years)
        m_exp = re.search(r'(\d+)\+?\s*(?:to|-)\s*(\d+)\+?\s*years', b_low)
        if m_exp:
            min_y = int(m_exp.group(1))
            if min_y >= 6:
                continue

        tech_stack = extract_tech_stack(body, t)
        processed_urls.add(clean_u)
        if jid: all_seen_ids.add(str(jid).lower())

        verified_roles.append({
            'company': c,
            'title': t,
            'location': l,
            'url': u,
            'job_id': jid,
            'tech_stack': tech_stack,
            'source_type': source,
            'exp': '2–5 years (SDE II fit)',
            'score': 95 if ('C#' in tech_stack or 'Azure' in tech_stack or 'Node' in tech_stack) else 90
        })
        print(f"  [VERIFIED OK] {c} - {t} ({l}) | Stack: {tech_stack}")
    except Exception as e:
        pass

driver.quit()

print(f"\nTotal verified pure engineering roles: {len(verified_roles)}")
with open('data/verified_wave13_extended_roles.json', 'w') as f:
    json.dump(verified_roles, f, indent=2)

