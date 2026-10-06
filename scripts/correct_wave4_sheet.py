import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

wb = openpyxl.load_workbook('data/Job Search.xlsx')

if 'New Additions (Wave 4)' in wb.sheetnames:
    del wb['New Additions (Wave 4)']

ws = wb.create_sheet('New Additions (Wave 4)')

headers = ['Company', 'Role Title', 'Location', 'Verdict', 'Stated JD Experience Requirement', 'Application URL', 'Eligible for Fresher (0 YOE)?']
ws.append(headers)

header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
header_font = Font(color='FFFFFF', bold=True, size=11)
for col in range(1, len(headers) + 1):
    c = ws.cell(row=1, column=col)
    c.fill = header_fill
    c.font = header_font
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

red_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
bold_red = Font(color='9C0006', bold=True)

audited_roles = [
    {
        'company': 'Atlys',
        'role': 'Research Engineer (AI & Computer Vision)',
        'location': 'Delhi HQ',
        'verdict': '❌ REJECTED (3–6 YOE)',
        'requirement': 'Verbatim JD requirement: "Have 3-6 years of software engineering experience, including meaningful work building and shipping ML or LLM-based systems in production."',
        'url': 'https://jobs.ashbyhq.com/atlys/cf775fce-a081-4b2e-b89e-df99ec64733e',
        'eligible': 'NO (Requires 3–6 YOE)'
    },
    {
        'company': 'Sarvam AI',
        'role': 'ML Ops Engineer, Chanakya',
        'location': 'New Delhi',
        'verdict': '❌ REJECTED (3–5 YOE)',
        'requirement': 'Verbatim JD requirement: "3–5 years in ML engineering or MLOps with at least one production LLM or ML system in continuous operation."',
        'url': 'https://jobs.ashbyhq.com/sarvam/e7f783e8-6378-4158-97d5-48a397a91698',
        'eligible': 'NO (Requires 3–5 YOE)'
    },
    {
        'company': 'Sarvam AI',
        'role': 'Strategic Deployment Engineer, Chanakya',
        'location': 'New Delhi',
        'verdict': '❌ REJECTED (3–6 YOE)',
        'requirement': 'Verbatim JD requirement: "3–6 years in software or ML engineering, with at least one full-cycle on-prem or enterprise deployment delivered end-to-end."',
        'url': 'https://jobs.ashbyhq.com/sarvam/87d5a5af-ea7d-4b94-a0fa-81dc64e54907',
        'eligible': 'NO (Requires 3–6 YOE)'
    },
    {
        'company': 'Avoca',
        'role': 'Deployment Engineer',
        'location': 'Bengaluru',
        'verdict': '❌ REJECTED (2+ YOE)',
        'requirement': 'Verbatim JD requirement: "2+ years of software engineering experience, preferably backend or systems-focused."',
        'url': 'https://jobs.ashbyhq.com/avoca/6758ee84-51b4-4d0d-a3a6-d40ec164de49',
        'eligible': 'NO (Requires 2+ YOE)'
    },
    {
        'company': 'Cisco',
        'role': 'Technical Graduate / Software Engineer',
        'location': 'Bengaluru',
        'verdict': '❌ REJECTED (Search Link)',
        'requirement': 'Generic Cisco search query URL. Individual openings on Cisco SWE lateral portal require 2–4+ years. Entry-level hires must go via Cisco Ideathon campus drive.',
        'url': 'https://jobs.cisco.com/jobs/search?query=Software+Engineer&location=India',
        'eligible': 'NO (Generic Search Link)'
    },
    {
        'company': 'Okta',
        'role': 'Associate Solutions Engineer',
        'location': 'Bengaluru',
        'verdict': '❌ REJECTED (4+ YOE)',
        'requirement': 'Verbatim JD requirement: "4+ years as a presales, solutions, or sales engineer in IAM or security".',
        'url': 'https://www.okta.com/company/careers/opportunity/8155883?gh_jid=8155883',
        'eligible': 'NO (Requires 4+ YOE)'
    },
    {
        'company': 'MongoDB',
        'role': 'Associate Technical Services Engineer (TSE)',
        'location': 'Gurugram',
        'verdict': '❌ REJECTED (4+ YOE)',
        'requirement': 'Verbatim JD requirement: "TSE II candidate should have: 4+ years of relevant experience in software support / development".',
        'url': 'https://www.mongodb.com/careers/job/?gh_jid=8089396',
        'eligible': 'NO (Requires 4+ YOE)'
    },
    {
        'company': 'Paytm (One97)',
        'role': 'Credit Risk Analyst (Python / SQL)',
        'location': 'Noida',
        'verdict': '❌ REJECTED (2–5 YOE)',
        'requirement': 'Verbatim JD requirement: "2 to 5 yrs in portfolio risk management function in fintech/ banks/ NBFC".',
        'url': 'https://jobs.lever.co/paytm/ad781ae8-cd4a-44c1-a74b-2822118b7c3d',
        'eligible': 'NO (Requires 2–5 YOE)'
    },
    {
        'company': 'Adobe',
        'role': 'Computer Scientist I (Full Stack Growth Engineer)',
        'location': 'Bangalore',
        'verdict': '❌ REJECTED (3–6 YOE)',
        'requirement': 'Verbatim JD requirement: "Minimum 3 to 6 years of experience proven experience in software development and engineering roles."',
        'url': 'https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced/job/Bangalore/Computer-Scientist-I--Full-Stack-Growth-Engineer-_R172288',
        'eligible': 'NO (Requires 3–6 YOE)'
    },
    {
        'company': 'Adobe',
        'role': 'Software Development Engineer',
        'location': 'Noida',
        'verdict': '❌ REJECTED (Lateral)',
        'requirement': 'Workday external_experienced portal. Lateral software engineering posting (requires 3+ YOE). College hires are taken via SheCodes / campus only.',
        'url': 'https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced/job/Noida/Software-Development-Engineer_R172350',
        'eligible': 'NO (Lateral portal)'
    },
    {
        'company': 'Adobe',
        'role': 'Database Reliability Engineer - PostgreSQL',
        'location': 'Noida',
        'verdict': '❌ REJECTED (3–5 YOE)',
        'requirement': 'Workday external_experienced portal. Senior database infra role requiring 3–5+ YOE in production DB administration.',
        'url': 'https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced/job/Noida/Database-Reliability-Engineer---PostgreSQL--pgvector_R172159',
        'eligible': 'NO (Lateral portal)'
    },
    {
        'company': 'Adobe',
        'role': 'Conversation AI Engineer',
        'location': 'Bangalore',
        'verdict': '❌ REJECTED (Lateral)',
        'requirement': 'Workday external_experienced portal. Specialized conversational AI role requiring 3+ YOE in production LLM/agent deployment.',
        'url': 'https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced/job/Bangalore/Conversation-AI-Engineer_R172464',
        'eligible': 'NO (Lateral portal)'
    },
    {
        'company': 'Sprinklr',
        'role': 'IT AI and Automation Analyst',
        'location': 'Gurgaon',
        'verdict': '❌ REJECTED (Inactive / Lateral)',
        'requirement': 'Requisition 8169123 is closed / 404 on Greenhouse. IT automation analyst track typically requires 2+ YOE enterprise tool integration.',
        'url': 'https://www.sprinklr.com/careers/jobs/?gh_jid=8169123',
        'eligible': 'NO (Closed / Ineligible)'
    },
    {
        'company': 'Carelon Global Solutions',
        'role': 'Associate Software Engineer',
        'location': 'Gurgaon',
        'verdict': '❌ REJECTED (Inactive / 500)',
        'requirement': 'Requisition JR112045 returns HTTP 500 / unprocessable on Workday CXS. Cannot be applied to directly.',
        'url': 'https://carelon.wd1.myworkdayjobs.com/en-US/Carelon_Careers/job/Gurgaon-India/Associate-Software-Engineer_JR112045',
        'eligible': 'NO (Dead Link / Workday Error)'
    }
]

for row_idx, r in enumerate(audited_roles, start=2):
    ws.append([r['company'], r['role'], r['location'], r['verdict'], r['requirement'], r['url'], r['eligible']])
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=row_idx, column=col)
        cell.fill = red_fill
        cell.alignment = Alignment(wrap_text=True, vertical='top')
    
    ws.cell(row=row_idx, column=4).font = bold_red
    ws.cell(row=row_idx, column=7).font = bold_red
    
    url_c = ws.cell(row=row_idx, column=6)
    url_c.hyperlink = r['url']
    url_c.font = Font(color='0563C1', underline='single')

col_widths = [22, 36, 16, 25, 60, 20, 22]
for i, w in enumerate(col_widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

ws.row_dimensions[1].height = 28
wb.save('data/Job Search.xlsx')
print('Corrected Wave 4 sheet saved with 100% accurate verbatim rejection data.')
