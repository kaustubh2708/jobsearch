import urllib.request
import json

companies = ['PaloAltoNetworks3', 'ServiceNow', 'WesternDigital', 'Postman', 'MediaNet']

for comp in companies:
    url = f"https://api.smartrecruiters.com/v1/companies/{comp}/postings"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            content = data.get('content', [])
            print(f"SmartRecruiters {comp}: {data.get('totalFound', len(content))} total postings")
            india_postings = []
            for item in content:
                loc = item.get('location', {})
                country = loc.get('country', '').lower()
                city = loc.get('city', '').lower()
                name = item.get('name', '')
                if country == 'in' or any(c in city for c in ['bangalore', 'bengaluru', 'noida', 'gurgaon', 'gurugram', 'hyderabad', 'pune', 'mumbai', 'india']):
                    india_postings.append(item)
            print(f"  -> {len(india_postings)} India postings found in first page")
            for item in india_postings:
                name = item.get('name', '')
                if any(k in name.lower() for k in ['software', 'engineer', 'developer', 'intern', 'graduate', 'associate', 'data', 'python', 'early', 'fresher']):
                    print(f"     * [{item.get('id')}] {name} | {item.get('location', {}).get('city')} | https://jobs.smartrecruiters.com/{comp}/{item.get('id')}")
    except Exception as e:
        print(f"SmartRecruiters {comp} error: {e}")
