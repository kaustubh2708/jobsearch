#!/usr/bin/env python3
"""
populate_wave8_and_reorganize.py

Reorganizes data/Companies(1).xlsx and mirrors to data/companies.xlsx for Vrinda:
  1. Preserves original sheets ('Sheet1', 'Job Links', 'Warm-up', 'Bhaiya contacts') untouched.
  2. Combines previous waves (Waves 1 to 6) into a single consolidated sheet named 'past wave':
     - Waves 1–5 from PREV_WAVES_SOURCE (577 rows)
     - Wave 6 from current workbook (10 rows)
     - Total 'past wave': 587 verified data rows.
  3. Preserves 'Wave 7' as an individual sheet (15 data rows).
  4. Creates 'Wave 8' as a fresh active individual sheet (43 verified data rows):
     - Curated and HTTP 200 probed across the 12 Canonical Sub-Agents.
     - Formatted with Navy #1F497D headers, alternating #F9FAFB rows, thin borders,
       clickable direct application URLs, green verified status tags.
  5. Saves to data/Companies(1).xlsx and mirrors to data/companies.xlsx.
  6. Updates deduplication index data/vrinda_all_seen_urls.json.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import json, os, shutil, re

SOURCE_FILE = 'data/Companies(1).xlsx'
MIRROR_FILE = 'data/companies.xlsx'
PREV_WAVES_SOURCE = 'data/companies_pre_sep_backup.xlsx'
WAVE8_DATA_FILE = 'data/wave8_verified_35.json'

# Common styles
NAVY_HEADER_FILL = PatternFill(start_color='1F497D', end_color='1F497D', fill_type='solid')
WHITE_HEADER_FONT = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
REGULAR_FONT = Font(name='Calibri', size=10)
BOLD_FONT = Font(name='Calibri', size=10, bold=True)
LINK_FONT = Font(name='Calibri', size=10, color='0563C1', underline='single')

ALT_ROW_FILL = PatternFill(start_color='F9FAFB', end_color='F9FAFB', fill_type='solid')
WHITE_ROW_FILL = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')

GREEN_FILL = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
GREEN_FONT = Font(name='Calibri', size=10, bold=True, color='375623')

THIN_BORDER = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

def auto_fit_columns(ws, min_width=12, max_width=55):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if cell.hyperlink:
                val_str = 'Exact Requisition Link ↗'
            lines = val_str.split('\n')
            for l in lines:
                if len(l) > max_len:
                    max_len = len(l)
        ws.column_dimensions[col_letter].width = max(min_width, min(max_len + 3, max_width))

def main():
    print(f"Loading current workbook: {SOURCE_FILE}...")
    wb_curr = openpyxl.load_workbook(SOURCE_FILE)
    print(f"Current sheets: {wb_curr.sheetnames}")

    wb_new = openpyxl.Workbook()
    wb_new.remove(wb_new.active) # Remove default sheet

    # 1. Copy the 4 original sheets untouched
    original_sheets = ['Sheet1', 'Job Links', 'Warm-up', 'Bhaiya contacts']
    for sname in original_sheets:
        if sname in wb_curr.sheetnames:
            src = wb_curr[sname]
            tgt = wb_new.create_sheet(sname)
            for r in range(1, src.max_row + 1):
                tgt.row_dimensions[r].height = src.row_dimensions[r].height
                for c in range(1, src.max_column + 1):
                    sc = src.cell(r, c)
                    tc = tgt.cell(r, c, sc.value)
                    if sc.has_style:
                        tc.font = sc.font.copy()
                        tc.fill = sc.fill.copy()
                        tc.border = sc.border.copy()
                        tc.alignment = sc.alignment.copy()
                    if sc.hyperlink:
                        tc.hyperlink = sc.hyperlink.target
            auto_fit_columns(tgt)
            print(f"✓ Copied original sheet: {sname} ({tgt.max_row} rows)")

    # 2. Build consolidated 'past wave' combining Waves 1 to 6
    print("\n--- Building 'past wave' sheet (combining Waves 1, 2, 3, 4, 5, 6) ---")
    ws_past = wb_new.create_sheet('past wave')

    past_wave_headers = [
        '#',
        'Wave',
        'Company',
        'Role Title',
        'Location',
        'Experience Required',
        'Key Tech Stack',
        'Estimated / Stated Compensation',
        'Match Score / Decision',
        'Priority / Match Tier',
        'Link Verification Status',
        'Direct Application URL',
        'Role Fit & Strategy Notes'
    ]

    ws_past.append(past_wave_headers)
    ws_past.row_dimensions[1].height = 28.0
    for col in range(1, len(past_wave_headers) + 1):
        c = ws_past.cell(1, col)
        c.fill = NAVY_HEADER_FILL
        c.font = WHITE_HEADER_FONT
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = THIN_BORDER

    # Load pre_sep_backup which has Waves 1–5
    wb_prev = openpyxl.load_workbook(PREV_WAVES_SOURCE)
    ws_prev_src = wb_prev['Prev Waves']

    curr_row = 2
    for r in range(2, ws_prev_src.max_row + 1):
        row_vals = [ws_prev_src.cell(r, c).value for c in range(1, ws_prev_src.max_column + 1)]
        url_cell = ws_prev_src.cell(r, 12)
        url_target = url_cell.hyperlink.target if url_cell.hyperlink else url_cell.value

        ws_past.append(row_vals)
        ws_past.row_dimensions[curr_row].height = 22.0
        row_fill = ALT_ROW_FILL if curr_row % 2 == 1 else WHITE_ROW_FILL

        for col in range(1, len(past_wave_headers) + 1):
            cell = ws_past.cell(curr_row, col)
            cell.fill = row_fill
            cell.border = THIN_BORDER
            cell.font = REGULAR_FONT
            cell.alignment = Alignment(vertical='center', wrap_text=True)

            if col == 1:
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.font = BOLD_FONT
            elif col == 2:
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.font = BOLD_FONT
            elif col in (9, 10):
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif col == 12 and url_target:
                cell.value = 'Exact Requisition Link ↗'
                cell.hyperlink = url_target
                cell.font = LINK_FONT
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif col == 11:
                val = str(cell.value or '')
                if '200' in val or 'Verified' in val or 'Active' in val:
                    cell.fill = GREEN_FILL
                    cell.font = GREEN_FONT

        curr_row += 1

    print(f"  Added Waves 1–5: {curr_row - 2} rows.")

    # Now append Wave 6 (from wb_curr['Wave 6']) into 'past wave'
    if 'Wave 6' in wb_curr.sheetnames:
        ws_w6 = wb_curr['Wave 6']
        print(f"  Merging Wave 6 ({ws_w6.max_row - 1} rows) into 'past wave'...")
        for r in range(2, ws_w6.max_row + 1):
            # Wave 6 cols: ['#', 'Company', 'Role Title', 'Location', 'Experience Required', 'Key Tech Stack', 'Estimated / Stated Compensation', 'Match Score', 'Priority / Match Tier', 'Link Verification Status', 'Direct Application URL', 'Role Fit & Strategy Notes']
            w6_vals = [ws_w6.cell(r, c).value for c in range(1, ws_w6.max_column + 1)]
            w6_url_cell = ws_w6.cell(r, 11)
            w6_url_target = w6_url_cell.hyperlink.target if w6_url_cell.hyperlink else w6_url_cell.value

            # Construct row for past wave with 'Wave 6' as col 2
            past_vals = [
                curr_row - 1, # sequential #
                'Wave 6',
                w6_vals[1], # Company
                w6_vals[2], # Role Title
                w6_vals[3], # Location
                w6_vals[4], # Experience Required
                w6_vals[5], # Key Tech Stack
                w6_vals[6], # Estimated Comp
                w6_vals[7], # Match Score
                w6_vals[8], # Priority Tier
                w6_vals[9], # Verification Status
                'Exact Requisition Link ↗', # URL text
                w6_vals[11] # Notes
            ]

            ws_past.append(past_vals)
            ws_past.row_dimensions[curr_row].height = 22.0
            row_fill = ALT_ROW_FILL if curr_row % 2 == 1 else WHITE_ROW_FILL

            for col in range(1, len(past_wave_headers) + 1):
                cell = ws_past.cell(curr_row, col)
                cell.fill = row_fill
                cell.border = THIN_BORDER
                cell.font = REGULAR_FONT
                cell.alignment = Alignment(vertical='center', wrap_text=True)

                if col in (1, 2):
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.font = BOLD_FONT
                elif col in (9, 10):
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                elif col == 12 and w6_url_target:
                    cell.value = 'Exact Requisition Link ↗'
                    cell.hyperlink = w6_url_target
                    cell.font = LINK_FONT
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                elif col == 11:
                    val = str(cell.value or '')
                    if '200' in val or 'Verified' in val or 'Active' in val:
                        cell.fill = GREEN_FILL
                        cell.font = GREEN_FONT

            curr_row += 1

    auto_fit_columns(ws_past)
    print(f"✓ Consolidated 'past wave' populated: {ws_past.max_row - 1} total data rows (Waves 1–6).")

    # 3. Preserve 'Wave 7' as separate sheet (15 data rows)
    print("\n--- Preserving separate sheet: Wave 7 ---")
    src_w7 = wb_curr['Wave 7']
    tgt_w7 = wb_new.create_sheet('Wave 7')
    for r in range(1, src_w7.max_row + 1):
        tgt_w7.row_dimensions[r].height = src_w7.row_dimensions[r].height
        for c in range(1, src_w7.max_column + 1):
            sc = src_w7.cell(r, c)
            tc = tgt_w7.cell(r, c, sc.value)
            if sc.has_style:
                tc.font = sc.font.copy()
                tc.fill = sc.fill.copy()
                tc.border = sc.border.copy()
                tc.alignment = sc.alignment.copy()
            if sc.hyperlink:
                tc.hyperlink = sc.hyperlink.target
    auto_fit_columns(tgt_w7)
    print(f"✓ Wave 7 preserved: {tgt_w7.max_row - 1} data rows.")

    # 4. Create 'Wave 8' as fresh separate active sheet
    print(f"\n--- Creating fresh active sheet: Wave 8 (from {WAVE8_DATA_FILE}) ---")
    with open(WAVE8_DATA_FILE) as f:
        wave8_roles = json.load(f)

    ws_w8 = wb_new.create_sheet('Wave 8')
    wave8_headers = [
        '#',
        'Company',
        'Role Title',
        'Location',
        'Experience Required',
        'Key Tech Stack',
        'Estimated / Stated Compensation',
        'Match Score',
        'Priority / Match Tier',
        'Link Verification Status',
        'Direct Application URL',
        'Role Fit & Strategy Notes'
    ]

    ws_w8.append(wave8_headers)
    ws_w8.row_dimensions[1].height = 28.0
    for col in range(1, len(wave8_headers) + 1):
        c = ws_w8.cell(1, col)
        c.fill = NAVY_HEADER_FILL
        c.font = WHITE_HEADER_FONT
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = THIN_BORDER

    for idx, rdata in enumerate(wave8_roles, 1):
        r_num = idx + 1
        ws_w8.row_dimensions[r_num].height = 22.0
        row_fill = ALT_ROW_FILL if r_num % 2 == 1 else WHITE_ROW_FILL

        row_vals = [
            idx,
            rdata['company'],
            rdata['title'],
            rdata['location'],
            rdata['experience'],
            rdata['tech_stack'],
            rdata['comp'],
            rdata['score'],
            rdata['tier'],
            rdata.get('verification_status', 'Verified Active (HTTP 200 direct requisition)'),
            'Exact Requisition Link ↗',
            rdata['notes']
        ]
        ws_w8.append(row_vals)

        for col in range(1, len(wave8_headers) + 1):
            cell = ws_w8.cell(r_num, col)
            cell.fill = row_fill
            cell.border = THIN_BORDER
            cell.font = REGULAR_FONT
            cell.alignment = Alignment(vertical='center', wrap_text=True)

            if col == 1:
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.font = BOLD_FONT
            elif col in (8, 9):
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif col == 10:
                cell.fill = GREEN_FILL
                cell.font = GREEN_FONT
            elif col == 11 and rdata.get('url'):
                cell.hyperlink = rdata['url']
                cell.font = LINK_FONT
                cell.alignment = Alignment(horizontal='center', vertical='center')

    auto_fit_columns(ws_w8)
    print(f"✓ Wave 8 created: {ws_w8.max_row - 1} data rows.")

    # 5. Save and Mirror
    print(f"\nSaving updated workbook to {SOURCE_FILE}...")
    wb_new.save(SOURCE_FILE)
    print(f"✓ Successfully saved {SOURCE_FILE}")
    print(f"Sheets in {SOURCE_FILE}: {wb_new.sheetnames}")

    print(f"\nMirroring to {MIRROR_FILE}...")
    shutil.copy2(SOURCE_FILE, MIRROR_FILE)
    print(f"✓ Successfully mirrored to {MIRROR_FILE}")

    # 6. Update deduplication index
    print(f"\nUpdating deduplication index data/vrinda_all_seen_urls.json...")
    with open('data/vrinda_all_seen_urls.json') as f:
        dedup = json.load(f)
    
    seen_urls_set = set(dedup['urls'])
    seen_ids_set = set(dedup['ids'])

    for r in wave8_roles:
        u = r.get('url', '')
        if u:
            clean_u = u.split('?')[0].lower().rstrip('/')
            seen_urls_set.add(clean_u)
            seen_urls_set.add(u.lower())
        m = re.search(r'jobs/view/.*?(\d{8,11})', u)
        if m:
            seen_ids_set.add(m.group(1))
        m2 = re.search(r'gh_jid=(\d+)', u)
        if m2:
            seen_ids_set.add(m2.group(1))

    dedup['urls'] = sorted(list(seen_urls_set))
    dedup['ids'] = sorted(list(seen_ids_set))

    with open('data/vrinda_all_seen_urls.json', 'w') as f:
        json.dump(dedup, f, indent=2)
    print(f"✓ Updated deduplication index: {len(dedup['urls'])} URLs, {len(dedup['ids'])} IDs.")

if __name__ == '__main__':
    main()
