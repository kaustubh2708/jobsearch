import openpyxl, time, json, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

print("Starting background audit of past wave links...")

wb = openpyxl.load_workbook('data/Companies(1).xlsx', data_only=True)
ws_past = wb['past wave']

rows_to_check = []
for r in range(2, ws_past.max_row + 1):
    comp = ws_past.cell(r, 3).value
    title = ws_past.cell(r, 4).value
    url_cell = ws_past.cell(r, 12)
    url = url_cell.hyperlink.target if url_cell.hyperlink else url_cell.value
    status = ws_past.cell(r, 11).value
    wave = ws_past.cell(r, 2).value
    
    if url and str(url).startswith('http'):
        rows_to_check.append({
            'row': r,
            'wave': str(wave),
            'company': str(comp),
            'title': str(title),
            'url': str(url).strip(),
            'prev_status': str(status)
        })

print(f"Total links with URLs in past wave: {len(rows_to_check)}")

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)

results = {
    'total_checked': 0,
    'still_open': 0,
    'closed_or_expired': 0,
    'error_or_blocked': 0,
    'details': []
}

closed_indicators = [
    'page not found', 'no longer available', 'job closed',
    'no longer accepting applications', 'this job is no longer active',
    'this posting has expired', 'the job you are looking for is no longer open',
    '404 not found', 'job not found'
]

log_interval = 25

try:
    for idx, item in enumerate(rows_to_check, 1):
        u = item['url']
        results['total_checked'] += 1
        status = 'unknown'
        reason = ''
        
        try:
            driver.get(u)
            time.sleep(1.5)
            b_text = driver.find_element('tag name', 'body').text.lower()
            
            is_closed = any(ci in b_text for ci in closed_indicators)
            if is_closed or len(b_text) < 250:
                results['closed_or_expired'] += 1
                status = 'closed_or_expired'
                reason = 'Page text contains closed/expired indicator or empty shell'
            else:
                results['still_open'] += 1
                status = 'still_open'
                reason = 'Page active and application visible'
        except Exception as e:
            results['error_or_blocked'] += 1
            status = 'error_or_blocked'
            reason = str(e)[:100]

        results['details'].append({
            'row': item['row'],
            'wave': item['wave'],
            'company': item['company'],
            'title': item['title'],
            'url': item['url'],
            'status': status,
            'reason': reason
        })

        if idx % log_interval == 0 or idx == len(rows_to_check):
            print(f"Progress: [{idx}/{len(rows_to_check)}] Checked. Open: {results['still_open']}, Closed: {results['closed_or_expired']}, Error: {results['error_or_blocked']}")
            # Save periodic progress
            with open('data/past_waves_link_audit_report.json', 'w') as f:
                json.dump(results, f, indent=2)

finally:
    driver.quit()

print("\nLink audit complete!")
print(f"Total Evaluated: {results['total_checked']}")
print(f"Still Open: {results['still_open']}")
print(f"Closed / Expired: {results['closed_or_expired']}")
print(f"Error / Blocked: {results['error_or_blocked']}")

with open('data/past_waves_link_audit_report.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Saved report to data/past_waves_link_audit_report.json")
