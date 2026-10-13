import json, urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

with open('data/wave11_final_verified_roles.json') as f:
    roles = json.load(f)

print(f"Testing live HTTP status for {len(roles)} roles...")

failed = 0
for idx, r in enumerate(roles, 1):
    url = r['url']
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            code = resp.getcode()
            if code != 200:
                print(f"[{idx}] FAILED ({code}): {r['company']} - {url}")
                failed += 1
            else:
                pass
    except Exception as e:
        print(f"[{idx}] ERROR ({e}): {r['company']} - {url}")
        failed += 1

print(f"Finished. Total failed: {failed} / {len(roles)}")
