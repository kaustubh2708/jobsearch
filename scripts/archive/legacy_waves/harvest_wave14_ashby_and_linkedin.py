import urllib.request, urllib.parse, json, ssl, time
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

with open('data/master_history_dedup_wave14.json') as f:
    dedup = json.load(f)
history_companies = {c.lower().strip() for c in dedup['companies']}
history_urls = {u.strip() for u in dedup['urls']}

# 1. Harvest Ashby
ashby_orgs = [
    'linear', 'warp', 'vanta', 'retool', 'synthesia', 'descript', 'harvey',
    'snyk', 'glean', 'cohere', 'mistral', 'together', 'groq', 'perplexity',
    'supabase', 'hex', 'deepgram', 'tome', 'dust', 'pave', 'magic', 'elevenlabs'
]

ashby_results = []
for org in ashby_orgs:
    if org in history_companies: continue
    url = f'https://api.ashbyhq.com/posting-api/job-board/{org}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for j in data.get('jobs', []):
                title = j.get('title', '')
                loc = (j.get('locationName') or '').lower()
                sec_locs = [str(x).lower() for x in (j.get('secondaryLocations') or [])]
                all_locs = loc + ' ' + ' '.join(sec_locs)
                if not any(k in all_locs for k in ['india', 'bengaluru', 'bangalore', 'noida', 'gurgaon', 'hyderabad', 'pune', 'remote']):
                    continue
                tl = title.lower()
                if any(w in tl for w in ['senior', 'sr.', 'principal', 'staff', 'lead', 'manager', 'director', 'intern', 'apprentice', 'trainee', 'head']):
                    continue
                if not any(w in tl for w in ['engineer', 'developer', 'sde', 'qa', 'analyst', 'systems', 'cloud']):
                    continue
                ashby_results.append({
                    'company': org.capitalize(),
                    'title': title,
                    'location': j.get('locationName') or 'India / Remote',
                    'url': j.get('jobUrl'),
                    'desc_html': j.get('descriptionHtml', ''),
                    'source': 'Ashby'
                })
    except:
        pass

print(f"Total Ashby candidates harvested: {len(ashby_results)}")
with open('data/wave14_ashby_raw.json', 'w') as f:
    json.dump(ashby_results, f, indent=2)

# 2. Harvest fresh LinkedIn cards across entry-level queries
queries = [
    'Junior Software Engineer India',
    'Associate Software Engineer India',
    'Graduate Software Engineer India',
    'Software Engineer Fresher India',
    'Entry Level Developer India',
    'SDE 1 India',
    'Junior Full Stack Engineer India',
    'Associate Backend Engineer India',
    'Junior Cloud Engineer India'
]

discovered_li = []
seen_urls = set(history_urls)

for q in queries:
    for start in [0, 25]:
        kw = urllib.parse.quote(q)
        url = f"https://in.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw}&location=India&geoId=102713980&start={start}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                soup = BeautifulSoup(resp.read().decode('utf-8', errors='ignore'), 'html.parser')
                cards = soup.find_all('div', class_='base-card') or soup.find_all('li')
                for c in cards:
                    t_el = c.find('h3', class_='base-search-card__title') or c.find('h3')
                    comp_el = c.find('h4', class_='base-search-card__subtitle') or c.find('h4')
                    loc_el = c.find('span', class_='job-search-card__location') or c.find('span')
                    link_el = c.find('a', class_='base-card__full-link') or c.find('a')

                    if t_el and comp_el and link_el:
                        comp = comp_el.get_text(strip=True)
                        title = t_el.get_text(strip=True)
                        u = link_el.get('href', '').split('?')[0].strip()
                        loc = loc_el.get_text(strip=True) if loc_el else 'India'

                        if u not in seen_urls and comp.lower() not in history_companies:
                            seen_urls.add(u)
                            discovered_li.append({
                                'company': comp,
                                'title': title,
                                'location': loc,
                                'url': u,
                                'source': 'LinkedIn'
                            })
        except:
            pass
        time.sleep(0.3)

print(f"Total newly harvested distinct LinkedIn cards: {len(discovered_li)}")
with open('data/wave14_linkedin_raw.json', 'w') as f:
    json.dump(discovered_li, f, indent=2)
