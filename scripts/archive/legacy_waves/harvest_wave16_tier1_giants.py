import urllib.request, json, ssl, re, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

with open('data/verified_wave16_all_pool.json') as f:
    verified_w16 = json.load(f)

seen_urls = {r['url'].lower().rstrip('/') for r in verified_w16}

with open('data/vrinda_all_seen_urls.json') as f:
    dedup = json.load(f)
for u in dedup.get('seen_urls', []):
    seen_urls.add(u.lower().rstrip('/'))

# Specific company targeting for giants / top product tech in India
target_companies = [
    'PayPal', 'Intuit', 'Cisco', 'Adobe', 'Salesforce', 'Oracle', 'Siemens',
    'Walmart Global Tech', 'Qualcomm', 'Nvidia', 'AMD', 'Atlassian', 'Uber',
    'Morgan Stanley', 'Goldman Sachs', 'JPMorganChase', 'American Express',
    'NatWest Group', 'Fidelity International', 'SAP Labs', 'Honeywell'
]

raw_leads = []
for comp in target_companies:
    for q in ['Software%20Engineer', 'Backend%20Engineer', '.NET']:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={comp}%20{q}&location=India&start=0"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
                html = r.read().decode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')
                for card in soup.find_all('li'):
                    title_el = card.find('h3', class_='base-search-card__title')
                    comp_el = card.find('h4', class_='base-search-card__subtitle')
                    loc_el = card.find('span', class_='job-search-card__location')
                    link_el = card.find('a', class_='base-card__full-link')
                    if title_el and comp_el and link_el:
                        title = title_el.get_text(strip=True)
                        comp_name = comp_el.get_text(strip=True)
                        location = loc_el.get_text(strip=True) if loc_el else 'India'
                        href = link_el.get('href', '').split('?')[0]

                        if comp_name.lower() in {'amazon', 'sarvam', 'sarvam ai', 'mongodb', 'microsoft'}: continue
                        t_lower = title.lower()
                        if any(dk in t_lower for dk in ['field engineer', 'solutions architect', 'solutions engineer', 'support engineer', 'sales engineer', 'network engineer', 'intern', 'manager', 'lead', 'principal', 'director', 'vp', 'head of', 'cursor', 'staff software engineer', 'qa engineer', 'sdet', 'data engineer']):
                            continue
                        if 'python developer' in t_lower or 'sr python' in t_lower: continue

                        if not any(ek in t_lower for ek in ['software engineer', 'backend', 'developer', 'sde', 'swe', 'full stack', 'cloud engineer', 'systems engineer']):
                            continue

                        clean_href = href.lower().rstrip('/')
                        if clean_href in seen_urls: continue
                        seen_urls.add(clean_href)

                        raw_leads.append({
                            'company': comp_name,
                            'title': title,
                            'location': location,
                            'url': href,
                            'source': 'LinkedIn'
                        })
            time.sleep(0.2)
        except Exception as e:
            pass

print(f"Harvested {len(raw_leads)} potential giant leads. Verifying with headless Chrome...")

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

options = Options()
options.add_argument('--headless=new')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
driver = webdriver.Chrome(options=options)

added_verified = []
for item in raw_leads:
    u = item['url']
    c = item['company']
    t = item['title']
    l = item['location']

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
        added_verified.append({
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

all_verified = verified_w16 + added_verified
print(f"Total verified candidates for Wave 16: {len(all_verified)}")

with open('data/verified_wave16_all_pool.json', 'w') as f:
    json.dump(all_verified, f, indent=2)

