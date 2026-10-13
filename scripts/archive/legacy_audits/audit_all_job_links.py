import json, time, re, ssl, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('data/job_links_extracted.json') as f:
    items = json.load(f)

targets = [x for x in items if not x.get('is_header') and x.get('url')]
print(f"Total targets to audit: {len(targets)}")

non_li = [x for x in targets if 'linkedin.com' not in x['url'].lower()]
li = [x for x in targets if 'linkedin.com' in x['url'].lower()]

results = {}

# 1. Audit non-LinkedIn ATS URLs via fast multi-threaded HTTP + DOM inspection
print(f"\n--- Phase 1: Auditing {len(non_li)} Non-LinkedIn ATS URLs ---")

def check_ats_url(item):
    r_idx = item['row']
    url = item['url']
    comp = item['company']
    
    # Specific Ashby API optimization
    m_ashby = re.search(r'ashbyhq\.com/([^/]+)/([a-f0-9\-]+)', url)
    if m_ashby:
        org = m_ashby.group(1)
        jid = m_ashby.group(2)
        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{org}"
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                live_ids = [str(j.get('id')).lower() for j in data.get('jobs', [])]
                if jid.lower() in live_ids:
                    return r_idx, {'status': 'open', 'reason': 'Ashby API confirmed active'}
                else:
                    return r_idx, {'status': 'closed', 'reason': 'Ashby API: Job not in active board'}
        except Exception as e:
            pass

    # Specific Greenhouse API optimization
    m_gh = re.search(r'greenhouse\.io/([^/]+)/jobs/(\d+)', url)
    if m_gh:
        org = m_gh.group(1)
        jid = m_gh.group(2)
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs/{jid}"
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                if resp.status == 200:
                    return r_idx, {'status': 'open', 'reason': 'Greenhouse API 200 OK'}
        except urllib.error.HTTPError as e:
            if e.code in [404, 410]:
                return r_idx, {'status': 'closed', 'reason': f'Greenhouse API HTTP {e.code}'}
        except:
            pass

    # Generic HTTP check
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            content = resp.read().decode('utf-8', errors='ignore').lower()
            if any(k in content for k in ['job does not exist', 'page not found', 'no longer available', 'job has expired', 'this job is closed', 'position is closed', 'posting has expired', '404 not found']):
                return r_idx, {'status': 'closed', 'reason': 'HTML contains expired/closed indicator'}
            return r_idx, {'status': 'open', 'reason': f'HTTP {resp.status} OK'}
    except urllib.error.HTTPError as e:
        if e.code in [404, 410]:
            return r_idx, {'status': 'closed', 'reason': f'HTTP Error {e.code}'}
        return r_idx, {'status': 'open', 'reason': f'HTTP Error {e.code} (needs headless verification)'}
    except Exception as e:
        return r_idx, {'status': 'open', 'reason': f'Request failed: {str(e)[:30]}'}

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(check_ats_url, item) for item in non_li]
    for fut in futures:
        r_idx, res = fut.result()
        results[r_idx] = res

# 2. Audit LinkedIn URLs via Selenium Headless Chrome
print(f"\n--- Phase 2: Auditing {len(li)} LinkedIn URLs with Selenium Headless Chrome ---")

options = Options()
options.add_argument('--headless=new')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
driver = webdriver.Chrome(options=options)

closed_li_count = 0
open_li_count = 0

for idx, item in enumerate(li, 1):
    r_idx = item['row']
    url = item['url']
    comp = item['company']
    title = item['title']

    try:
        driver.get(url)
        time.sleep(1.2)
        body = driver.find_element('tag name', 'body').text
        b_low = body.lower()

        if any(ci in b_low for ci in ['no longer accepting applications', 'job is closed', 'posting is no longer active', 'job has expired', 'page not found']):
            results[r_idx] = {'status': 'closed', 'reason': 'LinkedIn: No longer accepting applications / Closed'}
            closed_li_count += 1
            print(f"  [{idx}/{len(li)}] Row {r_idx}: CLOSED - {comp} ({title})")
        else:
            results[r_idx] = {'status': 'open', 'reason': 'LinkedIn: Active posting'}
            open_li_count += 1
            print(f"  [{idx}/{len(li)}] Row {r_idx}: OPEN - {comp} ({title})")
    except Exception as e:
        # Fallback to guest API or mark open
        results[r_idx] = {'status': 'open', 'reason': f'Error checking: {str(e)[:30]}'}
        open_li_count += 1

driver.quit()

print(f"\nAudit complete: {len(results)} evaluated.")
with open('data/job_links_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)

