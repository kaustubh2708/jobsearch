import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

workday_sites = [
    ('Adobe', 'https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs', 'https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced/job/'),
    ('Visa', 'https://visa.wd5.myworkdayjobs.com/wday/cxs/visa/Visa/jobs', 'https://visa.wd5.myworkdayjobs.com/en-US/Visa/job/'),
    ('Mastercard', 'https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs', 'https://mastercard.wd1.myworkdayjobs.com/en-US/CorporateCareers/job/'),
    ('Barclays', 'https://barclays.wd3.myworkdayjobs.com/wday/cxs/barclays/External_Career_Site_Barclays/jobs', 'https://barclays.wd3.myworkdayjobs.com/en-US/External_Career_Site_Barclays/job/'),
    ('Qualcomm', 'https://qualcomm.wd5.myworkdayjobs.com/wday/cxs/qualcomm/External/jobs', 'https://qualcomm.wd5.myworkdayjobs.com/en-US/External/job/'),
    ('Target', 'https://target.wd5.myworkdayjobs.com/wday/cxs/target/targetcareers/jobs', 'https://target.wd5.myworkdayjobs.com/en-US/targetcareers/job/'),
    ('ServiceNow', 'https://servicenow.wd1.myworkdayjobs.com/wday/cxs/servicenow/Early_Career/jobs', 'https://servicenow.wd1.myworkdayjobs.com/en-US/Early_Career/job/'),
    ('American Express', 'https://aexp.wd3.myworkdayjobs.com/wday/cxs/aexp/AmexCampus/jobs', 'https://aexp.wd3.myworkdayjobs.com/en-US/AmexCampus/job/')
]

found_roles = []

for company, endpoint, base_url in workday_sites:
    payload = {
        "appliedFacets": {
            "locationCountry": ["b4a8e2d424b94a0fb7fb2a188f5f4b93", "b4a8e2d424b94a0fb7fb2a188f5f4b93"] # India facet or search
        },
        "limit": 20,
        "offset": 0,
        "searchText": "Engineer"
    }
    try:
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            postings = data.get('jobPostings', [])
            for p in postings:
                title = p.get('title', '')
                loc = p.get('locationsText', '')
                ext_path = p.get('externalPath', '')
                full_url = endpoint.replace('/wday/cxs/', '/').replace('/jobs', '') + ext_path
                
                t_lower = title.lower()
                l_lower = loc.lower()
                
                is_india = any(k in l_lower for k in ['india', 'bengaluru', 'bangalore', 'gurgaon', 'gurugram', 'noida', 'delhi', 'hyderabad', 'pune', 'mumbai', 'remote'])
                if not is_india and loc:
                    continue
                    
                is_senior = any(k in t_lower for k in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director', 'manager', 'head', 'architect', 'ii', '2', '3', 'iii'])
                if is_senior:
                    continue
                    
                is_fresher_fit = any(k in t_lower for k in ['intern', 'graduate', 'campus', 'fresher', 'trainee', 'associate', 'i', '1', 'entry', 'junior', 'software engineer'])
                if is_fresher_fit:
                    found_roles.append({
                        'company': company,
                        'title': title,
                        'location': loc or 'India',
                        'url': full_url
                    })
            print(f"{company}: checked {len(postings)} postings, matched {len([r for r in found_roles if r['company'] == company])}")
    except Exception as e:
        print(f"{company} error: {e}")

with open('data/raw_workday_roles.json', 'w') as f:
    json.dump(found_roles, f, indent=2)

print(f"Total Workday roles found: {len(found_roles)}")
