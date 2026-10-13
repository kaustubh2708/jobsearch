import openpyxl, urllib.request, ssl, re, time
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

wb = openpyxl.load_workbook('data/Job Search.xlsx')
ws = wb['Wave 14']

print(f"Auditing all {ws.max_row - 1} roles in Wave 14...")

audit_results = []

for r in range(2, ws.max_row + 1):
    num = ws.cell(r, 1).value
    comp = ws.cell(r, 2).value
    title = ws.cell(r, 3).value
    loc = ws.cell(r, 4).value
    stated_exp = ws.cell(r, 6).value
    cell_u = ws.cell(r, 12)
    url = cell_u.hyperlink.target if cell_u.hyperlink else cell_u.value

    full_text = ""
    http_code = 0
    is_live = False
    is_closed = False
    error_msg = ""

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            http_code = resp.status
            html = resp.read().decode('utf-8', errors='ignore')
            hl = html.lower()
            if "no longer accepting applications" in hl or "this job is closed" in hl or "this job is no longer available" in hl:
                is_closed = True
            elif http_code == 200:
                is_live = True

            soup = BeautifulSoup(html, 'html.parser')
            desc = soup.find('div', class_='show-more-less-html__markup') or soup.find('section', class_='description') or soup.find('div', class_='content')
            full_text = desc.get_text(' ', strip=True) if desc else soup.get_text(' ', strip=True)
    except urllib.error.HTTPError as he:
        http_code = he.code
        error_msg = f"HTTP {he.code}"
    except Exception as e:
        error_msg = str(e)[:30]

    # Evaluate Experience in full_text
    text_lower = full_text.lower()
    exp_issues = []

    # Check for senior/intern in text
    if any(w in text_lower for w in ['apprenticeship intern', 'unpaid internship', 'trainee program', 'summer intern 202', 'winter intern 202']):
        exp_issues.append("Intern/Trainee detected in JD")

    # Check for 2+ YOE
    for pat in [
        r'\b([2-9]|\d{2})\+?\s*(?:to\s*\d+\s*)?years?\s*(?:of)?\s*(?:relevant|hands-on|work|software|professional|industry|engineering)?\s*experience',
        r'minimum\s+(?:of\s+)?([2-9]|\d{2})\s*\+?\s*years?',
        r'at\s+least\s+([2-9]|\d{2})\s*\+?\s*years?',
        r'\b([2-9]|\d{2})\s*[\u2013\u2014-]\s*\d+\s*years?',
        r'requires\s+([2-9]|\d{2})\s*\+?\s*years?'
    ]:
        m = re.search(pat, text_lower)
        if m:
            matched_str = m.group(0)
            if not any(ign in matched_str for ign in ['company', 'legacy', 'firm', 'history', 'business', '1-2', '1 to 2', '0-2', '0–2']):
                s_start = max(0, m.start() - 40)
                s_end = min(len(text_lower), m.end() + 40)
                ctx_window = text_lower[s_start:s_end]
                if any(kw in ctx_window for kw in ['requirement', 'qualification', 'candidate', 'experience', 'must have', 'years of experience']):
                    exp_issues.append(f"High exp found: '{matched_str}' in '{ctx_window.strip()}'")
                    break

    res = {
        'row': r,
        'num': num,
        'company': comp,
        'title': title,
        'url': url,
        'http_code': http_code,
        'is_live': is_live,
        'is_closed': is_closed,
        'error_msg': error_msg,
        'exp_issues': exp_issues,
        'stated_exp': stated_exp
    }
    audit_results.append(res)
    
    status_summary = "OK" if (is_live and not is_closed and not exp_issues) else f"FLAGGED (Live={is_live}, Closed={is_closed}, Issues={exp_issues})"
    print(f"[{num}/58] Row {r}: {comp} | {title} -> {status_summary}")
    time.sleep(0.5)

import json
with open('data/audit_wave14_all58_results.json', 'w') as f:
    json.dump(audit_results, f, indent=2)

flags = [r for r in audit_results if not r['is_live'] or r['is_closed'] or r['exp_issues']]
print(f"\nAudit Complete! Clean: {len(audit_results) - len(flags)} / {len(audit_results)}. Flagged: {len(flags)}")
for fl in flags:
    print(f"FLAGGED: Row {fl['row']} (# {fl['num']}) | {fl['company']} | {fl['title']} | Live={fl['is_live']} Closed={fl['is_closed']} Issues={fl['exp_issues']} Error={fl['error_msg']}")

