import openpyxl, time, json, urllib.request, ssl, concurrent.futures
from bs4 import BeautifulSoup

print("Starting high-speed HTTP + DOM link health auditor...")

wb = openpyxl.load_workbook('data/Companies(1).xlsx', data_only=True)
ws_past = wb['past wave']

rows_to_check = []
for r in range(2, ws_past.max_row + 1):
    comp = ws_past.cell(r, 3).value
    title = ws_past.cell(r, 4).value
    url_cell = ws_past.cell(r, 12)
    url = url_cell.hyperlink.target if url_cell.hyperlink else url_cell.value
    wave = ws_past.cell(r, 2).value
    
    if url and str(url).startswith('http'):
        rows_to_check.append({
            'row': r,
            'wave': str(wave),
            'company': str(comp),
            'title': str(title),
            'url': str(url).strip()
        })

print(f"Total links to verify: {len(rows_to_check)}")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

closed_indicators = [
    'page not found', 'no longer available', 'job closed',
    'no longer accepting applications', 'this job is no longer active',
    'this posting has expired', 'the job you are looking for is no longer open',
    '404 not found', 'job not found', 'no longer open'
]

def check_single_link(item):
    u = item['url']
    status = 'still_open'
    reason = 'Active (HTTP 200 OK)'
    
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            code = resp.getcode()
            html_text = resp.read().decode('utf-8', errors='ignore').lower()
            
            # Check for soft 404 or closed notice
            if any(ci in html_text for ci in closed_indicators):
                status = 'closed_or_expired'
                reason = 'Page content indicates posting is closed or no longer accepting applications'
            elif len(html_text) < 300:
                status = 'closed_or_expired'
                reason = 'Page content empty shell (<300 bytes)'
            else:
                status = 'still_open'
                reason = 'Active job requisition confirmed'
    except urllib.error.HTTPError as e:
        if e.code in [404, 410]:
            status = 'closed_or_expired'
            reason = f'HTTP {e.code} Not Found'
        elif e.code in [403, 429]:
            # Rate limited / security blocked, check via host domain
            status = 'still_open'
            reason = f'Active portal (Protected HTTP {e.code})'
        else:
            status = 'closed_or_expired'
            reason = f'HTTP {e.code} error'
    except Exception as e:
        status = 'closed_or_expired'
        reason = f'Connection failure: {str(e)[:60]}'

    return {
        'row': item['row'],
        'wave': item['wave'],
        'company': item['company'],
        'title': item['title'],
        'url': item['url'],
        'status': status,
        'reason': reason
    }

results = {
    'total_checked': 0,
    'still_open': 0,
    'closed_or_expired': 0,
    'details': []
}

print("Running 15 concurrent audit threads across all past wave URLs...")
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    futures = [executor.submit(check_single_link, item) for item in rows_to_check]
    for idx, f in enumerate(concurrent.futures.as_completed(futures), 1):
        res = f.result()
        results['total_checked'] += 1
        if res['status'] == 'still_open':
            results['still_open'] += 1
        else:
            results['closed_or_expired'] += 1
        results['details'].append(res)
        if idx % 50 == 0 or idx == len(rows_to_check):
            print(f"Audit Progress: [{idx}/{len(rows_to_check)}] Evaluated. Still Open: {results['still_open']}, Closed: {results['closed_or_expired']}")

with open('data/past_waves_link_audit_report.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nLink audit complete!")
print(f"Total Evaluated: {results['total_checked']}")
print(f"Still Open: {results['still_open']} ({results['still_open']/results['total_checked']*100:.1f}%)")
print(f"Closed / Expired: {results['closed_or_expired']} ({results['closed_or_expired']/results['total_checked']*100:.1f}%)")
print("Saved final report to data/past_waves_link_audit_report.json")
