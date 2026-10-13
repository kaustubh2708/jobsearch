#!/usr/bin/env python3
"""Build a conservative Vrinda portfolio from preserved evidence."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
from eligibility_rules import parse_experience_requirement

ARCHIVE = DATA / "archive_vrinda_wave2_backup/jobs_vrinda_discovery_wave2_verified.json"
OUT = DATA / "jobs_vrinda_portfolio_20260930.json"
QUEUE = DATA / "review_queue_vrinda_portfolio_20260930.json"
DEAD = DATA / "dead_links_vrinda_portfolio_20260930.json"
REPORT = DATA / "last_run_vrinda_portfolio_20260930.md"


def evidence_backed(x):
    return (
        x.get("verification_status") == "verified"
        and x.get("link_status") in {"active_exact", "active_canonical_redirect"}
        and x.get("needs_verification") is False
        and x.get("actual_http_status") == 200
        and x.get("application_form_visible") is True
        and x.get("page_company_actual")
        and x.get("page_job_id_actual")
    )


def key(x):
    return (str(x.get("company", "")).lower().strip(), str(x.get("job_id", "")).lower().strip(), str(x.get("canonical_source_url") or x.get("source_url") or "").lower().strip())


def classify(x):
    title = str(x.get("title", ""))
    low = title.lower()
    raw_exp = str(x.get("experience_required", ""))
    exp = parse_experience_requirement(raw_exp)
    minimum = exp.get("min_years")
    if any(w in low for w in ("lead", "manager", "director", "architect", "staff")):
        return "exclude", "Leadership/staff/architect title is not a normal three-year target."
    has_high_plus = bool(re.search(r"\b(?:5|6|7|8|9|10)\s*\+\s*years?", raw_exp, re.I))
    if any(w in low for w in ("senior", "sr.", "software engineer 3", "engineer iii")) or has_high_plus or (minimum is not None and minimum >= 5):
        return "stretch", "Senior/SDE III or 5+ year requirement; retain only as a stretch application."
    if minimum is not None and minimum > 3:
        return "stretch", f"Minimum requirement is {minimum} years, above Vrinda's approximate three years."
    if any(w in low for w in ("software", "sde", "backend", "platform", "distributed", "data", "cloud", "full stack", "fullstack", "java", "python", ".net", "c++")):
        return "strong_match", "Relevant software/backend/platform role with page-level evidence."
    return "potential_match", "Page-verified technical role requiring manual fit review."


def main():
    checked = datetime.now(timezone.utc).isoformat()
    archive = json.loads(ARCHIVE.read_text())
    records, seen, excluded = [], set(), []
    for raw in archive:
        if not evidence_backed(raw):
            continue
        k = key(raw)
        if k in seen:
            continue
        seen.add(k)
        x = dict(raw)
        label, reason = classify(x)
        x.update({
            "portfolio_checked_at": checked,
            "portfolio_match_label": label,
            "portfolio_match_reason": reason,
            "evidence_origin": "antigravity_vrinda_wave2_archive",
        })
        if label == "exclude":
            excluded.append(x)
        else:
            records.append(x)

    review = [x for x in archive if x.get("verification_status") in {"lead", "blocked_manual_check"}]
    dead = [x for x in archive if x.get("link_status") in {"dead_404", "gone_410", "expired_or_closed"} or x.get("verification_status") in {"closed", "not_relevant", "not_eligible"}]
    OUT.write_text(json.dumps(records, indent=2))
    QUEUE.write_text(json.dumps(review + excluded, indent=2))
    DEAD.write_text(json.dumps(dead, indent=2))

    strong = [x for x in records if x["portfolio_match_label"] == "strong_match"]
    potential = [x for x in records if x["portfolio_match_label"] == "potential_match"]
    stretch = [x for x in records if x["portfolio_match_label"] == "stretch"]
    REPORT.write_text(f"""# Vrinda — Portfolio Run 2026-09-30

This is a conservative portfolio built from the preserved Vrinda Wave 2 evidence archive. Historical records are retained only when the individual page had stored HTTP 200 evidence, an application signal, page-company evidence, and a page job ID.

## Results

- Evidence-backed active exact records retained: **{len(records)}**
- Strong matches: **{len(strong)}**
- Potential matches: **{len(potential)}**
- Stretch matches: **{len(stretch)}**
- Excluded leadership/staff roles moved to review: **{len(excluded)}**
- Historical review/blocked leads: **{len(review)}**
- Dead/closed/not-relevant records: **{len(dead)}**

## Matching policy

Vrinda is treated as an approximately three-year backend/SDE candidate. Relevant SDE II/backend/platform/data/cloud roles are prioritized. Senior, Sr., SDE III, staff, principal, lead, architect, and manager roles are not silently treated as ordinary matches. They are stretch or excluded according to the title and stated experience requirement.

## Limitations

- This run uses preserved page-level evidence from the Vrinda archive; it did not perform a new logged-in LinkedIn browser pass.
- Salary is not treated as confirmed unless employer-published. Existing salary estimates remain labeled according to their stored status.
- The 45 Claude batch roles remain separate checkpoints because their schemas are inconsistent and have not been merged into this portfolio.

## Files

- `data/jobs_vrinda_portfolio_20260930.json`
- `data/review_queue_vrinda_portfolio_20260930.json`
- `data/dead_links_vrinda_portfolio_20260930.json`
""")
    print(json.dumps({"records": len(records), "strong": len(strong), "potential": len(potential), "stretch": len(stretch), "excluded": len(excluded), "review": len(review), "dead": len(dead)}, indent=2))


if __name__ == "__main__":
    main()
