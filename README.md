# LocalJobAgent

An autonomous job search agent for the Indian market that runs entirely on your
own machine. It reads your resume, searches the boards daily, scores every
posting against your real skills with a local LLM, and applies to the ones you
approve.

**Nothing is sent to any cloud AI service.** Your resume, salary expectations and
application history stay on your computer.

---

## Quick start

```bash
git clone <this-repo> Jobsearch
cd Jobsearch
cp ~/Downloads/MyResume.pdf resume/
./start.sh
```

That's it. `start.sh` installs Python dependencies, Playwright's Chromium, Ollama
and the models, walks you through a short setup, and opens the dashboard at
**http://127.0.0.1:8765**.

Every run after the first just starts the agent.

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
- macOS, Linux, or Windows via WSL

---

## Commands

```bash
./start.sh               # install if needed, then run everything
./run.sh discover        # run one job search now
./run.sh apply           # apply to everything approved
./run.sh profile         # show your parsed skill library
./run.sh login linkedin  # log into a board once
./run.sh doctor          # check the setup
./run.sh status          # pipeline snapshot
```

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
