import openpyxl, json
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

with open('data/job_links_audit_results.json') as f:
    audit_results = json.load(f)

# Confirmed closed rows:
# Row 2 (Apple) was confirmed OPEN (Submit CV button active, active role 200677836).
# The truly closed rows are:
# Row 7 (Swiggy - SmartRecruiters expired)
# Row 11 (Sarvam AI - Ashby 404)
# Row 15 (Diligent - Greenhouse 404)
# Row 16 (Abnormal AI - 404 page)
# Row 25 (Lowe's - filled/closed)
# Row 61 (Amazon - LinkedIn no longer accepting applications)
# Row 74 (Walmart - LinkedIn closed)
# Row 75 (CredHive - LinkedIn closed)
# Row 110 (Policybazaar - LinkedIn closed)
# Row 141 (Level AI - Ashby 404)
# Row 157 (PAR Tech - Ashby 404)
# Row 163 (HackerRank - Greenhouse 404)
# Row 186 (Precisely - LinkedIn closed)
# Row 209 (Deliveroo - Greenhouse 404)

confirmed_closed_rows = {
    7, 11, 15, 16, 25, 61, 74, 75, 110, 141, 157, 163, 186, 209
}

print(f"Total confirmed closed rows: {len(confirmed_closed_rows)}")

# Load workbook
wb_path = 'data/Companies(2).xlsx'
wb = openpyxl.load_workbook(wb_path)
ws = wb['Job Links']

# Styles
closed_fill = PatternFill(start_color='FFD8D8', end_color='FFD8D8', fill_type='solid') # Soft/light red
closed_font = Font(name='Calibri', size=11, bold=True, color='9C0006') # Dark red text

center_align = Alignment(horizontal='center', vertical='center')
thin_side = Side(border_style='thin', color='D9D9D9')
thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

# Determine next available column:
# For rows 1-66, links are in col 5 (or 6). Col 6/7/8 has few notes.
# For rows 68+, links are in col 4. Col 5 is empty.
# In row 67 (header), col 4 is 'Direct Application Link'.
# Let's set the header for the status column:
# In row 67, col 5 is the header: 'Status / Link Verification'
header_font = Font(name='Arial', size=10, bold=True, color='000000')
header_cell = ws.cell(67, 5, 'Status / Verification')
header_cell.font = header_font
header_cell.alignment = center_align

# Now for each row with a link:
# If row is in confirmed_closed_rows:
#   Find the next available column for this row:
#   For rows <= 66: col 5 is the link cell. If col 6 is empty, use col 6. If col 6 has note, use col 7.
#   For rows >= 68: col 4 is the link cell. If col 5 is empty, use col 5. If col 5 has value, use col 6.
#   Write 'closed' and highlight with light red fill!

marked_count = 0

for r in range(1, ws.max_row + 1):
    if r == 67:
        continue # header row
    
    # Check if this row is closed
    if r in confirmed_closed_rows:
        # Determine next available column
        # Look from col 5 onwards
        target_col = None
        if r <= 66:
            # col 5 has the link. Check col 6, 7, 8...
            for c in range(6, 12):
                if ws.cell(r, c).value is None:
                    target_col = c
                    break
        else:
            # col 4 has the link. Check col 5, 6, 7...
            for c in range(5, 12):
                if ws.cell(r, c).value is None:
                    target_col = c
                    break

        if target_col:
            cell = ws.cell(r, target_col, 'closed')
            cell.fill = closed_fill
            cell.font = closed_font
            cell.alignment = center_align
            cell.border = thin_border
            marked_count += 1
            comp = ws.cell(r, 1).value
            title = ws.cell(r, 2).value
            print(f"Row {r:3d} [Col {target_col}]: Marked 'closed' for {comp} ({title})")

wb.save(wb_path)
print(f"\nSuccessfully saved {wb_path}. Marked {marked_count} closed links.")

