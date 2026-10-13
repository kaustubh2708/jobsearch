import urllib.request, json, ssl, time, re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

queries = [
    'Software Engineer Fresher India',
    'Junior Software Engineer India',
    'Associate Software Engineer India',
    'Graduate Engineer India',
    'SDE 1 India'
]

discovered_cards = []
seen_urls = set()

for q in queries:
    keywords = urllib.parse.quote(q)
    url = f"https://in.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location=India&geoId=102713980&start=0"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            html_text = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html_text, 'html.parser')
            cards = soup.find_all('div', class_='base-card') or soup.find_all('li')
            for c in cards:
                title_el = c.find('h3', class_='base-search-card__title') or c.find('h3')
                comp_el = c.find('h4', class_='base-search-card__subtitle') or c.find('h4')
                loc_el = c.find('span', class_='job-search-card__location') or c.find('span')
                link_el = c.find('a', class_='base-card__full-link') or c.find('a')

                if title_el and comp_el and link_el:
                    u = link_el.get('href', '').split('?')[0].strip()
                    comp = comp_el.get_text(strip=True)
                    title = title_el.get_text(strip=True)
                    loc = loc_el.get_text(strip=True) if loc_el else 'India'

                    if u and u not in seen_urls:
                        seen_urls.add(u)
                        discovered_cards.append({
                            'company': comp,
                            'title': title,
                            'location': loc,
                            'url': u,
                            'source': 'LinkedIn'
                        })
    except Exception as e:
        pass
    time.sleep(0.5)

print(f"Total newly crawled LinkedIn cards: {len(discovered_cards)}")
with open('data/wave13_linkedin_raw.json', 'w') as f:
    json.dump(discovered_cards, f, indent=2)
