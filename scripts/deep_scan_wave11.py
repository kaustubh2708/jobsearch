import urllib.request, json, ssl, re, time
from bs4 import BeautifulSoup
import openpyxl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

# 1. Load deduplication index
with open('data/vrinda_all_seen_urls.json') as f:
    dedup = json.load(f)
seen_urls = set(dedup.get('seen_urls', []))
seen_ids = set(dedup.get('seen_ids', []))

# 2. Check dynamic switches
with open('config/search_switches.json') as f:
    switches_cfg = json.load(f)
active_switches = switches_cfg.get('active_switches', {})

exclude_existing_companies = active_switches.get('exclude_companies_with_existing_openings', False)
exclude_python_heavy = active_switches.get('exclude_python_heavy_roles', False)

wb_check = openpyxl.load_workbook('data/Companies(1).xlsx', data_only=True)
existing_companies = set()
if exclude_existing_companies:
    if 'past wave' in wb_check.sheetnames:
        ws_p = wb_check['past wave']
        for r in range(2, ws_p.max_row + 1):
            val = ws_p.cell(r, 3).value
            if val: existing_companies.add(str(val).strip().lower())
    for s in ['Wave 9', 'Wave 10']:
        if s in wb_check.sheetnames:
            ws_s = wb_check[s]
            for r in range(2, ws_s.max_row + 1):
                val = ws_s.cell(r, 2).value
                if val: existing_companies.add(str(val).strip().lower())

print(f"Tracking {len(seen_urls)} seen URLs, {len(seen_ids)} seen IDs.")
print(f"Tracking {len(existing_companies)} existing companies to exclude (switch={exclude_existing_companies}).")

# Paused companies
paused_companies = {'amazon', 'sarvam', 'sarvam ai', 'mongodb'}

all_leads = []

# --- A. Ashby Boards ---
ashby_targets = [
    ('Supabase', 'supabase'),
    ('Ramp', 'ramp'),
    ('Retool', 'retool'),
    ('Brex', 'brex'),
    ('Linear', 'linear'),
    ('Vellum', 'vellum'),
    ('Braintrust', 'braintrust'),
    ('Decagon', 'decagon'),
    ('Cursor', 'cursor'),
    ('Sourcegraph', 'sourcegraph'),
    ('PostHog', 'posthog'),
    ('Railway', 'railway'),
    ('Render', 'render'),
    ('Neon', 'neon'),
    ('Turso', 'turso'),
    ('Encore', 'encore'),
    ('Together AI', 'together-ai'),
    ('Cartesia', 'cartesia'),
    ('Bolna', 'bolna'),
    ('Ema', 'ema'),
    ('Level AI', 'level-ai'),
    ('Plane', 'plane'),
    ('LlamaIndex', 'llamaindex'),
    ('LangChain', 'langchain'),
    ('PAR Technology', 'PAR%20Technology'),
    ('Commure', 'commure'),
    ('AiPrise', 'aiprise'),
    ('Astronomer', 'astronomer')
]

for comp_name, token in ashby_targets:
    if comp_name.lower() in paused_companies: continue
    if exclude_existing_companies and comp_name.lower() in existing_companies: continue
    try:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            data = json.loads(r.read().decode('utf-8'))
            for j in data.get('jobs', []):
                title = j.get('title', '').strip()
                loc = j.get('location', '') or ''
                sec_locs = [str(l) for l in j.get('secondaryLocations', [])]
                full_loc = loc + (' | ' + ', '.join(sec_locs) if sec_locs else '')
                jurl = j.get('jobUrl', '')
                jid = str(j.get('id', ''))
                
                # Check location
                loc_lower = full_loc.lower()
                if not any(k in loc_lower for k in ['india', 'gurgaon', 'gurugram', 'noida', 'delhi', 'bengaluru', 'bangalore', 'remote']):
                    continue
                # Reject senior/staff/intern/lead/manager
                t_lower = title.lower()
                if any(x in t_lower for x in ['intern', 'manager', 'lead', 'staff', 'principal', 'director', 'vp', 'head of', 'sr. manager']):
                    continue
                # Check tech keywords
                if not any(x in t_lower for x in ['engineer', 'developer', 'sde', 'swe', 'architect', 'applied scientist', 'backend', 'platform']):
                    continue
                
                all_leads.append({
                    'source': 'Ashby',
                    'company': comp_name,
                    'title': title,
                    'location': full_loc,
                    'url': jurl,
                    'job_id': jid,
                    'desc_html': j.get('descriptionHtml', '')
                })
    except Exception as e:
        pass

# --- B. Greenhouse Boards ---
gh_targets = [
    ('Grafana Labs', 'grafanalabs'),
    ('Temporal', 'temporal'),
    ('Databricks', 'databricks'),
    ('Stripe', 'stripe'),
    ('Elastic', 'elastic'),
    ('Coinbase', 'coinbase'),
    ('Cloudflare', 'cloudflare'),
    ('GitLab', 'gitlab'),
    ('HackerRank', 'hackerrank'),
    ('Atlan', 'atlan'),
    ('BrowserStack', 'browserstack'),
    ('SimCorp', 'simcorp'),
    ('Keysight Technologies', 'keysighttechnologies'),
    ('Honeywell', 'honeywell'),
    ('3Pillar Global', '3pillarglobal'),
    ('UKG', 'ukg'),
    ('Siemens Energy', 'siemensenergy'),
    ('NatWest Group', 'natwest'),
    ('Fidelity International', 'fidelityinternational'),
    ('Squarepoint Capital', 'squarepointcapital'),
    ('Tower Research Capital', 'towerresearchcapital'),
    ('Deliveroo', 'deliveroo'),
    ('Rubrik', 'rubrik'),
    ('Carta', 'carta'),
    ('Plaid', 'plaid'),
    ('Robinhood', 'robinhood'),
    ('Samsara', 'samsara'),
    ('Chainalysis', 'chainalysis'),
    ('Gusto', 'gusto'),
    ('Rippling', 'rippling'),
    ('Okta', 'okta'),
    ('Branch', 'branchmetrics'),
    ('Cvent', 'cvent'),
    ('S&P Global', 'spglobal'),
    ('ZS Associates', 'zsassociates')
]

for comp_name, token in gh_targets:
    if comp_name.lower() in paused_companies: continue
    if exclude_existing_companies and comp_name.lower() in existing_companies: continue
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            data = json.loads(r.read().decode('utf-8'))
            for j in data.get('jobs', []):
                title = j.get('title', '').strip()
                loc = j.get('location', {}).get('name', '') or ''
                jurl = j.get('absolute_url', '')
                jid = str(j.get('id', ''))
                
                loc_lower = loc.lower()
                if not any(k in loc_lower for k in ['india', 'gurgaon', 'gurugram', 'noida', 'delhi', 'bengaluru', 'bangalore', 'remote']):
                    continue
                t_lower = title.lower()
                if any(x in t_lower for x in ['intern', 'manager', 'lead', 'staff', 'principal', 'director', 'vp', 'head of', 'sr. manager']):
                    continue
                if not any(x in t_lower for x in ['engineer', 'developer', 'sde', 'swe', 'architect', 'applied scientist', 'backend', 'platform']):
                    continue
                
                all_leads.append({
                    'source': 'Greenhouse',
                    'company': comp_name,
                    'title': title,
                    'location': loc,
                    'url': jurl,
                    'job_id': jid,
                    'desc_html': j.get('content', '')
                })
    except Exception as e:
        pass

# --- C. LinkedIn Guest API Searches ---
linkedin_queries = [
    # C# / .NET / Azure
    ('C%23%20OR%20.NET', 'Gurugram', 0),
    ('C%23%20OR%20.NET', 'Gurugram', 25),
    ('C%23%20OR%20.NET', 'Noida', 0),
    ('C%23%20OR%20.NET', 'Noida', 25),
    ('Azure%20Cloud%20Engineer', 'Gurugram', 0),
    ('Azure%20Developer', 'Noida', 0),
    # Node.js / TypeScript
    ('Node.js%20OR%20TypeScript', 'Gurugram', 0),
    ('Node.js%20OR%20TypeScript', 'Gurugram', 25),
    ('TypeScript%20Backend', 'Noida', 0),
    # SDE 2 / Backend
    ('SDE%202%20OR%20SDE%20II', 'Gurugram', 0),
    ('SDE%202%20OR%20SDE%20II', 'Gurugram', 25),
    ('Software%20Engineer%20II', 'Noida', 0),
    ('Software%20Engineer%20II', 'Noida', 25),
    ('Backend%20Engineer', 'Gurugram', 0),
    ('Backend%20Engineer', 'Noida', 0),
    # AI Agents / LLM
    ('AI%20Agent%20OR%20LLM', 'Gurugram', 0),
    ('AI%20Engineer', 'Noida', 0),
    ('Generative%20AI%20Engineer', 'Gurugram', 0),
    # Distributed Systems / Microservices
    ('Distributed%20Systems', 'Gurugram', 0),
    ('Microservices%20Backend', 'Noida', 0),
    ('Microservices%20Backend', 'Gurugram', 0)
]

print(f"Running LinkedIn guest API queries ({len(linkedin_queries)} pages)...")
for kw, loc, start in linkedin_queries:
    try:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw}&location={loc}&start={start}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
            html_content = r.read().decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            for card in soup.find_all('li'):
                title_elem = card.find('h3', class_='base-search-card__title')
                comp_elem = card.find('h4', class_='base-search-card__subtitle')
                loc_elem = card.find('span', class_='job-search-card__location')
                link_elem = card.find('a', class_='base-card__full-link')
                if title_elem and comp_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    comp = comp_elem.get_text(strip=True)
                    location = loc_elem.get_text(strip=True) if loc_elem else loc
                    href = link_elem.get('href', '').split('?')[0]
                    
                    # Paused employers check
                    if comp.lower() in paused_companies: continue
                    if exclude_existing_companies and comp.lower() in existing_companies: continue
                    
                    t_lower = title.lower()
                    if any(x in t_lower for x in ['intern', 'manager', 'lead', 'staff', 'principal', 'director', 'vp', 'head of', 'architect', 'sr. manager']):
                        continue
                    if not any(x in t_lower for x in ['engineer', 'developer', 'sde', 'swe', 'specialist', 'associate', 'analyst', 'programmer']):
                        continue
                        
                    m_id = re.search(r'(\d{8,12})', href)
                    jid = m_id.group(1) if m_id else None
                    
                    all_leads.append({
                        'source': 'LinkedIn',
                        'company': comp,
                        'title': title,
                        'location': location,
                        'url': href,
                        'job_id': jid,
                        'desc_html': ''
                    })
        time.sleep(0.3)
    except Exception as e:
        pass

print(f"Total raw leads gathered across all sources: {len(all_leads)}")

# Filter and deduplicate
unique_leads = []
seen_current = set()

for lead in all_leads:
    clean_url = lead['url'].lower().rstrip('/')
    clean_id = lead['job_id']
    if clean_url in seen_urls or (clean_id and clean_id in seen_ids):
        continue
    if clean_url in seen_current or (clean_id and clean_id in seen_current):
        continue
    seen_current.add(clean_url)
    if clean_id: seen_current.add(clean_id)
    unique_leads.append(lead)

print(f"Total fresh deduplicated leads: {len(unique_leads)}")

with open('data/raw_wave11_leads.json', 'w') as f:
    json.dump(unique_leads, f, indent=2)

print("Saved raw leads to data/raw_wave11_leads.json")
