import urllib.request
import json

def check_greenhouse(board):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            jobs = data.get('jobs', [])
            india_jobs = [j for j in jobs if 'india' in (j.get('location', {}).get('name', '')).lower() or 'bengaluru' in (j.get('location', {}).get('name', '')).lower() or 'bangalore' in (j.get('location', {}).get('name', '')).lower() or 'noida' in (j.get('location', {}).get('name', '')).lower() or 'gurgaon' in (j.get('location', {}).get('name', '')).lower() or 'hyderabad' in (j.get('location', {}).get('name', '')).lower() or 'pune' in (j.get('location', {}).get('name', '')).lower() or 'remote' in (j.get('location', {}).get('name', '')).lower()]
            print(f"Greenhouse {board}: {len(jobs)} total jobs, {len(india_jobs)} India jobs")
            for j in india_jobs:
                title = j.get('title', '')
                if any(k in title.lower() for k in ['software', 'engineer', 'developer', 'intern', 'graduate', 'data', 'backend', 'associate', 'campus']):
                    print(f"  - [{j.get('id')}] {title} | {j.get('location', {}).get('name')} | {j.get('absolute_url')}")
    except Exception as e:
        print(f"Greenhouse {board} error: {e}")

for b in ['databricks', 'stripe', 'postman', 'coinbase', 'rubrik', 'phonepe', 'hotstar']:
    check_greenhouse(b)
