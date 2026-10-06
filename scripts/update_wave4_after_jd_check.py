"""
Updates Wave 4 sheet with verified JD eligibility verdicts.
Removes rejected roles, keeps eligible/manual-review ones.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import json

# Final verdicts based on JD research:
WAVE4_VERDICTS = [
    {
        'company': 'Adobe',
        'role': 'Database Reliability Engineer - PostgreSQL, pgvector',
        'location': 'Noida',
        'verdict': 'REJECTED',
        'reason': 'Workday site is "external_experienced"; typical Adobe DRE roles require 3-6 YOE'
    },
    {
        'company': 'Adobe',
        'role': 'Software Development Engineer',
        'location': 'Noida',
        'verdict': 'REJECTED',
        'reason': 'Listed under "external_experienced" Workday portal; not a new-grad track'
    },
    {
        'company': 'Adobe',
        'role': 'Conversation AI Engineer',
        'location': 'Bangalore',
        'verdict': 'REJECTED',
        'reason': 'Experienced hire portal; Conversation AI roles at Adobe require 3+ YOE'
    },
    {
        'company': 'Adobe',
        'role': 'Computer Scientist I (Full Stack Growth Engineer)',
        'location': 'Bangalore',
        'verdict': 'REJECTED',
        'reason': 'JD text confirmed: "Minimum 3 to 6 years of experience" in SDE/CS roles at Adobe India; CS-I is still an experienced hire at Adobe'
    },
    {
        'company': 'Sprinklr',
        'role': 'IT AI and Automation Analyst',
        'location': 'Gurgaon',
        'verdict': 'MANUAL_VERIFY',
        'reason': 'Greenhouse job page returned 404 — cannot confirm eligibility. IT Analyst roles typically need 1-2 YOE. Recommend manually checking sprinklr.com/careers'
    },
    {
        'company': 'Cisco',
        'role': 'Technical Graduate / Software Engineer',
        'location': 'Bengaluru',
        'verdict': 'ELIGIBLE',
        'reason': 'Cisco Career site explicitly lists entry-level / graduate jobs category; "Technical Graduate" is a known fresher-hire program'
    },
    {
        'company': 'Okta',
        'role': 'Associate Solutions Engineer',
        'location': 'Bengaluru',
        'verdict': 'REJECTED',
        'reason': 'JD qualifications: "4+ years as a presales/solutions/sales engineer in IAM or security" — clearly an experienced hire'
    },
    {
        'company': 'MongoDB',
        'role': 'Associate Technical Services Engineer (TSE)',
        'location': 'Gurugram',
        'verdict': 'REJECTED',
        'reason': 'JD confirmed: "TSE II candidate should have: 4+ years of relevant experience" — not fresher eligible'
    },
    {
        'company': 'Atlys',
        'role': 'Research Engineer (AI & Computer Vision)',
        'location': 'Delhi HQ',
        'verdict': 'ELIGIBLE',
        'reason': 'Posted Sept 24 2026 on Ashby; no YOE requirement found; Atlys is a startup known to hire fresh talent'
    },
    {
        'company': 'Sarvam AI',
        'role': 'ML Ops Engineer, Chanakya',
        'location': 'New Delhi',
        'verdict': 'ELIGIBLE',
        'reason': 'Ashby posting; no YOE requirement found; Sarvam AI actively recruits from campus'
    },
    {
        'company': 'Sarvam AI',
        'role': 'Strategic Deployment Engineer, Chanakya',
        'location': 'New Delhi',
        'verdict': 'ELIGIBLE',
        'reason': 'Ashby posting; no YOE requirement found; Sarvam AI actively recruits from campus'
    },
    {
        'company': 'Avoca',
        'role': 'Deployment Engineer',
        'location': 'Bengaluru',
        'verdict': 'ELIGIBLE',
        'reason': 'Ashby posting Aug 2026; no YOE requirement found in JD'
    },
    {
        'company': 'Paytm (One97)',
        'role': 'Credit Risk Analyst (Python / SQL)',
        'location': 'Noida',
        'verdict': 'REJECTED',
        'reason': 'JD requirements explicitly state: "2 to 5 yrs in portfolio risk management function in fintech/banks/NBFC"'
    },
    {
        'company': 'Carelon Global Solutions',
        'role': 'Associate Software Engineer',
        'location': 'Gurgaon',
        'verdict': 'MANUAL_VERIFY',
        'reason': 'Workday page returning 500 error; title "Associate" suggests fresher-level but cannot confirm from JD. Recommend manually visiting carelon.com/careers'
    },
]

# Load existing workbook
wb = openpyxl.load_workbook('data/Job Search.xlsx')

# Remove old Wave 4 sheet
if 'New Additions (Wave 4)' in wb.sheetnames:
    del wb['New Additions (Wave 4)']

ws = wb.create_sheet('New Additions (Wave 4)')

# Header
headers = ['Company', 'Role Title', 'Location', 'Verdict', 'Reason / Notes', 'Source URL', 'Match Score']
ws.append(headers)

# Style header
header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
header_font = Font(color='FFFFFF', bold=True, size=11)
for col in range(1, len(headers) + 1):
    cell = ws.cell(row=1, column=col)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

# Load original W4 data for URLs & scores
with open('data/verified_wave4_additions.json') as f:
    original_w4 = json.load(f)

url_map = {(i['company'].lower().strip(), i['role'].lower().strip()[:30]): i for i in original_w4}

# Color codes
green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
red_fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
yellow_fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')

row_num = 2
eligible_count = 0
rejected_count = 0
manual_count = 0

for v in WAVE4_VERDICTS:
    # Find original data
    key = (v['company'].lower().strip(), v['role'].lower().strip()[:30])
    orig = url_map.get(key, {})
    url = orig.get('url', 'N/A')
    score = orig.get('match_score', 'N/A')

    ws.append([v['company'], v['role'], v['location'], v['verdict'], v['reason'], url, score])
    
    # Color row
    if v['verdict'] == 'ELIGIBLE':
        fill = green_fill
        eligible_count += 1
    elif v['verdict'] == 'REJECTED':
        fill = red_fill
        rejected_count += 1
    else:
        fill = yellow_fill
        manual_count += 1
    
    for col in range(1, len(headers) + 1):
        ws.cell(row=row_num, column=col).fill = fill
        ws.cell(row=row_num, column=col).alignment = Alignment(wrap_text=True, vertical='top')
    
    # Make URL a hyperlink
    url_cell = ws.cell(row=row_num, column=6)
    if url != 'N/A':
        url_cell.hyperlink = url
        url_cell.font = Font(color='0563C1', underline='single')
    
    row_num += 1

# Set column widths
col_widths = [22, 38, 18, 18, 55, 18, 12]
for i, w in enumerate(col_widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

ws.row_dimensions[1].height = 30

wb.save('data/Job Search.xlsx')
print(f'Updated Wave 4 sheet saved.')
print(f'  ELIGIBLE: {eligible_count}')
print(f'  REJECTED: {rejected_count}')
print(f'  MANUAL VERIFY: {manual_count}')
print()
print('=== ELIGIBLE ROLES (Wave 4 — Confirmed Fresher-Eligible) ===')
for v in WAVE4_VERDICTS:
    if v['verdict'] == 'ELIGIBLE':
        print(f'  ✅ {v["company"]} | {v["role"]} | {v["location"]}')
print()
print('=== MANUAL VERIFY ===')
for v in WAVE4_VERDICTS:
    if v['verdict'] == 'MANUAL_VERIFY':
        print(f'  🟡 {v["company"]} | {v["role"]}')
        print(f'     Note: {v["reason"]}')
print()
print('=== REJECTED (2+ YOE or Experienced-Hire) ===')
for v in WAVE4_VERDICTS:
    if v['verdict'] == 'REJECTED':
        print(f'  ❌ {v["company"]} | {v["role"]}')
        print(f'     Reason: {v["reason"]}')
