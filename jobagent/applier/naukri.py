"""Naukri.com apply.

Naukri has two paths. Most listings are one-click "Apply" against your saved
Naukri profile — those are trivial. Some open a chatbot panel that asks
screening questions one at a time, which we answer through the resolver. A
minority redirect to the company site, which we hand back to the generic
handler.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from .browser import human_pause, type_like_human
from .forms import AnswerResolver

log = logging.getLogger("jobagent.applier.naukri")

CHATBOT = "div.chatbot_DrawerContentWrapper, div._chatBotContainer, div.chatbot_Drawer"


def apply(page, job, resolver: AnswerResolver, resume_pdf: Optional[Path],
          auto_submit: bool) -> Dict[str, Any]:
    page.goto(job.url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3500)

    if "login" in page.url.lower():
        return {"ok": False, "status": "login_required",
                "error": "Naukri session expired. Run: jobagent login naukri"}

    body = (page.content() or "").lower()
    if re.search(r"you have already applied|already applied", body):
        return {"ok": True, "status": "already_applied"}

    # Company-site redirect
    ext = page.locator("button:has-text('Apply on company site'), a:has-text('Apply on company site')")
    if ext.count():
        try:
            href = ext.first.get_attribute("href")
        except Exception:
            href = None
        return {"ok": False, "status": "external", "external_url": href or job.url,
                "error": "Naukri redirects to the company site."}

    btn = page.locator("button#apply-button, button:has-text('Apply'), span:has-text('Apply')")
    if not btn.count():
        return {"ok": False, "status": "failed", "error": "no Apply button found"}

    if not auto_submit:
        return {"ok": False, "status": "ready_not_submitted",
                "error": "auto_submit disabled — Apply button located but not clicked"}

    try:
        btn.first.click()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": "failed", "error": f"apply click failed: {e}"}
    page.wait_for_timeout(4000)

    # --- chatbot questionnaire ---
    answered = 0
    for _ in range(15):
        chat = page.locator(CHATBOT)
        if not chat.count() or not chat.first.is_visible():
            break
        try:
            question = chat.first.locator("div.botMsg, span.botMsg, div[class*=botItem]").last.inner_text().strip()
        except Exception:
            question = ""
        if not question:
            break

        # multiple choice chips
        chips = chat.first.locator("div.ssrc__radio-btn-container label, li.chatbot_MultipleOption, div[class*=option]")
        opts = []
        if chips.count():
            opts = [t.strip() for t in chips.all_inner_texts() if t.strip()]

        ans = resolver.resolve(question, "radio" if opts else "text", opts, True)
        if ans is None:
            return {"ok": False, "status": "needs_input", "pending": resolver.unresolved,
                    "notes": f"stopped at Naukri question: {question[:200]}"}

        if opts:
            for i in range(chips.count()):
                if chips.nth(i).inner_text().strip() == ans:
                    chips.nth(i).click()
                    break
        else:
            box = chat.first.locator("div.textArea, textarea, input[type=text]").last
            type_like_human(box, ans)

        try:
            chat.first.locator("div.sendMsg, button:has-text('Save'), div[class*=send]").last.click()
        except Exception:
            page.keyboard.press("Enter")
        answered += 1
        human_pause(page, 1.0, 2.2)

    page.wait_for_timeout(3000)
    done = (page.content() or "").lower()
    ok = bool(re.search(r"application sent|successfully applied|you have applied|applied to", done))
    return {"ok": ok, "status": "applied" if ok else "uncertain", "filled": answered}
