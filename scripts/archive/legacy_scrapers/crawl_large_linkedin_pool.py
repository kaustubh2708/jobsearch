import urllib.request, urllib.parse, json, ssl, time
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

with open('data/master_history_dedup_wave13.json') as f:
    dedup = json.load(f)
history_companies = {c.lower().strip() for c in dedup['companies']}
history_urls = {u.strip() for u in dedup['urls']}

queries = [
    'Associate Software Engineer',
    'Junior Software Engineer',
    'Graduate Engineer',
    'SDE 1',
    'Software Engineer Fresher',
    'Entry Level Software Engineer',
    'Junior Python Developer',
    'Junior Java Developer',
    'Associate Developer',
    'Junior Backend Engineer',
    'Junior Cloud Engineer',
    'Junior Full Stack Developer'
]

discovered = []
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
                            discovered.append({
                                'company': comp,
                                'title': title,
                                'location': loc,
                                'url': u,
                                'source': 'LinkedIn'
                            })
        except:
            pass
        time.sleep(0.4)

print(f"Total newly harvested distinct LinkedIn cards: {len(discovered)}")
with open('data/large_linkedin_harvest_wave13.json', 'w') as f:
    json.dump(discovered, f, indent=2)
