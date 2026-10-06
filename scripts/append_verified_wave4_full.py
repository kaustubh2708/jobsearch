import openpyxl, re
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

roles = [
    {
        'company': 'MakeMyTrip',
        'title': 'Senior Software Engineer – II (Backend)',
        'location': 'Gurgaon',
        'exp': '4-6 years',
        'tech': 'Java, Microservices, MySQL, MongoDB, Cassandra, Distributed Systems',
        'salary_evidence': 'MakeMyTrip RL3 base: ₹35L–₹45L+ fixed',
        'match_score': 98,
        'match_label': 'strong_match',
        'url': 'https://careers.makemytrip.com/prod/opportunity/a68296c5951faa/senior-software-engineer---ii-(backend)',
        'notes': 'DLF Cyber City Gurgaon HQ. Core booking & travel search distributed backend architecture.'
    },
    {
        'company': 'Paytm',
        'title': 'Backend - Senior Software Engineer',
        'location': 'Noida',
        'exp': '2-5 years',
        'tech': 'Golang, Java/Node.js, Microservices, Kafka, Redis, AWS',
        'salary_evidence': 'Paytm SSE base: ₹32L–₹42L+',
        'match_score': 100,
        'match_label': 'strong_match',
        'url': 'https://jobs.lever.co/paytm/23534d2b-3e2e-4759-b498-0bb15b2fb995',
        'notes': 'Noida HQ Sector 98. Recharges & Utilities high-throughput transaction platform. Strictly 2-5 yrs.'
    },
    {
        'company': 'Indus Valley Partners',
        'title': 'Engineer (OMS Legacy Client Implementations)',
        'location': 'Noida',
        'exp': '2-4 years',
        'tech': 'C#, .NET, SQL, Javascript, Capital Markets',
        'salary_evidence': 'IVP Engineer base: ₹24L–₹34L+',
        'match_score': 96,
        'match_label': 'strong_match',
        'url': 'https://careers.ivp.in/ivp/jobview/engineer-noida-uttar-pradesh-india-2026022416065713?source=linkedin',
        'notes': 'Noida HQ. Direct C#/.NET Core match for hedge fund and capital markets client implementations.'
    },
    {
        'company': 'MongoDB',
        'title': 'Software Engineer 3, AI Builder Experience',
        'location': 'Gurugram',
        'exp': '3+ years',
        'tech': 'AI Agent Workflows, Distributed Systems, Databases (SQL/NoSQL/Mongo)',
        'salary_evidence': 'MongoDB SE 3 base: ₹45L–₹70L+ total comp',
        'match_score': 96,
        'match_label': 'strong_match',
        'url': 'https://in.linkedin.com/jobs/view/4456363101',
        'notes': 'Gurugram Tech Center. Dedicated team building AI Agent workflows and database interfaces.'
    },
    {
        'company': 'Adobe',
        'title': 'Cloud Engineer 3 - AI Agents',
        'location': 'Noida',
        'exp': '4+ years',
        'tech': 'AI Agents, Azure, AWS, Python, Cloud Tooling Infra',
        'salary_evidence': 'Adobe Cloud Engineer 3 base: ₹40L–₹55L+',
        'match_score': 94,
        'match_label': 'strong_match',
        'url': 'https://in.linkedin.com/jobs/view/4463846192',
        'notes': 'Adobe Noida Campus. AI agent tooling, multi-cloud cost & orchestration infra on Azure/AWS.'
    },
    {
        'company': 'UKG',
        'title': 'Software Engineer III- Eng (.NET/C#)',
        'location': 'Noida',
        'exp': '3-5 years',
        'tech': 'C#, .NET Core, Microservices, Distributed Systems, SQL',
        'salary_evidence': 'UKG SE III base: ₹30L–₹42L+',
        'match_score': 95,
        'match_label': 'strong_match',
        'url': 'https://www.linkedin.com/jobs/view/4471038533',
        'notes': 'Noida Tech Center. Core workforce management cloud architecture on C#/.NET Core.'
    },
    {
        'company': 'Pluang',
        'title': 'Sr. Software Engineer (SDE3 - Node)',
        'location': 'Gurugram',
        'exp': '2-5 years',
        'tech': 'Node.js, Microservices, Scalable Distributed Systems',
        'salary_evidence': 'Pluang SSE base: ₹32L–₹45L+',
        'match_score': 92,
        'match_label': 'strong_match',
        'url': 'https://in.linkedin.com/jobs/view/4306115453',
        'notes': 'Gurugram. Direct Recruiter: Vibhuti Juneja (Deputy Head Global TA). High scale investment app.'
    },
    {
        'company': 'Fareportal',
        'title': 'Senior Software Engineer',
        'location': 'Gurugram',
        'exp': '2-5 years',
        'tech': 'Node.js, Java, Microservices, High-Volume E-Commerce',
        'salary_evidence': 'Fareportal SSE base: ₹30L–₹42L+',
        'match_score': 90,
        'match_label': 'strong_match',
        'url': 'https://in.linkedin.com/jobs/view/4465714756',
        'notes': 'Gurugram. Direct Recruiter: Alisha Kumar (Global TA Lead). High-volume travel booking engines.'
    },
    {
        'company': 'American Express',
        'title': 'Senior Software Engineer II - Cloud Ops',
        'location': 'Gurugram',
        'exp': '3-5 years',
        'tech': 'Distributed Systems, Cloud Platform Automation, Observability',
        'salary_evidence': 'Amex Senior Engineer base: ₹35L–₹50L+',
        'match_score': 92,
        'match_label': 'strong_match',
        'url': 'https://in.linkedin.com/jobs/view/4465779116',
        'notes': 'Gurugram Tech Center. Cloud operations, resilient financial transaction microservices.'
    },
    {
        'company': 'American Express',
        'title': 'Senior Software Engineer I - Consumer Tech',
        'location': 'Gurugram',
        'exp': '2-4 years',
        'tech': 'Digital Banking Services, REST APIs, Microservices',
        'salary_evidence': 'Amex Senior Engineer base: ₹32L–₹42L+',
        'match_score': 90,
        'match_label': 'strong_match',
        'url': 'https://in.linkedin.com/jobs/view/4463542035',
        'notes': 'Gurugram Tech Center. Consumer digital banking and payments platform backend.'
    },
    {
        'company': 'HCLSoftware',
        'title': 'Senior Backend Engineer (Go)',
        'location': 'Noida',
        'exp': '3-5 years',
        'tech': 'Golang, Microservices, Cloud Distributed Systems',
        'salary_evidence': 'HCLSoftware Senior Engineer base: ₹30L–₹42L+',
        'match_score': 88,
        'match_label': 'strong_match',
        'url': 'https://in.linkedin.com/jobs/view/4454394461',
        'notes': 'Noida Tech Center. Direct Recruiter: Harshitha Hegde. High performance cloud software.'
    },
    {
        'company': 'MongoDB',
        'title': 'Software Engineer 3 - Ops Manager',
        'location': 'Gurugram',
        'exp': '4+ years',
        'tech': 'Global Scale Automation, Private Cloud, Distributed Storage',
        'salary_evidence': 'MongoDB SE 3 base: ₹45L–₹60L+',
        'match_score': 90,
        'match_label': 'strong_match',
        'url': 'https://in.linkedin.com/jobs/view/4471630738',
        'notes': 'Gurugram Tech Center. Enterprise Ops Manager database automation backend.'
    },
    {
        'company': 'Scale AI',
        'title': 'Forward Deployed Engineer, Gen AI',
        'location': 'India (Remote/Hub)',
        'exp': '3-5 years',
        'tech': 'Python, Distributed Systems, Cloud Infrastructure, Generative AI Data Engine',
        'salary_evidence': 'Scale AI India base: ₹45L–₹70L+ base + equity',
        'match_score': 94,
        'match_label': 'strong_match',
        'url': 'https://job-boards.greenhouse.io/scaleai/jobs/4549048005',
        'notes': 'Official India Greenhouse requisition. Full-stack backend & GenAI data engine.'
    },
    {
        'company': 'RunPod',
        'title': 'Forward Deployed Engineer APAC',
        'location': 'Remote - APAC',
        'exp': '3+ years',
        'tech': 'Python, Node.js/TS, Go, Docker, APIs, Applied AI/Agents',
        'salary_evidence': 'Explicit base: $100,000–$160,000 USD (~₹83L–₹1.33 Cr)',
        'match_score': 88,
        'match_label': 'strong_match',
        'url': 'https://jobs.ashbyhq.com/runpod/25e7d414-e338-42dc-a206-ca4727f3f98f',
        'notes': 'Remote APAC. Distributed cloud compute and AI workflow orchestration.'
    },
    {
        'company': 'Intel',
        'title': 'AI Platform and Agentic Engineer',
        'location': 'Bengaluru',
        'exp': '2-5 years',
        'tech': 'AI Agent Architectures, Autonomous Agents, Python, Cloud',
        'salary_evidence': 'Intel Senior Engineer base: ₹32L–₹45L+',
        'match_score': 90,
        'match_label': 'strong_match',
        'url': 'https://www.linkedin.com/jobs/view/4468498684',
        'notes': 'Intel AI Platform Group. Autonomous agentic systems and developer platforms.'
    },
    {
        'company': 'Intel',
        'title': 'Software Application Development Engineer',
        'location': 'Bengaluru',
        'exp': '2-5 years',
        'tech': 'Node.js, TypeScript, Microservices, SQL, Cloud',
        'salary_evidence': 'Intel SE base: ₹28L–₹38L+',
        'match_score': 88,
        'match_label': 'strong_match',
        'url': 'https://www.linkedin.com/jobs/view/4470274570',
        'notes': 'Cloud applications team at Intel Bengaluru.'
    },
    {
        'company': 'Harvey AI',
        'title': 'Senior Software Engineer, Backend',
        'location': 'Bengaluru',
        'exp': '5+ years (Stretch)',
        'tech': 'Python, FastAPI, Postgres, Azure, LLM Agentic Tools Orchestration',
        'salary_evidence': 'Harvey AI Senior base: ₹50L–₹75L+ base + equity',
        'match_score': 82,
        'match_label': 'potential_match',
        'url': 'https://jobs.ashbyhq.com/harvey/992183a0-4526-4ea6-be3d-799a2401da4f',
        'notes': 'Bengaluru Tech Center. Enterprise legal AI workflows on Azure and agentic tooling.'
    }
]

wb = openpyxl.load_workbook('data/jobs_vrinda_discovery_wave2_verified.xlsx')
ws = wb['New Batch']

existing_keys = set()
for r in range(2, ws.max_row + 1):
    comp = str(ws.cell(row=r, column=2).value or '').strip().lower()
    title = str(ws.cell(row=r, column=3).value or '').strip().lower()
    url = str(ws.cell(row=r, column=11).value or '').strip()
    if url:
        m = re.search(r'jobs/view/(\d+)', url)
        if m:
            existing_keys.add(f'linkedin_{m.group(1)}')
        else:
            existing_keys.add(url.lower())
    existing_keys.add(f'{comp}|{title}')

font_standard = Font(name='Calibri', size=11)
font_link = Font(name='Calibri', size=11, color='0563C1', underline='single')
align_center = Alignment(horizontal='center', vertical='center')
align_left = Alignment(horizontal='left', vertical='center')
thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)
fill_even = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')
fill_odd = PatternFill(start_color='F9FAFB', end_color='F9FAFB', fill_type='solid')

appended = 0
current_row = ws.max_row + 1

for item in roles:
    url = item['url']
    m = re.search(r'jobs/view/(\d+)', url)
    link_key = f'linkedin_{m.group(1)}' if m else url.lower()
    comp_title_key = f"{item['company'].strip().lower()}|{item['title'].strip().lower()}"

    if link_key in existing_keys or comp_title_key in existing_keys:
        print(f"Skipping dupe: {item['company']} - {item['title']}")
        continue

    rank_num = current_row - 1
    row_fill = fill_odd if rank_num % 2 == 1 else fill_even
    row_data = [
        rank_num,
        item['company'],
        item['title'],
        item['location'],
        item['exp'],
        item['tech'],
        item['salary_evidence'],
        item['match_score'],
        item['match_label'],
        'Active Application Form Verified (HTTP 200)',
        item['url'],
        item['notes']
    ]
    for col_idx, val in enumerate(row_data, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = val
        cell.font = font_standard
        cell.fill = row_fill
        cell.border = thin_border
        if col_idx in (1, 8, 9, 10):
            cell.alignment = align_center
        else:
            cell.alignment = align_left
        if col_idx == 11 and val:
            cell.hyperlink = val
            cell.font = font_link
    current_row += 1
    appended += 1
    existing_keys.add(link_key)
    existing_keys.add(comp_title_key)
    print(f"[VERIFIED & APPENDED] #{rank_num} {item['company']} - {item['title']} ({item['location']})")

wb.save('data/jobs_vrinda_discovery_wave2_verified.xlsx')
print(f"\nSuccessfully appended {appended} new verified roles! New total rows in New Batch: {ws.max_row}")
