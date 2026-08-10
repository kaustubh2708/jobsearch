# CLAUDE.md — context for AI assistants working on this repo

Read this before changing anything. It's the architecture map and the set of
invariants that keep the agent safe to run unattended.

---

## What this project is

**LocalJobAgent** — an autonomous job search + auto-apply agent for the Indian
job market. Runs entirely offline against a local Ollama instance. Built for a
senior ML engineer, but the resume parser makes it role-agnostic.

Core loop: parse resume → search boards → score with local LLM → human approves
in a dashboard → agent auto-applies via Playwright → track outcomes.

---

## Non-negotiable invariants

Break any of these and the project stops being trustworthy.

1. **No cloud LLM calls, ever.** All inference goes through `jobagent/llm.py`
   against `http://localhost:11434`. If you add an AI call, it goes through
   `LLM.chat`, `LLM.chat_json` or `LLM.embed`. No exceptions.
2. **Never fabricate facts on an application form.** Name, phone, CTC, notice
   period and work authorisation come from `config.yaml` only — see
   `RULES` and `deterministic_answer()` in `applier/forms.py`. The LLM is a
   *fallback for novel questions*, and when it isn't confident the application
   halts and asks the user. Do not "helpfully" lower that bar.
3. **No credentials in the repo.** Auth is entirely via the persistent Playwright
   profile at `data/browser_profile/`, populated by the user logging in by hand.
   Never add username/password fields to config.
4. **Respect the caps.** `apply.daily_apply_cap` and `apply.delay_between_s` are
   ban-avoidance measures, not suggestions.
5. **Sources fail soft.** A broken scraper returns `[]` and logs at debug. It
   never raises into the pipeline. Job boards change constantly; a dead source
   must not kill the daily run.
6. **The human approves every application.** `JobStatus.APPROVED` is only ever
   set by an explicit user action in the dashboard or API. Nothing auto-approves.

---

## Layout

```
jobagent/
├── config.py           Config models + YAML loader. ROOT/DATA_DIR/paths live here.
│                       JOBAGENT_DATA_DIR env var relocates the DB (needed on
│                       filesystems without file locking).
├── db.py               SQLModel schema + helpers.
│                       Tables: jobs, applications, answer_bank, skill_library, run_log
│                       JobStatus  = review board  (pending/approved/rejected/archived)
│                       AppStatus  = tracker board (queued→applying→applied→…)
│                       fingerprint() = the dedupe key (company|title|location)
├── llm.py              Ollama wrapper. chat / chat_json (with JSON coercion) / embed.
│                       cosine() lives here too.
├── resume_parser.py    .pdf/.docx/.txt/.md/.pages → text → LLM → structured
│                       skill library → embedded → SkillLibrary row.
│                       .pages support decompresses iWork IWA snappy frames.
├── matcher.py          Two-stage scoring. Matcher.embed_score (stage 1),
│                       Matcher.llm_score (stage 2). derive_queries() picks
│                       search terms from the resume unless config overrides.
├── pipeline.py         run_discovery(): gather → hard_filter → dedupe →
│                       drop_already_seen → embed sort → LLM score → persist.
├── bootstrap.py        Cross-platform installer. ALL setup logic lives here —
│                       deps, playwright, ollama detect/start, GPU sizing, model
│                       pulls, db init. The shell launchers are thin wrappers so
│                       Windows and Unix cannot drift. Imports stdlib only.
├── scheduler.py        APScheduler. Cron discovery 2×/day + apply poll loop.
│                       Runs in-process with the server. tz falls back to local
│                       if no tz database (Windows without `tzdata`).
├── server.py           FastAPI. All routes under /api/*. Serves web/ statically.
├── cli.py              typer entry point. serve/discover/apply/profile/login/
│                       setup/status/doctor.
├── sources/
│   ├── base.py         RawJob dataclass + parse_salary_lpa + detect_ats + clean
│   ├── jobspy_source.py  linkedin/indeed/naukri/google/glassdoor via python-jobspy
│   ├── ats_boards.py     greenhouse/lever/ashby official JSON APIs  ← most reliable
│   ├── india_boards.py   instahyre/foundit/cutshort private JSON endpoints
│   ├── free_apis.py      adzuna/jooble/remotive/remoteok/himalayas/themuse/HN
│   └── wellfound.py      Playwright, needs a login
├── applier/
│   ├── browser.py      Persistent Chromium context + stealth + interactive_login
│   ├── forms.py        AnswerResolver — the brain of form filling. Three-tier
│   │                   resolution: profile rules → answer bank → LLM.
│   ├── generic.py      Greenhouse/Lever/Ashby/Workday/any HTML form.
│   │                   label_for() infers the question from aria-label/label/
│   │                   placeholder/name. fill_visible_fields() does the work.
│   ├── linkedin.py     Easy Apply multi-step modal loop
│   ├── naukri.py       One-click apply + chatbot questionnaire
│   └── engine.py       Orchestration: queue_approved → apply_to_job → _persist.
│                       Cover letter generation lives here.
└── web/                index.html + app.js + styles.css. Vanilla JS, no build.
```

---

## Key flows

### Discovery (`pipeline.run_discovery`)

```
gather()              all enabled sources, ATS boards first
hard_filter()         freshness / title blocklist / company blocklist / salary floor
dedupe()              fingerprint collision → keep richest description, best source rank
drop_already_seen()   45-day lookback against the jobs table
embed pre-screen      sort all candidates by cosine similarity, descending
LLM scoring loop      stops at max_jobs_per_day matched, or max_llm_calls
persist               score ≥ llm_min_score → PENDING, else ARCHIVED
```

Jobs skipped because the daily cap was hit are **not** persisted, so the next run
picks them up. This is intentional — don't "fix" it.

### Apply (`applier.engine.run_apply_batch`)

```
queue_approved()      APPROVED jobs without an Application row → create one (QUEUED)
daily cap check       daily_apply_cap minus applied in the last 24h
one browser context   reused across the whole batch
per job:
  _pick_handler()     ats/source → linkedin | naukri | generic
  apply_to_job()      cover letter → handler → screenshot
  fallback            not_easy_apply / external → retry via generic.apply
  _persist()          map handler status → AppStatus
  sleep               random within delay_between_s
```

Handler return contract — every handler returns a dict with:
`ok: bool`, `status: str`, and optionally `filled`, `error`, `pending`,
`external_url`. Statuses `_persist()` understands:
`applied | already_applied | needs_input | ready_not_submitted | uncertain |
login_required | not_easy_apply | external | failed`.

### Answer resolution (`applier/forms.py`)

```
deterministic_answer()   regex RULES against config.yaml profile   ← never guessed
bank_lookup()            answer_bank table, keyed on normalised question hash
llm_answer()             local LLM, constrained to options, returns confidence
low confidence           → resolver.unresolved[] → AppStatus.NEEDS_INPUT
user answers in drawer   → answer_pending() → bank_store(confirmed=True) → requeue
```

---

## Adding things

**A new job source.** Create `sources/yoursource.py` returning `List[RawJob]`.
Wrap everything in try/except returning `[]`. Register it in `pipeline.gather()`
and add a config block under `sources:`. Use `clean()`, `parse_salary_lpa()` and
`detect_ats()` from `sources/base.py` so the shape matches.

**A new ATS handler.** Add `applier/yourats.py` with the signature
`apply(page, job, resolver, resume_pdf, auto_submit) -> dict`, then wire it into
`_pick_handler()`. Reuse `generic.fill_visible_fields` and
`generic.upload_resume` — they handle most of it.

**A new API route.** `server.py`, prefix `/api/`. The frontend calls it through
the `api()` helper in `web/app.js`.

**A new dashboard view.** Add a `<section class="view" id="view-x">` in
`index.html`, a `.nav` button with `data-view="x"`, and a loader in `refresh()`.

---

## Testing without a live network or GPU

The pipeline is testable by monkeypatching two things:

```python
import jobagent.llm as L
L._llm = FakeLLM()            # needs is_up/embed/chat/chat_json
L.get_llm = lambda: L._llm
import jobagent.resume_parser as RP; RP.get_llm = L.get_llm
import jobagent.matcher as M;        M.get_llm = L.get_llm

import jobagent.pipeline as P
P.gather = lambda queries, cfg=None: [RawJob(...), ...]
```

Set `JOBAGENT_DATA_DIR=/tmp/test` to keep test databases out of the repo.

API routes are testable with `fastapi.testclient.TestClient(app)` with no
external services running — `/api/health` degrades gracefully when Ollama is
unreachable.

---

## Cross-platform rules

The project must run identically on Windows, macOS and Linux. When touching it:

- **Never put logic in a shell script.** `start.sh`, `start.ps1`, `start.bat`,
  `run.sh`, `run.ps1`, `run.bat` may only: find a Python, make a venv, load
  `.env`, and call `jobagent.bootstrap` / `jobagent.cli`. Anything else goes in
  `bootstrap.py`, which is written once and runs everywhere.
- **`bootstrap.py` imports stdlib only.** It runs *before* dependencies exist.
- **Always pass `encoding="utf-8"`** to `read_text`/`write_text`/`FileHandler`.
  Windows defaults to cp1252 and mangles ₹ and bullet characters.
- **SQLite URLs use `Path.as_posix()`** — `sqlite:///C:\Users\…` is malformed.
- **No hardcoded `/` in paths.** Use `pathlib`.
- **`python-snappy` is optional** and installed separately by `bootstrap.py`; it
  needs a C toolchain and usually fails on Windows. `.pages` support degrades
  with a clear message rather than crashing.
- **`tzdata` is a Windows-only requirement** — there's no system tz database
  there, and the scheduler is `Asia/Kolkata`-pinned.
- Unicode in console output goes through `bootstrap.TICK` / `ARROW` / `CROSS`,
  which fall back to ASCII when the console encoding can't represent them.

---

## Gotchas

- **SQLite needs file locking.** On network drives or some FUSE mounts you get
  `disk I/O error`. Fix: `JOBAGENT_DATA_DIR=~/jobagent-data`.
- **Never add a "Submit"-like label to the form-reveal click loop** in
  `generic.apply`. On a page that renders the form inline, that fires off an
  empty application. There's a regression test for this.
- **Skip form fields that already have a value.** Validation retries re-run
  `fill_visible_fields`; without the guard, selects get re-resolved forever.
- **`chat_json` never raises.** It coerces malformed model output and falls back
  to `{}`. Callers must handle empty dicts.
- **Playwright is sync API.** The whole applier is synchronous and runs in a
  thread from FastAPI. Don't mix in async Playwright.
- **`Job.matched_skills` etc. are JSON strings** in the DB. Use `Job.lists()` or
  `Job.as_dict()`, never the raw attribute.
- **Timezone.** `discovered_at`/`posted_at` are stored naive-UTC because SQLite
  drops tzinfo. Always `.replace(tzinfo=None)` before comparing in a query.
- **The scheduler is `Asia/Kolkata`-pinned** in `scheduler.py`.
- **LinkedIn description fetching is slow** (`linkedin_fetch_description=True`)
  but scoring is useless without it. Don't turn it off to speed things up.

---

## The user

Kaustubh Singh — ML Engineer II at Google (GCP Dataplex), founder of ARA
Intelligence. 4 years post-graduate experience. Deep in Python, LangGraph, vLLM,
RAG, GCP, and on-prem inference (dual RTX 4090). Also ships React/TypeScript.
Based in India, targeting ML/AI engineering roles.

He has built a similar system before, so the code can assume competence — but the
project should still run for someone who has never opened a terminal beyond
`./start.sh`.
