import json
import re

with open('data/scratch_wave9_verified_roles.json') as f:
    raw_roles = json.load(f)

# Filter out foreign locations
filtered_roles = []
seen_urls = set()

# Also load existing tracked URLs
with open('data/all_existing_urls.json') as f:
    for u in json.load(f):
        seen_urls.add(u.strip().lower().rstrip('/'))

# Curate and add the ATS verified roles
ats_verified = [
    {
        'company': 'Atlys',
        'title': 'Backend Engineer',
        'location': 'Delhi NCR (Gurugram / Delhi HQ)',
        'domain': 'Backend Engineering & Distributed Systems',
        'experience': 'Foundational engineering role open to 0–1 YOE / fresh engineering graduates with strong DSA.',
        'tech_stack': 'Python, FastAPI, PostgreSQL, Redis, Microservices, AWS',
        'compensation': '₹18L – ₹28L LPA (Top Tier-1 Fast-Growth Product Unicorn)',
        'score': 92,
        'tier': 'strong_match',
        'url': 'https://jobs.ashbyhq.com/atlys/a2158e46-0991-4235-aeec-758b1832c5fb',
        'notes': 'Direct live requisition on Ashby ATS. High-growth travel visa unicorn in Delhi NCR. Deep Python and microservices architecture.'
    },
    {
        'company': 'Atlys',
        'title': 'Backend Engineer AI',
        'location': 'Delhi NCR (Gurugram / Delhi HQ)',
        'domain': 'AI Engineering & Backend Systems',
        'experience': 'Open to fresh graduates (0 YOE) with strong foundations in Python, LLMs, and backend APIs.',
        'tech_stack': 'Python, LLMs, FastAPI, Vector DBs, Redis, Docker',
        'compensation': '₹18L – ₹28L LPA (Top Tier-1 Fast-Growth Product Unicorn)',
        'score': 92,
        'tier': 'strong_match',
        'url': 'https://jobs.ashbyhq.com/atlys/bef534e3-4ab4-4c61-a93c-5182d1d70e8c',
        'notes': 'Direct live requisition on Ashby ATS. Building generative AI backend services and automation pipelines in Delhi NCR.'
    },
    {
        'company': 'Avoca',
        'title': 'Software Engineer (Product)',
        'location': 'Bengaluru, Karnataka (Tech Hub)',
        'domain': 'Software Engineering & Product Architecture',
        'experience': 'B.Tech CS/ECE; strong programming in Python/TypeScript with foundational systems design; 0–1 YOE.',
        'tech_stack': 'Python, TypeScript, React, PostgreSQL, REST APIs',
        'compensation': '₹15L – ₹24L LPA (US-backed AI Startup, India Hub)',
        'score': 88,
        'tier': 'strong_match',
        'url': 'https://jobs.ashbyhq.com/avoca/ec05c135-ab26-437a-8fe9-f7a5c4da08e5',
        'notes': 'Direct live requisition on Ashby ATS. Product engineering with modern full-stack backend emphasis.'
    },
    {
        'company': 'Cursor',
        'title': 'Field Engineer - India',
        'location': 'Bengaluru, Karnataka (Tech Hub / Hybrid)',
        'domain': 'Developer Tooling & Applied AI Engineering',
        'experience': 'Bachelor’s in CS/Engineering; high proficiency in modern developer workflows, Python, and TypeScript; 0–1 YOE.',
        'tech_stack': 'Python, TypeScript, Developer Tools, LLM Workflows, Git',
        'compensation': '₹25L – ₹40L+ LPA (World-Leading AI Code Editor)',
        'score': 90,
        'tier': 'strong_match',
        'url': 'https://jobs.ashbyhq.com/cursor/a6c00f7f-2288-4461-a64d-0f1cd9878909',
        'notes': 'Direct live requisition on Ashby ATS. Working on cutting-edge AI software tooling in India.'
    },
    {
        'company': 'Plane',
        'title': 'Software Engineer, Frontend (React)',
        'location': 'Remote, India (High Flexibility)',
        'domain': 'Frontend / Full Stack Engineering',
        'experience': 'Open to fresh graduates with strong React, JavaScript/TypeScript, and modern web architectures (0–1 YOE).',
        'tech_stack': 'React, TypeScript, Next.js, REST APIs, Tailwind CSS',
        'compensation': '₹14L – ₹22L LPA (Global Open-Source Project Management)',
        'score': 86,
        'tier': 'strong_match',
        'url': 'https://jobs.ashbyhq.com/plane/15cf6387-af74-4616-924f-3659fb76de01',
        'notes': 'Direct live requisition on Ashby ATS. Open-source enterprise project tool; strong fit for Vaanya’s React/Vite skillset.'
    },
    {
        'company': 'Squarepoint Capital',
        'title': 'Platform Compute Specialist',
        'location': 'Bengaluru, Karnataka (Tech Hub)',
        'domain': 'Platform Engineering & Systems Infrastructure',
        'experience': 'Bachelor’s degree in CS/ECE; strong Linux, scripting (Python/Bash), and distributed computing foundations; entry level.',
        'tech_stack': 'Python, Linux, Shell Scripting, Distributed Systems, Cloud',
        'compensation': '₹25L – ₹45L+ LPA (Global Quantitative Trading Firm)',
        'score': 91,
        'tier': 'strong_match',
        'url': 'https://www.squarepoint-capital.com/open-opportunities?id=6119781&gh_jid=6119781',
        'notes': 'Direct requisition on Greenhouse ATS. High-performance compute infrastructure for global quant research.'
    }
]

# Add candidate roles from scraper
for r in raw_roles:
    loc = r.get('location', '').lower()
    if any(foreign in loc for foreign in ['canada', 'italy', 'milan', 'ottawa', 'united states', 'london', 'singapore', 'germany']):
        continue
    url = r.get('url', '').lower().rstrip('/')
    if url in seen_urls:
        continue
    seen_urls.add(url)
    filtered_roles.append(r)

# Add ATS roles
for r in ats_verified:
    url = r.get('url', '').lower().rstrip('/')
    if url in seen_urls:
        continue
    seen_urls.add(url)
    filtered_roles.append(r)

print(f"Total curated clean roles for Wave 9: {len(filtered_roles)}")
with open('data/wave9_final_verified_roles.json', 'w') as f:
    json.dump(filtered_roles, f, indent=2)

for idx, r in enumerate(filtered_roles):
    print(f"{idx+1}. [{r['company']}] {r['title']} | {r['location']} | Score: {r['score']} | {r['compensation']}")
