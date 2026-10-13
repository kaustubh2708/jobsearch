import urllib.request, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

boards = ['rippling', 'clevertap', 'hasura', 'chargebee', 'postman', 'browserstack', 'inmobi', 'swiggy', 'groww', 'razorpay', 'cred', 'meesho', 'cars24', 'lenskart', 'urbancompany', 'slice', 'zepto', 'blinkit', 'deliveroo', 'juspay']

for b in boards:
    url = f'https://api.lever.co/v0/postings/{b}?mode=json'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data:
                print(f"{b}: {len(data)} postings")
                for p in data[:3]:
                    print(f"  {p.get('text')} | {p.get('categories', {}).get('location')}")
    except Exception as e:
        # print(b, e)
        pass
