import json, time, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Load already verified Wave 14 roles
with open('data/verified_wave14_roles.json') as f:
    verified_w14 = json.load(f)

with open('data/raw_additional_ncr_wave14.json') as f:
    additional_leads = json.load(f)

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

disqualifiers = [
    'field engineer', 'solutions engineer', 'solutions architect', 'product support',
    'gtm engineer', 'customer reliability', 'support engineer', 'sales engineer',
    'network engineer', 'business analyst', 'marketing', 'trainee', 'türkiye',
    'intern', 'manager', 'lead', 'principal', 'director', 'vp', 'head of',
    'cursor', 'staff software engineer', 'lead engineer', 'associate solutions engineer',
    'senior staff', 'qa engineer', 'test engineer', 'automation engineer',
    'data analyst', 'sdet', 'sr software engineer', 'sr. software engineer',
    'senior software engineer', 'senior engineer', 'sr engineer', 'data engineer',
    'salesforce', 'sap abap', 'security analyst', 'technical account manager',
    'servicenow', 'boomi', 'ruby on rails'
]

options = Options()
options.add_argument('--headless=new')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
driver = webdriver.Chrome(options=options)

print(f"Verifying {len(additional_leads)} additional NCR candidate leads...")
seen_urls = {r['url'].lower().rstrip('/') for r in verified_w14}

for item in additional_leads:
    u = item['url']
    c = item['company']
    t = item['title']
    l = item.get('location', '')

    if u.lower().rstrip('/') in seen_urls: continue
    t_low = t.lower()
    if any(dk in t_low for dk in disqualifiers): continue
    if 'python developer' in t_low or 'python engineer' in t_low: continue

    try:
        driver.get(u)
        time.sleep(1.5)
        body = driver.find_element('tag name', 'body').text
        b_low = body.lower()

        if any(ci in b_low for ci in ['job does not exist', 'page not found', 'no longer available', 'job has expired', 'this job is closed', 'no longer accepting applications']):
            continue

        m_exp = re.search(r'(\d+)\+?\s*(?:to|-)\s*(\d+)\+?\s*years', b_low)
        if m_exp and int(m_exp.group(1)) >= 6:
            continue

        stack = extract_tech_stack(body, t)
        seen_urls.add(u.lower().rstrip('/'))

        verified_w14.append({
            'company': c,
            'title': t,
            'location': l,
            'url': u,
            'tech_stack': stack,
            'source_type': 'LinkedIn',
            'exp': '2–5 years (SDE II fit)',
            'score': 95 if ('C#' in stack or 'Azure' in stack or 'Node' in stack) else 90
        })
        print(f"  [OK] {c} - {t} ({l}) | Stack: {stack}")
    except Exception as e:
        pass

driver.quit()

print(f"Total verified candidates across both sweeps: {len(verified_w14)}")
with open('data/verified_wave14_all.json', 'w') as f:
    json.dump(verified_w14, f, indent=2)

