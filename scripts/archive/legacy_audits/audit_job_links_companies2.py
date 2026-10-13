import json, time, re, ssl, urllib.request
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('data/job_links_extracted.json') as f:
    items = json.load(f)

# Items with URLs
targets = [x for x in items if not x.get('is_header') and x.get('url')]
print(f"Total targets to audit: {len(targets)}")

# We can partition targets into LinkedIn vs Non-LinkedIn ATS
non_li = [x for x in targets if 'linkedin.com' not in x['url'].lower()]
li = [x for x in targets if 'linkedin.com' in x['url'].lower()]
print(f"Non-LinkedIn URLs: {len(non_li)}")
print(f"LinkedIn URLs: {len(li)}")

