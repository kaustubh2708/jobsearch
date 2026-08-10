"""Wellfound (ex-AngelList Talent) via Playwright.

Wellfound is React-rendered and gates a lot behind login, so we reuse the same
persistent browser profile the applier uses. Log in once with
`jobagent login wellfound` and this source starts returning results.
"""
from __future__ import annotations

import logging
import re
from typing import List
from urllib.parse import quote_plus

from .base import RawJob, clean, detect_ats

log = logging.getLogger("jobagent.sources.wellfound")


def scrape(queries: List[str], limit: int = 30, headless: bool = True) -> List[RawJob]:
    try:
        from ..applier.browser import browser_page
    except Exception as e:  # noqa: BLE001
        log.warning("playwright unavailable: %s", e)
        return []

    out: List[RawJob] = []
    seen = set()
    try:
        with browser_page(headless=headless) as page:
            for q in queries[:4]:
                url = (f"https://wellfound.com/jobs?"
                       f"role={quote_plus(q)}&location=india&remote=true")
                try:
                    page.goto(url, timeout=45000, wait_until="domcontentloaded")
                    page.wait_for_timeout(4000)
                    for _ in range(3):
                        page.mouse.wheel(0, 3000)
                        page.wait_for_timeout(1200)

                    cards = page.locator("div[data-test='StartupResult'], div[class*='styles_component']")
                    n = min(cards.count(), limit)
                    for i in range(n):
                        try:
                            card = cards.nth(i)
                            txt = clean(card.inner_text())
                            if len(txt) < 30:
                                continue
                            link = card.locator("a[href*='/jobs/']").first
                            href = link.get_attribute("href") if link.count() else ""
                            if href and href.startswith("/"):
                                href = "https://wellfound.com" + href
                            if not href or href in seen:
                                continue
                            seen.add(href)
                            lines = [l for l in txt.split("\n") if l.strip()]
                            title = lines[0][:140] if lines else q
                            company = lines[1][:80] if len(lines) > 1 else ""
                            out.append(RawJob(
                                title=title, company=company,
                                location="India / Remote", url=href, apply_url=href,
                                description=txt, source="wellfound",
                                ats=detect_ats(href),
                                is_remote="remote" in txt.lower(),
                                salary_text=(re.search(r"₹[\d,\s\-–LlPpAa]+", txt) or [""])[0]
                                if re.search(r"₹", txt) else "",
                            ))
                        except Exception:
                            continue
                except Exception as e:  # noqa: BLE001
                    log.debug("wellfound '%s': %s", q, e)
    except Exception as e:  # noqa: BLE001
        log.warning("wellfound source failed: %s", e)
    log.info("[wellfound] -> %d", len(out))
    return out
