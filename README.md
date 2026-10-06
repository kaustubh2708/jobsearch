# Job Search Agent + Orbit

A human-supervised job-discovery workspace (an Antigravity agent that finds and verifies openings) and **Orbit**, a local-first website that turns those results into a calm job-search workflow:

**choose companies (or stay open to any above a pay floor) -> a detective agent hunts career portals, LinkedIn posts and job platforms -> an analyst filters by skills and fit -> a verifier double-checks every link -> your tracker shows Jobs available with referral options beside them.** Orbit drafts notes; you review and send. It never applies or messages for you.

[![Orbit promo (click to play the full video)](website/assets/orbit-promo.gif)](website/assets/orbit-promo.mp4)

<sub>Click the preview to watch the 24-second promo ([`website/assets/orbit-promo.mp4`](website/assets/orbit-promo.mp4)). Source, plan and share copy live in [`brag-output/`](brag-output/).</sub>

## Orbit website

```bash
cp website/sheets.config.example.json website/sheets.config.json   # add your Google Sheet IDs (git-ignored)
python3 website/export_data.py                                     # builds website/data/dashboard_data.json
python3 website/server.py                                          # http://127.0.0.1:8766/home
```

Pages: **Home**, **Apply now** (choose companies, today's picks) and **Tracker** (Jobs available, board, list). Full details, the sheet status/notes mapping and the file map are in [`website/README.md`](website/README.md).

Personal data stays local and is git-ignored: your tracker state, the generated snapshot, workbooks, contact lists and `config/profile.json` (copy `config/profile.example.json` to start).

---

## The discovery agent (Google Antigravity)

This is an Antigravity-native, human-supervised job-discovery workspace. It is designed to run inside Google Antigravity using the Gemini model available through your Google AI plan.

Google AI Pro provides higher Antigravity usage quota, but it is not a general-purpose Gemini API key for an unattended scraper. This project therefore uses Antigravity's agent/browser workflow and keeps login, CAPTCHA, and approval steps with you.

## What it does

- Reads the 137-company target list from `config/companies.txt`.
- Keeps the spelling/normalization decisions in `config/company_aliases.json`.
- Reads your role, location, experience, and salary preferences from `config/profile.json`.
- Searches official career pages first.
- Searches approved public job sources and user-visible browser pages second.
- Extracts and normalizes jobs into `data/jobs.json`.
- Scores jobs against your profile.
- Deduplicates results.
- Produces a review queue without applying or messaging automatically.

## What it does not do

- Scrape LinkedIn profiles or connection databases.
- Infer hidden LinkedIn relationships.
- Create fake accounts or bypass login, CAPTCHA, paywalls, robots rules, or anti-bot controls.
- Send connection requests, messages, recruiter outreach, or job applications.

## Run it in Antigravity

1. Open this folder as a workspace in Antigravity.
2. Start an agent task using the prompt in `RUN_SEARCH.md`.
3. Let the agent search public career pages.
4. When the browser reaches a login, CAPTCHA, or approval point, take over the browser yourself.
5. Review `data/jobs.json` and `data/last_run.md`.
6. Run the validator:

```bash
python3 scripts/validate_jobs.py --jobs data/jobs.json
```

The resulting records can be copied into the existing `job_search_dashboard.xlsx` workbook's `Openings` tab.

## Files

- `AGENTS.md` — operating rules for the Antigravity agent.
- `RUN_SEARCH.md` — reusable task prompt.
- `config/profile.json` — candidate search criteria (git-ignored; start from `config/profile.example.json`).
- `config/companies.txt` — deduplicated target company list.
- `config/job.schema.json` — normalized job record schema.
- `data/jobs.json` — agent output.
- `scripts/validate_jobs.py` — local validation and duplicate detection.
- `skills/job-discovery/SKILL.md` — detailed collector workflow.
