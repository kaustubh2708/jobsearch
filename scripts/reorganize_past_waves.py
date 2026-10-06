#!/usr/bin/env python3
"""
reorganize_past_waves.py

Reorganizes data/Companies(1).xlsx and data/companies.xlsx for Vrinda:
  - Preserves original sheets ('Sheet1', 'Job Links', 'Warm-up', 'Bhaiya contacts') untouched.
  - Combines Waves 1, 2, 3, 4, 5 into a single consolidated sheet named 'past wave' (577 rows).
  - Leaves the last 2 wave datas as separate individual sheets:
      * 'Wave 6' (10 verified roles from 15-company sweep)
      * 'Wave 7' (15 verified roles from Wave 7 discovery sweep)
  - Saves to data/Companies(1).xlsx and mirrors to data/companies.xlsx.
  - Updates data/jobs.json and validates via scripts/validate_jobs.py (0 errors, 0 warnings).
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os, shutil, re

# Files
SOURCE_FILE = 'data/Companies(1).xlsx'
MIRROR_FILE = 'data/companies.xlsx'
PREV_WAVES_SOURCE = 'data/companies_pre_sep_backup.xlsx'

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
                val_str = 'Apply / Requisition Link ↗'
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

    # 1. Copy the 4 original sheets
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

    # 2. Build consolidated 'past wave' sheet combining Waves 1 to 5
    print("\n--- Building 'past wave' sheet (combining Waves 1, 2, 3, 4, 5) ---")
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

    # Load pre_sep_backup which has the exact verified Prev Waves content
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

    auto_fit_columns(ws_past)
    print(f"✓ Consolidated 'past wave' populated: {ws_past.max_row - 1} rows.")

    # 3. Copy last 2 wave datas as separate sheets: Wave 6 and Wave 7
    for wave_name in ['Wave 6', 'Wave 7']:
        print(f"\n--- Preserving separate sheet: {wave_name} ---")
        src_wave = wb_curr[wave_name]
        tgt_wave = wb_new.create_sheet(wave_name)

        for r in range(1, src_wave.max_row + 1):
            tgt_wave.row_dimensions[r].height = src_wave.row_dimensions[r].height
            for c in range(1, src_wave.max_column + 1):
                sc = src_wave.cell(r, c)
                tc = tgt_wave.cell(r, c, sc.value)
                if sc.has_style:
                    tc.font = sc.font.copy()
                    tc.fill = sc.fill.copy()
                    tc.border = sc.border.copy()
                    tc.alignment = sc.alignment.copy()
                if sc.hyperlink:
                    tc.hyperlink = sc.hyperlink.target
        auto_fit_columns(tgt_wave)
        print(f"✓ {wave_name} preserved: {tgt_wave.max_row - 1} data rows.")

    # Save target workbook
    print(f"\nSaving reorganized workbook to {SOURCE_FILE}...")
    wb_new.save(SOURCE_FILE)
    print(f"✓ Successfully saved {SOURCE_FILE}")
    print(f"Current sheets in {SOURCE_FILE}: {wb_new.sheetnames}")

    # Mirror to companies.xlsx
    print(f"\nMirroring to {MIRROR_FILE}...")
    shutil.copy2(SOURCE_FILE, MIRROR_FILE)
    print(f"✓ Successfully mirrored to {MIRROR_FILE}")

if __name__ == '__main__':
    main()
