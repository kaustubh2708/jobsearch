import urllib.request, ssl, json, time, re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

print("=== CHECKING ACTIVE UNSTOP / PORTAL HIRING DRIVES ===")

drives_to_verify = [
    {
        'company': 'Juspay',
        'program': 'Juspay Hiring Challenge 2026',
        'url': 'https://unstop.com/competitions/juspay-hiring-challenge',
        'batch': '2026 / 2025 B.Tech'
    },
    {
        'company': 'Flipkart',
        'program': 'Flipkart GRiD 6.0 / 7.0 Tech Track',
        'url': 'https://unstop.com/hackathons/flipkart-grid-60-software-development-track-flipkart-999335',
        'batch': '2026 / 2027 Engineering Students'
    },
    {
        'company': 'Walmart Global Tech',
        'program': 'Walmart CodeHers India',
        'url': 'https://unstop.com/hackathons/walmart-codehers-2024-walmart-global-tech-india-893049',
        'batch': 'Female Engineering Students 2026 Batch'
    },
    {
        'company': 'Tata Consultancy Services',
        'program': 'TCS NQT (National Qualifier Test) 2026',
        'url': 'https://learning.tcsionhub.in/hub/national-qualifier-test/',
        'batch': '2026 / 2025 B.Tech Graduates'
    },
    {
        'company': 'Cognizant',
        'program': 'Cognizant GenC / GenC Next Campus Drive',
        'url': 'https://careers.cognizant.com/global-en/entry-level-jobs/',
        'batch': '2026 Batch Graduates'
    },
    {
        'company': 'Accenture',
        'program': 'Accenture Associate Software Engineer (ASE) National Drive',
        'url': 'https://www.accenture.com/in-en/careers/local/entry-level-jobs',
        'batch': '2026 / 2025 Batch Engineering'
    },
    {
        'company': 'Wipro',
        'program': 'Wipro Elite National Talent Hunt (NTH)',
        'url': 'https://careers.wipro.com/elite',
        'batch': '2026 Batch B.Tech'
    },
    {
        'company': 'Capgemini',
        'program': 'Capgemini Exceller Off-Campus / On-Campus Drive',
        'url': 'https://www.capgemini.com/in-en/careers/entry-level-jobs/',
        'batch': '2026 Batch Engineering'
    }
]

verified_drives = []
for d in drives_to_verify:
    u = d['url']
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            code = resp.status
            if code == 200:
                print(f"  [ACTIVE 200 OK] {d['company']} | {d['program']} | {u}")
                d['status'] = 'Active & Live (HTTP 200)'
                verified_drives.append(d)
            else:
                print(f"  [STATUS {code}] {d['company']} | {u}")
    except Exception as e:
        print(f"  [ERROR] {d['company']} | {e}")
    time.sleep(0.5)

print(f"\nTotal verified live drives: {len(verified_drives)}")
with open('data/verified_active_drives.json', 'w') as f:
    json.dump(verified_drives, f, indent=2)
