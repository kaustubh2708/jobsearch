import openpyxl, urllib.request, ssl, time, json
from bs4 import BeautifulSoup

print("=== STARTING BACKGROUND AVAILABILITY AUDIT OF PREV WAVES ===")

wb = openpyxl.load_workbook('data/Job Search.xlsx')
prev_ws = wb['Prev Waves']

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

roles_to_check = []
for r in range(2, prev_ws.max_row + 1):
    wave = prev_ws.cell(r, 2).value
    comp = prev_ws.cell(r, 3).value
    title = prev_ws.cell(r, 4).value
    loc = prev_ws.cell(r, 5).value
    cell_u = prev_ws.cell(r, 10)
    u = cell_u.hyperlink.target if cell_u.hyperlink else cell_u.value
    if comp and u and u != 'N/A':
        roles_to_check.append({
            'row': r,
            'wave': wave,
            'company': comp,
            'title': title,
            'location': loc,
            'url': u
        })

print(f"Total historical roles in Prev Waves to audit: {len(roles_to_check)}")

active_roles = []
closed_roles = []
blocked_or_error_roles = []

# Audit each role with polite pacing
for idx, item in enumerate(roles_to_check, 1):
    u = item['url']
    comp = item['company']
    title = item['title']
    wave = item['wave']
    row_num = item['row']

    status = "unknown"
    reason = ""

    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=7) as resp:
            code = resp.status
            if code == 200:
                html_text = resp.read().decode('utf-8', errors='ignore')
                html_lower = html_text.lower()
                
                # Check closed / unlisted signals
                closed_markers = [
                    'no longer accepting applications',
                    'this job is no longer available',
                    'job expired',
                    'position has been filled',
                    'this job posting has closed',
                    'job posting is closed',
                    'this position is no longer accepting',
                    'the requisition you are trying to view has been unposted'
                ]
                
                is_closed = any(m in html_lower for m in closed_markers)
                if is_closed:
                    status = "closed"
                    reason = "Explicit closed/expired banner in page HTML"
                    closed_roles.append({**item, 'reason': reason})
                    print(f"[{idx:03d}/{len(roles_to_check)}] [CLOSED] {wave} | {comp} | {title}")
                else:
                    status = "active"
                    reason = "HTTP 200 OK & Application Form / Description Live"
                    active_roles.append(item)
                    if idx % 10 == 0 or idx == len(roles_to_check):
                        print(f"[{idx:03d}/{len(roles_to_check)}] [PROGRESS: {len(active_roles)} active, {len(closed_roles)} closed]")
            else:
                status = "error"
                reason = f"HTTP {code}"
                blocked_or_error_roles.append({**item, 'reason': reason})
                print(f"[{idx:03d}/{len(roles_to_check)}] [STATUS {code}] {wave} | {comp}")
    except urllib.error.HTTPError as e:
        if e.code in [404, 410]:
            status = "closed"
            reason = f"HTTP {e.code} (Requisition Dead / Taken Down)"
            closed_roles.append({**item, 'reason': reason})
            print(f"[{idx:03d}/{len(roles_to_check)}] [DEAD {e.code}] {wave} | {comp} | {title}")
        elif e.code in [403, 429]:
            status = "rate_limited"
            reason = f"HTTP {e.code} (WAF / Anti-bot Challenge)"
            blocked_or_error_roles.append({**item, 'reason': reason})
            print(f"[{idx:03d}/{len(roles_to_check)}] [RATE LIMITED {e.code}] {wave} | {comp}")
        else:
            status = "error"
            reason = f"HTTP {e.code}"
            blocked_or_error_roles.append({**item, 'reason': reason})
    except Exception as e:
        status = "error"
        reason = str(e)
        blocked_or_error_roles.append({**item, 'reason': reason})

    time.sleep(0.4)

results_summary = {
    'total_checked': len(roles_to_check),
    'active_count': len(active_roles),
    'closed_count': len(closed_roles),
    'rate_limited_or_error_count': len(blocked_or_error_roles),
    'active_roles': active_roles,
    'closed_roles': closed_roles,
    'blocked_or_error_roles': blocked_or_error_roles
}

with open('data/prev_waves_availability_audit.json', 'w') as f:
    json.dump(results_summary, f, indent=2)

print("\n=== BACKGROUND AVAILABILITY AUDIT COMPLETE ===")
print(f"Total checked: {len(roles_to_check)}")
print(f"Still Active & Open: {len(active_roles)}")
print(f"Closed / Stopped / Expired: {len(closed_roles)}")
print(f"Rate Limited / Blocked: {len(blocked_or_error_roles)}")
