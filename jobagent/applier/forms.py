"""Generic form intelligence: read a field, decide what to put in it, fill it.

Answers come from three places, in order:
  1. the profile in config.yaml        (deterministic — phone, notice period, CTC)
  2. the answer bank in SQLite         (something you or the agent answered before)
  3. the local LLM                     (novel screening questions)

Anything the LLM isn't confident about is escalated to you rather than guessed,
so the agent never invents a work-authorisation or salary answer.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlmodel import select

from ..config import load_config
from ..db import AnswerBank, get_session, utcnow
from ..llm import get_llm

log = logging.getLogger("jobagent.forms")


def qkey(q: str) -> str:
    norm = re.sub(r"[^a-z0-9 ]", "", (q or "").lower())
    norm = re.sub(r"\s+", " ", norm).strip()
    return hashlib.sha1(norm.encode()).hexdigest()[:20]


# --------------------------------------------------------------------------- #
#  Deterministic answers — these must never be hallucinated
# --------------------------------------------------------------------------- #
RULES: List[Tuple[str, str]] = [
    (r"first name|given name", "first_name"),
    (r"last name|surname|family name", "last_name"),
    (r"full name|^name$|your name|candidate name", "full_name"),
    (r"e-?mail", "email"),
    (r"phone|mobile|contact number|whatsapp", "phone"),
    (r"linkedin", "linkedin"),
    (r"github", "github"),
    (r"portfolio|website|personal site", "portfolio"),
    (r"current (city|location)|where are you (based|located)|your location", "location"),
    (r"total (years )?(of )?experience|years of experience|^experience", "years_experience"),
    (r"notice period|when can you (start|join)|availability to (start|join)|joining time", "notice"),
    (r"current (ctc|salary|compensation)|present ctc", "current_ctc"),
    (r"expected (ctc|salary|compensation)|salary expectation|desired (salary|compensation)", "expected_ctc"),
    (r"willing to relocate|open to relocat", "relocate"),
    (r"require (visa )?sponsorship|need sponsorship|will you (now or in the future) require", "sponsorship"),
    (r"authori[sz]ed to work|legally (authori|entitled)|right to work|work permit", "authorized"),
    (r"gender", "gender"),
    (r"date of birth|^dob", "dob"),
    (r"how did you hear|referral source|source", "how_heard"),
    (r"cover letter|why (do you want|are you interested)|tell us about yourself|message to.*hiring", "cover_letter"),
]


def deterministic_answer(question: str, cfg=None, cover_letter: str = "") -> Optional[str]:
    cfg = cfg or load_config()
    p = cfg.profile
    q = (question or "").lower()
    key = next((k for pat, k in RULES if re.search(pat, q)), None)
    if not key:
        return None

    name_parts = (p.full_name or "").split()
    yes_no = lambda b: "Yes" if b else "No"  # noqa: E731

    table: Dict[str, Optional[str]] = {
        "first_name": name_parts[0] if name_parts else "",
        "last_name": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
        "full_name": p.full_name,
        "email": p.email,
        "phone": p.phone,
        "linkedin": p.linkedin,
        "github": p.github,
        "portfolio": p.portfolio,
        "location": p.location,
        "years_experience": str(p.years_experience),
        "notice": (f"{p.notice_period_days} days"
                   if p.notice_period_days else "Immediate"),
        "current_ctc": (f"{p.current_ctc_lpa} LPA" if p.current_ctc_lpa else None),
        "expected_ctc": (f"{p.expected_ctc_lpa} LPA" if p.expected_ctc_lpa else None),
        "relocate": yes_no(p.willing_to_relocate),
        "sponsorship": yes_no(p.needs_visa_sponsorship),
        "authorized": yes_no(p.authorized_india),
        "gender": p.gender or None,
        "dob": p.date_of_birth or None,
        "how_heard": "Company website",
        "cover_letter": cover_letter or None,
    }
    val = table.get(key)
    return val if val else None


# --------------------------------------------------------------------------- #
#  Answer bank
# --------------------------------------------------------------------------- #
def bank_lookup(question: str) -> Optional[str]:
    with get_session() as s:
        row = s.exec(select(AnswerBank).where(AnswerBank.question_key == qkey(question))).first()
        if row:
            row.times_used += 1
            row.updated_at = utcnow()
            s.add(row)
            s.commit()
            return row.answer
    return None


def bank_store(question: str, answer: str, field_type: str = "text", confirmed: bool = False) -> None:
    with get_session() as s:
        row = s.exec(select(AnswerBank).where(AnswerBank.question_key == qkey(question))).first()
        if row:
            row.answer = answer
            row.confirmed_by_user = row.confirmed_by_user or confirmed
            row.updated_at = utcnow()
        else:
            row = AnswerBank(question_key=qkey(question), question_text=question[:500],
                             answer=answer, field_type=field_type, confirmed_by_user=confirmed)
        s.add(row)
        s.commit()


# --------------------------------------------------------------------------- #
#  LLM fallback
# --------------------------------------------------------------------------- #
ANSWER_SYSTEM = """You fill in job application forms on behalf of a candidate.
You answer ONLY from the candidate facts provided. You never invent experience, salary, dates or credentials.
If the facts do not support a confident answer, set confidence to "low".
Answers are short and literal — the value that goes in the box, nothing else.
You reply with a single valid JSON object."""

ANSWER_PROMPT = """CANDIDATE FACTS
{facts}

JOB
{job_title} at {job_company}

FORM FIELD
Question: {question}
Input type: {field_type}
{options_block}

Return JSON:
{{"answer": "the exact value to enter", "confidence": "high|medium|low", "why": "one short sentence"}}

Rules:
- For a select/radio field the answer MUST be exactly one of the listed options.
- For years-of-experience style numeric fields, return digits only.
- For yes/no questions, return exactly "Yes" or "No".
- If the question asks for something not in the candidate facts (a specific certification,
  a salary figure not given, a graduation date not given), confidence is "low"."""


def llm_answer(question: str, field_type: str, options: List[str],
               profile_facts: str, job_title: str, job_company: str) -> Dict[str, Any]:
    opts = ("Available options: " + " | ".join(options)) if options else ""
    res = get_llm().chat_json(
        ANSWER_SYSTEM,
        ANSWER_PROMPT.format(facts=profile_facts[:4000], job_title=job_title,
                             job_company=job_company, question=question[:600],
                             field_type=field_type, options_block=opts),
        fallback={"answer": "", "confidence": "low", "why": "llm unavailable"},
    )
    ans = str(res.get("answer", "")).strip()
    if options and ans:
        match = next((o for o in options if o.strip().lower() == ans.lower()), None)
        if not match:
            match = next((o for o in options if ans.lower() in o.lower() or o.lower() in ans.lower()), None)
        if match:
            ans = match
        else:
            res["confidence"] = "low"
    return {"answer": ans, "confidence": str(res.get("confidence", "low")).lower(),
            "why": str(res.get("why", ""))[:200]}


def profile_facts_blob(profile: Dict[str, Any], cfg=None) -> str:
    cfg = cfg or load_config()
    p = cfg.profile
    lines = [
        f"Name: {p.full_name}", f"Email: {p.email}", f"Phone: {p.phone}",
        f"Location: {p.location}", f"LinkedIn: {p.linkedin}", f"GitHub: {p.github}",
        f"Portfolio: {p.portfolio}",
        f"Total experience: {profile.get('total_years_experience', p.years_experience)} years",
        f"Seniority: {profile.get('seniority', '')}",
        f"Current role: {profile.get('current_role', '')}",
        f"Notice period: {p.notice_period_days} days",
        f"Current CTC: {p.current_ctc_lpa or 'not disclosed'} LPA",
        f"Expected CTC: {p.expected_ctc_lpa or 'negotiable'} LPA",
        f"Willing to relocate: {p.willing_to_relocate}",
        f"Needs visa sponsorship: {p.needs_visa_sponsorship}",
        f"Authorised to work in India: {p.authorized_india}",
        "Skills: " + ", ".join((profile.get("hard_skills") or [])[:60]),
        "Domains: " + ", ".join((profile.get("domains") or [])[:10]),
    ]
    for e in (profile.get("experience") or [])[:4]:
        lines.append(f"Experience: {e.get('title','')} at {e.get('company','')} ({e.get('duration','')})")
    for ed in (profile.get("education") or [])[:2]:
        lines.append(f"Education: {ed.get('degree','')} {ed.get('field','')}, {ed.get('institution','')} {ed.get('year','')}")
    return "\n".join(l for l in lines if l.strip().split(": ", 1)[-1] not in ("", "None"))


# --------------------------------------------------------------------------- #
#  The resolver used by every applier
# --------------------------------------------------------------------------- #
class AnswerResolver:
    def __init__(self, profile: Dict[str, Any], job_title: str, job_company: str,
                 cover_letter: str = "", cfg=None):
        self.cfg = cfg or load_config()
        self.profile = profile
        self.facts = profile_facts_blob(profile, self.cfg)
        self.job_title = job_title
        self.job_company = job_company
        self.cover_letter = cover_letter
        self.used: Dict[str, str] = {}
        self.unresolved: List[Dict[str, Any]] = []

    def resolve(self, question: str, field_type: str = "text",
                options: Optional[List[str]] = None, required: bool = True) -> Optional[str]:
        options = options or []

        ans = deterministic_answer(question, self.cfg, self.cover_letter)
        src = "profile"
        if ans is None:
            ans = bank_lookup(question)
            src = "bank"
        if ans is None:
            res = llm_answer(question, field_type, options, self.facts,
                             self.job_title, self.job_company)
            ans, src = res["answer"], f"llm:{res['confidence']}"
            if res["confidence"] == "low" or not ans:
                if required and self.cfg.apply.ask_on_unknown_question:
                    self.unresolved.append({
                        "question": question, "field_type": field_type,
                        "options": options, "suggested": ans, "why": res.get("why", ""),
                    })
                    return None
                if not ans:
                    return None
            else:
                bank_store(question, ans, field_type)

        # coerce to a valid option where the widget demands one
        if options and ans not in options:
            m = next((o for o in options if ans.lower() in o.lower() or o.lower() in ans.lower()), None)
            if m:
                ans = m
            elif required:
                self.unresolved.append({"question": question, "field_type": field_type,
                                        "options": options, "suggested": ans,
                                        "why": "no matching option"})
                return None

        self.used[question[:200]] = f"{ans}  [{src}]"
        return ans
