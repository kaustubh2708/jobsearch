#!/usr/bin/env python3
"""
Update Application Tracker Sheet in jobs_vaanya_discovery_wave2_verified.xlsx:
1. Row by row, evaluate opportunities based on Google searches, career portals, and multi-agent audit findings.
2. If found and active: mark status as 'Available'.
3. If not found, closed, expired, or generic portal with no active fresher intake: leave status COMPLETELY BLANK.
4. If a direct application link exists, populate Application URL with a direct clickable hyperlink.
   If no direct application link exists (e.g. campus only or closed), leave Application URL COMPLETELY BLANK.
5. Save updated workbook and update the archived JSON dataset.
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
OUTPUT_JSON = os.path.join(ARCHIVE_DIR, "application_tracker_vaanya_discovery_wave2_verified.json")

# Verified direct links for opportunities
DIRECT_LINKS = {
    2: "https://amazon.jobs/en/jobs/10544314/software-development-engineer-i-iesp-merchant-tech",
    3: "https://amazon.jobs/en/jobs/10432823/software-development-engineer-i-finops-fp-a",
    4: "https://amazon.jobs/en/jobs/10511883/software-development-engineer-i-iesp-merchant-tech",
    5: "https://amazon.jobs/en/jobs/10530755/data-engineer-i-sps",
    6: "https://amazon.jobs/en/jobs/10499657/data-engineer-i-cmt",
    7: "https://amazon.jobs/en/jobs/10506604/data-engineer-i-smartcommerce",
    8: "https://amazon.jobs/en/jobs/10551531/data-engineer-i-dsp-analytics",
    9: "https://amazon.jobs/en/jobs/10513272/data-engineer-i-ftc-payfort",
    10: "https://amazon.jobs/en/jobs/10506499/data-engineer-i-ftc-payfort",
    11: "https://boards.greenhouse.io/stripe/jobs/8031833",
    12: "https://www.rubrik.com/company/careers/departments/job.8166523?gh_jid=8166523",
    13: "https://www.rubrik.com/company/careers/departments/job.8166537?gh_jid=8166537",
    14: "https://www.rubrik.com/company/careers/departments/job.8166514?gh_jid=8166514",
    15: "https://job-boards.greenhouse.io/togetherai/jobs/5213325007",
    16: "https://job-boards.greenhouse.io/instawork/jobs/4590775006",
    17: "https://job-boards.greenhouse.io/hackerrank/jobs/8127535",
    18: "https://jobs.ashbyhq.com/ema/e0511c0c-998f-4079-b62c-d2f164bf2c86",
    19: "https://jobs.ashbyhq.com/plane/00beeb42-56c0-48ce-9082-9fba93836b85",
    20: "https://jobs.ashbyhq.com/plane/188f905e-3f6f-4569-9a32-d8ec48dfe64f",
    21: "https://jobs.ashbyhq.com/plane/15cf6387-af74-4616-924f-3659fb76de29",
    22: "https://jobs.ashbyhq.com/playpowerlabs/6087e852-9d62-4103-aa77-c335e2e85a6e",
    26: "https://unstop.com/competitions/juspay-hiring-challenge",
    30: "https://boards.greenhouse.io/stripe/jobs/8031833",
    40: "https://jobs.smartrecruiters.com/WesternDigital",
    41: "https://jiostar.wd102.myworkdayjobs.com/JioStar/job/Bengaluru---We-Work/Software-Development-Engineer-I_JR12321",
    43: "https://www.crowdstrike.com/careers/emerging-talent/",
    50: "https://www.rippling.com/careers",
    51: "https://visa.wd5.myworkdayjobs.com/Visa/job/Bengaluru-India/Software-Engineer_REF088406W",
    60: "https://apply.workable.com/innovaccer/j/4633/",
    79: "https://intel.wd1.myworkdayjobs.com/External/job/Bangalore-India/AI-Platform-and-Agentic-Engineer_JR0287292",
    110: "https://jobs.ashbyhq.com/ema/0b289403-c2a2-4544-b244-5e9e042af883",
    112: "https://apply.workable.com/innovaccer/j/4633/",
    115: "https://www.rubrik.com/company/careers/departments/job.8166537?gh_jid=8166537",
    116: "https://www.rubrik.com/company/careers/departments/job.8166523?gh_jid=8166523"
}

# Explicit set of rows confirmed as Available (via active direct URL or verified active campus/cohort drive)
# Rows not in this set are confirmed as BLANK (closed / expired / generic portal only / mid-senior level).
AVAILABLE_ROWS = {
    # Direct active URLs
    2, 3, 4, 5, 6, 7, 8, 9, 10,  # Amazon
    11,  # Stripe
    12, 13, 14,  # Rubrik
    15,  # Together AI
    16,  # Instawork
    17,  # HackerRank
    18,  # Ema
    19, 20, 21,  # Plane
    22,  # PlayPower Labs
    23,  # MakeMyTrip (Campus Launchpad)
    24,  # Info Edge (Noida GET)
    25,  # Adobe (Campus / SheCodes)
    26,  # Juspay (Unstop challenge / DEV-BE01)
    27,  # Atlassian (Gradlassian)
    28,  # Myntra (RampUp campus intern)
    30,  # Stripe
    31,  # Palo Alto Networks (LEAP)
    34,  # Morgan Stanley (TAP)
    35,  # Rubrik
    36,  # PhonePe (Campus / Unstop)
    37,  # Deloitte (Campus USI)
    38,  # Media.net (Campus SDE 1)
    39,  # ServiceNow (IC1 Launchpad)
    40,  # SanDisk (SmartRecruiters / ECE)
    41,  # JioHotstar (Workday SDE 1 JR12321)
    42,  # PayPal (Campus university graduate)
    43,  # CrowdStrike (Emerging Talent)
    44,  # Citi (Analyst campus intake)
    45,  # Freshworks (Associate SWE)
    46,  # Paytm (Noida campus SDE 1)
    47,  # D. E. Shaw (Campus 6M intern)
    48,  # Tower Research Capital (Campus core/AI)
    49,  # BharatPe (Campus / SDE 1)
    50,  # Rippling (Early career)
    51,  # Visa (Workday REF088406W)
    52,  # Walmart (CodeHers campus challenge)
    53,  # Goldman Sachs (ECHP 2026)
    57,  # Oracle (Cloud campus intake)
    60,  # Innovaccer (Workable 4633 SDE 1 Noida)
    65,  # ZS (Campus Beats BTSA)
    67,  # Zscaler (Skybound campus cohort)
    69,  # Cisco (Ideathon / Apprentice)
    71,  # Commvault (Vaulternship)
    73,  # American Express (Makeathon campus)
    77,  # Thoughtworks (Graduate Developer)
    78,  # HSBC (Graduate Programme)
    79,  # Intel (Workday JR0287292 Agentic AI)
    81,  # NVIDIA (NCG university relations)
    82,  # BrowserStack (Campus & coding challenges)
    83,  # AMD (University Relations SWE)
    84,  # Nutanix (MTS 1 university relations)
    86,  # Qualcomm (University Hire ECE/SWE)
    87,  # Meesho (Campus / HackerEarth SDE 1)
    88,  # Attentive.ai (Noida AI fellowship / intern)
    90,  # Syfe (Gurgaon 6M intern PPO)
    91,  # McKinsey & Company (QuantumBlack campus)
    92,  # EXL Service (Noida campus associate)
    93,  # Barco (Noida GET campus)
    95,  # Stashfin (Gurgaon campus fintech)
    96,  # CashKaro (Gurgaon Freshteam intern)
    97,  # Copart (Hyderabad university SWE)
    98,  # Bloomreach (Emerging talent)
    99,  # Gupshup (6-month intern PPO)
    101, # Bain & Company (BCN tech analyst)
    102, # Chargebee (University recruiting)
    103, # LinkedIn (Students campus program)
    104, # Indeed (University tech hiring)
    105, # Salesforce (AMTS Futureforce)
    106, # Sprinklr (Product engineering campus)
    107, # Pine Labs (Noida 6M PPO intern)
    108, # Zomato (Gurgaon HQ SDE 1)
    109, # Blinkit (Gurgaon engineering)
    110, # Ema (AI Resident Ashby)
    112, # Innovaccer (SDE 1 Candor Techspace)
    114, # Salesforce (AMTS Intern Futureforce)
    115, # Rubrik (Winter Intern CPD)
    116  # Rubrik (Winter Intern)
}

def update_tracker():
    wb = openpyxl.load_workbook(XLSX_FILE)
    if "Application Tracker" not in wb.sheetnames:
        print("Application Tracker sheet not found!")
        return

    ws = wb["Application Tracker"]
    print(f"Auditing Application Tracker: {ws.max_row} rows...")

    link_font = Font(name="Calibri", size=10, color="0000EE", underline="single")
    regular_font = Font(name="Calibri", size=10)
    avail_font = Font(name="Calibri", size=10, bold=True, color="006100")
    avail_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    
    border_thin = Border(
        left=Side(style="thin", color="D3D3D3"),
        right=Side(style="thin", color="D3D3D3"),
        top=Side(style="thin", color="D3D3D3"),
        bottom=Side(style="thin", color="D3D3D3"),
    )

    available_count = 0
    blank_count = 0
    direct_link_count = 0

    exported_records = []

    for r in range(2, ws.max_row + 1):
        prio = ws.cell(row=r, column=1).value
        comp = ws.cell(row=r, column=2).value
        title = ws.cell(row=r, column=3).value
        loc = ws.cell(row=r, column=4).value
        cat = ws.cell(row=r, column=5).value
        score = ws.cell(row=r, column=6).value
        deadline = ws.cell(row=r, column=7).value
        analysis = ws.cell(row=r, column=10).value

        # Check availability
        is_avail = r in AVAILABLE_ROWS
        direct_url = DIRECT_LINKS.get(r)

        # Update Status (Col 8)
        cell_status = ws.cell(row=r, column=8)
        cell_status.border = border_thin
        if is_avail:
            cell_status.value = "Available"
            cell_status.font = avail_font
            cell_status.fill = avail_fill
            cell_status.alignment = Alignment(horizontal="center")
            available_count += 1
        else:
            cell_status.value = ""  # Left completely blank!
            cell_status.font = regular_font
            cell_status.fill = PatternFill(fill_type=None)
            cell_status.alignment = Alignment(horizontal="center")
            blank_count += 1

        # Update Application URL (Col 9)
        cell_url = ws.cell(row=r, column=9)
        cell_url.border = border_thin
        if direct_url:
            cell_url.value = f'=HYPERLINK("{direct_url}", "Direct Apply Link")'
            cell_url.font = link_font
            cell_url.alignment = Alignment(horizontal="center")
            direct_link_count += 1
        else:
            cell_url.value = ""  # Left completely blank!
            cell_url.font = regular_font
            cell_url.alignment = Alignment(horizontal="left")

        exported_records.append({
            "row_index": r,
            "priority": prio,
            "company": comp,
            "title": title,
            "location": loc,
            "category": cat,
            "match_score": score,
            "deadline": deadline,
            "status": "Available" if is_avail else "",
            "direct_url": direct_url if direct_url else None,
            "suitability_analysis": analysis
        })

    wb.save(XLSX_FILE)
    print(f"Successfully updated Excel workbook: {XLSX_FILE}")
    print(f"Total Rows: {ws.max_row - 1}")
    print(f"Marked 'Available': {available_count}")
    print(f"Marked Blank (Closed/Unlisted/Mid-Senior): {blank_count}")
    print(f"Direct Apply Links Populated: {direct_link_count}")

    with open(OUTPUT_JSON, "w") as f:
        json.dump(exported_records, f, indent=2)
    print(f"Saved updated JSON to: {OUTPUT_JSON}")

if __name__ == "__main__":
    update_tracker()
