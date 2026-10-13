import openpyxl
import time
import ssl
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

wb = openpyxl.load_workbook('data/Job Search.xlsx')
ws = wb['Wave 10']

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)

print(f"Auditing all {ws.max_row - 1} links in Wave 10 with browser and requests...")

audit_report = []

try:
    for r in range(2, ws.max_row + 1):
        row_num = r - 1
        comp = ws.cell(r, 2).value
        title = ws.cell(r, 3).value
        c_link = ws.cell(r, 12)
        url = c_link.hyperlink.target if c_link.hyperlink else c_link.value

        is_live = False
        verdict = ""
        actual_title = ""

        try:
            driver.get(url)
            time.sleep(1.2)
            page_src = driver.page_source.lower()
            actual_title = driver.title

            if "404" in actual_title or "page not found" in page_src or "job no longer available" in page_src:
                verdict = "DEAD / 404"
            elif "too many requests" in actual_title.lower() or "too many requests" in page_src:
                verdict = "RATE_LIMITED_429"
            elif "403 forbidden" in actual_title.lower() or "access denied" in page_src:
                verdict = "BLOCKED_403"
            else:
                is_live = True
                verdict = "200_OK_LIVE"
        except Exception as e:
            verdict = f"ERROR_{str(e)[:30]}"

        audit_report.append({
            'row': row_num,
            'excel_row': r,
            'company': comp,
            'title': title,
            'url': url,
            'is_live': is_live,
            'verdict': verdict,
            'page_title': actual_title
        })
        print(f"[{row_num}/37] {comp} | {title[:30]} -> {verdict} (Title: {actual_title[:35]})")

finally:
    driver.quit()

live_count = sum(1 for a in audit_report if a['is_live'])
dead_count = sum(1 for a in audit_report if not a['is_live'])

print(f"\nAudit complete: {live_count} LIVE, {dead_count} FAILED.")
with open('data/wave10_link_audit_report.json', 'w') as f:
    json.dump(audit_report, f, indent=2)
