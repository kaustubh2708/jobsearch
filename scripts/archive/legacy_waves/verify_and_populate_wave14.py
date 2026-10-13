import openpyxl, urllib.request, ssl, time, json
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

print("=== STARTING FINAL VERIFICATION & EXCEL POPULATION FOR WAVE 14 ===")

with open('data/wave14_final_passed.json') as f:
    roles = json.load(f)

print(f"Total roles queued to audit & populate: {len(roles)}")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

audited_roles = []
for idx, r in enumerate(roles, 1):
    u = r['url']
    comp = r['company']
    title = r['title']
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=7) as resp:
            if resp.status == 200:
                print(f"  [{idx:02d} OK] {comp} | {title} | 200 OK")
                audited_roles.append(r)
            else:
                print(f"  [{idx:02d} FAIL] {comp} | Status: {resp.status}")
    except Exception as e:
        # If rate limited on LinkedIn, retry with delay
        if '429' in str(e):
            time.sleep(2.0)
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=7) as resp2:
                    if resp2.status == 200:
                        print(f"  [{idx:02d} OK (Retry)] {comp} | {title} | 200 OK")
                        audited_roles.append(r)
                    else:
                        print(f"  [{idx:02d} FAIL] {comp} | Status: {resp2.status}")
            except Exception as e2:
                print(f"  [{idx:02d} FAIL] {comp} | Error: {e2}")
        else:
            print(f"  [{idx:02d} FAIL] {comp} | Error: {e}")
    time.sleep(0.8)

print(f"\nTotal live verified roles (HTTP 200 OK): {len(audited_roles)}")

wb = openpyxl.load_workbook('data/Job Search.xlsx')
if 'Wave 14' in wb.sheetnames:
    del wb['Wave 14']

ws = wb.create_sheet(title='Wave 14')

headers_list = [
    '#',
    'Company',
    'Role Title',
    'Location',
    'Domain / Track',
    'Exact Stated Experience in JD (0–2 YOE)',
    'Key Tech Stack',
    'Estimated / Stated Compensation',
    'Match Score',
    'Priority / Match Tier',
    'Link Verification Status',
    'Direct Application URL',
    'Role Fit & Strategy Notes'
]

header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')

strong_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
strong_font = Font(name='Calibri', size=10, bold=True, color='375623')
potential_fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
potential_font = Font(name='Calibri', size=10, bold=True, color='806000')

verified_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
verified_font = Font(name='Calibri', size=10, bold=True, color='1F4E78')

border_thin = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

for col_num, h in enumerate(headers_list, 1):
    c = ws.cell(1, col_num, h)
    c.font = header_font
    c.fill = header_fill
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

for row_idx, r in enumerate(audited_roles, 2):
    ws.cell(row_idx, 1, row_idx - 1)
    ws.cell(row_idx, 2, r['company'])
    ws.cell(row_idx, 3, r['title'])
    ws.cell(row_idx, 4, r['location'])
    ws.cell(row_idx, 5, r['domain'])
    ws.cell(row_idx, 6, r['experience_stated'])
    ws.cell(row_idx, 7, r['tech_stack'])
    ws.cell(row_idx, 8, r['compensation'])
    ws.cell(row_idx, 9, r['match_score'])
    ws.cell(row_idx, 10, r['priority_tier'])
    ws.cell(row_idx, 11, 'Verified Live (HTTP 200)')

    u_cell = ws.cell(row_idx, 12, 'Direct Link')
    u_cell.hyperlink = r['url']
    u_cell.font = Font(name='Calibri', size=10, color='0563C1', underline='single')

    ws.cell(row_idx, 13, r['notes'])

    for col_num in range(1, 14):
        cell = ws.cell(row_idx, col_num)
        cell.border = border_thin
        if col_num not in [10, 11, 12]:
            cell.font = Font(name='Calibri', size=10)
        if col_num in [1, 9]:
            cell.alignment = Alignment(horizontal='center', vertical='center')
        elif col_num in [10, 11]:
            cell.alignment = Alignment(horizontal='center', vertical='center')
        else:
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

    tier_cell = ws.cell(row_idx, 10)
    if 'Strong' in r['priority_tier']:
        tier_cell.fill = strong_fill
        tier_cell.font = strong_font
    else:
        tier_cell.fill = potential_fill
        tier_cell.font = potential_font

    ver_cell = ws.cell(row_idx, 11)
    ver_cell.fill = verified_fill
    ver_cell.font = verified_font

col_widths = {
    1: 6,
    2: 24,
    3: 32,
    4: 26,
    5: 28,
    6: 45,
    7: 35,
    8: 26,
    9: 14,
    10: 20,
    11: 24,
    12: 16,
    13: 40
}
for col_num, width in col_widths.items():
    ws.column_dimensions[get_column_letter(col_num)].width = width

ws.row_dimensions[1].height = 28
for r in range(2, ws.max_row + 1):
    ws.row_dimensions[r].height = 36

# Update Tracker sheet
tracker_ws = wb['Tracker']
tracker_ws.cell(tracker_ws.max_row + 1, 1, 'Wave 14')
tracker_ws.cell(tracker_ws.max_row, 2, 'Completed')
tracker_ws.cell(tracker_ws.max_row, 3, len(audited_roles))
tracker_ws.cell(tracker_ws.max_row, 4, '100% Full-Time FTE Verified Roles (No Interns/Apprentices, Zero Pre-existing Company Overlap, Mix ATS & LinkedIn)')

wb.save('data/Job Search.xlsx')
print(f"Successfully populated Wave 14 in Job Search.xlsx with {len(audited_roles)} roles!")
print("Active sheets:", wb.sheetnames)

with open('data/wave14_final_approved.json', 'w') as f:
    json.dump(audited_roles, f, indent=2)
