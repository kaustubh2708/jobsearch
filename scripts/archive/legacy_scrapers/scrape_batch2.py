import json, re, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

with open('data/linkedin_crawled_cards.json') as f:
    cards = json.load(f)

# Priority: Noida (priority 2), Delhi NCR (priority 3), Remote (priority 4), Bengaluru
def loc_priority(loc):
    loc_l = loc.lower()
    if 'noida' in loc_l:
        return 1
    if 'delhi' in loc_l or 'faridabad' in loc_l:
        return 2
    if 'remote' in loc_l:
        return 3
    if 'bengaluru' in loc_l:
        return 4
    return 5

exclude_title_patterns = [
    r'\b(?:staff|principal|director|manager|lead|architect|vp|head)\b',
    r'\bintern\b',
    r'\bfresher\b',
    r'\bgraduate\b',
    r'\bqa\b|\btest\b|\bsdet\b',
    r'\bdevops\b|\bsre\b',
    r'\bfrontend\b|\bui developer\b',
    r'\bdata engineer\b|\bdata scientist\b',
    r'\btürkiye\b|\bturkey\b'
]

target_title_patterns = [
    r'\bsde\s*(?:ii|2|iii|3)\b',
    r'\bsoftware\s+(?:development\s+)?engineer\s+(?:ii|2|iii|3)\b',
    r'\bswe\s*(?:ii|2|iii|3)\b',
    r'\bbackend\b',
    r'\bback-end\b',
    r'\bback\s+end\b',
    r'\bsoftware\s+engineer\b',
    r'\bsoftware\s+development\s+engineer\b',
    r'\bdistributed\s+systems\b',
    r'\bplatform\s+engineer\b',
    r'\bdot\s*net\b|\bc#\b|\bnode\b',
    r'\bai\s+engineer\b|\bagent\b'
]

# Already scraped IDs
with open('data/linkedin_detailed_discovered.json') as f:
    batch1 = json.load(f)
seen_ids = set(j['job_id'] for j in batch1)

filtered = []
for c in cards:
    if c['job_id'] in seen_ids:
        continue
    t = c['title'].lower()
    if any(re.search(pat, t) for pat in exclude_title_patterns):
        continue
    if any(re.search(pat, t) for pat in target_title_patterns):
        filtered.append(c)

filtered.sort(key=lambda x: (loc_priority(x['location']), x['title']))

print(f"Batch 2 candidates to inspect: {len(filtered)}")

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)
batch2_jobs = []

try:
    for idx, c in enumerate(filtered[:35]):
        job_id = c['job_id']
        url = f"https://in.linkedin.com/jobs/view/{job_id}"
        print(f"[{idx+1}/{min(35, len(filtered))}] Loading {c['title']} @ {c['company']} ({c['location']})...")
        try:
            driver.get(url)
            time.sleep(2.5)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            page_text = soup.get_text(' ', strip=True).lower()
            is_closed = 'no longer accepting applications' in page_text or 'job is closed' in page_text
            
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
                'job_id': job_id,
                'title': c['title'],
                'company': c['company'],
                'location': c['location'],
                'url': url,
                'is_closed': is_closed,
                'recruiter': recruiter,
                'criteria': criteria,
                'experience_snippets': exp_matches[:5],
                'description_snippet': desc_text[:1200]
            }
            batch2_jobs.append(record)
            print(f"   -> Closed: {is_closed} | Recruiter: {bool(recruiter)} | Exp matches: {exp_matches[:2]}")
        except Exception as e:
            print(f"   -> Error loading {job_id}: {e}")
        time.sleep(1)

    combined = batch1 + batch2_jobs
    with open('data/linkedin_detailed_discovered.json', 'w') as f:
        json.dump(combined, f, indent=2)
    print(f"Total jobs saved now: {len(combined)}")
finally:
    driver.quit()
