"""Two-stage compatibility scoring.

Stage 1 — embedding cosine similarity between your profile and the JD.
          Cheap (~30ms), runs on every job, throws out the obvious noise.
Stage 2 — the reasoning model reads the JD properly and returns a structured
          verdict: score, why, matched skills, gaps, red flags, seniority fit.

Two stages because running a 14B model over 400 raw postings a day would take
hours; the embedding pass typically removes 70-80% of them in seconds.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from .config import load_config
from .llm import cosine, get_llm
from .sources.base import RawJob

log = logging.getLogger("jobagent.matcher")

SCORE_SYSTEM = """You are a brutally realistic technical recruiter who screens candidates for the Indian job market.
You are not optimistic and you do not flatter. A high score means the candidate would genuinely clear this company's screening round.
You reply with a single valid JSON object and nothing else."""

SCORE_PROMPT = """Score how well this candidate fits this job.

CANDIDATE
Headline: {headline}
Seniority: {seniority} | {years} years experience
Core skills: {core_skills}
All skills: {all_skills}
Domains: {domains}
Recent roles: {recent_roles}
Notable employers: {companies}
Should NOT be matched to: {red_lines}

JOB
Title: {title}
Company: {company}
Location: {location}{remote}
Salary: {salary}
Source: {source}

JOB DESCRIPTION
---
{description}
---

Return JSON:
{{
  "score": 0-100,
  "verdict": "one blunt sentence on whether to apply",
  "reasoning": "2-4 sentences. Reference specific requirements from the JD and specific evidence from the candidate. No generic filler.",
  "matched_skills": ["skills the JD asks for that the candidate demonstrably has"],
  "missing_skills": ["skills the JD asks for that the candidate lacks"],
  "red_flags": ["concrete concerns: seniority mismatch, wrong domain, unpaid, vague JD, staffing agency, contract-to-hire, relocation required, obvious mass-posting"],
  "seniority_fit": "underqualified|slight_stretch|good_fit|overqualified",
  "application_priority": "high|medium|low"
}}

Scoring discipline:
- 90-100: candidate clearly exceeds the bar, near-certain interview
- 75-89:  strong, genuine fit, worth applying
- 60-74:  plausible but with real gaps
- 40-59:  weak fit, likely auto-rejected by their ATS
- 0-39:   wrong role, wrong seniority, or wrong domain entirely
Penalise heavily for: seniority mismatch in either direction, staffing/consultancy
mass-postings, JDs that list 25 unrelated technologies, and roles that appear in
the candidate's "should NOT be matched to" list."""


class Matcher:
    def __init__(self, profile: Dict[str, Any], profile_embedding: Optional[List[float]] = None, cfg=None):
        self.cfg = cfg or load_config()
        self.profile = profile or {}
        self.llm = get_llm()
        self.pemb = profile_embedding or []
        self._skillset = {s.lower() for s in (profile.get("hard_skills") or [])}

    # ---- stage 1 ----------------------------------------------------------
    def embed_score(self, job: RawJob) -> float:
        text = f"{job.title} at {job.company}. {job.location}. {job.description[:4000]}"
        try:
            e = self.llm.embed(text)
        except Exception as ex:  # noqa: BLE001
            log.debug("embed failed for %s: %s", job.title, ex)
            return 1.0                      # fail open — let the LLM decide
        sim = cosine(self.pemb, e) if self.pemb else 1.0
        # small keyword bonus so a perfect-title match never gets filtered out
        return min(1.0, sim + self._keyword_bonus(job))

    def _keyword_bonus(self, job: RawJob) -> float:
        hay = f"{job.title} {job.description[:1500]}".lower()
        hits = sum(1 for s in self._skillset if len(s) > 3 and s in hay)
        title_hit = any(
            r.lower() in job.title.lower()
            for r in (self.profile.get("target_roles") or [])[:10]
        )
        return min(0.15, hits * 0.01) + (0.10 if title_hit else 0.0)

    # ---- stage 2 ----------------------------------------------------------
    def llm_score(self, job: RawJob) -> Dict[str, Any]:
        p = self.profile
        recent = "; ".join(
            f"{e.get('title','')} @ {e.get('company','')}"
            for e in (p.get("experience") or [])[:4]
        )
        prompt = SCORE_PROMPT.format(
            headline=p.get("headline", ""),
            seniority=p.get("seniority", "mid"),
            years=p.get("total_years_experience", self.cfg.profile.years_experience),
            core_skills=", ".join((p.get("core_skills") or [])[:20]),
            all_skills=", ".join((p.get("hard_skills") or [])[:70]),
            domains=", ".join((p.get("domains") or [])[:10]),
            recent_roles=recent,
            companies=", ".join((p.get("notable_companies") or [])[:8]),
            red_lines="; ".join((p.get("red_lines") or [])[:8]) or "none specified",
            title=job.title, company=job.company, location=job.location,
            remote=" (remote)" if job.is_remote else "",
            salary=job.salary_text or (
                f"{job.salary_min_lpa}-{job.salary_max_lpa} LPA"
                if job.salary_min_lpa else "not disclosed"),
            source=job.source,
            description=(job.description or "(no description available)")[:9000],
        )
        data = self.llm.chat_json(SCORE_SYSTEM, prompt, fallback={})
        return _normalise(data)

    def score(self, job: RawJob) -> Tuple[float, Optional[Dict[str, Any]]]:
        """Returns (embed_score, llm_result_or_None_if_filtered_at_stage_1)."""
        es = self.embed_score(job)
        if es < self.cfg.matching.embed_threshold:
            return es, None
        return es, self.llm_score(job)


def _normalise(d: Dict[str, Any]) -> Dict[str, Any]:
    def as_list(v):
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()][:15]
        if isinstance(v, str) and v.strip():
            return [p.strip() for p in re.split(r"[;,]", v) if p.strip()][:15]
        return []

    try:
        score = int(float(d.get("score", 0)))
    except Exception:
        score = 0
    return {
        "score": max(0, min(100, score)),
        "verdict": str(d.get("verdict", ""))[:400],
        "reasoning": str(d.get("reasoning", ""))[:2000],
        "matched_skills": as_list(d.get("matched_skills")),
        "missing_skills": as_list(d.get("missing_skills")),
        "red_flags": as_list(d.get("red_flags")),
        "seniority_fit": str(d.get("seniority_fit", ""))[:40],
        "application_priority": str(d.get("application_priority", "medium"))[:10],
    }


def derive_queries(profile: Dict[str, Any], cfg=None) -> List[str]:
    """Search terms: config override, else whatever the LLM pulled off the resume."""
    cfg = cfg or load_config()
    if cfg.search.queries:
        return cfg.search.queries
    q = (profile.get("target_role_keywords") or []) + (profile.get("target_roles") or [])
    seen, out = set(), []
    for x in q:
        k = x.lower().strip()
        if k and k not in seen and len(k) < 60:
            seen.add(k)
            out.append(x.strip())
    return out[:10] or ["software engineer"]
