import urllib.request
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

with open('data/verified_wave4_additions.json') as f:
    items = json.load(f)

# Also check Wave 3
with open('data/verified_new_sheet_additions.json') as f:
    wave3 = json.load(f)

all_items = [(i, 'W3') for i in wave3] + [(i, 'W4') for i in items]

def fetch_jd(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            raw = r.read(80000).decode('utf-8', errors='ignore')
            # strip HTML tags
            text = re.sub(r'<[^>]+>', ' ', raw)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
    except Exception as e:
        return f"ERROR: {e}"

def check_greenhouse_api(url):
    m = re.search(r'gh_jid=(\d+)', url)
    if not m:
        m = re.search(r'/jobs/(\d+)', url)
    if not m:
        return None
    jid = m.group(1)
    for board in ['okta', 'mongodb', 'sprinklr', 'aristanetworks', 'nutanix']:
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}"
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
                return json.loads(r.read()).get('content', '')
        except:
            continue
    return None

def check_ashby_api(url):
    # Extract org slug and job id
    m = re.match(r'https://jobs\.ashbyhq\.com/([^/]+)/([^/]+)', url)
    if m:
        slug, jid = m.group(1), m.group(2)
        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}/job/{jid}"
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
                data = json.loads(r.read())
                desc = data.get('descriptionHtml', '') or data.get('descriptionPlain', '')
                return re.sub(r'<[^>]+>', ' ', desc)
        except Exception as e:
            return None
    return None

def check_lever_api(url):
    m = re.search(r'lever\.co/[^/]+/([a-f0-9\-]+)', url)
    if m:
        jid = m.group(1)
        # extract org from URL
        org_m = re.search(r'lever\.co/([^/]+)/', url)
        if org_m:
            org = org_m.group(1)
            api_url = f"https://api.lever.co/v0/postings/{org}/{jid}?mode=json"
            try:
                req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
                    data = json.loads(r.read())
                    return data.get('descriptionPlain', '')
            except:
                pass
    return None

# Patterns indicating 2+ YOE required
hard_reject_patterns = [
    r'\b([2-9]|\d{2,})\+?\s*(?:or more\s*)?years?\s+(?:of\s+)?(?:professional|full.?time|industry|work|relevant)\s+(?:software|engineering|development)?\s*experience',
    r'\b(?:minimum|at least|min\.?|requires?)\s+([2-9]|\d{2,})\+?\s*years?\s+(?:of\s+)?experience',
    r'([2-9]|\d{2,})\+\s*years?\s+(?:of\s+)?(?:experience|exp\.)',
    r'\bsenior\b(?!.{0,20}interview)',  # senior in title context
    r'\b(?:2|3|4|5)\+\s*yr',
    r'\bexperienced\s+hire\b'
]

fresher_signals = [
    r'\b0.?2\s*years?\b',
    r'\b0.?1\s*years?\b',
    r'\bfresh(?:er|ers|ly?\s+graduated?)\b',
    r'\b(?:new\s+grad|new\s+graduate|recent\s+graduate|campus\s+hire|entry.?level)\b',
    r'\b(?:graduate\s+(?:engineer|trainee|program))\b',
    r'\b(?:intern|internship)\b',
    r'\bno\s+(?:prior\s+)?work\s+experience',
    r'\b2026\b',
    r'\b0\s*(?:to|-)\s*2\s*years?\s+experience\b',
    r'\brecent(?:ly)?\s+graduated?\b',
    r'\bjunior\s+(?:developer|engineer|data)\b'
]

results = []
print("Verifying JD eligibility for all Wave 3 & Wave 4 additions...")

for item, wave in all_items:
    company = item['company']
    role = item['role']
    url = item['url']
    
    print(f"\n[{wave}] Checking: {company} - {role[:40]}")
    
    # Try fast API paths first
    text = None
    if 'ashbyhq.com' in url:
        text = check_ashby_api(url)
    elif 'lever.co' in url:
        text = check_lever_api(url)
    elif 'gh_jid' in url or 'greenhouse.io' in url:
        text = check_greenhouse_api(url)
    
    if not text:
        text = fetch_jd(url)
    
    text_lower = text.lower() if text else ''
    
    # Check reject patterns
    is_rejected = False
    reject_reason = ''
    for pat in hard_reject_patterns:
        m = re.search(pat, text_lower)
        if m:
            # get context
            start = max(0, m.start()-60)
            end = min(len(text_lower), m.end()+60)
            snippet = text_lower[start:end].replace('\n', ' ')
            reject_reason = f"PATTERN: '{m.group()}' in: '...{snippet}...'"
            is_rejected = True
            break
    
    # Check fresher signals
    fresher_found = []
    for pat in fresher_signals:
        m = re.search(pat, text_lower)
        if m:
            start = max(0, m.start()-30)
            end = min(len(text_lower), m.end()+50)
            snippet = text_lower[start:end].replace('\n', ' ')
            fresher_found.append(f"'{m.group()}': ...{snippet}...")
    
    verdict = 'ELIGIBLE' if (fresher_found and not is_rejected) else ('REJECTED' if is_rejected else 'UNKNOWN')
    
    result = {
        'wave': wave,
        'company': company,
        'role': role,
        'url': url,
        'verdict': verdict,
        'reject_reason': reject_reason,
        'fresher_signals': fresher_found[:2],  # top 2
        'text_excerpt': text_lower[100:600] if text else 'NO TEXT'
    }
    results.append(result)
    
    print(f"  Verdict: {verdict}")
    if is_rejected:
        print(f"  Reject reason: {reject_reason[:120]}")
    elif fresher_found:
        print(f"  Fresher signal: {fresher_found[0][:100]}")
    else:
        print(f"  Text excerpt: {text_lower[50:200]}")

with open('data/jd_eligibility_check.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n\n=== SUMMARY ===")
for r in results:
    print(f"[{r['wave']}] {r['verdict']:8s} | {r['company']:26s} | {r['role'][:35]}")
