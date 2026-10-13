import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import json

wb = openpyxl.load_workbook('data/Job Search.xlsx')

# Load existing deduplication set
with open('data/all_existing_urls.json') as f:
    existing_meta = json.load(f)
existing_urls = set(u.lower().rstrip('/') for u in existing_meta.get('urls', []))

# Also read all URLs currently in Job Search.xlsx sheets
for sname in wb.sheetnames:
    ws_temp = wb[sname]
    for r in range(1, ws_temp.max_row + 1):
        for c in range(1, ws_temp.max_column + 1):
            cell = ws_temp.cell(r, c)
            if cell.hyperlink and cell.hyperlink.target:
                existing_urls.add(cell.hyperlink.target.lower().rstrip('/'))
            elif cell.value and isinstance(cell.value, str) and cell.value.startswith('http'):
                existing_urls.add(cell.value.lower().rstrip('/'))

print(f"Total existing URLs to deduplicate against: {len(existing_urls)}")

# Load verified roles
with open('data/verified_fresh_roles_w5.json') as f:
    verified = json.load(f)

# Also add the verified HPE role from Subagent 2
hpe_role = {
    'company': 'Hewlett Packard Enterprise (HPE)',
    'title': 'Graduate Software Engineer',
    'location': 'Bengaluru (Designated Remote / Teleworker)',
    'url': 'https://careers.hpe.com/us/en/job/1210218/Graduate-Software-Engineer',
    'source': 'HPE Workday (Job ID: 1210218)',
    'match_score': 88,
    'jd_snippet': 'Official HPE Graduate Software Engineer requisition open for fresh college graduates (0 YOE). Designated full teleworker/remote in India. Python/Java, systems design, testing and debugging.'
}
verified.append(hpe_role)

# Filter for score >= 65 and non-duplicate
candidates = []
seen_this_run = set()

# Curate and add notes tailored to Vaanya
for r in verified:
    url = r['url'].lower().rstrip('/')
    comp = r['company']
    title = r['title']
    loc = r['location']
    score = r['match_score']
    
    # Exclude non-software or non-relevant
    if any(k in title.lower() for k in ['supply chain', 'industrial design', 'apprentice trainee', 'founder\'s office', 'filmmaking', 'ug intern role- batch of 2027']):
        continue
    
    # Exclude score < 64
    if score < 64:
        continue
        
    # Deduplicate
    clean_key = f"{comp.lower()}_{title.lower()}"
    if url in existing_urls or clean_key in seen_this_run:
        continue
        
    seen_this_run.add(clean_key)
    existing_urls.add(url)
    candidates.append(r)

candidates.sort(key=lambda x: x['match_score'], reverse=True)
print(f"Total curated, brand-new, verified 0 YOE roles for Wave 5: {len(candidates)}")

# Create Sheet
sheet_name = 'New Additions (Wave 5)'
if sheet_name in wb.sheetnames:
    del wb[sheet_name]

ws = wb.create_sheet(sheet_name)

headers = ['Company', 'Role Title', 'Location', 'Experience Fit & Notes', 'Status / Match Score', 'Application URL']
ws.append(headers)

header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
header_font = Font(color='FFFFFF', bold=True, size=11)
for col in range(1, len(headers) + 1):
    c = ws.cell(row=1, column=col)
    c.fill = header_fill
    c.font = header_font
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
light_green_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
bold_green = Font(color='006100', bold=True)

for row_idx, r in enumerate(candidates, start=2):
    comp = r['company']
    title = r['title']
    loc = r['location']
    score = r['match_score']
    url = r['url']
    
    # Generate notes based on role
    snip = r.get('jd_snippet', '')
    notes = f"0 YOE / Fresher verified. Stack fit with Vaanya's Python/Data/ML background. {snip[:140]}..."
    status_label = f"{score} / 100 ({'Strong Match' if score >= 80 else 'Potential Match'})"
    
    ws.append([comp, title, loc, notes, status_label, url])
    
    fill = green_fill if score >= 80 else light_green_fill
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.fill = fill
        cell.alignment = Alignment(wrap_text=True, vertical='top')
    
    ws.cell(row=row_idx, column=5).font = bold_green
    
    url_c = ws.cell(row=row_idx, column=6)
    url_c.hyperlink = url
    url_c.font = Font(color='0563C1', underline='single')

col_widths = [24, 38, 22, 55, 22, 30]
for i, w in enumerate(col_widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

ws.row_dimensions[1].height = 28
wb.save('data/Job Search.xlsx')
print(f"Sheet '{sheet_name}' successfully written with {len(candidates)} verified 0 YOE roles.")

# Save JSON representation
with open('data/verified_wave5_additions.json', 'w') as f:
    json.dump(candidates, f, indent=2)
