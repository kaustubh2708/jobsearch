# CLAUDE.md — project memory for AI coding agents

This file is the long-lived context for anyone (human or AI) changing this repo. It records what the project is, how it is built, the rules that matter, and a chronological log of what has been done. For the *current* state and next steps, read [`HANDOFF-ORBIT.md`](HANDOFF-ORBIT.md).

> **Two systems live here.** (1) The **discovery AI agent** (`AGENTS.md`, `config/`, `scripts/`, `data/`) that finds and verifies openings. (2) **Orbit**, the local website (`website/`) that turns the results into a workflow. `AGENTS.md` governs the discovery agent only. Do not edit it as part of website work.

## Quick commands

```bash
cp website/sheets.config.example.json website/sheets.config.json   # once; put real Google Sheet IDs in (git-ignored)
python3 website/export_data.py        # sheets -> website/data/dashboard_data.json (falls back to local workbooks)
python3 website/server.py             # http://127.0.0.1:8766  (/home, /apply, /person, /v2)
node --check website/app.js           # also home.js, product.js, hunt.js, v2/v2.js  (there is no build step and no test suite)
python3 scripts/validate_jobs.py --jobs data/jobs.json   # discovery output validation
```

## Orbit at a glance

| Route | What |
|---|---|
| `/home` | Landing page: hero, scroll-driven agent "factory", crew, promo video, journey. |
| `/apply` | **Apply now**: tab 1 *Choose companies* (company blocks or "open to any" + min pay) then the hunt; tab 2 *Today's picks*. `/today` and `/hunt` open the matching tab. |
| `/person` | **Tracker**: *Jobs available* (company dropdowns, verification, reach-out panel), *Board* (drag between stages), *List*. |
| `/vaanya`, `/vrinda` | Company directories (reachable from Apply now, not the main nav). |
| `/v2` | Alternative design: keyboard-driven triage workspace (pipeline rail, inbox, detail pane). Same API and state as v1. |

Files: `website/app.js` (routing, data, directories, state, `window.OrbitApp`), `home.js` (+`home.css`: robots, factory, crew, journey, `window.OrbitRobots`), `product.js` (+`product.css`: picks, fit, board, goals, palette, dark mode, `window.OrbitProduct`), `hunt.js` (choose companies, hunt, link verification, Jobs available), `styles.css` + `refresh.css` (shared base), `server.py`, `export_data.py`, `v2/` (self-contained). The exporter logic lives in `scripts/export_dashboard_data.py`.

## Data and API contracts

- **Snapshot** `website/data/dashboard_data.json` (generated, git-ignored): `{generated_at, source_mode, sources, profiles:[{candidate, companies, contacts, jobs}]}`.
  - job: `id, candidate, company, title, location, url, status, experience, compensation, notes, category, tags[], appliedAt, source_sheet, source_row, ...`
  - company: `name, status, contacts[], tracking, trackingAt, notes, tags[]` (the last four come from the sheets' company-level rows).
- **State** `website/data/dashboard_state.json` (user data, git-ignored): `{jobs, companies, customCompanies, customJobs, meta}`. `jobs[key] = {candidate, status, appliedAt, applicationNotes, nextStep, updatedAt}`.
  - `meta` product keys (all optional): `prefs, goals, skips, today, milestones, followups, onboarded, mission, verify, reach, activity`. `seen`/`newOpportunities` belong to v1's "NEW" badge. The server only requires `meta` to be a dict.
  - `mission[candidate] = {companies:[normalised names], any, minLPA, unknownPay, started}`.
- **Job identity** (`keyOf`/`jobIdentity`, duplicated in app.js, product.js usage and v2): `candidate:` + `url:host+path(+ query params jk, gh_jid, jobid, job_id, requisitionid, reqid, folderid, id)`, else `role:company|title|location`, all normalised. Changing it orphans saved state, so do not change it casually.
- **Endpoints** (`server.py`, localhost only): `GET /api/data`, `GET|POST /api/state`, `POST /api/refresh` (runs export_data.py), `POST /api/verify {urls}` (max 40, only URLs already in the data, 1 request at a time per host, 8 s timeout, LinkedIn never fetched; returns `ok | closed | dead | manual | error`).
- **Sheets → statuses** (`scripts/export_dashboard_data.py`): free text in unnamed columns is classified into Applied / Watching (*Referral asked*) / Interviewing / Closed with tags and parsed `dd/mm` dates; `DA` / `ECE role` become the tag *Skills-adjacent role*; company-tracker rows attach to jobs by URL or create a tracked entry; titles are read from posting pages (`data/title_cache.json`, never LinkedIn). The mapping table is in `website/README.md`.

## Rules that matter

1. **Human in the loop.** Nothing applies, sends or messages automatically. "Apply" opens a listing; a status changes only when the user confirms or presses the key. Drafts are copied, never sent.
2. **Privacy.** The repo is public. `.gitignore` keeps out: `website/sheets.config.json`, `website/data/{dashboard_state,dashboard_data,title_cache}.json`, all `*.xlsx`, `data/archive/`, `config/profile.json`, `config/profiles/`, internal notes that name the candidates (`PROJECT.md`, `PROGRESS.md`, `HANDOFF.md`, `ARCHITECTURE.md`, `RUN_SEARCH_VAANYA.md`, `CLAUDE_RESUME_PROMPT.md`, `data/last_run.md`) and the licensed music file. Never commit candidate surnames, employers, colleges, contact names, sheet IDs or profile URLs. Run a content scan before every push.
3. **No AI attribution in git.** The owner asked for commits authored only by them: no `Co-Authored-By`, no "Generated with" lines, in commits or PR text.
4. **Commit only your own files.** The discovery agent regenerates `data/*.json` and edits `AGENTS.md` / `config/search_switches.json` in the same working tree. Stage explicit paths, never `git add -A` blindly.
5. **No salary inference**, scores come with reasons, third-party listings stay marked for verification (inherited from `AGENTS.md`).
6. **Keep it plain.** Vanilla HTML/CSS/JS, no bundler, no framework. Remove dead code when you find it.

## Gotchas learned the hard way

- The preview browser caches static files heuristically. The server now sends `Cache-Control: no-cache`, but after editing, force-refresh assets once (`fetch(url, {cache: "reload"})`) or you will debug a stale copy.
- A hidden/backgrounded preview tab pauses `requestAnimationFrame`, so GSAP animations look stuck in screenshots. Final states are still correct.
- Testing writes into the real `dashboard_state.json` (including from stale open tabs that re-save their in-memory copy). Close other tabs, and strip test keys (`prefs, goals, skips, today, milestones, followups, onboarded, mission, verify, reach, activity`) afterwards. Never delete the user's own job records.
- Sticky columns taller than the viewport hide their lower cards; the Today side column is deliberately not sticky.
- `app.js` skips company directory rows whose URL is on linkedin.com (they live in "Apply via LinkedIn"), so searching a LinkedIn-only role in the directory returns nothing by design.
- The sheets are hand-edited and messy: layouts drift between rows, so parse by signals (links, status phrases, dates), not by fixed columns.

## Change log (everything done so far)

Dates are 2026. Newest last.

### Oct 5–6 — video, redesign, product layer
- Finished the 30-second silent **Orbit explainer** (Hyperframes): fixed timeline IDs, contrast, scene 6 layout, rendered 1920x1080.
- **Home page rebuilt** ("The Factory"): SVG robot crew, scroll-pinned factory scene driven by one timeline function (`render(t)`), crew flip cards, tour video with chapters, journey explainer, live launch cards. Removed the Three.js galaxy.
- **Other pages restyled** (light design system in `refresh.css`): readable selects, cards, toolbar, tracker; robot waving fixed (CSS animations were overriding the arm's SVG transform; arms now have a positioning wrapper and an elbow).
- **Product layer** (`product.js`): Today's picks with an explainable local fit score, Apply/Watch/Skip (+reasons, undo), weekly goal ring, rhythm, 4-day follow-up reminders, shift report, kanban board, tuning dialog, ⌘K palette, dark mode (CSS invert trick), toasts and celebrations.
- **Story reworked** to: choose companies (or any above a pay floor) → *Detective* (hat + magnifier) → *Analyst* → *Verifier* → *Connector* → tracker. New `hunt.js`: company blocks (5 per row) with HR/alumni/engineer counts, hunt scene, **real link verification** via `POST /api/verify`, *Jobs available* with a reach-out panel and editable drafts.
- **Navigation collapsed** to Home / Apply now / Tracker (`/today` and `/hunt` still work as tabs).
- **Promo video** made with the brag workflow (`brag-output/`): plan, brief, Hyperframes composition, audio-reactive glow, 23.7 s render; also used on the home page.

### Oct 6 — sheets as data
- Statuses and notes parsed from the sheets (see Data above), sheet notes shown with provenance ("From your sheet", "Edited here · sheet: X"), applied dates drive the weekly ring, rhythm and follow-ups.
- Fixed a real bug: job identity ignored URL query strings, so several jobs shared one tracker record.
- Titles extracted from job pages, warm-up statuses recorded on companies, `DA`/`ECE role` tagged *Skills-adjacent role*.

### Oct 6 — cleanup and publishing
- Removed the old `dashboard/` app, `scene.js`, old explainer copies, caches; pruned ~18 KB of unused CSS (automated for `styles.css`, by hand elsewhere), dead JS, unused exports; added file map to `website/README.md`.
- Pushed to `github.com/kaustubh2708/jobsearch` on `master` (replaced the older LocalJobAgent project on top of its history, no force push). Sheet IDs moved to a git-ignored config; 44 scripts had candidate full names / employer / college replaced by first names and generic phrases; personal data ignored via `.gitignore`.
- README rewritten with an architecture diagram and the promo GIF; the discovery system is called "the AI agent" there.

### Oct 8 — v2 and docs
- **`/v2` triage workspace** (`website/v2/`): dark graphite + amber, keyboard first (`j/k`, `o`, `w`, `a`, `s`, `1`–`7`, `/`, `c`, `?`), pipeline rail with counts, daily brief tiles, inbox ranked by fit, detail pane (fit breakdown, verification, sheet notes, tracking fields, reach-out drafts), scope drawer sharing `meta.mission` with v1, light/dark theme. Footer link from v1.
- Added this file and `HANDOFF-ORBIT.md`.
