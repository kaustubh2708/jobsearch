import openpyxl, time, json, urllib.request, ssl, re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

print("Starting comprehensive LinkedIn link audit for past wave data...")

wb = openpyxl.load_workbook('data/Companies(1).xlsx', data_only=True)
ws_past = wb['past wave']

linkedin_roles = []
for r in range(2, ws_past.max_row + 1):
    comp = ws_past.cell(r, 3).value
    title = ws_past.cell(r, 4).value
    url_cell = ws_past.cell(r, 12)
    url = url_cell.hyperlink.target if url_cell.hyperlink else url_cell.value
    wave = ws_past.cell(r, 2).value
    
    if url and 'linkedin.com' in str(url).lower():
        linkedin_roles.append({
            'row': r,
            'wave': str(wave),
            'company': str(comp),
            'title': str(title),
            'url': str(url).strip()
        })

print(f"Total LinkedIn roles found in past wave: {len(linkedin_roles)}")

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)

closed_markers = [
    'no longer accepting applications',
    'this job is no longer available',
    'this job is no longer active',
    'job closed',
    'page not found'
]

results = {
    'total_linkedin_audited': len(linkedin_roles),
    'still_open': 0,
    'closed_or_expired': 0,
    'breakdown_by_wave': {},
    'open_roles': [],
    'closed_roles': []
}

def restart_driver():
    global driver
    try: driver.quit()
    except Exception: pass
    driver = webdriver.Chrome(options=options)

try:
    for idx, item in enumerate(linkedin_roles, 1):
        u = item['url']
        wave = item['wave']
        comp = item['company']
        title = item['title']
        
        if wave not in results['breakdown_by_wave']:
            results['breakdown_by_wave'][wave] = {'open': 0, 'closed': 0}

        status = 'still_open'
        reason = 'Active (Accepting applications)'

        try:
            driver.get(u)
            time.sleep(1.5)
            b_text = driver.find_element('tag name', 'body').text
            b_lower = b_text.lower()

            is_closed = any(cm in b_lower for cm in closed_markers)
            
            # Check for direct apply button
            has_apply = any(x in b_lower for x in ['easy apply', 'apply on company website', 'apply now'])
            
            if is_closed or not has_apply:
                status = 'closed_or_expired'
                reason = 'No longer accepting applications / closed'
                results['closed_or_expired'] += 1
                results['breakdown_by_wave'][wave]['closed'] += 1
                results['closed_roles'].append({
                    'row': item['row'],
                    'wave': wave,
                    'company': comp,
                    'title': title,
                    'url': u,
                    'reason': reason
                })
            else:
                results['still_open'] += 1
                results['breakdown_by_wave'][wave]['open'] += 1
                results['open_roles'].append({
                    'row': item['row'],
                    'wave': wave,
                    'company': comp,
                    'title': title,
                    'url': u
                })

        except Exception as e:
            err_msg = str(e)
            if 'invalid session' in err_msg or 'disconnected' in err_msg:
                print("Re-launching Chrome session...")
                restart_driver()
                try:
                    driver.get(u)
                    time.sleep(1.5)
                    b_text = driver.find_element('tag name', 'body').text.lower()
                    if any(cm in b_text for cm in closed_markers) or not any(x in b_text for x in ['apply', 'easy apply']):
                        status = 'closed_or_expired'
                        reason = 'No longer accepting applications'
                        results['closed_or_expired'] += 1
                        results['breakdown_by_wave'][wave]['closed'] += 1
                        results['closed_roles'].append({
                            'row': item['row'], 'wave': wave, 'company': comp, 'title': title, 'url': u, 'reason': reason
                        })
                    else:
                        results['still_open'] += 1
                        results['breakdown_by_wave'][wave]['open'] += 1
                        results['open_roles'].append({
                            'row': item['row'], 'wave': wave, 'company': comp, 'title': title, 'url': u
                        })
                except Exception:
                    results['closed_or_expired'] += 1
                    results['breakdown_by_wave'][wave]['closed'] += 1
            else:
                results['closed_or_expired'] += 1
                results['breakdown_by_wave'][wave]['closed'] += 1

        if idx % 25 == 0 or idx == len(linkedin_roles):
            print(f"Audit Progress: [{idx}/{len(linkedin_roles)}] Audited. Open: {results['still_open']}, Closed: {results['closed_or_expired']}")
            with open('data/linkedin_past_waves_audit_report.json', 'w') as f:
                json.dump(results, f, indent=2)

finally:
    driver.quit()

print("\nLinkedIn Audit Complete!")
print(f"Total LinkedIn Roles: {results['total_linkedin_audited']}")
print(f"Still Open: {results['still_open']} ({results['still_open']/results['total_linkedin_audited']*100:.1f}%)")
print(f"Closed / Expired: {results['closed_or_expired']} ({results['closed_or_expired']/results['total_linkedin_audited']*100:.1f}%)")
print("\nBreakdown by Wave:")
for w, cnts in sorted(results['breakdown_by_wave'].items()):
    tot = cnts['open'] + cnts['closed']
    pct = (cnts['open']/tot*100) if tot > 0 else 0
    print(f"  {w:8s}: Total {tot:2d} | Open: {cnts['open']:2d} ({pct:5.1f}%) | Closed: {cnts['closed']:2d}")

with open('data/linkedin_past_waves_audit_report.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Report saved to data/linkedin_past_waves_audit_report.json")
