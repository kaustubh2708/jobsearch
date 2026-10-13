import json, re

with open('data/wave12_gate_passed.json') as f:
    passed = json.load(f)

print(f"Auditing {len(passed)} candidate roles from gate passed list...")

clean_list = []
discarded = []

for idx, p in enumerate(passed, 1):
    comp = p['company']
    title = p['title']
    exp = p['experience_stated']
    tl = title.lower()
    el = exp.lower()

    # Rejection 1: Title checks
    if any(k in tl for k in ['iii', '3', 'senior', 'sr.', 'lead', 'architect', 'head', 'manager', 'director']):
        discarded.append((comp, title, 'Seniority in title'))
        continue

    # Rejection 2: Trainee/Intern keywords in title
    if any(k in tl for k in ['intern', 'apprentice', 'trainee']):
        discarded.append((comp, title, 'Intern/Apprentice/Trainee in title'))
        continue

    # Rejection 3: Experience text explicitly demanding >= 2 YOE
    high_match = re.search(r'\b([2-9]|\d{2})\+?\s*(?:to\s*\d+\s*)?years?', el)
    if high_match and not any(k in high_match.group(0) for k in ['company', 'history', '0-2', '0–2']):
        # If it explicitly says 1-2 years, that is acceptable for entry-level / SDE I
        if '1-2' not in el and '1 to 2' not in el:
            discarded.append((comp, title, f'Experience requirement too high: {high_match.group(0)}'))
            continue

    clean_list.append(p)

print(f"\nRemaining clean full-time entry-level roles: {len(clean_list)}")
print(f"Discarded roles: {len(discarded)}")
for c, t, r in discarded:
    print(f"  DISCARDED: {c} | {t} -> {r}")

print("\n--- FINAL APPROVED ROLES ---")
for i, r in enumerate(clean_list, 1):
    print(f"{i:02d}. {r['company']} | {r['title']} | {r['location']} | {r['source']}")

with open('data/wave12_audited_final.json', 'w') as f:
    json.dump(clean_list, f, indent=2)
