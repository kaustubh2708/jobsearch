import openpyxl
import re

wb = openpyxl.load_workbook('data/Job Search.xlsx')

def normalize_text(text):
    if not text:
        return ""
    t = str(text).lower()
    t = re.sub(r'[^a-z0-9]', ' ', t)
    return ' '.join(t.split())

# 1. Collect all roles from earlier sheets
existing_roles = [] # list of (sheet_name, company, title, norm_comp, norm_title, url)

check_sheets = ['Tracker', 'Job Links', 'Eligible role', 'Fresher Hiring Drives', 'New Additions (Wave 3)']

for sname in check_sheets:
    if sname not in wb.sheetnames:
        continue
    ws = wb[sname]
    for r in range(2, ws.max_row + 1):
        comp = ws.cell(r, 1).value
        title = ws.cell(r, 2).value
        
        # URL could be in col 5 or 6 or 4
        url = None
        for col_idx in [5, 6, 4, 3]:
            c = ws.cell(r, col_idx)
            if c.hyperlink and c.hyperlink.target:
                url = c.hyperlink.target
                break
            elif c.value and isinstance(c.value, str) and c.value.startswith('http'):
                url = c.value
                break
                
        if comp and title:
            existing_roles.append({
                'sheet': sname,
                'row': r,
                'company': str(comp).strip(),
                'title': str(title).strip(),
                'norm_comp': normalize_text(comp),
                'norm_title': normalize_text(title),
                'url': url.lower().rstrip('/') if url else ''
            })

print(f"Total roles indexed from previous sheets: {len(existing_roles)}")

# 2. Check Wave 5 against existing roles
ws5 = wb['New Additions (Wave 5)']
print(f"\nChecking Wave 5 ({ws5.max_row - 1} rows) for DUPLICATES...")

duplicates_found = []
clean_wave5 = []

for r in range(2, ws5.max_row + 1):
    comp = str(ws5.cell(r, 1).value or '').strip()
    title = str(ws5.cell(r, 2).value or '').strip()
    loc = str(ws5.cell(r, 3).value or '').strip()
    notes = str(ws5.cell(r, 4).value or '').strip()
    status = str(ws5.cell(r, 5).value or '').strip()
    c6 = ws5.cell(r, 6)
    url = c6.hyperlink.target if c6.hyperlink else (c6.value if isinstance(c6.value, str) else '')
    clean_url = url.lower().rstrip('/') if url else ''
    
    norm_comp = normalize_text(comp)
    norm_title = normalize_text(title)
    
    # Check duplicate against existing sheets
    is_dup = False
    dup_reason = ""
    
    for ex in existing_roles:
        # Same URL
        if clean_url and ex['url'] and clean_url == ex['url']:
            is_dup = True
            dup_reason = f"Exact URL match in '{ex['sheet']}' (Row {ex['row']}): {ex['company']} - {ex['title']}"
            break
            
        # Same company AND same role type
        if norm_comp and ex['norm_comp'] and (norm_comp in ex['norm_comp'] or ex['norm_comp'] in norm_comp):
            # Check if role matches
            t1, t2 = norm_title, ex['norm_title']
            if ('intern' in t1 and 'intern' in t2) or ('trainee' in t1 and 'trainee' in t2) or ('swe' in t1 and 'swe' in t2) or ('sde' in t1 and 'sde' in t2) or ('analyst' in t1 and 'analyst' in t2):
                is_dup = True
                dup_reason = f"Company & Role duplicate in '{ex['sheet']}' (Row {ex['row']}): '{ex['company']}' - '{ex['title']}'"
                break
                
    if is_dup:
        duplicates_found.append({
            'row': r,
            'company': comp,
            'title': title,
            'dup_reason': dup_reason
        })
        print(f"  ❌ DUPLICATE: [{comp}] {title} -> {dup_reason}")
    else:
        clean_wave5.append({
            'row': r,
            'company': comp,
            'title': title,
            'location': loc,
            'notes': notes,
            'status': status,
            'url': url
        })

print(f"\nSummary:")
print(f"  Duplicates found: {len(duplicates_found)}")
print(f"  Clean unique roles in Wave 5: {len(clean_wave5)}")
