"""LinkedIn Easy Apply.

Easy Apply is a multi-step modal: contact info -> resume -> screening questions
-> review -> submit. We loop until the Submit button appears, filling whatever
the current step shows. If the job is not Easy Apply, we hand it back so the
generic ATS handler can chase the external link instead.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from .browser import human_pause
from .forms import AnswerResolver
from .generic import fill_visible_fields, upload_resume

log = logging.getLogger("jobagent.applier.linkedin")

MODAL = "div.jobs-easy-apply-modal, div[data-test-modal], div[role=dialog]"


def _click(page, *names) -> bool:
    for n in names:
        try:
            b = page.get_by_role("button", name=re.compile(n, re.I))
            if b.count() and b.first.is_visible() and b.first.is_enabled():
                b.first.click()
                page.wait_for_timeout(2200)
                return True
        except Exception:
            continue
    return False


def apply(page, job, resolver: AnswerResolver, resume_pdf: Optional[Path],
          auto_submit: bool) -> Dict[str, Any]:
    page.goto(job.url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3500)

    if "login" in page.url or "authwall" in page.url:
        return {"ok": False, "status": "login_required",
                "error": "LinkedIn session expired. Run: jobagent login linkedin"}

    # Already applied?
    body = (page.content() or "").lower()
    if "applied" in body and re.search(r"you('ve| have) applied|application submitted", body):
        return {"ok": True, "status": "already_applied"}

    easy = page.locator("button.jobs-apply-button, button:has-text('Easy Apply')")
    if not easy.count():
        return {"ok": False, "status": "not_easy_apply",
                "error": "No Easy Apply button — falls through to the external ATS."}

    try:
        easy.first.click()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": "failed", "error": f"could not open Easy Apply: {e}"}
    page.wait_for_timeout(3000)

    modal = page.locator(MODAL).first
    scope = modal if modal.count() else page

    filled_total = 0
    for step in range(12):                     # Easy Apply is rarely > 6 steps
        try:
            upload_resume(scope, resume_pdf)
        except Exception:
            pass
        filled_total += fill_visible_fields(scope, resolver, max_fields=30)

        if resolver.unresolved:
            return {"ok": False, "status": "needs_input", "filled": filled_total,
                    "pending": resolver.unresolved}

        # Submit appears only on the final step
        submit = scope.get_by_role("button", name=re.compile(r"^submit application$", re.I))
        if submit.count() and submit.first.is_enabled():
            if not auto_submit:
                return {"ok": False, "status": "ready_not_submitted", "filled": filled_total}
            # untick "follow company" — cosmetic, but keeps your feed clean
            try:
                f = scope.locator("input#follow-company-checkbox")
                if f.count() and f.first.is_checked():
                    f.first.uncheck(force=True)
            except Exception:
                pass
            submit.first.click()
            page.wait_for_timeout(5000)
            done = (page.content() or "").lower()
            ok = bool(re.search(r"application sent|your application was sent|applied", done))
            _click(page, r"^done$", r"^dismiss$", r"^close$")
            return {"ok": ok, "status": "applied" if ok else "uncertain", "filled": filled_total}

        if not _click(scope, r"^next$", r"^continue", r"^review"):
            break
        human_pause(page, 0.8, 1.8)

    return {"ok": False, "status": "uncertain", "filled": filled_total,
            "error": "Easy Apply flow ended without reaching Submit."}
