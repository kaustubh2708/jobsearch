import json, re, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

with open('data/wave4_crawled_cards.json') as f:
    cards = json.load(f)

# Select priority startups and high-interest roles to check for recruiter cards
keywords_interest = ['backend', 'sde', 'software engineer', 'ai agent', 'node', 'c#', 'cloud']
priority_cards = []
for c in cards:
    t = c['title'].lower()
    loc = c['location'].lower()
    if ('gurgaon' in loc or 'gurugram' in loc or 'noida' in loc or 'delhi' in loc):
        if any(k in t for k in keywords_interest):
            priority_cards.append(c)

print(f"Checking {min(30, len(priority_cards))} priority NCR roles for recruiter cards...")

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
found_recruiters = []

try:
    for idx, c in enumerate(priority_cards[:30]):
        jid = c['job_id']
        url = f"https://in.linkedin.com/jobs/view/{jid}"
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rec_div = soup.find('div', class_='message-the-recruiter') or soup.find('div', class_='facepile') or soup.find('div', class_='hirer-card')
            if rec_div:
                rec_text = " ".join(rec_div.get_text(' ', strip=True).split())
                print(f"FOUND Recruiter for {c['title']} @ {c['company']} ({c['location']}):")
                print(f"  {rec_text}")
                found_recruiters.append({
                    'job_id': jid,
                    'title': c['title'],
                    'company': c['company'],
                    'location': c['location'],
                    'url': url,
                    'recruiter': rec_text
                })
        except Exception:
            pass
        time.sleep(0.5)

    print(f"\nTotal recruiter cards found: {len(found_recruiters)}")
    with open('data/wave4_recruiters_found.json', 'w') as f:
        json.dump(found_recruiters, f, indent=2)
finally:
    driver.quit()
