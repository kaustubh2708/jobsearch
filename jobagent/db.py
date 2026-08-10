"""SQLite schema + helpers. Two boards: the review queue and the tracker."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus(str, Enum):
    """Review board — you drive this."""
    PENDING = "pending"        # scored, waiting on your review
    APPROVED = "approved"      # you said yes -> applier picks it up
    REJECTED = "rejected"      # you said no
    ARCHIVED = "archived"      # auto-dropped, score below threshold


class AppStatus(str, Enum):
    """Tracker board — mostly agent-driven, you can override."""
    QUEUED = "queued"
    APPLYING = "applying"
    NEEDS_INPUT = "needs_input"   # form asked something we couldn't answer
    APPLIED = "applied"
    FAILED = "failed"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    fingerprint: str = Field(index=True, unique=True)

    title: str = ""
    company: str = ""
    location: str = ""
    is_remote: bool = False
    url: str = ""
    apply_url: str = ""
    source: str = ""                       # linkedin | naukri | indeed | google | wellfound | greenhouse ...
    ats: str = ""                          # greenhouse | lever | ashby | linkedin_easy | naukri | unknown
    description: str = Field(default="", sa_column=Column(Text))
    salary_text: str = ""
    salary_min_lpa: Optional[float] = None
    salary_max_lpa: Optional[float] = None
    posted_at: Optional[datetime] = None
    discovered_at: datetime = Field(default_factory=utcnow, index=True)

    # scoring
    embed_score: float = 0.0
    score: int = 0
    verdict: str = ""
    reasoning: str = Field(default="", sa_column=Column(Text))
    matched_skills: str = Field(default="[]", sa_column=Column(Text))
    missing_skills: str = Field(default="[]", sa_column=Column(Text))
    red_flags: str = Field(default="[]", sa_column=Column(Text))
    seniority_fit: str = ""

    status: str = Field(default=JobStatus.PENDING.value, index=True)
    reviewed_at: Optional[datetime] = None

    # --- convenience -------------------------------------------------------
    def lists(self) -> Dict[str, List[str]]:
        out = {}
        for f in ("matched_skills", "missing_skills", "red_flags"):
            try:
                out[f] = json.loads(getattr(self, f) or "[]")
            except Exception:
                out[f] = []
        return out

    def as_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d.update(self.lists())
        for k in ("posted_at", "discovered_at", "reviewed_at"):
            v = d.get(k)
            d[k] = v.isoformat() if isinstance(v, datetime) else v
        return d


class Application(SQLModel, table=True):
    __tablename__ = "applications"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(index=True)

    status: str = Field(default=AppStatus.QUEUED.value, index=True)
    attempts: int = 0
    method: str = ""                        # linkedin_easy_apply | greenhouse | manual ...
    submitted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    cover_letter: str = Field(default="", sa_column=Column(Text))
    answers: str = Field(default="{}", sa_column=Column(Text))     # question -> answer used
    pending_questions: str = Field(default="[]", sa_column=Column(Text))
    error: str = Field(default="", sa_column=Column(Text))
    evidence_path: str = ""
    notes: str = Field(default="", sa_column=Column(Text))
    external_url: str = ""

    def as_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        for k in ("submitted_at", "created_at", "updated_at"):
            v = d.get(k)
            d[k] = v.isoformat() if isinstance(v, datetime) else v
        for k in ("answers", "pending_questions"):
            try:
                d[k] = json.loads(d.get(k) or ("{}" if k == "answers" else "[]"))
            except Exception:
                d[k] = {} if k == "answers" else []
        return d


class AnswerBank(SQLModel, table=True):
    """Remembers how a given screening question was answered, so the agent
    gets faster and more consistent the more it applies."""
    __tablename__ = "answer_bank"

    id: Optional[int] = Field(default=None, primary_key=True)
    question_key: str = Field(index=True, unique=True)
    question_text: str = ""
    answer: str = Field(default="", sa_column=Column(Text))
    field_type: str = "text"
    times_used: int = 0
    confirmed_by_user: bool = False
    updated_at: datetime = Field(default_factory=utcnow)


class SkillLibrary(SQLModel, table=True):
    """One row = the parsed snapshot of your resume."""
    __tablename__ = "skill_library"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    source_file: str = ""
    raw_text: str = Field(default="", sa_column=Column(Text))
    payload: str = Field(default="{}", sa_column=Column(Text))     # structured JSON
    embedding: str = Field(default="[]", sa_column=Column(Text))
    is_active: bool = True

    def data(self) -> Dict[str, Any]:
        try:
            return json.loads(self.payload or "{}")
        except Exception:
            return {}


class RunLog(SQLModel, table=True):
    __tablename__ = "run_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=utcnow, index=True)
    kind: str = "info"                      # info | warn | error | discovery | apply
    message: str = Field(default="", sa_column=Column(Text))
    meta: str = Field(default="{}", sa_column=Column(Text))


# ---------------------------------------------------------------------------

def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def fingerprint(company: str, title: str, location: str = "") -> str:
    key = f"{(company or '').strip().lower()}|{(title or '').strip().lower()}|{(location or '').strip().lower()[:24]}"
    return hashlib.sha1(key.encode()).hexdigest()


def log(kind: str, message: str, **meta: Any) -> None:
    try:
        with get_session() as s:
            s.add(RunLog(kind=kind, message=message, meta=json.dumps(meta, default=str)))
            s.commit()
    except Exception:
        pass


def active_skill_library() -> Optional[SkillLibrary]:
    with get_session() as s:
        return s.exec(
            select(SkillLibrary).where(SkillLibrary.is_active == True)  # noqa: E712
            .order_by(SkillLibrary.created_at.desc())
        ).first()
