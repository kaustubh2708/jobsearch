#!/usr/bin/env python3
"""Build a conservative Vaanya portfolio from preserved evidence baselines."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
from eligibility_rules import evaluate_vaanya_eligibility

ARCHIVE = DATA / "vaanya_data_archive/jobs_vaanya_discovery_wave2_verified.json"
CLAUDE = DATA / "jobs_vaanya_claude.json"
LIVE = DATA / "jobs_vaanya_incremental_20260930_v2.json"
OUT = DATA / "jobs_vaanya_portfolio_20260930.json"
QUEUE = DATA / "review_queue_vaanya_portfolio_20260930.json"
DEAD = DATA / "dead_links_vaanya_portfolio_20260930.json"
REPORT = DATA / "last_run_vaanya_portfolio_20260930.md"


def evidence_backed(x):
    return (
        x.get("verification_status") == "verified"
        and x.get("link_status") == "active_exact"
        and x.get("needs_verification") is False
        and x.get("actual_http_status") == 200
        and x.get("application_form_visible") is True
        and x.get("page_company_actual")
        and x.get("page_location_actual")
        and x.get("page_job_id_actual")
    )


def key(x):
    return (str(x.get("company", "")).lower().strip(), str(x.get("job_id", "")).lower().strip(), str(x.get("canonical_source_url") or x.get("source_url") or "").lower().strip())


def main():
    checked = datetime.now(timezone.utc).isoformat()
    archive = json.loads(ARCHIVE.read_text())
    claude = json.loads(CLAUDE.read_text()) if CLAUDE.exists() else []
    live = json.loads(LIVE.read_text()) if LIVE.exists() else []

    records = []
    seen = set()
    manual = []
    excluded = []

    for source_name, source in (("antigravity_archive", archive), ("claude_pilot", claude)):
        for raw in source:
            if not evidence_backed(raw):
                continue
            k = key(raw)
            if k in seen:
                continue
            seen.add(k)
            x = dict(raw)
            e = evaluate_vaanya_eligibility(x.get("title", ""), x.get("experience_required"), x.get("notes"))
            x.update({
                "evidence_origin": source_name,
                "portfolio_checked_at": checked,
                "experience_eligibility_decision": e["decision"],
                "experience_eligibility_reason": e["reason"],
                "experience_min_years_detected": e.get("min_years"),
                "experience_max_years_detected": e.get("max_years"),
            })
            if e["decision"] == "eligible":
                x["portfolio_status"] = "eligible_active_exact"
                records.append(x)
            elif e["decision"] == "review":
                x["portfolio_status"] = "active_exact_manual_eligibility_review"
                records.append(x)
                manual.append(x)
            else:
                x["portfolio_status"] = "excluded_experience_mismatch"
                excluded.append(x)

    # Preserve live-run results only if they pass the same evidence gate.
    for raw in live:
        if not evidence_backed(raw):
            continue
        k = key(raw)
        if k in seen:
            continue
        seen.add(k)
        x = dict(raw)
        x["evidence_origin"] = "live_public_portal_20260930"
        x["portfolio_checked_at"] = checked
        x["portfolio_status"] = "eligible_active_exact"
        records.append(x)

    historical_review = [x for x in archive if x.get("verification_status") in {"lead", "blocked_manual_check", "browser_manual_check"}]
    queue = historical_review + manual
    dead = [x for x in archive if x.get("link_status") in {"dead_404", "gone_410", "expired_or_closed"} or x.get("verification_status") in {"closed", "not_relevant", "not_eligible"}]

    OUT.write_text(json.dumps(records, indent=2))
    QUEUE.write_text(json.dumps(queue, indent=2))
    DEAD.write_text(json.dumps(dead, indent=2))

    eligible = [x for x in records if x.get("portfolio_status") == "eligible_active_exact"]
    report = f"""# Vaanya — Portfolio Run 2026-09-30

This is a conservative continuation run using preserved Antigravity evidence, the Claude pilot, and a fresh public-portal pass.

## Results

- Evidence-backed active exact records retained: **{len(records)}**
- Fresher/graduate eligible: **{len(eligible)}**
- Active exact but manual experience review: **{len(manual)}**
- Historical review/blocked queue records: **{len(queue)}**
- Dead/closed/excluded records: **{len(dead)}**
- New records from the fresh public-portal pass: **{len([x for x in live if evidence_backed(x)])}**

## Fresh public-portal pass

The 137-company portal map was checked in resumable batches. It produced candidate pages, but no new record passed every gate: direct requisition URL, HTTP 200, application signal, India evidence, and Vaanya's strict eligibility rule. Generic career and early-career landing pages were deliberately rejected.

## Eligibility rule

Roles requiring a minimum of two or more years were excluded. Roles requiring one year without a clear fresher/campus exception remain in manual review. Missing experience requirements are not treated as 0–2 years.

## Limitations

- The fresh pass used public ATS/HTML access and did not use a logged-in LinkedIn browser session.
- Historical records are retained only when their stored evidence passed the strict evidence gate.
- Salary values are not re-certified by this run; use each record's salary status and source evidence.
- Hiring drives remain a separate workstream and are not silently inferred from normal job postings.

## Files

- `data/jobs_vaanya_portfolio_20260930.json`
- `data/review_queue_vaanya_portfolio_20260930.json`
- `data/dead_links_vaanya_portfolio_20260930.json`
- `data/jobs_vaanya_incremental_20260930_v2.json`
"""
    REPORT.write_text(report)
    print(json.dumps({"records": len(records), "eligible": len(eligible), "manual_review": len(manual), "queue": len(queue), "dead": len(dead), "new_live": len([x for x in live if evidence_backed(x)])}, indent=2))


if __name__ == "__main__":
    main()

