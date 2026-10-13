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

# Targeted search queries specifically for 0 YOE / Fresher / Intern / GET
searches = [
    # Gurgaon / Noida Fresher & Intern Queries
    {'kw': 'Software Engineer Intern', 'loc': 'Gurgaon, Haryana, India', 'extra': '&f_E=1'},
    {'kw': 'Backend Engineer Intern', 'loc': 'Gurgaon, Haryana, India', 'extra': '&f_E=1'},
    {'kw': 'AI ML Intern', 'loc': 'Gurgaon, Haryana, India', 'extra': '&f_E=1'},
    {'kw': 'Graduate Engineer Trainee', 'loc': 'Noida, Uttar Pradesh, India', 'extra': '&f_E=1,2'},
    {'kw': 'Software Engineer Intern', 'loc': 'Noida, Uttar Pradesh, India', 'extra': '&f_E=1'},
    {'kw': 'Python Intern', 'loc': 'Noida, Uttar Pradesh, India', 'extra': '&f_E=1'},
    {'kw': 'SDE Intern', 'loc': 'Gurgaon, Haryana, India', 'extra': '&f_E=1'},
    {'kw': 'Junior Backend Developer', 'loc': 'Delhi, India', 'extra': '&f_E=2'},
    # Enterprise & Unicorn Fresher / Intern Queries
    {'kw': 'Zomato Software Engineer Intern', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Blinkit Software Intern', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Cars24 SDE Intern', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Paytm Software Engineer Intern', 'loc': 'Noida, Uttar Pradesh, India'},
    {'kw': 'Tower Research Capital Intern', 'loc': 'Gurgaon, Haryana, India'},
    {'kw': 'Adobe College Graduate Software Engineer', 'loc': 'Noida, Uttar Pradesh, India'},
    {'kw': 'American Express Campus Analyst', 'loc': 'Gurgaon, Haryana, India'},
    # Pan-India / Remote Fresher Roles
    {'kw': 'Software Engineer Intern', 'loc': 'Remote', 'extra': '&f_WT=2&f_E=1'},
    {'kw': 'Python Backend Intern', 'loc': 'Remote', 'extra': '&f_WT=2&f_E=1'},
    {'kw': 'Data Engineer Intern', 'loc': 'Bengaluru, Karnataka, India', 'extra': '&f_E=1'},
    {'kw': 'Graduate Software Engineer', 'loc': 'Bengaluru, Karnataka, India', 'extra': '&f_E=1,2'},
    {'kw': 'Junior Machine Learning Engineer', 'loc': 'India', 'extra': '&f_E=2'},
]

# Load seen URLs
with open('data/all_existing_urls.json') as f:
    existing_meta = json.load(f)
seen_urls = set(existing_meta.get('urls', []))

driver = webdriver.Chrome(options=options)
discovered_cards = {}

non_tech_filter = ['talent acquisition', 'recruiter', 'hr', 'sales', 'marketing', 'business development', 'finance intern', 'accounting', 'fulfillment', 'content writer', 'legal']

try:
    for idx, s in enumerate(searches):
        kw = s['kw']
        loc = s['loc']
        extra = s.get('extra', '')
        url = f"https://www.linkedin.com/jobs/search?keywords={urllib.parse.quote(kw)}&location={urllib.parse.quote(loc)}{extra}"
        print(f"[{idx+1}/{len(searches)}] Searching: '{kw}' in '{loc}'...")
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            cards = soup.find_all('div', class_='base-card')
            found_count = 0
            for c in cards:
                t = c.find('h3', class_='base-search-card__title')
                comp = c.find('h4', class_='base-search-card__subtitle')
                l = c.find('span', class_='job-search-card__location')
                a = c.find('a', class_='base-card__full-link')
                
                title = t.get_text(strip=True) if t else ''
                company = comp.get_text(strip=True) if comp else ''
                location = l.get_text(strip=True) if l else ''
                link = a['href'] if a and a.has_attr('href') else ''
                
                if not link:
                    continue
                
                # Clean URL (strip tracking params)
                clean_url = link.split('?')[0]
                
                # Check non-tech filter
                if any(nt in title.lower() for nt in non_tech_filter):
                    continue
                
                # Extract job ID
                m = re.search(r'-([0-9]{8,12})(?:$)', clean_url)
                jid = m.group(1) if m else clean_url
                
                if clean_url.lower() not in seen_urls and jid not in discovered_cards:
                    discovered_cards[jid] = {
                        'company': company,
                        'title': title,
                        'location': location,
                        'url': clean_url,
                        'source': 'LinkedIn',
                        'search_kw': kw,
                        'search_loc': loc
                    }
                    found_count += 1
            print(f"   -> Found {found_count} new candidate cards (Total: {len(discovered_cards)})")
        except Exception as e:
            print(f"   -> Error: {e}")
        time.sleep(1)

    print(f"\nDiscovered total {len(discovered_cards)} raw fresher LinkedIn cards.")
    with open('data/fresher_linkedin_cards.json', 'w') as f:
        json.dump(list(discovered_cards.values()), f, indent=2)
finally:
    driver.quit()
