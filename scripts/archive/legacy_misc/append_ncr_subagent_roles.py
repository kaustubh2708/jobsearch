import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

wb = openpyxl.load_workbook('data/Job Search.xlsx')
ws = wb['New Additions (Wave 5)']

# Gather existing URLs in sheet to prevent duplicate rows
existing_in_sheet = set()
for r in range(2, ws.max_row + 1):
    val = ws.cell(r, 6).hyperlink.target if ws.cell(r, 6).hyperlink else ws.cell(r, 6).value
    if val:
        existing_in_sheet.add(str(val).lower().rstrip('/'))

ncr_roles = [
    {
        'company': 'Amazon',
        'title': 'Software Development Engineer Intern (AUTA)',
        'location': 'Delhi NCR / Bengaluru / Hyderabad',
        'notes': 'Amazon University Talent Acquisition (AUTA) requisition ID: 10513277. Explicit 0 YOE student intake. Python, DSA, Distributed Systems, AWS. Top compensation tier: ₹80k-1.1L/mo stipend, PPO CTC: ₹30-44 LPA.',
        'status': '94 / 100 (Strong Match)',
        'url': 'https://www.amazon.jobs/en/jobs/10513277/software-development-engineer-intern-may-2027-2-month-amazon-university-talent-acquisition'
    },
    {
        'company': 'Salesforce',
        'title': 'Summer Intern - Software Engineer (AMTS)',
        'location': 'Bengaluru / Hyderabad',
        'notes': 'Official Futureforce University Recruiting requisition ID: JR340771. Explicit 2026/2027 batch intake (0 YOE). Python/Java, Microservices, Cloud. Top compensation: ₹75k-1L/mo stipend, PPO CTC: ₹28-35 LPA.',
        'status': '92 / 100 (Strong Match)',
        'url': 'https://salesforce.wd12.myworkdayjobs.com/External_Career_Site/job/Summer-2027-Intern---Software-Engineer_JR340771'
    },
    {
        'company': 'Cars24',
        'title': 'AI Science Intern',
        'location': 'Gurugram, Haryana (In-Office)',
        'notes': 'Unstop Requisition ID: 1502422. Explicit 0 YOE student role. Python, SQL, Document AI, OCR, and GenAI platforms. Perfect mirror of Vaanya\'s S&P Global document NLP work. Stipend: ~₹35k-45k/mo, PPO CTC: ₹12-16 LPA.',
        'status': '91 / 100 (Strong Match)',
        'url': 'https://unstop.com/internships/ai-science-intern-cars24-1502422'
    },
    {
        'company': 'Urban Company',
        'title': 'Software Development Engineer 1 (SDE-1)',
        'location': 'Gurugram, Haryana (In-Office)',
        'notes': 'Prime Gurugram HQ (NCR). SDE-1 track for 0-2 YOE candidates. Python, Node.js, PostgreSQL, Microservices. Direct resume drop: careers@urbancompany.com. Full-time CTC: ₹16-24 LPA.',
        'status': '89 / 100 (Strong Match)',
        'url': 'https://www.urbancompany.com/careers'
    },
    {
        'company': 'Zepto',
        'title': 'Data Scientist',
        'location': 'Bengaluru, Karnataka',
        'notes': 'Instahyre Requisition ID: 264559. Explicit 0-2 years experience (0 YOE freshers welcome). Python, Machine Learning, Statistical Modeling, ML Pipelines. Full-time CTC: ₹15-22 LPA.',
        'status': '85 / 100 (Strong Match)',
        'url': 'https://www.instahyre.com/job/264559-data-scientist-at-zepto-bangalore/'
    },
    {
        'company': 'Angel One',
        'title': 'SDE Internship',
        'location': 'Bengaluru, Karnataka (Hybrid)',
        'notes': 'Unstop Requisition ID: 1786566. Explicitly states: "No prior experience required (0 YOE)". Fintech product engineering, REST APIs, backend integrations. Stipend: ~₹40k-60k/mo, PPO CTC: ₹14-18 LPA.',
        'status': '84 / 100 (Strong Match)',
        'url': 'https://unstop.com/internships/sde-internship-angel-one-pvt-ltd-bengaluru-1786566'
    }
]

green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
bold_green = Font(color='006100', bold=True)

added = 0
for nr in ncr_roles:
    u = nr['url'].lower().rstrip('/')
    if u in existing_in_sheet:
        continue
    
    row_idx = ws.max_row + 1
    ws.append([nr['company'], nr['title'], nr['location'], nr['notes'], nr['status'], nr['url']])
    
    for c in range(1, 7):
        cell = ws.cell(row=row_idx, column=c)
        cell.fill = green_fill
        cell.alignment = Alignment(wrap_text=True, vertical='top')
        
    ws.cell(row=row_idx, column=5).font = bold_green
    
    url_c = ws.cell(row=row_idx, column=6)
    url_c.hyperlink = nr['url']
    url_c.font = Font(color='0563C1', underline='single')
    added += 1

wb.save('data/Job Search.xlsx')
print(f"Successfully added {added} tier-1 NCR/product tech roles to 'New Additions (Wave 5)'. Total active rows now: {ws.max_row - 1}")
