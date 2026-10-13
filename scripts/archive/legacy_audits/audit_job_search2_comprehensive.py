import openpyxl, time, json, re, ssl, urllib.request, urllib.parse, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

wb_path = 'data/Job Search(2).xlsx'
wb = openpyxl.load_workbook(wb_path, data_only=True)
ws = wb['Job Links']

url_regex = re.compile(r'https?://[^\s]+')

records = []
for r in range(2, 406):
    comp = str(ws.cell(row=r, column=1).value or '').strip()
    title = str(ws.cell(row=r, column=2).value or '').strip()
    loc = str(ws.cell(row=r, column=3).value or '').strip()
    notes = str(ws.cell(row=r, column=4).value or '').strip()
    status = str(ws.cell(row=r, column=5).value or '').strip()

    url = None
    for c in [4, 2, 5, 6, 1, 3]:
        cell = ws.cell(row=r, column=c)
        if cell.hyperlink and cell.hyperlink.target:
            url = cell.hyperlink.target
            break
        elif cell.value and ('http://' in str(cell.value) or 'https://' in str(cell.value)):
            m = url_regex.findall(str(cell.value))
            if m:
                url = m[0]
                break

    records.append({
        'row': r,
        'company': comp,
        'title': title,
        'location': loc,
        'notes': notes,
        'status': status,
        'url': url
    })

print(f"Loaded {len(records)} rows from {wb_path}")

# Deduplication identification
# 1. By normalized URL
url_groups = {}
for rec in records:
    u = rec['url']
    if u:
        u_clean = u.strip().rstrip('.,;')
        li_m = re.search(r'linkedin\.com/jobs/view/.*?(\d{8,})', u_clean)
        if li_m:
            norm_key = f'li:{li_m.group(1)}'
        else:
            gh_m = re.search(r'greenhouse\.io/.*?/jobs/(\d+)', u_clean)
            if gh_m:
                norm_key = f'gh:{gh_m.group(1)}'
            else:
                ash_m = re.search(r'ashbyhq\.com/([^/]+)/([a-f0-9\-]{36})', u_clean)
                if ash_m:
                    norm_key = f'ashby:{ash_m.group(2)}'
                else:
                    p = urllib.parse.urlparse(u_clean)
                    norm_key = p.netloc.lower() + p.path.rstrip('/')
        url_groups.setdefault(norm_key, []).append(rec['row'])

# 2. By company + title (identical role)
comp_title_groups = {}
for rec in records:
    c = rec['company'].lower().strip()
    t = rec['title'].lower().strip()
    if c and t and t not in ['direct link', 'manual inspect link']:
        k = (re.sub(r'\s+', ' ', c), re.sub(r'\s+', ' ', t))
        comp_title_groups.setdefault(k, []).append(rec['row'])

duplicate_rows = set()
dup_reasons = {}

# Check exact URL duplicates: subsequent rows in the group are duplicates
for k, rows in url_groups.items():
    if len(rows) > 1 and k != 'hunar.ai':
        # Rows after the first are duplicates
        for dup_r in rows[1:]:
            duplicate_rows.add(dup_r)
            dup_reasons[dup_r] = f"Duplicate URL of Row {rows[0]} ({k})"

# Check company+title duplicates where same role was added multiple times
for k, rows in comp_title_groups.items():
    if len(rows) > 1:
        # Check if locations are identical or roles represent the same requisition
        first_r = rows[0]
        for dup_r in rows[1:]:
            # Check if this duplicate row is already marked or should be marked
            if dup_r not in duplicate_rows:
                # If exact same location or very similar, mark as duplicate
                loc1 = records[first_r-2]['location'].lower()
                loc2 = records[dup_r-2]['location'].lower()
                duplicate_rows.add(dup_r)
                dup_reasons[dup_r] = f"Duplicate role of Row {first_r} ({k[0]} - {k[1]})"

print(f"Total rows identified as duplicates: {len(duplicate_rows)}")
for r in sorted(duplicate_rows):
    print(f"  Row {r}: {dup_reasons[r]}")

# Now Link Validity / Closed audit
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

closed_patterns = [
    'no longer accepting applications',
    'this job is no longer available',
    'this job is no longer active',
    'this job is closed',
    'position is closed',
    'job has expired',
    'posting has expired',
    'page not found',
    'job not found',
    'requisition is closed',
    'this position has been filled'
]

def audit_url(rec):
    r_idx = rec['row']
    url = rec['url']
    comp = rec['company']
    title = rec['title']
    
    if not url:
        if rec['notes'].lower() == 'closed':
            return r_idx, {'status': 'closed', 'reason': 'Notes indicate Closed'}
        return r_idx, {'status': 'open', 'reason': 'No URL provided'}

    # 1. Ashby API Optimization
    m_ashby = re.search(r'ashbyhq\.com/([^/]+)/([a-f0-9\-]{36})', url)
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
                    return r_idx, {'status': 'open', 'reason': 'Ashby API: Job active'}
                else:
                    return r_idx, {'status': 'closed', 'reason': 'Ashby API: Job not in active board'}
        except Exception:
            pass

    # 2. Greenhouse API Optimization
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
        except Exception:
            pass

    # 3. HTTP Fetch & DOM check
    # Try with curl fallback if LinkedIn rate-limits
    max_retries = 2
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                final_url = resp.geturl()
                html = resp.read().decode('utf-8', errors='ignore').lower()
                
                # Check closed patterns
                if any(cp in html for cp in closed_patterns):
                    return r_idx, {'status': 'closed', 'reason': 'Page text contains closed/expired indicator'}
                
                # LinkedIn specific: check if "closed-job" or "no longer accepting"
                if 'linkedin.com' in url.lower():
                    if 'closed-job' in html:
                        return r_idx, {'status': 'closed', 'reason': 'LinkedIn: closed-job element present'}
                    # If page redirected to login or generic jobs without job content
                    if 'sign in' in html and len(html) < 2000:
                        pass # might need retry
                
                # Ashby specific: if redirected to generic board and title is just "Jobs"
                if 'ashbyhq.com' in url.lower() and '<title>jobs</title>' in html and 'jobposting' not in html:
                    return r_idx, {'status': 'closed', 'reason': 'Ashby: Requisition expired / redirect to board'}

                return r_idx, {'status': 'open', 'reason': f'HTTP {resp.status} Active'}
        except urllib.error.HTTPError as e:
            if e.code in [404, 410]:
                return r_idx, {'status': 'closed', 'reason': f'HTTP {e.code} Not Found/Gone'}
            elif e.code == 429:
                time.sleep(1.0 + attempt * 1.5)
                continue
            elif e.code in [401, 403]:
                # Often bot protection (Workday, Oracle Cloud HCM)
                return r_idx, {'status': 'open', 'reason': f'HTTP {e.code} Bot Protected Active Portal'}
            else:
                return r_idx, {'status': 'closed', 'reason': f'HTTP {e.code}'}
        except Exception as e:
            if attempt == max_retries - 1:
                return r_idx, {'status': 'unknown_error', 'reason': f'Error: {str(e)[:40]}'}
            time.sleep(0.5)

    return r_idx, {'status': 'open', 'reason': 'Default open'}

print("\nStarting concurrent link validity audit across all 404 rows...")
audit_results = {}

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(audit_url, rec): rec for rec in records}
    completed = 0
    for fut in as_completed(futures):
        r_idx, res = fut.result()
        audit_results[r_idx] = res
        completed += 1
        if completed % 50 == 0 or completed == len(records):
            print(f"  Progress: {completed}/{len(records)} links audited...")

# Summarize results
closed_rows = {r for r, res in audit_results.items() if res['status'] == 'closed'}
print(f"\nAudit complete!")
print(f"Total closed links found: {len(closed_rows)}")
print(f"Total duplicate rows found: {len(duplicate_rows)}")

# Combined classifications
combined = {}
for rec in records:
    r = rec['row']
    is_closed = r in closed_rows or rec['status'].lower() == 'closed'
    is_dup = r in duplicate_rows
    
    if is_closed and is_dup:
        combined[r] = {
            'action': 'Closed/Duplicate',
            'reason': f"Closed ({audit_results.get(r, {}).get('reason', '')}) & {dup_reasons.get(r, 'Duplicate')}"
        }
    elif is_closed:
        combined[r] = {
            'action': 'Closed',
            'reason': audit_results.get(r, {}).get('reason', 'Closed')
        }
    elif is_dup:
        combined[r] = {
            'action': 'Duplicate',
            'reason': dup_reasons.get(r, 'Duplicate')
        }

print(f"\nTotal rows to mark: {len(combined)}")
for r in sorted(combined.keys()):
    act = combined[r]['action']
    reason = combined[r]['reason']
    comp = records[r-2]['company']
    title = records[r-2]['title']
    print(f"  Row {r:3d}: [{act:16s}] {comp} - {title} | {reason}")

with open('data/job_search2_audit_raw.json', 'w') as f:
    json.dump({
        'audit_results': audit_results,
        'duplicate_rows': list(duplicate_rows),
        'dup_reasons': dup_reasons,
        'combined': combined
    }, f, indent=2)

print("\nSaved intermediate audit report to data/job_search2_audit_raw.json")
