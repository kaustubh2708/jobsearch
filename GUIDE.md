# LocalJobAgent — User Guide

A job search agent that runs entirely on your own machine. It reads your resume,
searches Indian job boards every day, scores each posting against your actual
skills using a local LLM, and shows you the good ones. You approve the ones you
want; it fills in and submits the applications for you and tracks what happens
next.

Nothing is sent to any cloud AI service. Your resume, your salary expectations
and your application history never leave your computer.

---

## 1. Install

One command, from this folder.

**macOS / Linux / WSL**

```bash
./start.sh
```

**Windows** — double-click `start.bat`, or from Windows Terminal / PowerShell:

```powershell
.\start.bat
```

That will:

- create a Python virtualenv in `.venv/`
- install all Python dependencies
- install the Chromium build Playwright drives
- install Ollama if it's missing (or point you at the download on macOS/Windows)
- detect your GPU and offer the right model size
- download the two models the agent thinks with
- create the SQLite database
- walk you through a short setup, then start the agent

It's safe to run any time — every step is idempotent, and after the first run it
skips straight to starting the agent.

> **On Windows**, install Python from python.org and **tick "Add python.exe to
> PATH"** during setup. If you skip that, the launcher can't find it. Ollama for
> Windows is at [ollama.com/download/windows](https://ollama.com/download/windows).
>
> `start.bat` runs the PowerShell script with `-ExecutionPolicy Bypass`, so you
> never need to change your machine's execution policy.

The models are the big download. On a 12GB+ NVIDIA GPU the defaults are:

| Model | Size | What it does |
|---|---|---|
| `qwen2.5:14b-instruct` | ~9 GB | reads job descriptions, scores fit, answers form questions, writes cover letters |
| `nomic-embed-text` | ~275 MB | fast first-pass similarity screen |

**Want better quality?** If you have 24 GB of VRAM, change `llm.chat_model` in
`config.yaml` to `qwen2.5:32b-instruct` and run `ollama pull qwen2.5:32b-instruct`.
It's noticeably sharper at reading between the lines of a vague JD. On 8 GB, drop
to `llama3.1:8b-instruct-q4_K_M`.

---

## 2. Set yourself up (5 minutes, once)

### a. Drop your resume in

Put it in `resume/`. PDF works best. `.docx`, `.txt` and `.pages` also work.

You also want a PDF specifically for uploading to application forms, because
almost every ATS demands one. Point `resume.upload_pdf` in `config.yaml` at it:

```yaml
resume:
  dir: "resume"
  upload_pdf: "resume/KaustubhSingh_Resume.pdf"
```

> If your resume is a `.pages` file, export it to PDF from Pages
> (**File → Export To → PDF**) and put that in `resume/` too. The agent can read
> `.pages` for the skill library, but it can't upload one.

### b. Fill in `config.yaml`

The bits that actually matter:

```yaml
profile:
  phone: "+91XXXXXXXXXX"        # required — nearly every form asks
  expected_ctc_lpa: 45          # leave null and the agent says "negotiable"
  current_ctc_lpa: 28           # leave null to not disclose
  notice_period_days: 30
```

Everything else has a sensible default.

### c. Log into the job boards

The agent drives a real Chrome window using *your* logged-in session. You log in
by hand, once, and the cookies persist in `data/browser_profile/`. No passwords
are stored anywhere in this project.

```bash
./run.sh login linkedin        # Windows: run.bat login linkedin
./run.sh login naukri
./run.sh login wellfound       # optional
```

A browser opens. Log in normally, solve any OTP or captcha, then come back to the
terminal and press Enter.

### d. Check everything's wired up

```bash
./run.sh doctor                # Windows: run.bat doctor
```

Green ticks all the way down means you're ready.

---

## 3. Run it

```bash
./start.sh                     # Windows: start.bat
```

That starts the dashboard at **http://127.0.0.1:8765** and the background agent
in the same process. Leave it running.

From then on it:

- searches at **08:30** and **18:30** IST every day
- checks every 10 minutes for jobs you've approved, and applies to them

You can change those times under `schedule:` in `config.yaml`.

### The dashboard

**Review queue** — everything found and scored, best first. Each card shows the
match score, a one-line verdict, which of your skills matched, what's missing,
and any red flags (staffing agency, seniority mismatch, vague JD). Click a card
to read the full JD and the model's reasoning.

Two buttons per job: **Approve** and **Reject**. Approve is the trigger — the
agent picks it up within 10 minutes and applies. You can also tick several jobs
and approve them in bulk.

**Application tracker** — a Kanban board of everything sent. Cards move
automatically from Queued → Applying → Applied. You drag them onward yourself as
things develop: Screening, Interview, Offer, Rejected.

**Skill library** — what the model extracted from your resume, and what every job
is scored against. If the target roles look wrong, that's the first thing to fix.

**Activity** — a live log of everything the agent does.

### Or drive it from the terminal

| What | macOS / Linux | Windows |
|---|---|---|
| Run one search now | `./run.sh discover` | `run.bat discover` |
| Apply to everything approved | `./run.sh apply` | `run.bat apply` |
| Show your skill library | `./run.sh profile` | `run.bat profile` |
| Pipeline snapshot | `./run.sh status` | `run.bat status` |
| Check the setup | `./run.sh doctor` | `run.bat doctor` |

---

## 4. How a job gets from a board to an application

```
  1. GATHER      ~300-500 raw postings/day from every enabled source
       ↓
  2. HARD FILTER freshness (7 days), title blocklist, company blocklist, salary floor
       ↓
  3. DEDUPE      same role on 5 boards → keep the one with the best description
                 and the most directly applyable link
       ↓
  4. EMBED SCREEN cosine similarity vs your profile. Kills ~75% in seconds.
       ↓
  5. LLM SCORE   the 14B model reads the JD properly: score /100, reasoning,
                 matched skills, gaps, red flags, seniority fit
       ↓
  6. YOUR REVIEW anything ≥70 lands in the review queue. Below that is archived.
       ↓
  7. YOU APPROVE
       ↓
  8. AUTO-APPLY  real browser, your logged-in session, resume uploaded,
                 form filled, cover letter generated, submitted
       ↓
  9. TRACKER     screenshot saved as evidence, card lands on the board
```

Steps 4 and 5 are split deliberately. Running a 14B model over 400 raw postings
would take hours; the embedding pass removes most of them in seconds so the
expensive model only reads plausible candidates.

---

## 5. Where the jobs come from

| Source | How | India coverage | Reliability |
|---|---|---|---|
| **Greenhouse / Lever / Ashby** | official public JSON APIs | Razorpay, PhonePe, CRED, Swiggy, Meesho, Groww, Sarvam AI, Atlan, DevRev + more | ★★★★★ never breaks |
| **LinkedIn** | JobSpy | excellent | ★★★☆☆ rate-limits |
| **Naukri** | JobSpy | the biggest Indian index | ★★★☆☆ rate-limits |
| **Indeed India** | JobSpy | very good | ★★★★☆ |
| **Google Jobs** | JobSpy | aggregates career pages | ★★★★☆ |
| **Instahyre** | public API | curated Indian product roles | ★★★☆☆ |
| **Foundit** (ex-Monster India) | public API | huge Indian enterprise volume | ★★★☆☆ |
| **Cutshort** | public API | Indian startups | ★★★☆☆ |
| **Wellfound** | Playwright + your login | startups, India filter | ★★★☆☆ |
| **Adzuna** | free API key | genuine India index | ★★★★★ |
| **Jooble** | free API key | aggregates Indian boards | ★★★★☆ |
| **Remotive / RemoteOK / Himalayas / The Muse** | free, no key | remote-first companies that hire from India | ★★★★☆ |
| **HN "Who is hiring?"** | Algolia API, free | low volume, unusually high quality | ★★★★★ |

**The ATS boards are the best source in the list** and cost nothing in ban risk.
Add any company you'd like to work at — find the slug in their careers URL:

```
boards.greenhouse.io/razorpay      → greenhouse: [razorpay]
jobs.lever.co/swiggy               → lever:      [swiggy]
jobs.ashbyhq.com/atlan             → ashby:      [atlan]
```

### Free API keys (optional, 2 minutes each)

Copy `.env.example` to `.env` and fill in whichever you want:

- **Adzuna** — [developer.adzuna.com](https://developer.adzuna.com/) — instant, free, real India coverage
- **Jooble** — [jooble.org/api/about](https://jooble.org/api/about) — free key by email
- **The Muse** — [themuse.com/developers](https://www.themuse.com/developers/api/v2) — works without a key, higher limits with one

Everything works without any of these. They just widen the net.

---

## 6. What auto-apply actually does

When you approve a job, the agent opens your real browser session and:

1. Picks a handler based on the ATS — LinkedIn Easy Apply, Naukri, or the
   generic form filler (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, and
   most plain HTML forms).
2. Uploads your resume PDF.
3. Walks every visible field, works out what it's asking from its label, and
   fills it.
4. Generates a tailored cover letter with the local model if the form wants one.
5. Submits, then saves a full-page screenshot to `data/evidence/`.

### Where answers come from

In strict order:

1. **Your profile in `config.yaml`** — name, phone, notice period, CTC,
   work authorisation. These are never guessed.
2. **The answer bank** — anything you or the agent has answered before, stored
   in SQLite. It gets faster and more consistent the more it applies.
3. **The local LLM** — for novel screening questions, answering only from facts
   in your resume and profile.

If the model isn't confident, it **stops rather than guessing**. The card moves
to "Needs you" on the tracker, you type the answer in the drawer, and it's
remembered forever — the same question never blocks the agent twice.

### Safety rails

- `apply.daily_apply_cap: 15` — a hard ceiling on real applications per day
- `apply.delay_between_s: [45, 120]` — randomised human-like pacing
- `apply.auto_submit: false` — fills everything and stops at Submit, if you want
  to watch it work for the first few
- every submission is screenshotted

> **Start with `auto_submit: false` for your first day.** Watch three or four
> applications get filled in, confirm the answers look right, then switch it on.

---

## 7. Tuning it

**Too few jobs a day?**

```yaml
matching:
  llm_min_score: 65        # from 70
search:
  hours_old: 336           # 14 days instead of 7
  queries: ["ML engineer", "AI engineer", "LLM engineer", "MLOps engineer"]
```

Also add more company slugs under `ats_boards`.

**Too much junk?**

```yaml
matching:
  llm_min_score: 78
  embed_threshold: 0.62
search:
  min_salary_lpa: 30
  exclude_companies: ["Infosys", "Wipro", "Cognizant", "TCS"]
  exclude_title_keywords: ["intern", "trainee", "support", "QA", "manual testing"]
```

**Wrong roles entirely?** Check the Skill library tab. If the extracted target
roles are off, either fix your resume's wording or override directly:

```yaml
search:
  queries: ["machine learning engineer", "AI engineer", "LLM engineer"]
```

**Scoring feels too generous or too harsh?** Use a bigger model. `qwen2.5:32b-instruct`
is meaningfully better at reading a JD sceptically than the 14B.

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `Ollama not reachable` | `ollama serve` in another terminal, or reinstall from ollama.com |
| `model missing` | `ollama pull qwen2.5:14b-instruct` |
| LinkedIn finds nothing | You're rate-limited. Wait an hour. Reduce `linkedin.max_results` to 25. |
| `LinkedIn session expired` | `./run.sh login linkedin` |
| Naukri applications stall | Naukri's chatbot changed. The card lands in "Needs you" — apply manually via the link. |
| Lots of "Needs input" | Normal at first. Answer them once; the bank remembers. |
| Wellfound returns nothing | `./run.sh login wellfound` |
| Discovery run is slow | Expected — a 14B model scoring 40 JDs takes 10-20 min on a 12GB GPU. It runs in the background. |
| `disk I/O error` from SQLite | The repo is on a filesystem without file locking (network drive). Set `JOBAGENT_DATA_DIR` to a local folder. |
| Playwright won't launch | `.venv/bin/python -m playwright install chromium` (Windows: `.venv\Scripts\python -m playwright install chromium`) |

### Windows-specific

| Symptom | Fix |
|---|---|
| "Python 3.10 or newer is required" but it *is* installed | It isn't on PATH. Reinstall from python.org with **"Add python.exe to PATH"** ticked, then open a **new** terminal. |
| A Microsoft Store page opens instead of Python | That's the Store stub. The launcher skips it automatically — but install real Python from python.org to be safe. |
| "running scripts is disabled on this system" | Use `start.bat` rather than `start.ps1`. It bypasses the policy for that one run. |
| `.pages` resume won't parse | `python-snappy` needs a C compiler and usually can't build on Windows. Export your resume to PDF instead — better anyway, since forms need a PDF. |
| Boxes instead of ✓ in the terminal | Old `conhost`. Use Windows Terminal, or ignore it — the launcher falls back to ASCII automatically. |
| Scheduler times look wrong | `pip install tzdata` inside `.venv` (it's in requirements, but worth checking). |

Logs live in `logs/jobagent.log` and in the Activity tab.

---

## 9. Honest limitations

- **LinkedIn and Naukri actively fight automation.** JobSpy is well maintained
  but scraping breaks periodically. The ATS boards and free APIs never break,
  which is why they're weighted heavily. If a source goes quiet, the run
  continues with the others rather than failing.
- **Automated applying carries some account risk.** The pacing, the daily cap and
  the real-browser-with-your-session approach all reduce it, but it isn't zero.
  Keep `daily_apply_cap` modest.
- **Complex ATS flows won't always complete.** Workday multi-page wizards, video
  screens and timed assessments will land in "Needs you" rather than being faked.
  That's deliberate.
- **The model is a screen, not an oracle.** A 14B model scoring 82 doesn't mean
  you'll get an interview. Skim the queue rather than approving on score alone.
- **Salary parsing on Indian boards is approximate.** Most postings don't
  disclose, and the ones that do use six different formats.

---

## 10. Where things live

```
Jobsearch/
├── config.yaml              ← everything you tune
├── .env                     ← optional free API keys
├── start.sh / start.bat     ← the one command (installs, then runs)
├── run.sh   / run.bat       ← CLI passthrough
├── resume/                  ← your resume goes here
├── data/
│   ├── jobagent.db          ← jobs, applications, answer bank, skill library
│   ├── browser_profile/     ← your logged-in sessions
│   └── evidence/            ← screenshot of every submitted application
├── logs/
└── jobagent/                ← the code (see CLAUDE.md for architecture)
```

Back up `data/jobagent.db` and you keep your entire history and answer bank.
