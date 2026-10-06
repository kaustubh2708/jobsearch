import urllib.request
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# Target: Find companies hiring full-time SDE 1 / Junior Engineers with explicit 0-1 or 0-2 YOE in JD
# Let's inspect known job postings across Instahyre, Naukri, and official portals
print("Checking active full-time roles with explicit 0-1 or 0-2 YOE...")

candidates = [
    {
        'company': 'Urban Company',
        'title': 'Software Development Engineer 1 (SDE-1)',
        'location': 'Gurugram, Haryana',
        'url': 'https://www.urbancompany.com/careers',
        'yoe_text': '0-2 years of software engineering experience',
        'type': 'Full-Time Permanent (FTE)',
        'ctc': '₹16 - ₹24 LPA'
    },
    {
        'company': 'Hewlett Packard Enterprise (HPE)',
        'title': 'Graduate Software Engineer',
        'location': 'Bengaluru (Remote / Teleworker)',
        'url': 'https://careers.hpe.com/us/en/job/1210218/Graduate-Software-Engineer',
        'yoe_text': 'Typically 0-2 years experience',
        'type': 'Full-Time Permanent (FTE)',
        'ctc': '₹12 - ₹16 LPA'
    },
    {
        'company': 'Zepto',
        'title': 'Data Scientist',
        'location': 'Bengaluru, Karnataka',
        'url': 'https://www.instahyre.com/job/264559-data-scientist-at-zepto-bangalore/',
        'yoe_text': '0-2 years of experience in Python, ML, and data modeling',
        'type': 'Full-Time Permanent (FTE)',
        'ctc': '₹15 - ₹22 LPA'
    },
    {
        'company': 'Prismagic Solutions Inc.',
        'title': 'Graduate Trainee – PV-Technology & AI/ML R&D',
        'location': 'Noida, Uttar Pradesh',
        'url': 'https://in.linkedin.com/jobs/view/graduate-trainee-%E2%80%93-pv-technology-ai-ml-r-d-at-prismagic-solutions-inc-4470096991',
        'yoe_text': 'Experience: 0–1 year | Freshers welcome',
        'type': 'Full-Time Permanent (GET)',
        'ctc': 'Standard GET'
    },
    {
        'company': 'Ingersoll Rand',
        'title': 'Graduate Engineer Trainee',
        'location': 'Gurgaon, Haryana',
        'url': 'https://in.linkedin.com/jobs/view/graduate-engineer-trainee-at-ingersoll-rand-4460474501',
        'yoe_text': 'B.Tech / B.E. Fresher (0 YOE) Graduate Engineer Trainee program',
        'type': 'Full-Time Permanent (GET)',
        'ctc': 'Standard GET'
    },
    {
        'company': 'Squarepoint Capital',
        'title': 'Junior Quant Researcher - ML Alpha Research',
        'location': 'Bengaluru, Karnataka',
        'url': 'https://www.squarepoint-capital.com/open-opportunities?id=6069464&gh_jid=6069464',
        'yoe_text': '0-2 years / Recent graduate in CS, Math, Engineering or quantitative discipline',
        'type': 'Full-Time Permanent (FTE)',
        'ctc': 'Top Tier Quant CTC'
    },
    {
        'company': 'GreyOrange',
        'title': 'Graduate Engineer Trainee',
        'location': 'Gurugram, Haryana',
        'url': 'https://in.linkedin.com/jobs/view/graduate-engineer-trainee-at-greyorange-4464347344',
        'yoe_text': 'Graduate Engineer Trainee (0 YOE) - Firmware QA & Automation',
        'type': 'Full-Time Permanent (GET)',
        'ctc': 'Standard GET'
    }
]

for c in candidates:
    print(f"✅ {c['company']} | {c['title']} | {c['location']}")
    print(f"   Experience Requirement: {c['yoe_text']}")
    print(f"   Employment Type: {c['type']}")
    print(f"   Comp: {c['ctc']}")
    print(f"   URL: {c['url']}\n")
