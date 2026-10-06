import json
import re
import time
import os
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.path.insert(0, os.path.dirname(__file__))
from linkedin_freshness import extract_linkedin_freshness

# Key selected Job IDs from Wave 4
selected_job_ids = [
    # Amazon SDE II Gurgaon
    '4455906772', '4468328473', '4460331411', '4455902440',
    # MongoDB AI Builder Experience Gurugram
    '4456363101', '4471630738', '4452436908',
    # American Express Gurugram
    '4465779116', '4463542035',
    # Adobe Noida (AI Agents, MTS 2, CS 2)
    '4463846192', '4457471026', '4425549381', '4461962326',
    # Optum Noida (Agentic AI, Azure Backend)
    '4471124712', '4454322164', '4470635270',
    # PwC GenAI & Agentic AI Noida
    '4472068152',
    # UKG Noida
    '4471038533', '4471581852',
    # Aristocrat Gurugram
    '4457465776', '4468892666',
    # GreyOrange Gurgaon
    '4377166673', '4416631641',
    # PhysicsWallah Noida
    '4442576406',
    # Barco Noida
    '4425877575', '4448256922'
]

# Also load metadata from wave4_crawled_cards.json
with open('data/wave4_crawled_cards.json') as f:
    cards = json.load(f)
cards_by_id = {c['job_id']: c for c in cards}

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)
detailed_wave4 = []

try:
    for idx, jid in enumerate(selected_job_ids):
        meta = cards_by_id.get(jid, {})
        title = meta.get('title', 'Software Engineer')
        company = meta.get('company', 'Company')
        loc = meta.get('location', 'Gurgaon/Noida')
        url = f"https://in.linkedin.com/jobs/view/{jid}"
        
        print(f"[{idx+1}/{len(selected_job_ids)}] Scraping: {title} @ {company} ({loc})...")
        try:
            driver.get(url)
            time.sleep(2.5)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            page_text = soup.get_text(' ', strip=True).lower()
            is_closed = 'no longer accepting applications' in page_text or 'job is closed' in page_text
            freshness = extract_linkedin_freshness(page_text)
            
            # Recruiter / poster card
            recruiter = None
            rec_div = soup.find('div', class_='message-the-recruiter')
            if rec_div:
                recruiter = rec_div.get_text(' ', strip=True)
            else:
                rec_card = soup.find('div', class_='facepile') or soup.find('div', class_='hirer-card')
                if rec_card:
                    recruiter = rec_card.get_text(' ', strip=True)
            
            criteria = {}
            for li in soup.find_all('li', class_='description__job-criteria-item'):
                sub = li.find('h3')
                val = li.find('span')
                if sub and val:
                    criteria[sub.get_text(strip=True)] = val.get_text(strip=True)
            
            desc_div = soup.find('div', class_='show-more-less-html__markup')
            desc_text = desc_div.get_text('\n', strip=True) if desc_div else ''
            
            exp_matches = re.findall(r'(\d+[\s\-\–to]+\d+\s+years?(?:\s+of)?\s+experience|\d+\+?\s+years?(?:\s+of)?\s+experience)', desc_text, re.IGNORECASE)
            
            record = {
                'job_id': jid,
                'title': title,
                'company': company,
                'location': loc,
                'url': url,
                'is_closed': is_closed,
                **freshness,
                'recruiter': recruiter,
                'criteria': criteria,
                'experience_snippets': exp_matches[:5],
                'description_snippet': desc_text[:1500]
            }
            detailed_wave4.append(record)
            print(f"   -> Closed: {is_closed} | Recruiter: {bool(recruiter)} | Exp matches: {exp_matches[:2]}")
        except Exception as e:
            print(f"   -> Error scraping {jid}: {e}")
        time.sleep(1)

    with open('data/wave4_detailed_jobs.json', 'w') as f:
        json.dump(detailed_wave4, f, indent=2)
    print(f"\nSaved {len(detailed_wave4)} detailed Wave 4 jobs to data/wave4_detailed_jobs.json")
finally:
    driver.quit()
