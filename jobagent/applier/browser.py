"""One persistent, logged-in Chromium profile shared by every applier.

You log into LinkedIn / Naukri / Wellfound once, by hand, and the session
cookies live in data/browser_profile/ forever. Nothing ever asks you for a
password and no credentials are stored anywhere in this repo.
"""
from __future__ import annotations

import contextlib
import logging
import random
from typing import Iterator, Optional

from ..config import BROWSER_PROFILE_DIR, load_config

log = logging.getLogger("jobagent.browser")

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-IN', 'en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
window.chrome = { runtime: {} };
"""

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


@contextlib.contextmanager
def browser_context(headless: Optional[bool] = None):
    from playwright.sync_api import sync_playwright

    cfg = load_config()
    headless = cfg.apply.headless if headless is None else headless

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_PROFILE_DIR),
            headless=headless,
            viewport={"width": 1440, "height": 900},
            user_agent=UA,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            geolocation={"latitude": 12.9716, "longitude": 77.5946},
            permissions=["geolocation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
                "--no-first-run",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        ctx.add_init_script(STEALTH_JS)
        ctx.set_default_timeout(30000)
        try:
            yield ctx
        finally:
            with contextlib.suppress(Exception):
                ctx.close()


@contextlib.contextmanager
def browser_page(headless: Optional[bool] = None) -> Iterator:
    with browser_context(headless=headless) as ctx:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        yield page


def human_pause(page, lo: float = 0.4, hi: float = 1.4) -> None:
    page.wait_for_timeout(int(random.uniform(lo, hi) * 1000))


def type_like_human(locator, text: str) -> None:
    locator.click()
    locator.fill("")
    for ch in str(text):
        locator.type(ch, delay=random.uniform(25, 90))


def is_logged_in(page, site: str) -> bool:
    """Cheap heuristic — does the site still think we're a guest?"""
    probes = {
        "linkedin": ("https://www.linkedin.com/feed/", "global-nav__me"),
        "naukri": ("https://www.naukri.com/mnjuser/homepage", "nI-gNb-drawer"),
        "wellfound": ("https://wellfound.com/jobs", "logged-in"),
    }
    url, marker = probes.get(site, (None, None))
    if not url:
        return False
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2500)
        if "login" in page.url or "signup" in page.url:
            return False
        return marker in page.content() or "logout" in page.content().lower()
    except Exception:
        return False


def interactive_login(site: str) -> bool:
    """Opens a real window and waits for you to log in. Run once per site."""
    urls = {
        "linkedin": "https://www.linkedin.com/login",
        "naukri": "https://www.naukri.com/nlogin/login",
        "wellfound": "https://wellfound.com/login",
        "instahyre": "https://www.instahyre.com/login/",
        "indeed": "https://in.indeed.com/account/login",
    }
    url = urls.get(site)
    if not url:
        raise ValueError(f"unknown site '{site}'. one of: {', '.join(urls)}")

    print(f"\n  Opening {site}. Log in in the window that appears.")
    print("  Take your time — solve any captcha or OTP.")
    print("  When you're on your logged-in homepage, come back here and press Enter.\n")
    with browser_context(headless=False) as ctx:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, wait_until="domcontentloaded")
        input("  Press Enter once you're logged in... ")
        ok = is_logged_in(page, site)
    print(f"  {site}: {'session saved' if ok else 'could not confirm login — try again'}\n")
    return ok
