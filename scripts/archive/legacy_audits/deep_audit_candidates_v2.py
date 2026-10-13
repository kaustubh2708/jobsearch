import json, re

with open('data/wave12_audited_final.json') as f:
    passed = json.load(f)

print(f"Refining {len(passed)} candidates...")

filtered = []
for p in passed:
    comp = p['company']
    title = p['title']
    loc = p['location']
    
    # 1. Fastly is Australia Remote -> reject, must be India
    if 'australia' in loc.lower():
        print(f"  REJECT: {comp} | {title} -> Not India ({loc})")
        continue

    # 2. Amrita Vishwa Vidyapeetham is a university staff web developer -> reject for tech career
    if 'amrita' in comp.lower():
        print(f"  REJECT: {comp} | {title} -> Academic institution staff role")
        continue

    filtered.append(p)

print(f"Pristine India Tech Full-Time roles: {len(filtered)}")
with open('data/wave12_audited_final.json', 'w') as f:
    json.dump(filtered, f, indent=2)
