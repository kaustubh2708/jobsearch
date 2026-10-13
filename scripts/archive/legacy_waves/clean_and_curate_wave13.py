import json, re

with open('data/wave13_passed.json') as f:
    passed = json.load(f)

print(f"Initial gate-passed roles: {len(passed)}")

curated = []
non_cs = ['civil', 'mechanical', 'electrical', 'structural', 'telecom']

for p in passed:
    title = p['title'].lower()
    comp = p['company'].lower()
    
    # 1. Reject non-CS/IT engineering (civil, mechanical, electrical, structural, telecom)
    if any(k in title for k in non_cs):
        print(f"  REJECT Non-CS: {p['company']} | {p['title']}")
        continue

    curated.append(p)

print(f"Curated CS/IT tech roles: {len(curated)}")

# Add more tech candidates if needed from the earlier ATS findings (e.g. Yugabyte, Starburst, etc.)
# Let's inspect how many we have
with open('data/wave13_curated.json', 'w') as f:
    json.dump(curated, f, indent=2)
