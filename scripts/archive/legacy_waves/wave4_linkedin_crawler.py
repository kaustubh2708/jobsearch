import urllib.parse
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

searches = [
    # Gurgaon Target Unicorns & Startups
    {'kw': 'Zomato Software Engineer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Blinkit Backend Engineer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Urban Company Software Development Engineer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'MakeMyTrip SDE 2', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'CARS24 Backend', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Shiprocket Software Engineer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Airtel Digital Backend Engineer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Sprinklr Software Engineer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'American Express Engineer II', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Expedia Software Development Engineer II', 'loc': 'Gurgaon, Haryana, India'},
    # Specific Tech & Role queries Gurgaon
    {'kw': 'AI Agent Backend', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'GenAI Engineer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Node.js Backend Developer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'C# .NET Backend Engineer', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Microservices Backend', 'loc': 'Gurgaon, Haryana, India'},
    # Noida
    {'kw': 'SDE 2', 'loc': 'Noida, Uttar Pradesh, India'},
    {'kw': 'Software Engineer II', 'loc': 'Noida, Uttar Pradesh, India'},
    {'kw': 'Backend Engineer', 'loc': 'Noida, Uttar Pradesh, India'},
    {'kw': 'InfoEdge Backend Engineer', 'loc': 'Noida, Uttar Pradesh, India'},
    {'kw': 'Paytm Software Engineer', 'loc': 'Noida, Uttar Pradesh, India'},
    {'kw': 'Adobe Computer Scientist', 'loc': 'Noida, Uttar Pradesh, India'},
    # Delhi NCR / Remote India
    {'kw': 'Backend Engineer', 'loc': 'Remote', 'extra': '&f_WT=2'},
    {'kw': 'Software Engineer II', 'loc': 'Remote', 'extra': '&f_WT=2'},
    {'kw': 'AI Agent Engineer', 'loc': 'India'},
    {'kw': 'Backend SDE II', 'loc': 'Delhi, India'},
]

# Load seen IDs
try:
    with open('data/qualified_linkedin_leads.json') as f:
        existing = json.load(f)
    seen_ids = set(x['job_id'] for x in existing)
except Exception:
    seen_ids = set()

print(f"Loaded {len(seen_ids)} existing job IDs to avoid duplicate re-crawling.")

driver = webdriver.Chrome(options=options)
new_cards = {}

try:
    for idx, s in enumerate(searches):
        kw = s['kw']
        loc = s['loc']
        extra = s.get('extra', '')
        url = f"https://www.linkedin.com/jobs/search?keywords={urllib.parse.quote(kw)}&location={urllib.parse.quote(loc)}{extra}"
        print(f"[{idx+1}/{len(searches)}] Crawling: '{kw}' in '{loc}'...")
        try:
            driver.get(url)
            time.sleep(2.5)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            cards = soup.find_all('div', class_='base-card')
            found_count = 0
            for c in cards:
                urn = c.get('data-entity-urn', '')
                job_id = urn.split(':')[-1] if urn else ''
                t = c.find('h3', class_='base-search-card__title')
                comp = c.find('h4', class_='base-search-card__subtitle')
                l = c.find('span', class_='job-search-card__location')
                a = c.find('a', class_='base-card__full-link')
                
                title = t.get_text(strip=True) if t else ''
                company = comp.get_text(strip=True) if comp else ''
                location = l.get_text(strip=True) if l else ''
                link = a['href'] if a and a.has_attr('href') else ''
                
                if not job_id and link:
                    m = re.search(r'-([0-9]{8,12})(?:\?|$)', link)
                    if m:
                        job_id = m.group(1)
                
                if job_id and job_id not in seen_ids and job_id not in new_cards:
                    new_cards[job_id] = {
                        'job_id': job_id,
                        'title': title,
                        'company': company,
                        'location': location,
                        'link': f"https://in.linkedin.com/jobs/view/{job_id}",
                        'search_kw': kw,
                        'search_loc': loc
                    }
                    found_count += 1
            print(f"   -> Added {found_count} fresh candidate cards (Total new: {len(new_cards)})")
        except Exception as e:
            print(f"   -> Error crawling '{kw}': {e}")
        time.sleep(1)

    print(f"\nCrawling complete! Discovered {len(new_cards)} brand-new candidate cards.")
    with open('data/wave4_crawled_cards.json', 'w') as f:
        json.dump(list(new_cards.values()), f, indent=2)
finally:
    driver.quit()
