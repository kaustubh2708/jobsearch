import json

with open('data/wave13_curated.json') as f:
    curated = json.load(f)

# Add verified Yugabyte and Starburst FTE roles
additional_ats = [
    {
        'company': 'Yugabyte',
        'title': 'Technical Support Engineer APJ',
        'location': 'India (Remote / Hybrid)',
        'domain': 'Distributed SQL & Database Infrastructure',
        'experience_stated': "Degree in Computer Science or related quantitative field; Linux, SQL, Database internals; 0–1 YOE entry-level full-time intake.",
        'tech_stack': 'Distributed SQL, PostgreSQL, Linux, Shell Scripting, Networking',
        'compensation': 'INR 14 - 20 LPA (Base est.)',
        'match_score': 92,
        'priority_tier': 'Strong Match',
        'verification_status': 'Verified Live (HTTP 200)',
        'url': 'https://job-boards.greenhouse.io/yugabyte/jobs/4677134006',
        'notes': 'Full-time permanent FTE requisition verified on official Yugabyte Greenhouse ATS.',
        'source': 'Greenhouse'
    },
    {
        'company': 'Starburst',
        'title': 'Security Engineer',
        'location': 'India (Remote / Hybrid)',
        'domain': 'Cloud Security & Distributed Data Platform',
        'experience_stated': "Degree in CS/IT or related field; Python, Go, Java, CI/CD, Cloud security fundamentals; 1–2 YOE / Entry-level FTE intake.",
        'tech_stack': 'Python, Java, Go, Cloud Security, AWS, CI/CD',
        'compensation': 'INR 16 - 24 LPA (Base est.)',
        'match_score': 94,
        'priority_tier': 'Strong Match',
        'verification_status': 'Verified Live (HTTP 200)',
        'url': 'https://job-boards.greenhouse.io/starburst/jobs/5399498008',
        'notes': 'Full-time permanent FTE requisition verified on official Starburst Greenhouse ATS.',
        'source': 'Greenhouse'
    },
    {
        'company': 'MiQ',
        'title': 'Software Engineer I',
        'location': 'Bengaluru, Karnataka, India',
        'domain': 'AdTech & Large-Scale Data Systems',
        'experience_stated': "Bachelor’s or Master’s degree in Computer Science; Core Java, Python, Cloud; 0–1 YOE full-time intake.",
        'tech_stack': 'Java, Python, Cloud Infrastructure, REST APIs, SQL',
        'compensation': 'INR 10 - 15 LPA (Base est.)',
        'match_score': 90,
        'priority_tier': 'Strong Match',
        'verification_status': 'Verified Live (HTTP 200)',
        'url': 'https://in.linkedin.com/jobs/view/software-engineer-i-at-miq-4458319227',
        'notes': 'Full-time permanent FTE role verified via LinkedIn Direct.',
        'source': 'LinkedIn'
    }
]

curated.extend(additional_ats)
print(f"Total curated Wave 13 roles now: {len(curated)}")

with open('data/wave13_curated.json', 'w') as f:
    json.dump(curated, f, indent=2)
