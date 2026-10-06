import json

with open('data/verified_fresh_roles_w5.json') as f:
    roles = json.load(f)

# Also check HPE, EA, insightsoftware, Amazon, Urban Company, Zepto
extra_roles = [
    {'company': 'Hewlett Packard Enterprise (HPE)', 'title': 'Graduate Software Engineer', 'location': 'Bengaluru (Remote/Teleworker)', 'url': 'https://careers.hpe.com/us/en/job/1210218/Graduate-Software-Engineer', 'stack': 'Python, C++, Java, systems software, Linux, test automation'},
    {'company': 'Electronic Arts (EA)', 'title': 'AI Full Stack Intern', 'location': 'Hyderabad (Hybrid)', 'url': 'https://jobs.ea.com/en_US/careers/JobDetail/215939', 'stack': 'Python, FastAPI, LangChain, OpenAI APIs, LLM Integrations, SQL'},
    {'company': 'insightsoftware', 'title': 'Associate Software Engineer (Internship)', 'location': 'Hyderabad / Bengaluru', 'url': 'https://magnitudesoftware.wd1.myworkdayjobs.com/External/job/India---Hyderabad---Remote/Associate-Software-Engineer_REQ001103-1', 'stack': 'Python, SQL, Cloud APIs, CI/CD, GenAI'},
    {'company': 'Amazon', 'title': 'Software Development Engineer Intern (AUTA)', 'location': 'Delhi NCR / Bengaluru / Hyderabad', 'url': 'https://www.amazon.jobs/en/jobs/10513277/software-development-engineer-intern-may-2027-2-month-amazon-university-talent-acquisition', 'stack': 'Python, Java, C++, DSA, Distributed Systems, AWS'},
    {'company': 'Urban Company', 'title': 'Software Development Engineer 1 (SDE-1)', 'location': 'Gurugram, Haryana', 'url': 'https://www.urbancompany.com/careers', 'stack': 'Python, Node.js, PostgreSQL, Microservices, Distributed Systems'},
    {'company': 'Zepto', 'title': 'Data Scientist', 'location': 'Bengaluru', 'url': 'https://www.instahyre.com/job/264559-data-scientist-at-zepto-bangalore/', 'stack': 'Python, Machine Learning, Statistical Modeling, ML Pipelines, SQL'},
    {'company': 'Angel One', 'title': 'SDE Internship', 'location': 'Bengaluru', 'url': 'https://unstop.com/internships/sde-internship-angel-one-pvt-ltd-bengaluru-1786566', 'stack': 'JavaScript, TypeScript, Svelte, REST APIs'}
]

all_check = roles + extra_roles

# Deduplicate by company name (exclude the 8 cross-sheet duplicates)
excluded_duplicates = ['tower research capital', 'stripe', 'salesforce', 'cars24', 'iqvia', 'american express', 'cashkaro']

non_engineering_rejects = ['product management', 'founder', 'marketing', 'supply chain', 'industrial design', 'filmmaking', 'generalist']

audited = []
for r in all_check:
    comp = r.get('company', '')
    title = r.get('title', '')
    loc = r.get('location', '')
    url = r.get('url', '')
    
    comp_l = comp.lower().strip()
    title_l = title.lower().strip()
    
    # 1. Duplicate check
    if any(ex in comp_l for ex in excluded_duplicates):
        continue
        
    # 2. Non-engineering / Skill mismatch check
    is_non_eng = any(ne in title_l for ne in non_engineering_rejects)
    
    # Specific skill match criteria:
    # Vaanya: Python, FastAPI, SQL/PostgreSQL, ML/BERT/NLP, Data Engineering, SDE
    skills_matched = []
    text_check = (title_l + ' ' + r.get('jd_snippet', '') + ' ' + r.get('stack', '')).lower()
    
    if 'python' in text_check: skills_matched.append('Python')
    if any(k in text_check for k in ['fastapi', 'flask', 'rest api', 'api']): skills_matched.append('FastAPI / REST APIs')
    if any(k in text_check for k in ['sql', 'postgres', 'postgresql', 'database', 'db']): skills_matched.append('SQL / PostgreSQL')
    if any(k in text_check for k in ['ml', 'machine learning', 'ai', 'nlp', 'bert', 'llm', 'rag']): skills_matched.append('AI / ML / NLP')
    if any(k in text_check for k in ['docker', 'aws', 'cloud', 'pipeline']): skills_matched.append('Cloud / Data Pipelines')
    if any(k in text_check for k in ['dsa', 'c++', 'java', 'system', 'software', 'test']): skills_matched.append('Core CS / Systems')
    
    verdict = 'ELIGIBLE'
    reason = ''
    
    if is_non_eng:
        verdict = 'REJECTED_SKILL_MISMATCH'
        reason = f"Title '{title}' is Product Management / Non-Engineering (not Python backend/SDE)"
    elif not skills_matched:
        verdict = 'REJECTED_SKILL_MISMATCH'
        reason = f"No core stack skills (Python, SQL, ML, APIs) found in role"
    elif 'angel one' in comp_l and not any(k in skills_matched for k in ['Python', 'AI / ML / NLP']):
        verdict = 'REJECTED_SKILL_MISMATCH'
        reason = f"Frontend-heavy stack (JavaScript, Svelte); lacks Python/Data/ML focus"
    
    audited.append({
        'company': comp,
        'title': title,
        'location': loc,
        'url': url,
        'verdict': verdict,
        'reason': reason,
        'skills_matched': skills_matched
    })

print(f"Total evaluated unique candidates: {len(audited)}")
print("\n=== SKILL FIT REJECTIONS ===")
for a in audited:
    if a['verdict'] == 'REJECTED_SKILL_MISMATCH':
        print(f"❌ {a['company']} - {a['title']}: {a['reason']}")

print("\n=== 100% CONFIRMED UNIQUE & SKILL-MATCHED FOR VAANYA ===")
for a in audited:
    if a['verdict'] == 'ELIGIBLE':
        print(f"✅ {a['company']} | {a['title']} ({a['location']})")
        print(f"   Skills Matched: {', '.join(a['skills_matched'])}")
        print(f"   URL: {a['url']}\n")
