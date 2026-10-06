import urllib.request
import json

url = "https://jiostar.wd102.myworkdayjobs.com/wday/cxs/jiostar/JioStar/jobs"
offset = 0
limit = 20
total = 247

while offset < total:
    payload = json.dumps({"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            postings = data.get("jobPostings", [])
            for p in postings:
                title = p.get("title", "")
                loc = p.get("locationsText", "")
                bullet = p.get("bulletFields", [""])
                bid = bullet[0] if bullet else ""
                ext = p.get("externalPath", "")
                if any(k in title.lower() for k in ["software", "engineer", "developer", "intern", "associate", "data", "analyst", "sde", "ai"]):
                    print(f"[{bid}] {title} | {loc} | https://jiostar.wd102.myworkdayjobs.com/en-US/JioStar{ext}")
            offset += limit
    except Exception as e:
        print("Error at offset", offset, e)
        break
