import openpyxl, time, json, re, ssl, urllib.request, urllib.parse, subprocess
from urllib.parse import urlparse

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

# Load the candidate flagged rows from raw audit
with open('data/job_search2_audit_raw.json') as f:
    raw_data = json.load(f)

# Re-audit each candidate closed link with precision curl / request
def check_single_url_precision(url, notes, status):
    if not url:
        if 'closed' in notes.lower() or 'closed' in status.lower():
            return True, 'Notes/Status indicates Closed'
        return False, 'No URL'

    u = url.strip()
    
    # 1. Ashby
    m_ash = re.search(r'ashbyhq\.com/([^/]+)/([a-f0-9\-]{36})', u)
    if m_ash:
        org, jid = m_ash.group(1), m_ash.group(2)
        try:
            req = urllib.request.Request(f"https://api.ashbyhq.com/posting-api/job-board/{org}", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                d = json.loads(resp.read().decode('utf-8'))
                live_ids = [str(j.get('id')).lower() for j in d.get('jobs', [])]
                if jid.lower() in live_ids:
                    return False, 'Ashby: Active'
                else:
                    return True, 'Ashby: Job not in active board'
        except Exception:
            pass

    # 2. Greenhouse
    m_gh = re.search(r'greenhouse\.io/([^/]+)/jobs/(\d+)', u)
    if m_gh:
        org, jid = m_gh.group(1), m_gh.group(2)
        try:
            req = urllib.request.Request(f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs/{jid}", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                if resp.status == 200:
                    return False, 'Greenhouse: Active'
        except urllib.error.HTTPError as e:
            if e.code in [404, 410]:
                return True, f'Greenhouse: HTTP {e.code}'
        except Exception:
            pass

    # 3. Use curl to avoid 429 and get accurate page content
    cmd = [
        'curl', '-s', '-L',
        '--max-time', '8',
        '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        '-H', 'Accept-Language: en-US,en;q=0.9',
        u
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
        html = res.stdout.lower()
        if not html:
            return True, 'Empty response / connection failed'
        
        # Check specific closed signals
        closed_signals = [
            'no longer accepting applications',
            'this job is no longer available',
            'this job is no longer active',
            'this job is closed',
            'position is closed',
            'job has expired',
            'posting has expired',
            'job not found',
            'requisition is closed',
            'this position has been filled',
            'closed-job__flavor'
        ]
        for sig in closed_signals:
            if sig in html:
                return True, f'Found signal: {sig}'

        if '404 not found' in html or '<title>404' in html or '<title>page not found' in html:
            return True, '404 Page Not Found'

        # Ashby redirect check
        if 'ashbyhq.com' in u and '<title>jobs</title>' in html and 'jobposting' not in html:
            return True, 'Ashby redirected to board'

        return False, 'Active'
    except Exception as e:
        return False, f'Error: {e}'

print("Starting Precision Verification of all 404 links...")
verified_audit = {}

for rec in records:
    r = rec['row']
    # Check if already marked closed by user
    user_marked_closed = (rec['status'].strip().lower() == 'closed' or rec['notes'].strip().lower() == 'closed')
    
    is_closed, reason = check_single_url_precision(rec['url'], rec['notes'], rec['status'])
    if user_marked_closed and not is_closed:
        # Respect user's explicit manual marking
        is_closed = True
        reason = 'User previously marked Closed'
        
    verified_audit[r] = {
        'is_closed': is_closed,
        'reason': reason
    }
    time.sleep(0.08) # polite throttle
    if (r - 1) % 50 == 0:
        print(f"  Processed {r - 1} / 404...")

print(f"Precision verification complete!")
closed_count = sum(1 for v in verified_audit.values() if v['is_closed'])
print(f"Confirmed closed links: {closed_count}")

with open('data/job_search2_verified_audit.json', 'w') as f:
    json.dump(verified_audit, f, indent=2)
