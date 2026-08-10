"""Configuration loading. Single source of truth = config.yaml at repo root."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
# JOBAGENT_DATA_DIR lets you move the database and browser profile off the repo
# — useful if the repo lives on a network drive or a filesystem without proper
# file locking (SQLite needs locking).
DATA_DIR = Path(os.environ.get("JOBAGENT_DATA_DIR", ROOT / "data")).expanduser()
LOG_DIR = Path(os.environ.get("JOBAGENT_LOG_DIR", ROOT / "logs")).expanduser()
BROWSER_PROFILE_DIR = DATA_DIR / "browser_profile"
EVIDENCE_DIR = DATA_DIR / "evidence"
DOCS_DIR = DATA_DIR / "generated_docs"
DB_PATH = DATA_DIR / "jobagent.db"

for _d in (DATA_DIR, LOG_DIR, BROWSER_PROFILE_DIR, EVIDENCE_DIR, DOCS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


class Profile(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = "India"
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    years_experience: int = 0
    current_ctc_lpa: Optional[float] = None
    expected_ctc_lpa: Optional[float] = None
    notice_period_days: int = 30
    willing_to_relocate: bool = True
    needs_visa_sponsorship: bool = False
    authorized_india: bool = True
    gender: str = ""
    date_of_birth: str = ""


class ResumeCfg(BaseModel):
    dir: str = "resume"
    upload_pdf: str = ""


class LLMCfg(BaseModel):
    host: str = "http://localhost:11434"
    chat_model: str = "qwen2.5:14b-instruct"
    embed_model: str = "nomic-embed-text"
    temperature: float = 0.1
    num_ctx: int = 8192
    request_timeout_s: int = 240


class SearchCfg(BaseModel):
    queries: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=lambda: ["India"])
    remote_ok: bool = True
    hours_old: int = 168
    target_jobs_per_day: int = 20
    min_jobs_per_day: int = 15
    max_jobs_per_day: int = 25
    exclude_title_keywords: List[str] = Field(default_factory=list)
    exclude_companies: List[str] = Field(default_factory=list)
    min_salary_lpa: Optional[float] = None


class MatchCfg(BaseModel):
    embed_threshold: float = 0.55
    llm_min_score: int = 70
    strong_match_score: int = 85


class ApplyCfg(BaseModel):
    auto_submit: bool = False
    daily_apply_cap: int = 15
    delay_between_s: List[int] = Field(default_factory=lambda: [45, 120])
    ask_on_unknown_question: bool = True
    generate_cover_letter: bool = True
    screenshot_evidence: bool = True
    headless: bool = False


class ScheduleCfg(BaseModel):
    enabled: bool = True
    discovery_time: str = "08:30"
    discovery_time_2: Optional[str] = "18:30"
    apply_poll_minutes: int = 10


class ServerCfg(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765
    open_browser_on_start: bool = True


class Config(BaseModel):
    profile: Profile = Field(default_factory=Profile)
    resume: ResumeCfg = Field(default_factory=ResumeCfg)
    llm: LLMCfg = Field(default_factory=LLMCfg)
    search: SearchCfg = Field(default_factory=SearchCfg)
    sources: Dict[str, Any] = Field(default_factory=dict)
    matching: MatchCfg = Field(default_factory=MatchCfg)
    apply: ApplyCfg = Field(default_factory=ApplyCfg)
    schedule: ScheduleCfg = Field(default_factory=ScheduleCfg)
    server: ServerCfg = Field(default_factory=ServerCfg)

    # ---- helpers -----------------------------------------------------------
    def source_enabled(self, name: str) -> bool:
        s = self.sources.get(name)
        if isinstance(s, dict):
            return bool(s.get("enabled", False))
        return False

    def source_limit(self, name: str, default: int = 30) -> int:
        s = self.sources.get(name)
        if isinstance(s, dict):
            return int(s.get("max_results", default))
        return default

    @property
    def resume_dir(self) -> Path:
        return (ROOT / self.resume.dir).resolve()

    @property
    def resume_pdf(self) -> Optional[Path]:
        if not self.resume.upload_pdf:
            return None
        p = (ROOT / self.resume.upload_pdf).resolve()
        return p if p.exists() else None


_CACHE: Optional[Config] = None


def load_config(path: Optional[Path] = None, reload: bool = False) -> Config:
    global _CACHE
    if _CACHE is not None and not reload:
        return _CACHE
    path = path or Path(os.environ.get("JOBAGENT_CONFIG", ROOT / "config.yaml"))
    raw: Dict[str, Any] = {}
    if Path(path).exists():
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    _CACHE = Config(**raw)
    return _CACHE


def save_config(cfg: Config, path: Optional[Path] = None) -> None:
    """Write config back to disk (used when the dashboard edits settings)."""
    global _CACHE
    path = path or Path(os.environ.get("JOBAGENT_CONFIG", ROOT / "config.yaml"))
    Path(path).write_text(
        yaml.safe_dump(cfg.model_dump(mode="json"), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    _CACHE = cfg
