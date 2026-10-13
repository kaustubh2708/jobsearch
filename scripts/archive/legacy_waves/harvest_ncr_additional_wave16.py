import urllib.request, json, ssl, re, time
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

with open('data/raw_wave16_candidates.json') as f:
    existing_cands = json.load(f)

existing_urls = {item['url'].lower().rstrip('/') for item in existing_cands}

with open('data/vrinda_all_seen_urls.json') as f:
    dedup = json.load(f)
for u in dedup.get('seen_urls', []):
    existing_urls.add(u.lower().rstrip('/'))

# Targeted queries for Gurugram & Noida .NET / Azure / Node.js
queries = [
    ('C%23%20NET%20Core%20Gurugram', 'Gurugram', 0),
    ('C%23%20NET%20Core%20Noida', 'Noida', 0),
    ('Azure%20Cloud%20Engineer%20Gurugram', 'Gurugram', 0),
    ('Azure%20Cloud%20Engineer%20Noida', 'Noida', 0),
    ('Node.js%20TypeScript%20backend%20Gurugram', 'Gurugram', 0),
    ('Node.js%20TypeScript%20backend%20Noida', 'Noida', 0),
    ('Backend%20Engineer%20Microservices%20Gurugram', 'Gurugram', 0),
    ('Backend%20Engineer%20Microservices%20Noida', 'Noida', 0),
    ('SDE%20II%20Gurugram', 'Gurugram', 25),
    ('SDE%20II%20Noida', 'Noida', 25),
    ('Full%20Stack%20NET%20developer%20Gurgaon', 'Gurugram', 0),
    ('Full%20Stack%20NET%20developer%20Noida', 'Noida', 0),
]

disqualifiers = [
    'field engineer', 'solutions architect', 'solutions engineer', 'product support',
    'gtm engineer', 'customer reliability', 'support engineer', 'sales engineer',
    'network engineer', 'business analyst', 'marketing', 'trainee', 'türkiye',
    'intern', 'manager', 'lead', 'principal', 'director', 'vp', 'head of',
    'cursor', 'staff software engineer', 'lead engineer', 'associate solutions engineer',
    'senior staff', 'qa engineer', 'test engineer', 'automation engineer',
    'data analyst', 'sdet', 'data engineer', 'salesforce', 'sap abap', 'servicenow',
    'boomi', 'ruby on rails'
]

raw_additional = []
for q, loc, start in queries:
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q}&location={loc}&start={start}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6, context=ctx) as r:
            html = r.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            for card in soup.find_all('li'):
                title_el = card.find('h3', class_='base-search-card__title')
                comp_el = card.find('h4', class_='base-search-card__subtitle')
                loc_el = card.find('span', class_='job-search-card__location')
                link_el = card.find('a', class_='base-card__full-link')
                if title_el and comp_el and link_el:
                    title = title_el.get_text(strip=True)
                    comp = comp_el.get_text(strip=True)
                    location = loc_el.get_text(strip=True) if loc_el else loc
                    href = link_el.get('href', '').split('?')[0]

                    if comp.lower() in {'amazon', 'sarvam', 'sarvam ai', 'mongodb', 'microsoft'}: continue
                    t_lower = title.lower()
                    if any(dk in t_lower for dk in disqualifiers): continue
                    if 'python developer' in t_lower or 'sr python' in t_lower or 'python engineer' in t_lower: continue

                    if not any(ek in t_lower for ek in ['software engineer', 'backend', 'developer', 'sde', 'swe', 'full stack', 'cloud engineer', 'systems engineer']):
                        continue

                    clean_href = href.lower().rstrip('/')
                    if clean_href in existing_urls: continue
                    existing_urls.add(clean_href)

                    raw_additional.append({
                        'company': comp,
                        'title': title,
                        'location': location,
                        'url': href,
                        'source': 'LinkedIn'
                    })
        time.sleep(0.3)
    except Exception as e:
        pass

print(f"Discovered {len(raw_additional)} additional raw candidate leads for Wave 16.")

combined = existing_cands + raw_additional
print(f"Total pool for verification: {len(combined)}")
with open('data/raw_wave16_full_pool.json', 'w') as f:
    json.dump(combined, f, indent=2)

