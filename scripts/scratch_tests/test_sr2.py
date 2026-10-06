import urllib.request
import json

for comp in ['ServiceNow', 'WesternDigital']:
    url = f"https://api.smartrecruiters.com/v1/companies/{comp}/postings?country=in&limit=100"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            postings = data.get('content', [])
            print(f"{comp} in India: {data.get('totalFound')} total postings found")
            for item in postings:
                name = item.get('name', '')
                loc = item.get('location', {}).get('city', '')
                id = item.get('id')
                if any(w in name.lower() for w in ['associate', 'intern', 'graduate', 'junior', 'entry', 'software', 'engineer', 'developer', 'data', 'analyst']):
                    print(f"  [{id}] {name} | {loc} | https://jobs.smartrecruiters.com/{comp}/{id}")
    except Exception as e:
        print(f"Error {comp}: {e}")
