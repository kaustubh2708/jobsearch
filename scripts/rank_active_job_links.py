import json, re

with open('data/audit_companies_links_final.json') as f:
    results = json.load(f)

active_jobs = [r for r in results if r['is_active']]

print(f"Total active jobs to rank: {len(active_jobs)}")

def evaluate_job(j):
    comp = j['company'].strip()
    title = j['title'].strip()
    loc = j['location'].strip()
    url = j['url'].strip()
    notes = j.get('notes', '') or ''
    job_id = j.get('job_id', '')

    # Location scoring
    loc_l = loc.lower()
    loc_score = 15 # default
    loc_tier = "Tier 4 (Bengaluru / Hyd)"
    if any(k in loc_l for k in ['gurgaon', 'gurugram']):
        loc_score = 25
        loc_tier = "Priority 1 (Gurugram)"
    elif any(k in loc_l for k in ['noida', 'delhi']):
        loc_score = 22
        loc_tier = "Priority 2 (Noida / Delhi NCR)"
    elif 'remote' in loc_l or 'work from home' in loc_l:
        loc_score = 20
        loc_tier = "Priority 3 (Remote India)"
    elif 'bengaluru' in loc_l or 'bangalore' in loc_l:
        loc_score = 17
        loc_tier = "Bengaluru Tech Hub"

    # Skill fit scoring
    title_l = title.lower()
    notes_l = notes.lower()
    url_l = url.lower()

    tech_score = 20 # baseline
    skill_fit_label = "Good Fit (Distributed Systems)"
    stack_tags = []
    callback_prob = "Medium"

    # Check Microsoft sweet spots
    is_dotnet_azure = any(k in title_l or k in notes_l for k in ['dotnet', '.net', 'c#', 'azure'])
    is_node_ts = any(k in title_l or k in notes_l for k in ['node', 'typescript', 'javascript', 'fullstack', 'full stack'])
    is_ai_agent = any(k in title_l or k in notes_l for k in ['ai', 'agent', 'gen ai', 'llm', 'voicebot', 'prompt', 'rag'])
    is_distributed = any(k in title_l or k in notes_l for k in ['distributed', 'microservices', 'backend', 'sde ii', 'sde 2', 'sde-2', 'sde-ii', 'software engineer 2', 'software engineer ii', 'data pipeline'])
    is_cpp_quant = any(k in title_l or k in notes_l for k in ['c++', 'low latency', 'hft', 'quant'])

    if is_dotnet_azure:
        tech_score = 35
        skill_fit_label = "Exact Match (C# / .NET / Azure)"
        stack_tags.append("C#/.NET Core")
        stack_tags.append("Azure")
        callback_prob = "Very High (Direct MSFT Stack Match)"
    elif is_ai_agent:
        tech_score = 34
        skill_fit_label = "High Alignment (AI Agents & LLM Workflows)"
        stack_tags.append("AI Agents / LLM")
        stack_tags.append("Cloud APIs")
        callback_prob = "High (Scarce Skill Advantage)"
    elif is_node_ts:
        tech_score = 32
        skill_fit_label = "Strong Fit (Node.js / TypeScript Backend)"
        stack_tags.append("Node.js/TypeScript")
        stack_tags.append("REST APIs")
        callback_prob = "High (Proven Microsoft Experience)"
    elif is_distributed:
        tech_score = 28
        skill_fit_label = "Solid Fit (Distributed Systems & Microservices)"
        stack_tags.append("Distributed Architecture")
        stack_tags.append("Microservices")
        callback_prob = "Medium-High (Standard Tier-1 Pool)"
    elif is_cpp_quant:
        tech_score = 22
        skill_fit_label = "Stretch / Quant Transition (C++ Low Latency)"
        stack_tags.append("Low-Latency / C++")
        callback_prob = "Medium (Requires Quant/C++ screening)"

    # Seniority Fit (3 years exp sweet spot)
    exp_score = 20
    if any(k in title_l for k in ['ii', '2', 'intermediate']):
        exp_score = 25
    elif 'iii' in title_l or 'senior' in title_l or '3' in title_l:
        exp_score = 22
    elif 'trainee' in title_l or 'intern' in title_l:
        exp_score = 10

    # Company compensation & pedigree
    tier1_comps = ['Amazon', 'Google', 'Apple', 'Coinbase', 'Stripe', 'Tower Research Capital', 'Graviton Research Capital', 'MongoDB', 'PostHog', 'Atlys', 'CrowdStrike', 'BlackRock', 'Adobe', 'Optum', 'Trexquant Investment LP', 'Slice (GaragePreneurs)', 'Honeywell', 'Mastercard', 'Visa', 'PayPal']
    comp_score = 15 if comp in tier1_comps else 10

    total_score = min(100, loc_score + tech_score + exp_score + comp_score)

    # Priority Tier assignment
    if total_score >= 88:
        app_priority = "Tier 1: Apply Immediately (Highest Probability & Fit)"
    elif total_score >= 80:
        app_priority = "Tier 2: High Priority (Strong Fit / Great Brand)"
    else:
        app_priority = "Tier 3: Moderate Priority / Stretch"

    return {
        'row': j['row'],
        'company': comp,
        'title': title,
        'location': loc,
        'loc_tier': loc_tier,
        'total_score': total_score,
        'app_priority': app_priority,
        'skill_fit_label': skill_fit_label,
        'stack_tags': stack_tags,
        'callback_prob': callback_prob,
        'url': url,
        'job_id': job_id,
        'notes': notes
    }

evaluated = [evaluate_job(j) for j in active_jobs]
evaluated.sort(key=lambda x: (-x['total_score'], x['row']))

with open('data/ranked_active_jobs.json', 'w') as f:
    json.dump(evaluated, f, indent=2)

print(f"Successfully ranked {len(evaluated)} active jobs!")
print("\n--- TOP 15 RANKED OPPORTUNITIES ---")
for idx, r in enumerate(evaluated[:15], 1):
    print(f"{idx}. [{r['total_score']} pts] {r['company']} - {r['title']} ({r['location']})")
    print(f"   Fit: {r['skill_fit_label']} | Callback: {r['callback_prob']}")
    print(f"   URL: {r['url']}")
