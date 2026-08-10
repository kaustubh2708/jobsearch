# LocalJobAgent

An autonomous job search agent for the Indian market that runs entirely on your
own machine. It reads your resume, searches the boards daily, scores every
posting against your real skills with a local LLM, and applies to the ones you
approve.

**Nothing is sent to any cloud AI service.** Your resume, salary expectations and
application history stay on your computer.

---

## Quick start

**macOS / Linux / WSL**

```bash
git clone https://github.com/kaustubh2708/jobsearch.git Jobsearch
cd Jobsearch
cp ~/Downloads/MyResume.pdf resume/
./start.sh
```

**Windows** (PowerShell, Windows Terminal, or just double-click `start.bat`)

```powershell
git clone https://github.com/kaustubh2708/jobsearch.git Jobsearch
cd Jobsearch
copy "$env:USERPROFILE\Downloads\MyResume.pdf" resume\
.\start.bat
```

That's it. The launcher installs Python dependencies, Playwright's Chromium and
the Ollama models, sizes the model to your GPU, walks you through a short setup,
and opens the dashboard at **http://127.0.0.1:8765**.

Every run after the first just starts the agent.

> Both launchers are thin wrappers. All the real setup logic lives in
> `jobagent/bootstrap.py`, so every platform behaves identically.

---

## What it does

- **Reads your resume** into a structured skill library — skills, seniority,
  domains, achievements, and the job titles you should actually be searching for
- **Searches 13+ sources daily** — LinkedIn, Naukri, Indeed, Google Jobs,
  Instahyre, Foundit, Cutshort, Wellfound, Adzuna, Jooble, HN Who's Hiring, and
  company career portals via their official Greenhouse / Lever / Ashby APIs
- **Scores every posting 0-100** with a two-stage pipeline: a fast embedding
  screen, then a 14B reasoning model that reads the JD properly and returns
  matched skills, gaps, red flags and seniority fit
- **Shows you 15-25 real matches a day** in a review dashboard
- **Applies for you** when you approve — real browser, your logged-in session,
  resume uploaded, form filled, cover letter generated, screenshot saved
- **Tracks everything** on a Kanban board through to offer

It stops and asks rather than guessing whenever a form asks something it can't
answer from your resume — and remembers your answer forever.

---

## Requirements

- Python 3.10+
- ~10 GB free disk for the models
- A GPU helps a lot (12GB+ VRAM recommended), but CPU works with a smaller model
- Windows 10/11, macOS, or Linux

---

## Commands

| What | macOS / Linux | Windows |
|---|---|---|
| Install + run everything | `./start.sh` | `start.bat` |
| Run one job search now | `./run.sh discover` | `run.bat discover` |
| Apply to everything approved | `./run.sh apply` | `run.bat apply` |
| Show your skill library | `./run.sh profile` | `run.bat profile` |
| Log into a board once | `./run.sh login linkedin` | `run.bat login linkedin` |
| Check the setup | `./run.sh doctor` | `run.bat doctor` |
| Pipeline snapshot | `./run.sh status` | `run.bat status` |

On Windows you can also use `.\start.ps1` / `.\run.ps1` directly if your
execution policy allows it — the `.bat` files just wrap them with
`-ExecutionPolicy Bypass` so you never have to change a machine setting.

---

## Docs

- **[GUIDE.md](GUIDE.md)** — full user guide: setup, tuning, troubleshooting,
  how auto-apply works, source-by-source reliability
- **[CLAUDE.md](CLAUDE.md)** — architecture and code map, for AI assistants and
  future you

---

## A note on risk

LinkedIn and Naukri actively discourage automation. This project reduces the risk
— it drives a real browser with your own session, paces applications randomly,
and caps daily volume — but it does not eliminate it. Start with
`apply.auto_submit: false`, watch a few applications get filled in, and keep the
daily cap modest.
