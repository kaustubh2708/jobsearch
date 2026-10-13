#!/usr/bin/env python3
"""
run_wave8_discovery.py

Automated multi-cluster discovery engine executing the Canonical 12 Sub-Agents roster
to discover, probe, filter, and verify 30+ top SDE II opportunities for Vrinda (Wave 8).
"""

import urllib.request, ssl, re, json, time
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Load Deduplication Index
with open('data/vrinda_all_seen_urls.json') as f:
    meta = json.load(f)
seen_urls = set(meta['urls'])
seen_ids = set(meta['ids'])

print(f"Loaded {len(seen_urls)} URLs and {len(seen_ids)} IDs in deduplication index.")

# 2. Multi-Cluster Search Endpoints
search_queries = [
    # Cluster 1: .NET / C# / Azure (Gurugram & Noida)
    ('Dotnet Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=.NET%20Developer&location=Gurugram&f_TPR=r604800'),
    ('CSharp Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=C%23%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Dotnet Core Noida', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=.NET%20Core%20Software%20Engineer&location=Noida&f_TPR=r604800'),
    ('Azure Cloud Engineer Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Azure%20Cloud%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Azure Microservices Noida', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Azure%20Microservices&location=Noida&f_TPR=r604800'),
    ('Siemens Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Siemens%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Honeywell Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Honeywell%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('UKG Noida', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=UKG%20Software%20Engineer&location=Noida&f_TPR=r604800'),
    ('Johnson Controls Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Johnson%20Controls%20Software%20Engineer&location=Gurgaon&f_TPR=r604800'),
    ('Amdocs Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Amdocs%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Wolters Kluwer Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Wolters%20Kluwer%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Dunnhumby Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Dunnhumby%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),

    # Cluster 2: Node.js / TypeScript / Distributed Systems (NCR & Remote)
    ('Node Backend Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Node.js%20Backend%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('TypeScript SDE 2 Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=TypeScript%20SDE%202&location=Gurugram&f_TPR=r604800'),
    ('NestJS Backend Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=NestJS%20Backend%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Distributed Systems Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Distributed%20Systems%20SDE%202&location=Gurugram&f_TPR=r604800'),
    ('GoKwik Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=GoKwik%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Cars24 Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=CARS24%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Spinny Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Spinny%20Backend%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Shiprocket Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Shiprocket%20Backend&location=Gurugram&f_TPR=r604800'),
    ('Delhivery Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Delhivery%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Moglix Noida', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Moglix%20Software%20Engineer&location=Noida&f_TPR=r604800'),
    ('Info Edge Noida', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Info%20Edge%20Software%20Engineer&location=Noida&f_TPR=r604800'),

    # Cluster 3: AI Agents / MCP / LLM Tool-Calling
    ('AI Agent Software Engineer India', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=AI%20Agent%20Software%20Engineer&location=India&f_TPR=r604800'),
    ('Agentic AI Engineer Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Agentic%20AI%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('LLM Software Engineer India', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=LLM%20Software%20Engineer&location=India&f_TPR=r604800'),
    ('Generative AI Backend India', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Generative%20AI%20Backend%20Engineer&location=India&f_TPR=r604800'),

    # Cluster 4: High-Growth FinTech & Tier-1 Platforms
    ('PayPay India', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=PayPay%20India%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('PhonePe Bangalore', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=PhonePe%20Software%20Engineer&location=Bengaluru&f_TPR=r604800'),
    ('Slice Backend', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Slice%20Backend%20Engineer&location=India&f_TPR=r604800'),
    ('Navi SDE 2', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Navi%20SDE%202&location=Bengaluru&f_TPR=r604800'),
    ('JPMC SWE II India', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=JPMorganChase%20Software%20Engineer%20II&location=India&f_TPR=r604800'),
    ('Barclays SWE India', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Barclays%20Software%20Engineer&location=India&f_TPR=r604800'),

    # Cluster 5: Global Remote, E-Commerce & Platform Unicorns (Amazon strictly paused)
    ('Swiggy SDE II', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Swiggy%20Software%20Engineer%20II&location=Bengaluru&f_TPR=r604800'),
    ('Meesho SDE II', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Meesho%20Software%20Engineer%20II&location=Bengaluru&f_TPR=r604800'),
    ('BrowserStack Remote India', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=BrowserStack%20Software%20Engineer&location=India&f_TPR=r604800'),
    ('Zepto SDE 2 India', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Zepto%20SDE%202&location=India&f_TPR=r604800'),
    ('Urban Company Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Urban%20Company%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Lenskart Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Lenskart%20Software%20Engineer&location=Gurgaon&f_TPR=r604800'),
    ('Sprinklr Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Sprinklr%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('NatWest Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=NatWest%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Fidelity Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Fidelity%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('MakeMyTrip Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=MakeMyTrip%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Zomato Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Zomato%20Software%20Engineer&location=Gurugram&f_TPR=r604800'),
    ('Blinkit Gurgaon', 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Blinkit%20Software%20Engineer&location=Gurugram&f_TPR=r604800')
]

raw_cards = []
seen_in_run = set()

print(f"\n--- Scraping {len(search_queries)} discovery query endpoints ---")
for label, url in search_queries:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            soup = BeautifulSoup(resp.read().decode('utf-8', errors='ignore'), 'html.parser')
            cards = soup.find_all('div', class_='base-card')
            found_count = 0
            for c in cards:
                t = c.find('h3', class_='base-search-card__title')
                comp = c.find('h4', class_='base-search-card__subtitle')
                loc = c.find('span', class_='job-search-card__location')
                link = c.find('a', class_='base-card__full-link')
                time_tag = c.find('time', class_='job-search-card__listdate')
                
                title_str = t.text.strip() if t else ''
                comp_str = comp.text.strip() if comp else ''
                loc_str = loc.text.strip() if loc else ''
                link_str = link['href'] if link else ''
                time_str = time_tag.text.strip() if time_tag else ''

                if not title_str or not comp_str or not link_str:
                    continue

                m = re.search(r'jobs/view/.*?(\d{8,11})', link_str)
                jid = m.group(1) if m else ''
                clean_url = link_str.split('?')[0].lower().rstrip('/')

                # Basic exclusions on title
                t_lower = title_str.lower()
                c_lower = comp_str.lower()
                if 'amazon' in c_lower:
                    continue
                if any(k in t_lower for k in [
                    'director', 'principal', 'head of', 'architect', 'lead', 
                    'manager', 'vp', 'vice president', 'staff', 'intern', 'trainee', 
                    'graduate', 'qa automation', 'sdet', 'manual testing', 'salesforce', 
                    'sap ', 'sap-', 'abap', 'peoplesoft', 'workday consultant'
                ]):
                    continue
                if 'frontend' in t_lower or 'ui developer' in t_lower or 'angular developer' in t_lower:
                    if 'fullstack' not in t_lower and 'full stack' not in t_lower:
                        continue

                # Deduplicate against global seen and run seen
                if jid and jid in seen_ids:
                    continue
                if clean_url in seen_urls or jid in seen_in_run:
                    continue

                seen_in_run.add(jid)
                raw_cards.append({
                    'cluster': label,
                    'company': comp_str,
                    'title': title_str,
                    'location': loc_str,
                    'job_id': jid,
                    'url': link_str.split('?')[0],
                    'posted': time_str
                })
                found_count += 1
            print(f"  [{label}] fetched {len(cards)} -> {found_count} new unique candidates")
    except Exception as e:
        print(f"  [{label}] error: {e}")

print(f"\nTotal raw unique candidate cards for deep audit: {len(raw_cards)}")
with open('data/wave8_raw_candidates.json', 'w') as f:
    json.dump(raw_cards, f, indent=2)
