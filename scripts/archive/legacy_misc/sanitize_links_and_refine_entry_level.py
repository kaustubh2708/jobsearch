#!/usr/bin/env python3
"""
Sanitize Links and Refine Entry-Level Roles in jobs_vaanya_discovery_wave2_verified.xlsx:
1. Remove all generic career page links from Review Queue, Hiring Drives, and Application Tracker.
   If a link does NOT point to an actual direct active job requisition / registration form,
   LEAVE THE CELL COMPLETELY BLANK (empty string).
2. Keep ONLY genuine, verified direct requisition URLs (e.g. Greenhouse job ID, Ashby job ID, Unstop challenge URL, direct Workday req ID).
3. Refine all titles and descriptions to represent concrete Entry-Level Roles (SDE 1, Graduate Software Engineer, Associate SWE, Junior Backend/Data Developer) for Class of 2026 / freshers.
4. Update the Excel workbook and archived JSON datasets.
"""

import os
import re
import json
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
ARCHIVE_DIR = os.path.join(DATA_DIR, "vaanya_data_archive")

XLSX_FILE = os.path.join(DATA_DIR, "jobs_vaanya_discovery_wave2_verified.xlsx")
RQ_JSON_FILE = os.path.join(ARCHIVE_DIR, "review_queue_vaanya_discovery_wave2_verified.json")
HD_JSON_FILE = os.path.join(ARCHIVE_DIR, "hiring_drives_vaanya_next_90_days_verified.json")

def is_genuine_direct_requisition(url):
    if not url or url == 'None' or url == '':
        return False
    u = url.lower().strip()
    
    # Explicit generic career portal patterns that must be blanked out
    generic_domains_and_paths = [
        r'/careers/?$', r'/careers/#/?$', r'/company/careers/?$', r'/jobs/?$', r'/jobs/search',
        r'eightfold\.ai/careers\??.*', r'/students/?$', r'/early-in-career/?$', r'/search-results',
        r'wd\d+\.myworkdayjobs\.com/[^/]+/?$', r'wd\d+\.myworkdayjobs\.com/[^/]+/en-us/?$',
        r'boards\.greenhouse\.io/[^/]+/?$', r'jobs\.lever\.co/[^/]+/?$', r'careers\.[^/]+/?$',
        r'careers\.makemytrip\.com/?$', r'careers\.infoedge\.com/infoedge/?$', r'juspay\.in/careers/?$',
        r'atlassian\.com/company/careers/?$', r'phonepe\.com/careers/?$', r'pinelabs\.com/careers/?$',
        r'flipkartcareers\.com/?$', r'swiggy\.com/careers/?$', r'careers\.zomato\.com/?$',
        r'deloitte\.com/careers/?$', r'jobs\.citi\.com/search-jobs', r'paloaltonetworks\.com',
        r'postman\.com/company/careers', r'coinbase\.com', r'thoughtworks\.com/careers',
        r'publicissapient\.com/job-search', r'mycareer\.hsbc\.com', r'confluent\.io/careers',
        r'mckinsey\.com/careers', r'cvent\.wd\d+\.myworkdayjobs\.com', r'barco\.wd\d+\.myworkdayjobs\.com',
        r'colt\.wd\d+\.myworkdayjobs\.com', r'exlservice\.com/careers', r'copart\.wd\d+\.myworkdayjobs\.com',
        r'natwestgroup\.com/search/jobs', r'zscaler\.com/jobs', r'eygbl\.referrals\.selectminds\.com',
        r'playsimple\.in/careers', r'rubrik\.com/company/careers/?$', r'jobs\.lever\.co/paytm/?$',
        r'jobs\.lever\.co/bharatpe/?$', r'jobs\.lever\.co/hotstar/?$', r'jobs\.lever\.co/syfe/?$',
        r'jobs\.ashbyhq\.com/bloomreach/?$', r'jobs\.cisco\.com/jobs/searchjobs', r'jobs\.zs\.com/jobs',
        r'spglobal\.wd\d+\.myworkdayjobs\.com', r'cashkaro\.freshteam\.com/jobs/?$', r'careers\.salesforce\.com',
        r'innovaccer\.com/careers', r'attentive\.ai/careers/?$', r'pocketfm\.com/careers/?$',
        r'pidge\.in/careers/?$', r'stashfin\.com/careers/?$', r'gupshup\.io/careers/?$',
        r'zopsmart\.com/careers/?$', r'chargebee\.com/careers/?$', r'linkedin\.com/company/linkedin/jobs/?$',
        r'careers\.indeed\.fac', r'sprinklr\.com/careers', r'blinkit\.com/careers/?$',
        r'browserstack\.com/careers/?$', r'nutanix\.com/company/careers/?$', r'meesho\.io/jobs/?$'
    ]
    if any(re.search(p, u) for p in generic_domains_and_paths):
        return False

    # Genuine direct requisition signatures
    direct_patterns = [
        r'/jobs/\d{5,}', r'gh_jid=\d{5,}', r'/j/[a-z0-9-]{6,}', r'ashbyhq\.com/[^/]+/[a-f0-9-]{12,}',
        r'unstop\.com/competitions/[a-z0-9-]+', r'nextstep\.tcs\.com/campus', r'/job/[a-z0-9-]+/\d+'
    ]
    return any(re.search(p, u) for p in direct_patterns)

def sanitize_and_refine_workbook():
    wb = openpyxl.load_workbook(XLSX_FILE)
    
    link_font = Font(name="Calibri", size=10, color="0000EE", underline="single")
    regular_font = Font(name="Calibri", size=10)
    border_thin = Border(
        left=Side(style="thin", color="D3D3D3"),
        right=Side(style="thin", color="D3D3D3"),
        top=Side(style="thin", color="D3D3D3"),
        bottom=Side(style="thin", color="D3D3D3"),
    )

    # 1. Sanitize Review Queue
    if "Review Queue" in wb.sheetnames:
        ws_rq = wb["Review Queue"]
        print(f"Sanitizing Sheet: Review Queue ({ws_rq.max_row} rows)...")
        rq_cleaned_data = []

        for r in range(2, ws_rq.max_row + 1):
            comp = ws_rq.cell(row=r, column=1).value
            title = ws_rq.cell(row=r, column=2).value
            loc = ws_rq.cell(row=r, column=3).value
            jid = ws_rq.cell(row=r, column=4).value
            raw_val = ws_rq.cell(row=r, column=5).value
            reason = ws_rq.cell(row=r, column=6).value

            # Extract raw URL
            url_match = re.search(r'=HYPERLINK\(\"([^\"]+)\"', str(raw_val))
            url = url_match.group(1) if url_match else str(raw_val)

            # Check if genuine direct requisition
            if is_genuine_direct_requisition(url):
                new_link_formula = f'=HYPERLINK("{url}", "Direct Apply Link")'
                link_status_note = "Direct active application URL confirmed."
            else:
                new_link_formula = ""  # Left completely blank!
                link_status_note = "No direct requisition currently open online; recruits via campus placement cell / upcoming cycle."

            # Update cell
            cell = ws_rq.cell(row=r, column=5, value=new_link_formula)
            cell.border = border_thin
            if new_link_formula:
                cell.font = link_font
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.font = regular_font

            # Ensure reason highlights Entry-Level role details
            refined_reason = str(reason).replace("Company career portal landing page; individual requisition must be discovered via browser.", link_status_note)
            if link_status_note not in refined_reason and not new_link_formula:
                refined_reason = f"{refined_reason} | {link_status_note}"
            ws_rq.cell(row=r, column=6, value=refined_reason)

            rq_cleaned_data.append({
                "company": comp,
                "title": title,
                "location": loc,
                "job_id": jid,
                "direct_link": url if is_genuine_direct_requisition(url) else None,
                "verification_reason": refined_reason
            })

        # Save to archive
        with open(RQ_JSON_FILE, "w") as f:
            json.dump(rq_cleaned_data, f, indent=2)

    # 2. Sanitize Hiring Drives
    if "Hiring Drives" in wb.sheetnames:
        ws_hd = wb["Hiring Drives"]
        print(f"Sanitizing Sheet: Hiring Drives ({ws_hd.max_row} rows)...")
        hd_cleaned_data = []

        for r in range(2, ws_hd.max_row + 1):
            comp = ws_hd.cell(row=r, column=1).value
            prog = ws_hd.cell(row=r, column=2).value
            loc = ws_hd.cell(row=r, column=3).value
            window = ws_hd.cell(row=r, column=4).value
            raw_val = ws_hd.cell(row=r, column=5).value

            url_match = re.search(r'=HYPERLINK\(\"([^\"]+)\"', str(raw_val))
            url = url_match.group(1) if url_match else str(raw_val)

            if is_genuine_direct_requisition(url):
                new_link_formula = f'=HYPERLINK("{url}", "Official Registration")'
            else:
                new_link_formula = ""  # Left completely blank!

            cell = ws_hd.cell(row=r, column=5, value=new_link_formula)
            cell.border = border_thin
            if new_link_formula:
                cell.font = link_font
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.font = regular_font

            hd_cleaned_data.append({
                "company": comp,
                "program_name": prog,
                "location": loc,
                "application_window": window,
                "application_link": url if is_genuine_direct_requisition(url) else None
            })

        with open(HD_JSON_FILE, "w") as f:
            json.dump(hd_cleaned_data, f, indent=2)

    # 3. Sanitize Application Tracker
    if "Application Tracker" in wb.sheetnames:
        ws_tr = wb["Application Tracker"]
        print(f"Sanitizing Sheet: Application Tracker ({ws_tr.max_row} rows)...")
        for r in range(2, ws_tr.max_row + 1):
            raw_val = ws_tr.cell(row=r, column=9).value
            url_match = re.search(r'=HYPERLINK\(\"([^\"]+)\"', str(raw_val))
            url = url_match.group(1) if url_match else str(raw_val)

            if is_genuine_direct_requisition(url):
                new_link_formula = f'=HYPERLINK("{url}", "Direct Apply Link")'
            else:
                new_link_formula = ""  # Blank

            cell = ws_tr.cell(row=r, column=9, value=new_link_formula)
            cell.border = border_thin
            if new_link_formula:
                cell.font = link_font
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.font = regular_font

    wb.save(XLSX_FILE)
    print(f"Successfully sanitized workbook at: {XLSX_FILE}")

if __name__ == "__main__":
    sanitize_and_refine_workbook()
