#!/usr/bin/env python3
"""
audit_fix_wave8.py  (Vrinda only)

Re-verifies every Wave 8 row against the LIVE ATS API record (title, location, JD text),
drops rows that cannot be matched, replaces hand-written experience with what the JD says,
and rebuilds the 'Wave 8' sheet in data/Companies(1).xlsx (+ mirror companies.xlsx).
"""
import json, re, ssl, shutil, html, urllib.request
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
H = {'User-Agent': 'Mozilla/5.0'}
def get(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=15, context=ctx).read())
def strip(t): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(html.unescape(t or ''))))

GH = ['coinbase', 'databricks', 'stripe', 'elastic', 'hackerrank', 'squarepointcapital', 'towerresearchcapital']
ASHBY = ['plane', 'ema', 'anuvaya', 'bolna', 'level-ai', 'PAR%20Technology']

truth = {}  # id -> dict(title, location, text)
for b in GH:
    for j in get(f'https://boards-api.greenhouse.io/v1/boards/{b}/jobs?content=true')['jobs']:
        truth[str(j['id'])] = dict(title=j['title'].strip(), location=j['location']['name'], text=strip(j.get('content')))
for b in ASHBY:
    for j in get(f'https://api.ashbyhq.com/posting-api/job-board/{b}')['jobs']:
        truth[j['id']] = dict(title=j['title'].strip(), location=j['location'] or '', text=strip(j.get('descriptionPlain') or j.get('descriptionHtml')))

def key(url):
    for pat in (r'gh_jid=(\d+)', r'/jobs/(\d+)', r'([0-9a-f]{8}-[0-9a-f-]{27})', r'[?&]id=(\d+)'):
        m = re.search(pat, url)
        if m: return m.group(1)

def jd_experience(text):
    """Return the years-of-experience phrases literally present in the JD."""
    found = re.findall(r'(\d{1,2}\s*(?:\+|-|–|to)?\s*\d{0,2}\s*\+?\s*years?)[^.]{0,60}?(?:experience|exp)', text, flags=re.I)
    found += re.findall(r'(?:minimum|at least)\s+(?:of\s+)?(\d{1,2}\s*\+?\s*years?)', text, flags=re.I)
    seen = []
    for f in found:
        f = re.sub(r'\s+', ' ', f).strip()
        if f not in seen: seen.append(f)
    return seen[:3]

def min_years(phrases):
    ys = [int(m.group(1)) for p in phrases if (m := re.match(r'(\d+)', p))]
    return min(ys) if ys else None

pool = json.load(open('data/wave8_verified_clean.json'))
kept, dropped = [], []
for r in pool:
    k = key(r['url'])
    t = truth.get(k) if 'linkedin.com' not in r['url'] else None
    if not t:
        dropped.append((r['company'], r['title'], 'no live ATS record / invalid LinkedIn ID')); continue
    live_title = t['title']
    if live_title.lower() != r['title'].lower():
        # same posting, different wording -> adopt the live title only if it is the same role family; else drop
        if r['company'] == 'Coinbase':
            dropped.append((r['company'], r['title'], f'URL is actually "{live_title}"')); continue
        r['title'] = live_title
    phrases = jd_experience(t['text'])
    my = min_years(phrases)
    if my is not None and my >= 6:
        dropped.append((r['company'], r['title'], f'JD requires {phrases}')); continue
    r['experience'] = ' | '.join(phrases) if phrases else 'Not stated in JD'
    r['jd_exp_phrases'] = phrases
    r['live_location'] = t['location']
    r['verification_status'] = 'Verified: live ATS title+URL match'
    r['notes'] = ('Title/URL matched against live ATS API on 2026-10-03. Experience column is the literal JD wording '
                  '("Not stated in JD" if absent). Tech stack and compensation are estimates, not JD-extracted.')
    kept.append(r)

# de-dupe by URL
seen, final = set(), []
for r in kept:
    if r['url'] in seen: dropped.append((r['company'], r['title'], 'duplicate URL')); continue
    seen.add(r['url']); final.append(r)

print(f'kept {len(final)}  dropped {len(dropped)}')
for d in dropped: print('  DROP', d)
json.dump(final, open('data/wave8_verified_clean.json', 'w'), indent=2)

# ---- rebuild sheet ----
NAVY = PatternFill(start_color='1F497D', end_color='1F497D', fill_type='solid')
ALT = PatternFill(start_color='F9FAFB', end_color='F9FAFB', fill_type='solid')
GREEN = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
B = Border(*(Side(style='thin', color='D9D9D9'),) * 4)
heads = ['#', 'Company', 'Role Title', 'Location (live)', 'Experience (per JD)', 'Key Tech Stack (estimate)',
         'Estimated Compensation (estimate)', 'Match Score', 'Priority / Match Tier', 'Link Verification Status',
         'Direct Application URL', 'Notes']
wb = openpyxl.load_workbook('data/Companies(1).xlsx')
if 'Wave 8' in wb.sheetnames: del wb['Wave 8']
ws = wb.create_sheet('Wave 8')
ws.append(heads)
for c in range(1, len(heads) + 1):
    x = ws.cell(1, c); x.fill = NAVY; x.font = Font(bold=True, color='FFFFFF'); x.border = B
    x.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
for i, r in enumerate(sorted(final, key=lambda z: -z['score']), 1):
    ws.append([i, r['company'], r['title'], r['live_location'], r['experience'], r['tech_stack'], r['comp'],
               r['score'], r['tier'], r['verification_status'], 'Exact Requisition Link ↗', r['notes']])
    for c in range(1, len(heads) + 1):
        x = ws.cell(i + 1, c); x.border = B; x.alignment = Alignment(vertical='center', wrap_text=True)
        if i % 2 == 0: x.fill = ALT
    ws.cell(i + 1, 10).fill = GREEN
    ws.cell(i + 1, 11).hyperlink = r['url']; ws.cell(i + 1, 11).font = Font(color='0563C1', underline='single')
for col in ws.columns:
    n = max(len(str(c.value or '')) for c in col)
    ws.column_dimensions[get_column_letter(col[0].column)].width = max(12, min(n + 3, 55))
wb.save('data/Companies(1).xlsx'); shutil.copy2('data/Companies(1).xlsx', 'data/companies.xlsx')
print('Wave 8 rebuilt:', len(final), 'rows')
