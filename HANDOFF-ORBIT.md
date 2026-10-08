# Handoff — Orbit (as of 2026-10-08)

Read [`CLAUDE.md`](CLAUDE.md) first for architecture, contracts and rules. This file is the *state of play*: what works, how to resume, what is unfinished.

## State of play

- **Branch:** `master` on `github.com/kaustubh2708/jobsearch`. Last pushed work: README architecture rewrite. v2 and these docs are added in the commit that introduced this file.
- **Working tree is shared with the discovery agent.** It regenerates `data/*.json` (many new `wave12`–`wave14` and audit files), and edited `AGENTS.md`, `config/search_switches.json`, `scripts/export_and_validate_jobs.py`, `scripts/generate_last_run.py`. Those changes are *not* mine and may be uncommitted; leave them to their owner unless asked.
- **Servers:** none are meant to stay running. Start with `python3 website/server.py` (port 8766).
- **User tracker state** is in `website/data/dashboard_state.json`. It currently holds only the user's own records (a few Vaanya edits and one Indeed "applied 5 Oct" record) plus `seen`/`newOpportunities`. Test keys were stripped.

## What works (verified in the browser)

- v1: Home, Apply now (both tabs, real link verification), Tracker (Jobs available, Board, List), directories, ⌘K, dark mode, mobile layouts.
- Sheet ingestion: Vrinda ≈ 39 Applied / 12 Watching / 4 Closed / 1 Interviewing, Vaanya ≈ 8 Applied / 2 Closed / 1 Watching; applied dates drive the ring, rhythm and follow-ups (27 due).
- v2 (`/v2`): keyboard flow, undo, scope drawer (inbox 197 → 7 with one company and a 20 LPA floor), both themes, sheet-derived stages.

## How to resume

1. `git pull`, then run the three commands in `CLAUDE.md` → *Quick commands*.
2. Open `/home`, `/apply`, `/person`, `/v2`. If something looks stale, hard-refresh assets (see Gotchas).
3. Before any push: scan staged content for names, employers, sheet IDs, emails, `linkedin.com/in/`; confirm `.gitignore` still covers the personal files.

## Open items and ideas (none are blocking)

1. **Share the fit logic.** The scoring heuristic exists in `product.js` and (simplified) in `v2/v2.js`, and job identity is implemented three times. A small shared module would remove the duplication; it needs care because identity changes orphan saved state.
2. **Unreferenced workbooks** in `website/data/*.xlsx` (three files, ignored by git). Confirm with the owner whether they can be deleted.
3. **Antigravity wording** remains in `AGENTS.md` (title) and other discovery docs; only the README was renamed to "AI agent" on request.
4. **Real-time hunting.** The "hunt" reads the latest sheet snapshot; the discovery agent itself runs separately. A button that triggers a supervised agent run, or a scheduled `export_data.py`, would close the loop.
5. **Verification coverage.** Many ATS sites block automatic checks and show as "check it yourself". A headless-browser verifier could raise confidence but must respect the "never bypass anti-bot or CAPTCHA" rule.
6. **Titles for link-only entries** read "Role at <Company>" when the page is LinkedIn or script-rendered; the user can name them in the sheet.
7. **v2 gaps:** no company directory, no weekly goals/rhythm, no onboarding tuning (it reads `meta.prefs` if v1 wrote them), no drag-and-drop board. Add only if the owner prefers v2.
8. **Tests.** There is no automated test suite. The parser (`classify_status`, `row_signals`) is the best first target for unit tests with real phrases from the sheets.

## Decisions already made with the owner

- Public repo, personal data kept out (code and docs only); push replaced the old project on `master` (history kept).
- Navigation is exactly Home / Apply now / Tracker.
- `DA` and `ECE role` mean "not a pure tech role but close to the candidate's skills" (tag only). Ignore the "Role not named in your sheet" rows.
- No AI attribution in commits.
- Some employers are paused for discovery (see `AGENTS.md`); the website simply displays whatever the sheets contain.

## Verification checklist for the next change

- [ ] `node --check` on every JS file touched; `python3 -m py_compile` on Python.
- [ ] Load `/home`, `/apply?tab=choose`, `/apply?tab=picks`, `/person?view=board|available|list`, `/vaanya`, `/vrinda`, `/v2`; console clean.
- [ ] Strip test keys from `dashboard_state.json`.
- [ ] `git status`: stage only your files; scan for personal data; commit without attribution trailers.
