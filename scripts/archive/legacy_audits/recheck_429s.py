import urllib.request, ssl, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

urls = [
    ('IDEAL IT TECHNO', 'https://in.linkedin.com/jobs/view/python-django-developer-at-ideal-it-techno-4468694084'),
    ('super.money', 'https://in.linkedin.com/jobs/view/software-engineer-i-at-super-money-4444583163'),
    ('MiQ', 'https://in.linkedin.com/jobs/view/software-engineer-i-at-miq-4458319227')
]

for name, u in urls:
    time.sleep(2.0)
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            print(f"{name}: {resp.status} OK")
    except Exception as e:
        print(f"{name}: {e}")
