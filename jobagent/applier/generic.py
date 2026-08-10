"""Generic ATS form filler — Greenhouse, Lever, Ashby, Workday, SmartRecruiters
and anything else with a plain HTML form.

Strategy: walk every visible input on the page, work out what it's asking by
reading its label, resolve an answer, fill it. Upload the resume PDF wherever a
file input appears. Then find the submit button.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .browser import human_pause, type_like_human
from .forms import AnswerResolver

log = logging.getLogger("jobagent.applier.generic")

SKIP_PAT = re.compile(
    r"search|filter|newsletter|subscribe|captcha|password|confirm password|coupon", re.I
)
SUBMIT_PAT = re.compile(r"^(submit|submit application|apply|send application|finish|complete)", re.I)


def label_for(page, el) -> str:
    """Get the human-readable question for a form control."""
    for attr in ("aria-label", "placeholder", "name", "id"):
        try:
            v = el.get_attribute(attr)
        except Exception:
            v = None
        if v and len(v) > 2 and not re.fullmatch(r"[a-f0-9\-]{20,}", v):
            if attr in ("name", "id"):
                v = re.sub(r"[_\-\.]+", " ", v)
                v = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", v)
                v = re.sub(r"\b(job|application|question|field|answer|input|cards?)\b", " ", v, flags=re.I)
                v = re.sub(r"\s+", " ", v).strip()
                if len(v) < 3:
                    continue
            return v.strip()[:300]
    # associated <label>
    try:
        eid = el.get_attribute("id")
        if eid:
            lab = page.locator(f"label[for='{eid}']")
            if lab.count():
                return lab.first.inner_text().strip()[:300]
    except Exception:
        pass
    # nearest ancestor label text
    try:
        txt = el.evaluate(
            """e => { let n = e.closest('label, .field, [class*=field], [class*=question], fieldset');
                      return n ? n.innerText : ''; }"""
        )
        if txt:
            return re.sub(r"\s+", " ", txt).strip()[:300]
    except Exception:
        pass
    return ""


def upload_resume(page, resume_pdf: Optional[Path]) -> bool:
    if not resume_pdf or not Path(resume_pdf).exists():
        return False
    ok = False
    try:
        inputs = page.locator("input[type=file]")
        for i in range(min(inputs.count(), 3)):
            el = inputs.nth(i)
            name = (el.get_attribute("name") or "") + (el.get_attribute("id") or "")
            if "cover" in name.lower():
                continue
            try:
                el.set_input_files(str(resume_pdf))
                ok = True
                page.wait_for_timeout(2500)
            except Exception:
                # some ATSs hide the input behind a styled button
                try:
                    with page.expect_file_chooser(timeout=5000) as fc:
                        page.locator("button:has-text('Upload'), label:has-text('Resume')").first.click()
                    fc.value.set_files(str(resume_pdf))
                    ok = True
                except Exception:
                    continue
    except Exception as e:  # noqa: BLE001
        log.debug("resume upload: %s", e)
    return ok


def fill_visible_fields(page, resolver: AnswerResolver, max_fields: int = 60) -> int:
    """Fill everything we can see. Returns number of fields filled."""
    filled = 0

    # --- text / email / tel / number / textarea ---
    sel = ("input[type=text]:visible, input[type=email]:visible, input[type=tel]:visible, "
           "input[type=url]:visible, input[type=number]:visible, input:not([type]):visible, "
           "textarea:visible")
    els = page.locator(sel)
    for i in range(min(els.count(), max_fields)):
        el = els.nth(i)
        try:
            if not el.is_editable() or (el.input_value() or "").strip():
                continue
            q = label_for(page, el)
            if not q or SKIP_PAT.search(q):
                continue
            required = bool(el.get_attribute("required")) or "*" in q
            ftype = "textarea" if el.evaluate("e => e.tagName.toLowerCase()") == "textarea" else "text"
            ans = resolver.resolve(q, ftype, [], required)
            if ans:
                type_like_human(el, ans)
                filled += 1
                human_pause(page, 0.2, 0.6)
        except Exception:
            continue

    # --- native selects ---
    sels = page.locator("select:visible")
    for i in range(min(sels.count(), 25)):
        el = sels.nth(i)
        try:
            # already answered on an earlier pass — don't re-resolve it, or a
            # validation retry loops forever re-picking the same option
            try:
                if (el.input_value() or "").strip():
                    continue
            except Exception:
                pass
            q = label_for(page, el)
            if not q or SKIP_PAT.search(q):
                continue
            opts = [o.strip() for o in el.locator("option").all_inner_texts() if o.strip()]
            opts = [o for o in opts if not re.match(r"^(select|choose|--)", o, re.I)]
            if not opts:
                continue
            ans = resolver.resolve(q, "select", opts, True)
            if ans:
                el.select_option(label=ans)
                filled += 1
                human_pause(page, 0.2, 0.5)
        except Exception:
            continue

    # --- radio groups (yes/no compliance questions) ---
    try:
        groups: Dict[str, List] = {}
        radios = page.locator("input[type=radio]:visible")
        for i in range(min(radios.count(), 40)):
            el = radios.nth(i)
            name = el.get_attribute("name") or f"_g{i}"
            groups.setdefault(name, []).append(el)
        for name, els_ in groups.items():
            if any(e.is_checked() for e in els_):
                continue
            q = label_for(page, els_[0]) or re.sub(r"[_\-]", " ", name)
            opts = []
            for e in els_:
                t = e.evaluate("""e => { const l = e.closest('label') ||
                    document.querySelector(`label[for="${e.id}"]`); return l ? l.innerText.trim() : e.value; }""")
                opts.append((t or e.get_attribute("value") or "").strip())
            ans = resolver.resolve(q, "radio", [o for o in opts if o], True)
            if ans:
                for e, t in zip(els_, opts):
                    if t == ans:
                        e.check(force=True)
                        filled += 1
                        break
    except Exception:
        pass

    # --- consent checkboxes: tick anything that reads like agreement ---
    try:
        boxes = page.locator("input[type=checkbox]:visible")
        for i in range(min(boxes.count(), 20)):
            el = boxes.nth(i)
            if el.is_checked():
                continue
            q = label_for(page, el).lower()
            if re.search(r"agree|consent|terms|privacy|acknowledge|confirm|gdpr|declaration", q):
                el.check(force=True)
                filled += 1
    except Exception:
        pass

    return filled


def apply(page, job, resolver: AnswerResolver, resume_pdf: Optional[Path],
          auto_submit: bool) -> Dict[str, Any]:
    """Drive a generic ATS application to completion."""
    url = job.apply_url or job.url
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    # Greenhouse/Ashby often need a click to reveal the form.
    # Deliberately NOT including any "Submit" wording here — on a page that
    # renders the form inline, that would fire off an empty application.
    for label in ("Apply for this job", "Apply now", "Apply to this job",
                  "I'm interested", "Apply"):
        try:
            btn = page.get_by_role("button", name=re.compile(f"^{label}$", re.I))
            if btn.count() and btn.first.is_visible():
                btn.first.click()
                page.wait_for_timeout(2500)
                break
        except Exception:
            continue

    # Ashby renders the form inside an iframe on some boards
    frames = [page] + [f for f in page.frames if f != page.main_frame]
    target = page
    for f in frames:
        try:
            if f.locator("input[type=file], input[type=email]").count():
                target = f
                break
        except Exception:
            continue

    uploaded = upload_resume(target, resume_pdf)
    page.wait_for_timeout(2000)
    filled = fill_visible_fields(target, resolver)

    if resolver.unresolved:
        return {"ok": False, "status": "needs_input", "filled": filled,
                "uploaded": uploaded, "pending": resolver.unresolved}

    if not auto_submit:
        return {"ok": False, "status": "ready_not_submitted", "filled": filled, "uploaded": uploaded}

    submitted = False
    for _ in range(3):
        clicked = False
        for name in ("Submit application", "Submit Application", "Submit", "Apply", "Send application"):
            try:
                btn = target.get_by_role("button", name=re.compile(f"^{name}$", re.I))
                if btn.count() and btn.first.is_enabled():
                    btn.first.click()
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            try:
                b = target.locator("button[type=submit]:visible, input[type=submit]:visible").first
                if b.count():
                    b.click()
                    clicked = True
            except Exception:
                pass
        if not clicked:
            break
        page.wait_for_timeout(6000)
        body = (page.content() or "").lower()
        if re.search(r"thank you|application (was )?(received|submitted)|we('| ha)ve received|successfully applied", body):
            submitted = True
            break
        # a validation error may have surfaced new required fields
        more = fill_visible_fields(target, resolver, max_fields=25)
        if resolver.unresolved:
            return {"ok": False, "status": "needs_input", "filled": filled + more,
                    "uploaded": uploaded, "pending": resolver.unresolved}
        if not more:
            submitted = True     # no error text and nothing left to fill
            break

    return {"ok": submitted, "status": "applied" if submitted else "uncertain",
            "filled": filled, "uploaded": uploaded}
