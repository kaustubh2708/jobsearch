import json, re

with open('data/audit_companies_links_final.json') as f:
    results = json.load(f)

active_jobs = [r for r in results if r['is_active']]

def evaluate_job(j):
    comp = j['company'].strip()
    raw_title = j['title'].strip()
    raw_loc = j['location'].strip()
    url = j['url'].strip()
    notes = j.get('notes', '') or ''
    job_id = j.get('job_id', '')

    # Extract location from title if pin present
    clean_title = raw_title
    clean_loc = raw_loc
    if '📍' in raw_title:
        parts = raw_title.split('📍')
        clean_title = parts[0].strip()
        clean_loc = parts[1].strip()

    loc_l = clean_loc.lower()
    loc_tier = "Tier 4 (Bengaluru / Hyd)"
    loc_score = 15

    if any(k in loc_l for k in ['gurgaon', 'gurugram']):
        loc_score = 25
        loc_tier = "Priority 1 (Gurugram)"
    elif any(k in loc_l for k in ['noida', 'delhi']):
        loc_score = 22
        loc_tier = "Priority 2 (Noida / Delhi NCR)"
    elif any(k in loc_l for k in ['remote', 'work from home']):
        loc_score = 20
        loc_tier = "Priority 3 (Remote India)"
    elif any(k in loc_l for k in ['bengaluru', 'bangalore']):
        loc_score = 17
        loc_tier = "Bengaluru Tech Hub"

    # Tech stack and fit scoring
    title_l = clean_title.lower()
    notes_l = notes.lower()
    url_l = url.lower()
    comp_l = comp.lower()

    # Base match
    tech_score = 20
    skill_fit_label = "Solid Fit (Distributed Systems & Backend)"
    stack_tags = []
    callback_prob = "Medium-High (Standard Tier-1 Pool)"

    is_dotnet_azure = any(k in title_l or k in notes_l for k in ['dotnet', '.net', 'c#', 'azure'])
    is_ai_agent = any(k in title_l or k in notes_l for k in ['ai', 'agent', 'gen ai', 'llm', 'voicebot', 'prompt', 'rag'])
    is_node_ts = any(k in title_l or k in notes_l for k in ['node', 'typescript', 'javascript', 'fullstack', 'full stack'])
    is_distributed = any(k in title_l or k in notes_l for k in ['distributed', 'microservices', 'backend', 'sde ii', 'sde 2', 'sde-2', 'sde-ii', 'software engineer 2', 'software engineer ii', 'data pipeline'])
    is_cpp_quant = any(k in title_l or k in notes_l for k in ['c++', 'low latency', 'hft', 'quant'])

    if is_dotnet_azure:
        tech_score = 35
        skill_fit_label = "Exact Match: C# / .NET Core & Azure"
        stack_tags.extend(["C#/.NET Core", "Azure Microservices"])
        callback_prob = "Very High (Direct Microsoft Core Stack Fit)"
    elif is_ai_agent:
        tech_score = 34
        skill_fit_label = "High Alignment: AI Agents & LLM Architectures"
        stack_tags.extend(["AI Agents / LLM", "Cloud APIs / Microservices"])
        callback_prob = "High (High Demand / Specialized Skill Fit)"
    elif is_node_ts:
        tech_score = 32
        skill_fit_label = "Strong Fit: Node.js & TypeScript Backend"
        stack_tags.extend(["Node.js/TypeScript", "REST APIs / Distributed"])
        callback_prob = "High (Direct Experience Advantage)"
    elif is_distributed:
        tech_score = 28
        skill_fit_label = "Solid Fit: High-Scale Distributed Systems"
        stack_tags.extend(["Distributed Architecture", "Cloud Microservices"])
        callback_prob = "Medium-High (Microsoft SDE Pedigree)"
    elif is_cpp_quant:
        tech_score = 24
        skill_fit_label = "Stretch / Quant Pivot: C++ Low Latency Systems"
        stack_tags.extend(["C++", "Low Latency / Order Routing"])
        callback_prob = "Medium (Requires Quant / Systems Interview)"

    # Seniority score (3 years sweet spot)
    exp_score = 20
    if any(k in title_l for k in ['ii', '2', 'intermediate']):
        exp_score = 25
    elif any(k in title_l for k in ['iii', 'senior', '3']):
        exp_score = 22
    elif 'trainee' in title_l or 'intern' in title_l:
        exp_score = 10

    # Company compensation likelihood & pedigree
    tier1_comps = [
        'amazon', 'google', 'apple', 'coinbase', 'stripe', 'tower research capital',
        'graviton research capital', 'mongodb', 'posthog', 'atlys', 'crowdstrike',
        'blackrock', 'adobe', 'optum', 'trexquant investment lp', 'slice (garagepreneurs)',
        'honeywell', 'mastercard', 'visa', 'paypal', 'par technology', 'hdfc bank',
        'cadence design systems', 'chegg india', 'gitlab', 'cars24'
    ]
    comp_score = 15 if comp_l in tier1_comps else 10

    total_score = min(100, loc_score + tech_score + exp_score + comp_score)

    if total_score >= 88:
        app_priority = "Tier 1: Apply Immediately (Highest Fit & Priority Location)"
    elif total_score >= 80:
        app_priority = "Tier 2: High Priority (Strong Fit / Great Brand)"
    else:
        app_priority = "Tier 3: Secondary / Strategic Stretch"

    return {
        'row': j['row'],
        'company': comp,
        'clean_title': clean_title,
        'clean_location': clean_loc,
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

with open('data/ranked_active_jobs_v2.json', 'w') as f:
    json.dump(evaluated, f, indent=2)

t1 = [r for r in evaluated if 'Tier 1' in r['app_priority']]
t2 = [r for r in evaluated if 'Tier 2' in r['app_priority']]
t3 = [r for r in evaluated if 'Tier 3' in r['app_priority']]

print(f"Total Active Jobs: {len(evaluated)}")
print(f"Tier 1 (Apply Immediately): {len(t1)}")
print(f"Tier 2 (High Priority): {len(t2)}")
print(f"Tier 3 (Secondary / Stretch): {len(t3)}")

print("\n--- TIER 1 SAMPLES ---")
for idx, r in enumerate(t1[:12], 1):
    print(f"{idx}. [{r['total_score']} pts] {r['company']} - {r['clean_title']} ({r['clean_location']})")
    print(f"   Fit: {r['skill_fit_label']} | Callback: {r['callback_prob']}")
    print(f"   URL: {r['url']}\n")
