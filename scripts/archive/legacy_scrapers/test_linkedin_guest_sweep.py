import urllib.request, json, ssl, re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

queries = [
    ('C%23%20OR%20.NET', 'Gurugram'),
    ('Node.js%20OR%20TypeScript', 'Gurugram'),
    ('SDE%202%20OR%20SDE%20II', 'Gurugram'),
    ('.NET%20OR%20Azure', 'Noida'),
    ('Backend%20Engineer', 'Noida'),
    ('AI%20Agent%20OR%20LLM', 'Gurugram'),
    ('Distributed%20Systems', 'Gurugram')
]

found_jobs = []

for q, loc in queries:
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q}&location={loc}&start=0"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            html_content = r.read().decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            cards = soup.find_all('li')
            print(f"Query '{q}' in '{loc}': {len(cards)} job cards found")
            for card in cards:
                title_elem = card.find('h3', class_='base-search-card__title')
                comp_elem = card.find('h4', class_='base-search-card__subtitle')
                loc_elem = card.find('span', class_='job-search-card__location')
                link_elem = card.find('a', class_='base-card__full-link')
                if title_elem and comp_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    comp = comp_elem.get_text(strip=True)
                    location = loc_elem.get_text(strip=True) if loc_elem else loc
                    href = link_elem.get('href', '').split('?')[0]
                    # extract numeric id
                    m_id = re.search(r'(\d{8,12})', href)
                    jid = m_id.group(1) if m_id else None
                    found_jobs.append({
                        'title': title,
                        'company': comp,
                        'location': location,
                        'url': href,
                        'job_id': jid
                    })
    except Exception as e:
        print(f"Error for '{q}' in '{loc}': {e}")

print(f"\nTotal LinkedIn cards collected: {len(found_jobs)}")
unique_ids = set()
dedup_jobs = []
for j in found_jobs:
    if j['job_id'] and j['job_id'] not in unique_ids:
        unique_ids.add(j['job_id'])
        dedup_jobs.append(j)
print(f"Unique job IDs: {len(dedup_jobs)}")
for j in dedup_jobs[:10]:
    print(f"  [{j['company']}] {j['title']} ({j['location']}) -> {j['url']}")
