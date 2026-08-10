"""End-to-end test of the apply lifecycle without a browser or a GPU.

Drives the *real* generic.apply handler against a mock Playwright page that
mimics a Greenhouse application form, then walks the full state machine:

    approve -> queue -> apply -> persist -> tracker
    needs_input -> user answers -> answer bank -> requeue -> applied

Run:  python -m tests.test_apply_lifecycle
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile

os.environ.setdefault("JOBAGENT_DATA_DIR", tempfile.mkdtemp(prefix="jobagent-test-"))

# --------------------------------------------------------------------------- #
#  Fake local LLM (stands in for Ollama)
# --------------------------------------------------------------------------- #
import jobagent.llm as L  # noqa: E402


class FakeLLM:
    """Answers novel screening questions the way a small local model would."""

    def __init__(self):
        self.calls = []

    def is_up(self):
        return True

    def ensure_models(self):
        return {}

    def embed(self, t):
        return [0.1] * 32

    def chat(self, system, user, **kw):
        return ("I lead ML backend work on GCP Dataplex at Google and built an "
                "on-prem voice AI stack now live in 14 call centres. Both map "
                "directly onto what this role needs.")

    def chat_json(self, system, user, fallback=None, **kw):
        self.calls.append(user)
        q = ""
        m = re.search(r"Question:\s*(.+)", user)
        if m:
            q = m.group(1).strip().lower()

        # confident answers
        if "how many years" in q and "python" in q:
            return {"answer": "4", "confidence": "high", "why": "resume states 4 years"}
        if "why do you want" in q or "cover letter" in q:
            return {"answer": "Because the role is production LLM serving.",
                    "confidence": "high", "why": "derived from resume"}
        if "pronouns" in q:
            return {"answer": "Decline to self identify", "confidence": "high", "why": "optional"}

        # the one it should refuse to guess
        if "security clearance" in q:
            return {"answer": "", "confidence": "low",
                    "why": "resume says nothing about clearances"}

        return {"answer": "", "confidence": "low", "why": "not in the resume"}


_fake = FakeLLM()
L._llm = _fake
L.get_llm = lambda: _fake
import jobagent.resume_parser as RP  # noqa: E402
import jobagent.matcher as M  # noqa: E402
import jobagent.applier.forms as F  # noqa: E402
import jobagent.applier.engine as E  # noqa: E402

RP.get_llm = L.get_llm
M.get_llm = L.get_llm
F.get_llm = L.get_llm
E.get_llm = L.get_llm


# --------------------------------------------------------------------------- #
#  Mock Playwright surface
# --------------------------------------------------------------------------- #
class El:
    def __init__(self, page, tag="input", type_="text", name="", label="",
                 required=False, options=None, checked=False, value=""):
        # NB: itype, not `type` — `type` is a Playwright *method* on a locator,
        # and shadowing it with a string breaks typing into the field.
        self.page, self.tag, self.itype = page, tag, type_
        self.name, self.label = name, label
        self.required, self.options = required, options or []
        self.checked, self.value = checked, value
        self.filled = None

    # -- playwright-ish API --------------------------------------------------
    def get_attribute(self, a):
        return {"name": self.name, "id": self.name, "aria-label": self.label,
                "required": "true" if self.required else None,
                "placeholder": None, "type": self.itype}.get(a)

    def is_editable(self):
        return True

    def is_visible(self):
        return True

    def is_enabled(self):
        return True

    def is_checked(self):
        return self.checked

    def input_value(self):
        return self.value

    def evaluate(self, js):
        if "tagName" in js:
            return self.tag
        return self.label

    def click(self):
        self.page.clicked.append(self.label)
        self.page.on_click(self.label)

    def fill(self, v):
        self.value = v

    def type(self, ch, delay=None):
        self.filled = (self.filled or "") + ch
        self.value = self.filled
        self.page.record(self.label or self.name, self.value)

    def select_option(self, label=None, **kw):
        self.value = label
        self.page.record(self.label or self.name, label)

    def check(self, force=False):
        self.checked = True
        self.page.record(self.label or self.name, "checked")

    def uncheck(self, force=False):
        self.checked = False

    def set_input_files(self, p):
        self.page.uploaded = p

    def inner_text(self):
        return self.label

    def all_inner_texts(self):
        return self.options

    def count(self):
        return 1

    @property
    def first(self):
        return self

    def locator(self, sel):
        if "option" in sel:
            return Loc(self.page, [El(self.page, label=o) for o in self.options])
        return Loc(self.page, [])


class Loc:
    def __init__(self, page, els):
        self.page, self.els = page, els

    def count(self):
        return len(self.els)

    def nth(self, i):
        return self.els[i]

    @property
    def first(self):
        return self.els[0] if self.els else El(self.page)

    @property
    def last(self):
        return self.els[-1] if self.els else El(self.page)

    def all_inner_texts(self):
        return [e.label for e in self.els]

    def is_visible(self):
        return bool(self.els)

    def is_enabled(self):
        return bool(self.els)

    def click(self):
        if self.els:
            self.page.clicked.append(self.els[0].label)
            self.page.on_click(self.els[0].label)

    def inner_text(self):
        return self.els[0].label if self.els else ""

    def locator(self, sel):
        return Loc(self.page, [])

    def get_attribute(self, a):
        return self.els[0].get_attribute(a) if self.els else None


class MockPage:
    """A Greenhouse-shaped application form."""

    def __init__(self, fields, submit_text="Submit application", success=True):
        self.fields = fields
        self.submit_text = submit_text
        self.success = success
        self.answers = {}
        self.clicked = []
        self.uploaded = None
        self.submitted = False
        self._body = "<html>application form</html>"
        self.url = "https://boards.greenhouse.io/testco/jobs/1"
        self.main_frame = self
        self.frames = [self]

    # -- recording -----------------------------------------------------------
    def record(self, q, v):
        self.answers[q] = v

    def on_click(self, label):
        if re.match(r"^(submit|apply|send)", (label or "").lower()):
            self.submitted = True
            self._body = ("<html>Thank you for applying. Your application was "
                          "received.</html>" if self.success else "<html>form</html>")

    # -- page API ------------------------------------------------------------
    def goto(self, url, **kw):
        self.url = url

    def wait_for_timeout(self, ms):
        pass

    def content(self):
        return self._body

    def screenshot(self, path=None, full_page=False):
        from pathlib import Path

        Path(path).write_bytes(b"\x89PNG\r\n\x1a\n")

    def keyboard_press(self, k):
        pass

    def get_by_role(self, role, name=None):
        pat = name if hasattr(name, "search") else re.compile(re.escape(str(name)), re.I)
        if pat.search(self.submit_text):
            return Loc(self, [El(self, tag="button", label=self.submit_text)])
        return Loc(self, [])

    def locator(self, sel):
        s = sel.lower()
        if "input[type=file]" in s:
            return Loc(self, [El(self, type_="file", name="resume")])
        if "select" in s and "input" not in s:
            return Loc(self, [f for f in self.fields if f.tag == "select"])
        if "input[type=radio]" in s:
            return Loc(self, [f for f in self.fields if f.itype == "radio"])
        if "input[type=checkbox]" in s:
            return Loc(self, [f for f in self.fields if f.itype == "checkbox"])
        if "textarea" in s or "input[type=text]" in s:
            return Loc(self, [f for f in self.fields
                              if f.tag in ("input", "textarea") and f.itype == "text"])
        if "button[type=submit]" in s:
            return Loc(self, [El(self, tag="button", label=self.submit_text)])
        return Loc(self, [])

    def expect_file_chooser(self, timeout=None):
        raise RuntimeError("not used")


# --------------------------------------------------------------------------- #
#  Test
# --------------------------------------------------------------------------- #
from sqlmodel import select  # noqa: E402

from jobagent.applier import generic  # noqa: E402
from jobagent.config import load_config  # noqa: E402
from jobagent.db import (AnswerBank, Application, AppStatus, Job, JobStatus,  # noqa: E402
                         SkillLibrary, fingerprint, get_session, init_db)

PROFILE = {
    "headline": "ML Engineer II",
    "seniority": "senior",
    "total_years_experience": 4,
    "current_role": "ML Engineer II @ Google",
    "hard_skills": ["Python", "PyTorch", "vLLM", "LangGraph", "GCP"],
    "core_skills": ["Python", "vLLM", "LangGraph"],
    "domains": ["voice AI", "MLOps"],
    "achievements": ["50% cost reduction across 14 BPO call centres"],
    "experience": [{"title": "ML Engineer II", "company": "Google", "duration": "2024-"}],
    "education": [{"degree": "B.Tech", "field": "CSE", "institution": "Galgotias", "year": "2021"}],
    "target_roles": ["Machine Learning Engineer"],
    "red_lines": [],
}

PASS, FAIL = [], []


def check(label, cond, detail=""):
    (PASS if cond else FAIL).append(label)
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {label}" + (f"  -> {detail}" if detail else ""))


def seed():
    init_db()
    with get_session() as s:
        for row in s.exec(select(Job)).all():
            s.delete(row)
        for row in s.exec(select(Application)).all():
            s.delete(row)
        for row in s.exec(select(AnswerBank)).all():
            s.delete(row)
        for row in s.exec(select(SkillLibrary)).all():
            s.delete(row)
        s.commit()
        job = Job(fingerprint=fingerprint("TestCo", "Senior ML Engineer"),
                  title="Senior ML Engineer", company="TestCo", location="Bengaluru",
                  url="https://boards.greenhouse.io/testco/jobs/1",
                  apply_url="https://boards.greenhouse.io/testco/jobs/1",
                  source="greenhouse", ats="greenhouse", score=91,
                  description="Own production LLM serving.",
                  status=JobStatus.PENDING.value)
        s.add(job)
        s.add(SkillLibrary(source_file="r.pdf", raw_text="x",
                           payload=json.dumps(PROFILE), embedding="[]"))
        s.commit()
        s.refresh(job)
        return job.id


def clean_form():
    """A form the agent can complete entirely on its own."""
    p_fields = []

    def add(**kw):
        p_fields.append(kw)
        return p_fields

    page = MockPage([])
    page.fields = [
        El(page, label="First Name *", name="first_name", required=True),
        El(page, label="Last Name *", name="last_name", required=True),
        El(page, label="Email *", name="email", required=True),
        El(page, label="Phone *", name="phone", required=True),
        El(page, label="LinkedIn Profile", name="linkedin"),
        El(page, label="How many years of Python experience do you have? *",
           name="q_python", required=True),
        El(page, tag="select", label="Are you legally authorized to work in India? *",
           name="q_auth", options=["Yes", "No"], required=True),
        El(page, tag="select", label="Will you now or in the future require sponsorship? *",
           name="q_sponsor", options=["Yes", "No"], required=True),
        El(page, tag="select", label="What is your notice period? *", name="q_notice",
           options=["Immediate", "15 days", "30 days", "60 days", "90 days"], required=True),
        El(page, tag="textarea", label="Why do you want to work here? *",
           name="q_why", required=True),
        El(page, type_="checkbox", label="I agree to the privacy policy *"),
    ]
    return page


def blocked_form():
    """Same form plus a question the model must refuse to guess."""
    page = clean_form()
    page.fields.append(
        El(page, label="Do you hold an active government security clearance? *",
           name="q_clearance", required=True))
    return page


def main():
    from pathlib import Path

    cfg = load_config()
    # a stand-in resume PDF so the upload path is genuinely exercised
    fake_pdf = Path(os.environ["JOBAGENT_DATA_DIR"]) / "resume_for_upload.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4\n% test\n")
    cfg.resume.upload_pdf = str(fake_pdf)

    cfg.profile.full_name = "Kaustubh Singh"
    cfg.profile.email = "kaustubhsk2708@gmail.com"
    cfg.profile.phone = "+919876543210"
    cfg.profile.linkedin = "https://linkedin.com/in/kaustubh2708"
    cfg.profile.notice_period_days = 30
    cfg.profile.years_experience = 4
    cfg.apply.auto_submit = True
    cfg.apply.screenshot_evidence = True

    job_id = seed()
    print("\n" + "=" * 68)
    print("  APPLY LIFECYCLE TEST")
    print("=" * 68)

    # ---------------------------------------------------------------- step 1
    print("\n1. Approve the job in the dashboard")
    with get_session() as s:
        j = s.get(Job, job_id)
        j.status = JobStatus.APPROVED.value
        s.add(j)
        s.commit()
    n = E.queue_approved()
    with get_session() as s:
        app = s.exec(select(Application).where(Application.job_id == job_id)).first()
    check("approving creates a queued application", n == 1 and app.status == AppStatus.QUEUED.value,
          f"status={app.status}")
    app_id = app.id

    # ---------------------------------------------------------------- step 2
    print("\n2. Agent fills and submits the form")
    page = clean_form()
    with get_session() as s:
        job, app = s.get(Job, job_id), s.get(Application, app_id)
        res = E.apply_to_job(job, app, PROFILE, page, cfg)

    check("resume PDF uploaded", page.uploaded is not None or cfg.resume_pdf is None,
          f"uploaded={page.uploaded}")
    check("form was submitted", res.get("ok") and res["status"] == "applied",
          f"status={res['status']}, fields filled={res.get('filled')}")
    check("cover letter generated", bool(res.get("cover_letter")),
          f"{len(res.get('cover_letter',''))} chars")
    check("screenshot evidence saved", bool(res.get("evidence_path")))

    a = page.answers
    check("name split correctly", a.get("First Name *") == "Kaustubh"
          and a.get("Last Name *") == "Singh", f"{a.get('First Name *')} / {a.get('Last Name *')}")
    check("phone came from config, not the model", a.get("Phone *") == "+919876543210",
          a.get("Phone *"))
    check("notice period matched a dropdown option", a.get("What is your notice period? *") == "30 days",
          a.get("What is your notice period? *"))
    check("work authorisation answered Yes", a.get("Are you legally authorized to work in India? *") == "Yes")
    check("sponsorship answered No", a.get("Will you now or in the future require sponsorship? *") == "No")
    check("novel question answered by the model", a.get(
        "How many years of Python experience do you have? *") == "4")
    check("consent checkbox ticked", a.get("I agree to the privacy policy *") == "checked")

    # ---------------------------------------------------------------- step 3
    print("\n3. Result is persisted to the tracker")
    E._persist(app_id, job_id, res)
    with get_session() as s:
        app = s.get(Application, app_id)
    check("moved to APPLIED", app.status == AppStatus.APPLIED.value, app.status)
    check("submitted_at stamped", app.submitted_at is not None)
    check("method recorded", app.method in ("greenhouse", "generic"), app.method)
    check("answers audit trail stored", len(json.loads(app.answers)) >= 8,
          f"{len(json.loads(app.answers))} answers")

    # ---------------------------------------------------------------- step 4
    print("\n4. Daily cap accounting")
    check("counts toward today's cap", E.applied_today() == 1, str(E.applied_today()))

    # ---------------------------------------------------------------- step 5
    print("\n5. A form with an unanswerable question must STOP, not guess")
    with get_session() as s:
        job2 = Job(fingerprint=fingerprint("SecureCo", "ML Engineer"),
                   title="ML Engineer", company="SecureCo", location="Pune",
                   url="https://boards.greenhouse.io/secureco/jobs/2",
                   apply_url="https://boards.greenhouse.io/secureco/jobs/2",
                   source="greenhouse", ats="greenhouse", score=88,
                   description="Cleared work.", status=JobStatus.APPROVED.value)
        s.add(job2)
        s.commit()
        s.refresh(job2)
        job2_id = job2.id
    E.queue_approved()
    with get_session() as s:
        app2 = s.exec(select(Application).where(Application.job_id == job2_id)).first()
        app2_id = app2.id
        job2, app2 = s.get(Job, job2_id), s.get(Application, app2_id)
        page2 = blocked_form()
        res2 = E.apply_to_job(job2, app2, PROFILE, page2, cfg)

    check("halted instead of guessing", res2["status"] == "needs_input", res2["status"])
    check("did NOT submit", not page2.submitted)
    pending = res2.get("pending") or []
    check("escalated the right question", any("clearance" in p["question"].lower() for p in pending),
          "; ".join(p["question"][:48] for p in pending))

    E._persist(app2_id, job2_id, res2)
    with get_session() as s:
        app2 = s.get(Application, app2_id)
    check("tracker shows NEEDS_INPUT", app2.status == AppStatus.NEEDS_INPUT.value, app2.status)
    check("question surfaced to the dashboard drawer",
          len(json.loads(app2.pending_questions)) == 1)

    # ---------------------------------------------------------------- step 6
    print("\n6. You answer it in the drawer -> remembered -> requeued")
    question = json.loads(app2.pending_questions)[0]["question"]
    E.answer_pending(app2_id, {question: "No"})
    with get_session() as s:
        app2 = s.get(Application, app2_id)
        banked = s.exec(select(AnswerBank)).all()
    check("requeued for another attempt", app2.status == AppStatus.QUEUED.value, app2.status)
    check("pending questions cleared", json.loads(app2.pending_questions) == [])
    check("answer saved to the bank as user-confirmed",
          any(b.confirmed_by_user and b.answer == "No" for b in banked),
          f"{len(banked)} entries banked")

    # ---------------------------------------------------------------- step 7
    print("\n7. Retry now completes without asking again")
    with get_session() as s:
        job2, app2 = s.get(Job, job2_id), s.get(Application, app2_id)
        page3 = blocked_form()
        res3 = E.apply_to_job(job2, app2, PROFILE, page3, cfg)
    check("second attempt submitted", res3.get("ok") and res3["status"] == "applied",
          res3["status"])
    check("used the banked answer",
          page3.answers.get("Do you hold an active government security clearance? *") == "No",
          page3.answers.get("Do you hold an active government security clearance? *"))
    E._persist(app2_id, job2_id, res3)
    with get_session() as s:
        app2 = s.get(Application, app2_id)
    check("attempt count incremented", app2.attempts == 2, str(app2.attempts))
    check("finished as APPLIED", app2.status == AppStatus.APPLIED.value, app2.status)

    # ---------------------------------------------------------------- step 8
    print("\n8. Dashboard reflects all of it")
    from fastapi.testclient import TestClient

    from jobagent.server import app as api
    c = TestClient(api)
    apps = c.get("/api/applications").json()
    stats = c.get("/api/stats").json()
    check("tracker lists both applications", len(apps) == 2, str(len(apps)))
    check("each card carries its job", all(a["job"] for a in apps))
    check("stats show 2 applied", stats["applied_total"] == 2, str(stats["applied_total"]))
    check("no cards left needing input", stats["needs_input"] == 0, str(stats["needs_input"]))
    moved = c.patch(f"/api/applications/{app_id}", json={"status": "interview"})
    check("can drag a card to Interview", moved.status_code == 200
          and c.get("/api/stats").json()["interview"] == 1)

    # ---------------------------------------------------------------- summary
    print("\n" + "=" * 68)
    print(f"  {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        for f in FAIL:
            print(f"    FAILED: {f}")
    print("=" * 68 + "\n")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
