import json

with open('data/prev_waves_availability_audit.json') as f:
    data = json.load(f)

print(f"Total checked: {data['total_checked']}")
print(f"Active & Open: {data['active_count']} ({data['active_count']/data['total_checked']*100:.1f}%)")
print(f"Closed / Dead / Stopped: {data['closed_count']} ({data['closed_count']/data['total_checked']*100:.1f}%)")
print(f"Rate limited: {data['rate_limited_or_error_count']}")

print("\n--- SAMPLE CLOSED / STOPPED ROLES ---")
for r in data['closed_roles']:
    print(f"  * {r['wave']} | {r['company']} | {r['title']} -> {r.get('reason')}")

