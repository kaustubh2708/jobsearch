"""Shared experience parsing and candidate eligibility rules.

The search agents may discover a role from a title, a card, an ATS page, or a
job description.  This module is deliberately conservative: a fresher role
must not become eligible merely because its title contains SDE I or Engineer.
"""

from __future__ import annotations

import re
from typing import Any


_RANGE = re.compile(r"\b(\d+)\s*(?:-|–|—|to)\s*(\d+)\s*years?\b", re.I)
_PLUS = re.compile(r"\b(\d+)\s*\+\s*years?\b", re.I)
_PLAIN = re.compile(
    r"\b(?:minimum|at least|min\.?|requires?|need(?:s)?|of)\s+(\d+)\s*years?\b",
    re.I,
)
_YEARS = re.compile(r"\b(\d+)\s+years?\s+(?:of\s+)?(?:professional|industry|relevant|work|software|engineering|experience)\b", re.I)

FRESHER_SIGNALS = (
    "fresher", "new grad", "new graduate", "graduate", "campus", "early career",
    "entry level", "entry-level", "class of 2026", "2026 batch", "intern",
    "internship", "trainee", "apprentice", "resident", "no prior experience",
)


def parse_experience_requirement(text: str | None) -> dict[str, Any]:
    """Return conservative min/max experience evidence from free text."""
    raw = (text or "").strip()
    low = raw.lower()
    ranges = [(int(a), int(b)) for a, b in _RANGE.findall(raw)]
    plus = [int(x) for x in _PLUS.findall(raw)]
    plain = [int(x) for x in _PLAIN.findall(raw)]
    years = [int(x) for x in _YEARS.findall(raw)]

    mins = [a for a, _ in ranges] + plus + plain + years
    maxes = [b for _, b in ranges]
    explicit_zero_to_two = bool(re.search(r"\b0\s*(?:-|–|—|to)\s*2\s*years?\b", low))
    fresher_signal = any(s in low for s in FRESHER_SIGNALS)

    return {
        "raw": raw,
        "min_years": min(mins) if mins else None,
        "max_years": max(maxes) if maxes else None,
        "has_numeric_requirement": bool(mins or maxes),
        "fresher_signal": fresher_signal,
        "explicit_zero_to_two": explicit_zero_to_two,
    }


def evaluate_vaanya_eligibility(title: str, experience_text: str | None, description: str | None = None) -> dict[str, Any]:
    """Apply the Class-of-2026 gate.

    A role requiring 2+ years, 2 years, 2–4 years, or a higher minimum is not
    a fresher match.  A 0–2 role remains eligible when the posting also has a
    genuine entry-level/intern/campus signal.  Unknown requirements are sent
    to review rather than silently treated as fresher-eligible.
    """
    combined = " ".join(x for x in [experience_text, description, title] if x)
    parsed = parse_experience_requirement(combined)
    title_low = title.lower()
    intern_title = any(x in title_low for x in ("intern", "trainee", "apprentice", "resident"))
    entry_title = any(x in title_low for x in ("graduate", "campus", "new grad", "entry", "junior"))

    minimum = parsed["min_years"]
    if minimum is not None and minimum >= 2:
        return {"decision": "not_eligible", "reason": f"Requires at least {minimum} years of experience; Vaanya is a fresher.", **parsed}
    if minimum == 1 and not (parsed["fresher_signal"] or parsed["explicit_zero_to_two"] or intern_title or entry_title):
        return {"decision": "review", "reason": "Requires 1+ year of experience without a clear fresher or campus exception.", **parsed}
    if parsed["explicit_zero_to_two"] or parsed["fresher_signal"] or intern_title or entry_title:
        return {"decision": "eligible", "reason": "Contains an explicit fresher, campus, intern, graduate, or 0–2-year eligibility signal.", **parsed}
    if minimum is None:
        return {"decision": "review", "reason": "No reliable experience requirement or fresher signal was found.", **parsed}
    return {"decision": "review", "reason": "Experience requirement needs manual confirmation.", **parsed}
