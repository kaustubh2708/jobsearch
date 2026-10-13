import openpyxl, time, json, urllib.request, ssl, concurrent.futures
from collections import Counter

print("Starting high-speed HTTP inspection of all LinkedIn links in past waves...")

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

print(f"Total LinkedIn roles in past waves: {len(linkedin_roles)}")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

closed_patterns = [
    'no longer accepting applications',
    'this job is no longer available',
    'this job is no longer active',
    'job closed',
    'page not found'
]

def check_linkedin_url(item):
    u = item['url']
    status = 'still_open'
    reason = 'Active (Accepting applications)'
    
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
            code = resp.getcode()
            html = resp.read().decode('utf-8', errors='ignore').lower()
            
            if any(cp in html for cp in closed_patterns):
                status = 'closed_or_expired'
                reason = 'HTML contains "No longer accepting applications" / closed'
            elif len(html) < 500:
                status = 'closed_or_expired'
                reason = 'Empty HTML shell'
            else:
                status = 'still_open'
                reason = 'Active posting on LinkedIn'
    except urllib.error.HTTPError as e:
        status = 'closed_or_expired'
        reason = f'HTTP {e.code}'
    except Exception as e:
        status = 'closed_or_expired'
        reason = f'Connection timeout/error: {str(e)[:40]}'

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
    'total_audited': len(linkedin_roles),
    'still_open': 0,
    'closed_or_expired': 0,
    'breakdown_by_wave': {},
    'details': []
}

print("Dispatching 20 concurrent worker threads to audit all 218 LinkedIn links...")
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(check_linkedin_url, item) for item in linkedin_roles]
    for idx, f in enumerate(concurrent.futures.as_completed(futures), 1):
        res = f.result()
        w = res['wave']
        if w not in results['breakdown_by_wave']:
            results['breakdown_by_wave'][w] = {'open': 0, 'closed': 0}

        if res['status'] == 'still_open':
            results['still_open'] += 1
            results['breakdown_by_wave'][w]['open'] += 1
        else:
            results['closed_or_expired'] += 1
            results['breakdown_by_wave'][w]['closed'] += 1
            
        results['details'].append(res)
        if idx % 50 == 0 or idx == len(linkedin_roles):
            print(f"Audit Progress: [{idx}/{len(linkedin_roles)}] Audited. Open: {results['still_open']}, Closed: {results['closed_or_expired']}")

with open('data/linkedin_past_waves_audit_report.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n=== LinkedIn Past Waves Audit Complete ===")
print(f"Total LinkedIn URLs Audited: {results['total_audited']}")
print(f"Still Open: {results['still_open']} ({results['still_open']/results['total_audited']*100:.1f}%)")
print(f"Closed / Expired: {results['closed_or_expired']} ({results['closed_or_expired']/results['total_audited']*100:.1f}%)")
print("\nBreakdown by Wave:")
for w in sorted(results['breakdown_by_wave'].keys()):
    c = results['breakdown_by_wave'][w]
    tot = c['open'] + c['closed']
    pct = (c['open']/tot*100) if tot > 0 else 0
    print(f"  {w:8s}: Total {tot:2d} | Open: {c['open']:2d} ({pct:5.1f}%) | Closed: {c['closed']:2d}")

print("\nSaved report to data/linkedin_past_waves_audit_report.json")
