import json
import openpyxl

with open('data/existing_job_links_set.json') as f:
    existing = json.load(f)
existing_urls = set(existing['urls'])

new_additions = [
    {
        "company": "Pitney Bowes",
        "role": "Graduate Engineer Trainee (GET)",
        "url": "https://pitneybowes.wd1.myworkdayjobs.com/en-US/PBCareers/job/Graduate-Engineer-Trainee_R22095",
        "location": "Noida (Sector 142), UP",
        "notes": "Home location in Noida Sector 142 (minutes from her college). Explicit 0 YOE fresher intake for B.Tech ECE/CSE. Python, REST APIs, cloud test automation. Callback: Very High.",
        "match_score": 93,
        "status_label": "93 / 100 (Strong Match)"
    },
    {
        "company": "Level AI",
        "role": "Machine Learning Engineer (NLP / Speech)",
        "url": "https://jobs.ashbyhq.com/level-ai/73fe922e-7a59-477f-b343-4c79db0c9a0c",
        "location": "Noida, UP (Hybrid)",
        "notes": "Noida-based AI unicorn. Direct match for BERT/Transformer architectures, PyTorch, and NLP document processing from S&P Global. Callback: High.",
        "match_score": 92,
        "status_label": "92 / 100 (Strong Match)"
    },
    {
        "company": "Level AI",
        "role": "Backend Engineer - Analytics",
        "url": "https://jobs.ashbyhq.com/level-ai/dfc5b25c-9532-4ebc-896e-40879f16ef21",
        "location": "Noida, UP",
        "notes": "Noida location. High-throughput analytics pipelines. Python, PostgreSQL indexing, and Redis caching. Callback: High.",
        "match_score": 91,
        "status_label": "91 / 100 (Strong Match)"
    },
    {
        "company": "Graviton Research Capital",
        "role": "Software Engineer- Python",
        "url": "https://job-boards.greenhouse.io/gravitonresearchcapital/jobs/8147013002",
        "location": "Gurugram, HR",
        "notes": "Gurgaon HQ. Top quant firm hiring Python engineers for quantitative execution pipelines. Rare dedicated Python role in HFT. High pay (₹40L+ base). Callback: Medium-High.",
        "match_score": 92,
        "status_label": "92 / 100 (Strong Match)"
    },
    {
        "company": "Atlys",
        "role": "Backend Engineer",
        "url": "https://jobs.ashbyhq.com/atlys/a2158e46-0991-4235-aeec-758b1832c5fb",
        "location": "Delhi HQ",
        "notes": "Delhi/NCR HQ. YC-backed travel-tech unicorn. Python, FastAPI, microservices, asynchronous queues. Direct engineering team review. Callback: Very High.",
        "match_score": 91,
        "status_label": "91 / 100 (Strong Match)"
    },
    {
        "company": "Sarvam AI",
        "role": "Embedded Data Scientist, Chanakya",
        "url": "https://jobs.ashbyhq.com/sarvam/dc047f4f-97be-4bb3-a9f1-cebbfc4de3e6",
        "location": "New Delhi / NCR",
        "notes": "Delhi NCR location. Sovereign AI lab. Document & unstructured data modeling pipelines, NLP, Pandas/NumPy. Capitalizes on ex-S&P Global BERT pipeline work. Callback: High.",
        "match_score": 90,
        "status_label": "90 / 100 (Strong Match)"
    },
    {
        "company": "AiPrise",
        "role": "Software Engineer I",
        "url": "https://jobs.ashbyhq.com/aiprise/3763c791-a387-4078-9ca4-00cbfbf9b1a6",
        "location": "Bengaluru (Remote-friendly)",
        "notes": "YC-backed compliance orchestration platform. 0-2 YOE opening. Python, PostgreSQL, microservices, Docker. 100% stack match. Callback: High.",
        "match_score": 90,
        "status_label": "90 / 100 (Strong Match)"
    },
    {
        "company": "Sarvam AI",
        "role": "Backend Engineer - Studio Media Platform",
        "url": "https://jobs.ashbyhq.com/sarvam/b07dfd8a-208d-43c1-a811-f1c447df26f9",
        "location": "Bengaluru",
        "notes": "Rare direct match for Celery distributed task queues, FastAPI, and ML model serving (PyTorch). Exact match with Vaanya's production resume stack. Callback: Medium-High.",
        "match_score": 89,
        "status_label": "89 / 100 (Strong Match)"
    },
    {
        "company": "Sarvam AI",
        "role": "Agent Engineer",
        "url": "https://jobs.ashbyhq.com/sarvam/36f89b00-2010-4d23-aae3-17a2f53d9eaa",
        "location": "Bengaluru",
        "notes": "Automated LLM workflows and AI agents in Python. Matches dual background in backend architecture and modern NLP/Transformers. Callback: Medium-High.",
        "match_score": 88,
        "status_label": "88 / 100 (Strong Match)"
    },
    {
        "company": "Hewlett Packard Enterprise (HPE)",
        "role": "Graduate Software Engineer",
        "url": "https://hpe.wd5.myworkdayjobs.com/en-US/Jobsathpe/job/Bengaluru-Karntaka-India/Graduate-Software-Engineer_1210218-2",
        "location": "Bengaluru (Remote / Teleworker)",
        "notes": "Official Graduate Engineer requisition open to 2026 batch freshers. Designated full teleworker/remote in India. Python/Java, systems design, testing. Callback: High.",
        "match_score": 88,
        "status_label": "88 / 100 (Strong Match)"
    },
    {
        "company": "Boeing (BIETC)",
        "role": "Associate Software Engineer",
        "url": "https://boeing.wd1.myworkdayjobs.com/en-US/EXTERNAL_CAREERS/job/Associate-Software-Engineer_JR2026517817-1",
        "location": "Bengaluru (Hybrid)",
        "notes": "BIETC global tech hub entry-level Associate Engineer requisition on Workday. B.Tech ECE/CSE freshers welcome. Python, C++, cloud services. Callback: Medium-High.",
        "match_score": 87,
        "status_label": "87 / 100 (Strong Match)"
    },
    {
        "company": "Forma.ai",
        "role": "Analytics Engineer Intern",
        "url": "https://job-boards.greenhouse.io/formaaiinc3/jobs/4235664005",
        "location": "Pune (Hybrid)",
        "notes": "Dedicated 2026 intern opening. Automated ETL/ELT pipelines, Python, SQL, Pandas. Direct mirror of S&P Global and KPMG data advisory pipelines. Callback: High.",
        "match_score": 87,
        "status_label": "87 / 100 (Strong Match)"
    },
    {
        "company": "Automation Anywhere",
        "role": "Software Engineering Intern",
        "url": "https://automationanywhere.wd5.myworkdayjobs.com/en-US/AutomationAnywhereJobs/job/Bengaluru-India/Software-Engineering-Intern_JR1504",
        "location": "Bengaluru",
        "notes": "6-month intern-to-hire opportunity for 2026 batch. Python, AI agents, automation pipelines, microservices. Callback: High.",
        "match_score": 86,
        "status_label": "86 / 100 (Strong Match)"
    },
    {
        "company": "Paytm (One97)",
        "role": "Risk Analyst (Data & Technology)",
        "url": "https://jobs.lever.co/paytm/beb24813-6250-46c4-b8af-63aae1f2bbe6",
        "location": "Noida / Bengaluru",
        "notes": "Noida HQ. 0-2 YOE opening. Python, SQL, PostgreSQL, quantitative analytics. Levers S&P Global and KPMG background. Callback: Very High.",
        "match_score": 86,
        "status_label": "86 / 100 (Strong Match)"
    },
    {
        "company": "Atlan",
        "role": "Associate Technical Specialist",
        "url": "https://jobs.ashbyhq.com/atlan/107864a1-7090-4a0c-9cd5-a1c6478ff2b2",
        "location": "Delhi NCR / Remote",
        "notes": "Founded in Delhi NCR. Modern data catalog category leader. Python, SQL, metadata APIs, data pipeline integration. Callback: High.",
        "match_score": 85,
        "status_label": "85 / 100 (Strong Match)"
    },
    {
        "company": "Avoca",
        "role": "Software Engineer (Product)",
        "url": "https://jobs.ashbyhq.com/avoca/ec05c135-ab26-437a-8fe9-f7a5c4da08e5",
        "location": "Bengaluru",
        "notes": "Voice AI agent startup. Python, REST APIs, PostgreSQL, LLMs. Fast-moving engineering team reviewing developer portfolios. Callback: High.",
        "match_score": 85,
        "status_label": "85 / 100 (Strong Match)"
    },
    {
        "company": "IQVIA",
        "role": "Intern (Software & Data Engineering)",
        "url": "https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Intern_R1567860",
        "location": "Bengaluru / Kochi",
        "notes": "Healthcare data analytics leader. Python, SQL, data pipelines, REST APIs. Structured 2026 student internship track. Callback: High.",
        "match_score": 84,
        "status_label": "84 / 100 (Strong Match)"
    },
    {
        "company": "insightsoftware",
        "role": "Associate Software Engineer",
        "url": "https://magnitudesoftware.wd1.myworkdayjobs.com/en-US/External/job/Associate-Software-Engineer_REQ001103-1",
        "location": "Hyderabad / Bengaluru",
        "notes": "0-1 YOE opening for fresh college graduates. High-throughput data connectivity, relational DBs, SQL, Python/Java. Callback: Medium-High.",
        "match_score": 83,
        "status_label": "83 / 100 (Potential Match)"
    },
    {
        "company": "Point72",
        "role": "Database Support / Data Platform Associate",
        "url": "https://boards.greenhouse.io/point72/jobs/8488671002",
        "location": "Bengaluru",
        "notes": "Elite global hedge fund tech division. SQL, PostgreSQL, Python scripting, ETL reliability. High compensation. Callback: Medium.",
        "match_score": 83,
        "status_label": "83 / 100 (Potential Match)"
    },
    {
        "company": "Graviton Research Capital",
        "role": "Software Engineer (C++)",
        "url": "https://job-boards.greenhouse.io/gravitonresearchcapital/jobs/4004920002",
        "location": "Gurugram, HR",
        "notes": "Gurgaon HQ. Low-latency trading systems. Modern C++, algorithms, OS fundamentals. Top tier comp (₹45L+). Selective test. Callback: Medium.",
        "match_score": 82,
        "status_label": "82 / 100 (Potential Match)"
    }
]

# Verify against existing URLs
filtered_additions = []
for item in new_additions:
    u = item['url'].lower().rstrip('/')
    if u not in existing_urls:
        filtered_additions.append(item)

print(f'Total new verified unique additions: {len(filtered_additions)}')

with open('data/verified_new_sheet_additions.json', 'w') as f:
    json.dump(filtered_additions, f, indent=2)

# Also create an updated excel sheet or append sheet
wb = openpyxl.load_workbook('data/Job Search.xlsx')
if 'New Additions (Wave 3)' in wb.sheetnames:
    del wb['New Additions (Wave 3)']
ws = wb.create_sheet('New Additions (Wave 3)')

headers = ['Company', 'Role Title', 'Location', 'Notes', 'Status']
ws.append(headers)

for item in filtered_additions:
    row_vals = [
        item['company'],
        item['role'],
        item['location'],
        item['notes'],
        item['status_label']
    ]
    ws.append(row_vals)
    # Add hyperlink to Role Title
    cell = ws.cell(row=ws.max_row, column=2)
    cell.hyperlink = item['url']
    cell.style = "Hyperlink"

wb.save('data/Job Search.xlsx')
print('Successfully appended new sheet [New Additions (Wave 3)] to data/Job Search.xlsx!')
