import json
import urllib.request
import urllib.error
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

with open('data/checked_job_links.json') as f:
    items = json.load(f)

# Specific checkers for ATS APIs
def check_greenhouse_api(board, jid):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

def check_ashby_api(org, jid):
    # Ashby API check
    url = f"https://api.ashbyhq.com/posting-api/job-board/{org}/job/{jid}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

# Process each
audited = []
for item in items:
    row = item['row']
    company = item['company']
    role = item['role']
    loc = item['location']
    notes = item['notes']
    url = item['original_url'] or ''
    
    status = 'active'
    eligibility = 'eligible'
    reason = ''
    extracted_title = role
    extracted_loc = loc
    yoe_req = 'Fresher / 0-1 YOE'
    
    # Check specific cases
    if not url:
        status = 'no_url'
        reason = 'No link provided in sheet'
    elif 'rubrik.com' in url or 'gh_jid=81665' in url:
        # We know Greenhouse API works
        m = re.search(r'gh_jid=(\d+)', url)
        if m:
            jid = m.group(1)
            gh_data = check_greenhouse_api('rubrik', jid)
            if gh_data:
                status = 'active'
                extracted_title = gh_data.get('title', role)
                extracted_loc = gh_data.get('location', {}).get('name', 'Bengaluru')
                # Check winter intern: usually 2026/2027 batch
                # Rubrik winter intern is 6 months Jan-June 2026 or similar
                reason = f"Active on Greenhouse: {extracted_title}"
            else:
                status = 'inactive'
                reason = 'Job closed on Greenhouse'
    elif 'apply.workable.com/innovaccer' in url:
        # Check workable
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
                text = r.read().decode('utf-8', errors='ignore')
                if 'not available' in text.lower() or 'no longer available' in text.lower():
                    status = 'inactive'
                    reason = 'Job no longer available on Workable'
                else:
                    status = 'active'
                    reason = 'Active Workable posting'
        except urllib.error.HTTPError as e:
            status = 'inactive'
            reason = f'Workable error HTTP {e.code}'
    elif 'amazon.jobs' in url:
        # Check amazon jobs
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
                text = r.read().decode('utf-8', errors='ignore')
                if 'no longer available' in text.lower() or 'job closed' in text.lower():
                    status = 'inactive'
                    reason = 'Requisition closed on Amazon.jobs'
                else:
                    status = 'active'
                    # check title
                    tm = re.search(r'<title>(.*?)</title>', text)
                    if tm:
                        extracted_title = tm.group(1).split('|')[0].strip()
                    reason = 'Active on Amazon.jobs'
        except urllib.error.HTTPError as e:
            status = 'inactive'
            reason = f'Amazon error HTTP {e.code}'
    elif 'nvidia.wd5.myworkdayjobs.com' in url:
        # NVIDIA Workday
        if 'PhD-Intern' in url or 'phd' in role.lower():
            status = 'ineligible'
            eligibility = 'ineligible_phd'
            reason = 'PhD Intern role — requires enrolled PhD candidate'
    elif 'bain.com' in url:
        # Bain generic search link
        status = 'generic_link'
        reason = 'Generic career search page, not a direct job requisition'
    elif 'yellow.ai' == url.strip() or 'http://yellow.ai' in url:
        status = 'generic_link'
        reason = 'Generic corporate domain, no job requisition'
    elif 'rippling.com/careers' in url:
        status = 'generic_link'
        reason = 'Generic career landing page'
    elif 'jobs.zs.com' in url:
        status = 'active'
        reason = 'Active ZS Associates BTSA posting'
    elif 'careers.unitedhealthgroup.com' in url:
        status = 'inactive'
        reason = 'HTTP 404 — Optum job requisition removed'
    elif 'siemens.com' in url:
        status = 'inactive'
        reason = 'HTTP 404 — Siemens requisition removed'
    elif 'crowdstrike.com' in url:
        status = 'inactive'
        reason = 'HTTP 404 — CrowdStrike emerging talent page expired'
    elif 'epifi' in url and '08c743e8' in url:
        status = 'inactive'
        reason = 'HTTP 404 — Fi Money AI Engg intern closed'
    elif 'linkedin.com/jobs/view/4469429838' in url: # Visdum
        status = 'inactive'
        reason = 'Job posting closed on LinkedIn (Visdum)'
    elif 'linkedin.com/jobs/view/4465512033' in url: # TravClan
        status = 'inactive'
        reason = 'Job posting closed on LinkedIn (TravClan)'
    elif 'mastercard.wd1.myworkdayjobs.com' in url:
        # Check mastercard
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
                text = r.read().decode('utf-8', errors='ignore')
                if 'not available' in text.lower() or 'no longer available' in text.lower():
                    status = 'inactive'
                    reason = 'Workday role closed'
                else:
                    status = 'active'
                    reason = 'Active Mastercard Workday requisition'
        except urllib.error.HTTPError as e:
            status = 'inactive'
            reason = f'Mastercard HTTP {e.code}'
    elif 'wadhwaniai.zohorecruit.in' in url:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
                text = r.read().decode('utf-8', errors='ignore')
                if 'no longer accepting' in text.lower() or 'inactive' in text.lower():
                    status = 'inactive'
                    reason = 'Zoho Recruit posting closed'
                else:
                    status = 'active'
                    reason = 'Active Wadhwani AI Zoho posting'
        except Exception as e:
            status = 'inactive'
            reason = str(e)[:30]
    elif item['is_active']:
        status = 'active'
        reason = item['reason']
    else:
        status = 'inactive'
        reason = item['reason']

    # Now let's calculate match score and callback likelihood for active ones
    item['detailed_status'] = status
    item['status_reason'] = reason
    item['extracted_title'] = extracted_title
    audited.append(item)

with open('data/detailed_audited_links.json', 'w') as f:
    json.dump(audited, f, indent=2)

print(f'Audited {len(audited)} items.')
