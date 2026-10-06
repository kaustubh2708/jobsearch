import urllib.request
import json
import re

url = "https://www.atlassian.com/company/careers/resources/jobs"
# or let's check greenhouse atlassian
for b in ['atlassian', 'atlassiancareers']:
    try:
        u = f"https://boards-api.greenhouse.io/v1/boards/{b}/jobs"
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"Greenhouse {b}: {len(data.get('jobs', []))} jobs")
    except Exception as e:
        print(f"Greenhouse {b} failed: {e}")

# check atlassian website careers api
try:
    req = urllib.request.Request("https://www.atlassian.com/endpoint/careers/jobs", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        print("Atlassian endpoint:", resp.status)
except Exception as e:
    print(e)
