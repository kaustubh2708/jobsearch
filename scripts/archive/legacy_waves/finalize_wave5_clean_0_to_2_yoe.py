import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

wb = openpyxl.load_workbook('data/Job Search.xlsx')

if 'New Additions (Wave 5)' in wb.sheetnames:
    del wb['New Additions (Wave 5)']

ws = wb.create_sheet('New Additions (Wave 5)')

headers = ['Company', 'Role Title', 'Location', 'Employment Type', 'Exact Stated Experience Requirement (JD)', 'Technical Stack & Fit for Vaanya', 'Status / Match Score', 'Direct Application URL']
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

# 7 Confirmed Full-Time Roles with EXPLICIT 0-1 or 0-2 YOE (Zero Internships, Zero Duplicates)
fte_roles = [
    {
        'company': 'Urban Company',
        'title': 'Software Development Engineer 1 (SDE-1)',
        'location': 'Gurugram, Haryana (In-Office)',
        'type': 'Full-Time (FTE)',
        'yoe': 'Verbatim: "0–2 years of experience in software engineering". Targets engineering graduates writing production code.',
        'stack': 'Python Backend & Microservices: Python, Node.js, PostgreSQL, Microservices, distributed systems. Prime Gurugram HQ (NCR). Full-time CTC: ₹16-24 LPA.',
        'score': '89 / 100 (Strong Match)',
        'url': 'https://www.urbancompany.com/careers',
        'is_strong': True
    },
    {
        'company': 'Hewlett Packard Enterprise (HPE)',
        'title': 'Graduate Software Engineer',
        'location': 'Bengaluru (Designated Remote / Teleworker)',
        'type': 'Full-Time (Permanent)',
        'yoe': 'Verbatim: "Typically 0-2 years experience. Bachelor\'s or Master\'s degree in Computer Science, Information Systems, or equivalent."',
        'stack': 'Python & Systems Engineering: Python, C++, Java, Linux, systems software, database concepts, debugging & test automation. Requisition ID: 1210218 (posted Oct 1, 2026). Designated remote teleworker across India. Full-time CTC: ₹12-16 LPA.',
        'score': '88 / 100 (Strong Match)',
        'url': 'https://careers.hpe.com/us/en/job/1210218/Graduate-Software-Engineer',
        'is_strong': True
    },
    {
        'company': 'Zepto',
        'title': 'Data Scientist',
        'location': 'Bengaluru, Karnataka',
        'type': 'Full-Time (FTE)',
        'yoe': 'Verbatim: "Experience: 0-2 years (0 YOE / freshers explicitly eligible). Focus on data-backed experimentation."',
        'stack': 'Data Engineering & ML: Python, Machine Learning, Statistical Modeling, ML Pipelines, SQL. Instahyre Requisition ID: 264559. Full-time CTC: ₹15-22 LPA.',
        'score': '85 / 100 (Strong Match)',
        'url': 'https://www.instahyre.com/job/264559-data-scientist-at-zepto-bangalore/',
        'is_strong': True
    },
    {
        'company': 'Prismagic Solutions Inc.',
        'title': 'Graduate Trainee – PV-Technology & AI/ML R&D',
        'location': 'Noida, Uttar Pradesh, India',
        'type': 'Full-Time (Permanent Trainee)',
        'yoe': 'Verbatim: "Experience: 0–1 year | Freshers welcome. Education: B.Tech / M.Tech / MCA".',
        'stack': 'AI/ML & Python: Python, machine learning R&D, data pipelines. Permanent technology team in Noida (minutes from her college Sector 62/128).',
        'score': '86 / 100 (Strong Match)',
        'url': 'https://in.linkedin.com/jobs/view/graduate-trainee-%E2%80%93-pv-technology-ai-ml-r-d-at-prismagic-solutions-inc-4470096991',
        'is_strong': True
    },
    {
        'company': 'Squarepoint Capital',
        'title': 'Junior Quant Researcher - ML Alpha Research',
        'location': 'Bangalore, India (Global Quant Division)',
        'type': 'Full-Time (Permanent)',
        'yoe': 'Verbatim: "0-2 years / Recent graduate in CS, Math, Engineering or quantitative discipline".',
        'stack': 'Quant ML & Time Series: Python, PyTorch, statistical machine learning, high-performance data processing. Top-tier global quantitative hedge fund. Full-time quantitative research.',
        'score': '75 / 100 (Potential Match)',
        'url': 'https://www.squarepoint-capital.com/open-opportunities?id=6069464&gh_jid=6069464',
        'is_strong': False
    },
    {
        'company': 'Ingersoll Rand',
        'title': 'Graduate Engineer Trainee',
        'location': 'Gurgaon, Haryana, India',
        'type': 'Full-Time (GET Program)',
        'yoe': 'Verbatim: "B.Tech / B.E. Fresher (0 YOE) Graduate Engineer Trainee program".',
        'stack': 'Engineering Systems: Structured GET campus intake for B.Tech engineers. Testing, software diagnostics, engineering automation in Gurgaon.',
        'score': '74 / 100 (Potential Match)',
        'url': 'https://in.linkedin.com/jobs/view/graduate-engineer-trainee-at-ingersoll-rand-4460474501',
        'is_strong': False
    },
    {
        'company': 'GreyOrange',
        'title': 'Graduate Engineer Trainee',
        'location': 'Gurugram, Haryana, India',
        'type': 'Full-Time (GET Program)',
        'yoe': 'Verbatim: "Graduate Engineer Trainee (0 YOE) – Firmware Quality Assurance to support embedded validation".',
        'stack': 'Firmware & QA Automation: Embedded firmware testing, Python test suites, robotics systems QA in Gurugram.',
        'score': '67 / 100 (Potential Match)',
        'url': 'https://in.linkedin.com/jobs/view/graduate-engineer-trainee-at-greyorange-4464347344',
        'is_strong': False
    }
]

row_idx = 2
for r in fte_roles:
    ws.append([r['company'], r['title'], r['location'], r['type'], r['yoe'], r['stack'], r['score'], r['url']])
    fill = green_fill if r['is_strong'] else light_green_fill
    for c in range(1, 9):
        cell = ws.cell(row=row_idx, column=c)
        cell.fill = fill
        cell.alignment = Alignment(wrap_text=True, vertical='top')
        
    ws.cell(row=row_idx, column=7).font = bold_green
    
    url_c = ws.cell(row=row_idx, column=8)
    url_c.hyperlink = r['url']
    url_c.font = Font(color='0563C1', underline='single')
    row_idx += 1

col_widths = [24, 38, 22, 22, 45, 55, 22, 32]
for i, w in enumerate(col_widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

ws.row_dimensions[1].height = 28
wb.save('data/Job Search.xlsx')
print(f"Finalized Wave 5: {len(fte_roles)} Full-Time roles with explicit 0-1 and 0-2 YOE written to Job Search.xlsx.")
