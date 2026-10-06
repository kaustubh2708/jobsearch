# Orbit job search website

All site code and its generated snapshot live in this `website/` directory. The app is local-first. The story: **choose companies (or stay open to any above a pay floor) → a detective agent hunts career portals, LinkedIn posts and job platforms → an analyst filters by skills and fit score → a verifier double-checks every link → your tracker shows Jobs available with referral options beside them.** Navigation is three pages: **Home**, **Apply now** and **Tracker**. The Vaanya/Vrinda company directories remain reachable from Apply now ("Browse all by company"). `/today` and `/hunt` still open the matching Apply now tab. Views:

- `/home`: the landing page. Hero, a scroll-driven factory scene, the agent crew, the promo video and a journey explainer.
- `/apply` (**Apply now**): two tabs, *Choose companies* and *Today's picks* (described below). `/today` and `/hunt` still open the matching tab.
- `/person` (**Tracker**): Jobs available, Board and List (described below).
- `/vaanya`, `/vrinda`: the company directories (roles grouped by employer). They are linked from Apply now rather than from the main navigation.

The candidate views default to current job openings, order company groups by opening count, and render 12 companies at a time. Use the company picker or search for a direct jump; **Show next 12** reveals more only when wanted. Switch to **All records** to include drives and older source rows. Home-page reveal animations use an IntersectionObserver with a reduced-motion / unsupported-browser fallback, so content does not remain hidden if the animation API is unavailable.

LinkedIn listing URLs are separated into an **Apply via LinkedIn** section on each candidate view. The section detects URLs in either the record URL field or its notes, and keeps these roles out of the regular company directory to avoid duplicate listings. Opening a LinkedIn link marks that role **Applied** and records today’s date in local tracker state; this records that the listing was opened, not proof that an application was submitted. The current source snapshot has 10 LinkedIn listing URLs for Vaanya and none for Vrinda.

## Run

From the project root:

```bash
/Users/kaustubhsingh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 website/export_data.py
/Users/kaustubhsingh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 website/server.py
```

Then open <http://127.0.0.1:8766/home>. Keep the terminal process running. The server binds only to localhost.

## Workbook refresh and new opportunities

The exporter fetches the supplied Google Sheets as XLSX exports and parses them in memory. It never writes back to either Sheet or saves a downloaded workbook. Refresh reads the current tabs and updates `website/data/dashboard_data.json`; new source rows are compared with the first-run baseline and marked **NEW** for 30 days. If Google's export is unavailable, the exporter falls back to `data/Job Search.xlsx` or `data/companies.xlsx`, and the page labels that snapshot as a local-workbook fallback. You can also add a one-off opportunity from a short form; it is saved to the local tracker, not back to a spreadsheet.

The two supplied Sheets currently allow XLSX export through their share links, so this setup does not require API keys or Google OAuth. If their sharing permissions change, the site will use the local workbook fallback and show that status. The site does not scrape LinkedIn profiles or connection data and never sends applications, messages or referral requests.

## Tracking and privacy

Application status, application date, follow-up notes, next steps, custom companies and manually added opportunities are stored in `website/data/dashboard_state.json`. They are kept separate from workbook source notes and do not modify the source workbooks. Use **Export** to download a JSON copy of the selected candidate's data and tracker state.

Company favicons and web fonts load from public providers when online. GSAP and ScrollTrigger load from jsDelivr for the home-page animation; everything else works without them, and reduced-motion preferences switch the motion off.


## The hunt, Today and Jobs available

- `/apply` (**Apply now**): two tabs. **1 Choose companies**: pick company blocks (5 per row, with HR/TA, alumni and engineer contact counts from your sheets) or choose **Open to any company** with a minimum pay. The detective scene then runs the pipeline on your real data. Listings with no published pay are kept unless you untick that option; Orbit never infers salary.
  **2 Today's picks**: five picks a day with an explainable local fit score ("How is this scored?"), Apply (opens the listing, then asks you to confirm) / Watch / Skip with a reason, weekly goal ring, rhythm, 4-day follow-up reminders and a shift report.
- `/person` (Tracker): **Jobs available** (companies as dropdowns with job details, link, verification badge, stage and notes; reach-out panel beside them), plus the Board (drag cards between stages) and the original List.
- ⌘K / `/`: command palette. The moon button toggles dark mode.

**Verification.** `POST /api/verify` (local server only) checks listing URLs that already exist in your data: one request at a time per host, 8 s timeout, small body read. Results are `ok`, `closed`, `dead`, `manual` (blocked by the site; check yourself) or `error`. LinkedIn URLs are never fetched; open them in your own visible session. Results are cached in `dashboard_state.json` under `meta.verify`.

**Reach-out.** Contacts come only from the lists you added. Orbit drafts a note you can edit; it never sends anything. "I sent it" only records that you did.

**Fit score.** A transparent local heuristic from title, level, place, contacts and link (capped until you add skills, because the sheets hold no job description). It is not the Analyst agent's score and never a promise of an interview.

**Google Sheets.** The daily agent run updates your two sheets; `export_data.py` reads them via their share links. **Run now** / **Refresh from sheets** re-reads them.

## Statuses and notes from your sheets

The exporter (`scripts/export_dashboard_data.py`, run by `export_data.py`) reads the free-text status and notes you type into the **Job Links**, **Warm-up** and company tracker (**Sheet1**) tabs, including unnamed columns and continuation rows. Your own words are kept verbatim as "Sheet note"; Orbit adds structure on top:

| You wrote | Orbit shows |
|---|---|
| `applied on 30/09`, `applied thru sanya's ref`, `applied (no referral)` | **Applied**, applied date parsed from `dd/mm`, tag *Referred* / *No referral* |
| `rejected`, `rejected on 01/10` | **Closed**, tag *Rejected* (wins over any earlier "applied" on the same role) |
| `message sent for referral on 5/10`, `resume sent to …`, `left cold emails…` | **Watching**, tag *Referral asked* |
| `gave OA for one on 29/09` | **Interviewing** |
| `no longer active`, `invalid link`, `no relevant opening`, `Closes on 4/10` (past) | **Closed**, tag *Not available* / *Not relevant* / *Deadline passed* |
| `Priority 1`, `First Priority`, `Active Hiring` | a tag |
| anything else | kept as your note |

Company tracker rows that name a job link are matched to the same job by URL; if the job isn't in Job Links yet, a tracked entry is created. Sheets are never written to. Edits made in Orbit take precedence on the site and are marked **Edited here · sheet: …** when they differ from the sheet.

Job identity now includes the query params that name a job (`jk`, `gh_jid`, `jobId`…), so jobs that share a path (Indeed, Greenhouse boards) no longer share one tracker record.

**Shorthand and titles.** `DA` / `ECE role` in a status cell is read as "not a pure tech role, but close to the candidate's skills" and shows as a *Skills-adjacent role* tag (your original text is kept as a note). Tracker entries that only had a link get their title read from the job page itself (JSON-LD `JobPosting`, then `og:title`, then the page title), cached in `data/title_cache.json` so re-exports make no repeat requests. LinkedIn links are never fetched; those entries show as "Role at <Company>" until you name them. Warm-up statuses and notes are also recorded on the company, next to the company tracker's.


## File map

| File | Purpose |
|---|---|
| `index.html` | One page shell for every route. |
| `app.js` | Data loading, routing, the company directories, tracker list, local state and `window.OrbitApp`. |
| `home.js` / `home.css` | Landing page: robots, factory scene, crew, tour video, journey. Exposes `window.OrbitRobots`. |
| `product.js` / `product.css` | Today's picks, fit score, board, goals and rhythm, tuning, command palette, dark mode. Exposes `window.OrbitProduct`. |
| `hunt.js` | Choose companies, the hunt pipeline, link verification and the Jobs available tracker view. |
| `styles.css`, `refresh.css` | Shared base styles (pruned of unused rules) and the light design layer for header, forms and directories. |
| `server.py` | Local-only server, tracker state API and `POST /api/verify`. |
| `export_data.py` | Reads the Google Sheets (falls back to the local workbooks) via `scripts/export_dashboard_data.py`. |
| `data/` | `dashboard_data.json` (generated snapshot), `dashboard_state.json` (your tracker state), `title_cache.json`. |
| `assets/` | Promo video and poster. `videos/` holds the earlier explainer project. |
