import openpyxl, urllib.request, ssl, re, json
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

wb = openpyxl.load_workbook('data/Job Search.xlsx')
ws = wb['Wave 15']

# Universal regex for ANY 2+ to 15+ years experience
high_exp_regex = re.compile(
    r'\b(?:'
    r'[2-9]\s*\+?\s*(?:to|[-–—])?\s*(?:\d+)?\s*(?:years?|yrs?)|'
    r'[1-9]\d\s*\+?\s*(?:to|[-–—])?\s*(?:\d+)?\s*(?:years?|yrs?)|'
    r'(?:experience|exp)\s*[:\-–—]?\s*[2-9]|'
    r'minimum\s+(?:of\s+)?[2-9]\s*\+?\s*(?:years?|yrs?)|'
    r'at\s+least\s+[2-9]\s*\+?\s*(?:years?|yrs?)|'
    r'[2-9]\s*(?:years?|yrs?)\s+minimum'
    r')\b',
    re.IGNORECASE
)

# Fresher positive signals
fresher_regex = re.compile(
    r'\b(?:'
    r'0\s*[-–—to]\s*1\s*(?:years?|yrs?)|'
    r'0\s*[-–—to]\s*2\s*(?:years?|yrs?)|'
    r'0\s*\+?\s*(?:years?|yrs?)|'
    r'fresh\s*graduates?|'
    r'college\s*graduates?|'
    r'campus\s*hires?|'
    r'university\s*graduates?|'
    r'entry[\s-]level|'
    r'freshers?|'
    r'no\s*(?:prior\s*)?experience\s*(?:required|needed)'
    r')\b',
    re.IGNORECASE
)

print(f"Auditing all {ws.max_row - 1} roles in Wave 15 with bulletproof regex...")

passed = []
failed = []

for r in range(2, ws.max_row + 1):
    comp = ws.cell(r, 2).value
    title = ws.cell(r, 3).value
    loc = ws.cell(r, 4).value
    cell_u = ws.cell(r, 12)
    url = cell_u.hyperlink.target if cell_u.hyperlink else cell_u.value

    full_text = ""
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            desc = soup.find('div', class_='show-more-less-html__markup') or soup.find('section', class_='description') or soup.find('div', class_='content')
            full_text = desc.get_text(' ', strip=True) if desc else soup.get_text(' ', strip=True)
    except Exception as e:
        full_text = ""

    high_matches = []
    if full_text:
        # Find all matches
        for m in high_exp_regex.finditer(full_text):
            m_str = m.group(0)
            # Filter out false alarms like "for 100 years", "over 20 years in business", "2024"
            s_start = max(0, m.start() - 30)
            s_end = min(len(full_text), m.end() + 30)
            window = full_text[s_start:s_end].lower()
            if not any(ign in window for ign in ['in business', 'legacy', 'established', 'company has', 'firm has', 'for more than', 'over']):
                high_matches.append(m_str)

    has_fresher = bool(fresher_regex.search(full_text)) if full_text else False

    if high_matches:
        failed.append({
            'row': r,
            'company': comp,
            'title': title,
            'url': url,
            'reason': f"High exp mentions: {high_matches[:3]}"
        })
        print(f"❌ FAIL Row {r}: {comp} | {title} -> {high_matches[:2]}")
    elif not full_text:
        failed.append({
            'row': r,
            'company': comp,
            'title': title,
            'url': url,
            'reason': "Page empty or failed to load"
        })
        print(f"❌ FAIL Row {r}: {comp} | {title} -> Could not fetch text")
    else:
        passed.append({
            'row': r,
            'company': comp,
            'title': title,
            'url': url,
            'has_fresher_tag': has_fresher
        })
        print(f"✅ PASS Row {r}: {comp} | {title} (fresher_signal={has_fresher})")

print(f"\nAudit complete! Passed: {len(passed)}, Failed: {len(failed)}")
with open('data/wave15_audit_failure_breakdown.json', 'w') as f:
    json.dump({'passed': passed, 'failed': failed}, f, indent=2)

