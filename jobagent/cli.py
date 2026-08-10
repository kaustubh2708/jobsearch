"""jobagent — command line entry point."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import LOG_DIR, load_config
from .db import init_db

app = typer.Typer(add_completion=False, help="Local, private, autonomous job search agent.")
c = Console()


def _logging(verbose: bool = False):
    # Windows consoles default to cp1252 and blow up on ₹ / ✓ in a log line.
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(name)-26s %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(LOG_DIR / "jobagent.log", encoding="utf-8")],
    )
    for noisy in ("httpx", "urllib3", "apscheduler.executors", "playwright", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


@app.command()
def serve(no_schedule: bool = typer.Option(False, help="Dashboard only, no background runs.")):
    """Start the dashboard and the background agent. This is the main command."""
    _logging()
    init_db()
    from . import scheduler
    from .server import serve as _serve

    cfg = load_config()
    if not no_schedule:
        scheduler.start()
    c.print(f"\n[bold cyan]LocalJobAgent[/] → [link]http://{cfg.server.host}:{cfg.server.port}[/]\n")
    _serve()


@app.command()
def discover():
    """Run one job search + scoring pass right now."""
    _logging()
    init_db()
    from .pipeline import run_discovery

    s = run_discovery()
    c.print(f"\n[green]{s['matched']}[/] jobs waiting for review "
            f"({s['scored']} scored from {s['raw']} raw postings in {s['duration_s']/60:.1f} min)\n")


@app.command("apply")
def apply_cmd(limit: Optional[int] = typer.Option(None, help="Max applications this run.")):
    """Apply to everything you've approved."""
    _logging()
    init_db()
    from .applier.engine import run_apply_batch

    r = run_apply_batch(limit=limit)
    c.print(f"\n[green]{r['message']}[/]\n")


@app.command()
def profile(rebuild: bool = typer.Option(False, "--rebuild", help="Force a re-parse.")):
    """Parse your resume into the skill library and show it."""
    _logging()
    init_db()
    from .resume_parser import get_or_build, ingest

    row = ingest() if rebuild else get_or_build()
    d = row.data()
    c.print(f"\n[bold]{d.get('headline','')}[/]")
    c.print(f"[dim]{d.get('summary','')}[/]\n")
    t = Table(show_header=False, box=None, padding=(0, 2))
    t.add_row("Seniority", f"{d.get('seniority','')} · {d.get('total_years_experience',0)} yrs")
    t.add_row("Target roles", ", ".join(d.get("target_roles", [])[:8]))
    t.add_row("Core skills", ", ".join(d.get("core_skills", [])[:15]))
    t.add_row("Skills indexed", str(len(d.get("hard_skills", []))))
    t.add_row("Domains", ", ".join(d.get("domains", [])[:8]))
    c.print(t)
    c.print()


@app.command()
def login(site: str = typer.Argument(..., help="linkedin | naukri | wellfound | instahyre | indeed")):
    """Open a browser so you can log in once. The session is then reused forever."""
    _logging()
    from .applier.browser import interactive_login

    interactive_login(site.lower())


@app.command()
def status():
    """Quick snapshot of the pipeline."""
    init_db()
    from sqlmodel import func, select
    from .db import Application, AppStatus, Job, JobStatus, get_session
    from .llm import get_llm

    try:
        llm = get_llm()
        up = llm.is_up()
    except Exception as e:  # noqa: BLE001
        llm, up = None, False
        c.print(f"[yellow]LLM client error: {e}[/]")
    c.print(f"\nOllama: {'[green]connected[/]' if up else '[red]not reachable[/]'}")
    if up and llm:
        for m, ok in llm.ensure_models().items():
            c.print(f"  {m}: {'[green]ready[/]' if ok else '[red]missing — run: ollama pull ' + m + '[/]'}")

    with get_session() as s:
        cnt = lambda M, f, v: s.exec(select(func.count()).select_from(M).where(f == v)).one()  # noqa: E731
        t = Table("", "", show_header=False, box=None, padding=(0, 2))
        t.add_row("Awaiting review", str(cnt(Job, Job.status, JobStatus.PENDING.value)))
        t.add_row("Approved", str(cnt(Job, Job.status, JobStatus.APPROVED.value)))
        t.add_row("Queued to apply", str(cnt(Application, Application.status, AppStatus.QUEUED.value)))
        t.add_row("Needs your input", str(cnt(Application, Application.status, AppStatus.NEEDS_INPUT.value)))
        t.add_row("Applied", str(cnt(Application, Application.status, AppStatus.APPLIED.value)))
        t.add_row("Interviews", str(cnt(Application, Application.status, AppStatus.INTERVIEW.value)))
        c.print()
        c.print(t)
        c.print()


@app.command()
def setup(force: bool = typer.Option(False, "--force", help="Re-run even if already done.")):
    """First-run wizard: fill in your details and build the skill library."""
    _logging()
    init_db()
    from .config import ROOT, load_config, save_config
    from .resume_parser import find_resume, ingest
    from .db import active_skill_library
    from .llm import get_llm

    stamp = ROOT / "data" / ".setup_done"
    cfg = load_config(reload=True)

    if stamp.exists() and not force:
        # quiet path — just make sure the skill library exists
        if not active_skill_library():
            c.print("[dim]Building skill library from your resume…[/]")
            try:
                ingest()
            except Exception as e:  # noqa: BLE001
                c.print(f"[red]Could not parse your resume: {e}[/]")
                raise typer.Exit(1)
        return

    c.print("\n[bold]Let's get you set up.[/] [dim]Press Enter to accept the default in brackets.[/]\n")

    def ask(label, current, cast=str, allow_blank=True):
        shown = current if current not in (None, "") else "—"
        v = typer.prompt(f"  {label} [{shown}]", default="", show_default=False).strip()
        if not v:
            return current
        try:
            return cast(v)
        except Exception:
            c.print("  [yellow]didn't understand that, keeping the existing value[/]")
            return current

    p = cfg.profile
    p.full_name = ask("Your full name", p.full_name)
    p.email = ask("Email", p.email)
    p.phone = ask("Phone (with +91 — most forms require it)", p.phone)
    p.location = ask("Current city", p.location)
    p.linkedin = ask("LinkedIn URL", p.linkedin)
    p.notice_period_days = ask("Notice period in days", p.notice_period_days, int)
    p.current_ctc_lpa = ask("Current CTC in LPA (blank = prefer not to say)", p.current_ctc_lpa, float)
    p.expected_ctc_lpa = ask("Expected CTC in LPA (blank = negotiable)", p.expected_ctc_lpa, float)

    locs = ", ".join(cfg.search.locations)
    new_locs = ask("Cities to search, comma separated", locs)
    if new_locs != locs:
        cfg.search.locations = [x.strip() for x in new_locs.split(",") if x.strip()]

    c.print("")
    live = typer.confirm("  Let the agent actually submit applications you approve?", default=True)
    cfg.apply.auto_submit = live
    if live:
        cfg.apply.daily_apply_cap = ask("Max real applications per day", cfg.apply.daily_apply_cap, int)
    else:
        c.print("  [dim]It will fill every form and stop at Submit. Flip apply.auto_submit later.[/]")

    # resume PDF for uploads
    r = find_resume(cfg)
    pdfs = list(cfg.resume_dir.glob("*.pdf"))
    if pdfs:
        cfg.resume.upload_pdf = str(pdfs[0].relative_to(ROOT))
        c.print(f"\n  [green]✓[/] uploads will use {pdfs[0].name}")
    else:
        c.print(f"\n  [yellow]![/] no PDF in {cfg.resume_dir.name}/ — most forms need one.")
        c.print(f"    [dim]Export your resume to PDF and drop it in {cfg.resume_dir.name}/ when you can.[/]")

    save_config(cfg)
    c.print("\n[green]✓[/] saved to config.yaml")

    # skill library
    llm = get_llm()
    if not llm.is_up():
        c.print("\n[red]Ollama isn't reachable — start it with `ollama serve` and re-run ./start.sh[/]")
        raise typer.Exit(1)
    c.print(f"\n[dim]Reading {r.name} with {cfg.llm.chat_model}… this takes 30-90 seconds.[/]")
    try:
        row = ingest()
    except Exception as e:  # noqa: BLE001
        c.print(f"[red]Could not parse your resume: {e}[/]")
        raise typer.Exit(1)
    d = row.data()
    c.print(f"[green]✓[/] {len(d.get('hard_skills', []))} skills indexed")
    c.print(f"[green]✓[/] will search for: [cyan]{', '.join(d.get('target_roles', [])[:6])}[/]")

    # logins
    c.print("\n[bold]One last thing[/] — the agent applies using your own logged-in browser session.")
    for site in ("linkedin", "naukri"):
        if typer.confirm(f"  Log into {site} now?", default=True):
            from .applier.browser import interactive_login
            try:
                interactive_login(site)
            except Exception as e:  # noqa: BLE001
                c.print(f"  [yellow]skipped: {e}[/]")

    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.touch()
    c.print("\n[green]All set.[/] Starting the dashboard…\n")


@app.command()
def doctor():
    """Check that everything the agent needs is actually in place."""
    _logging()
    init_db()
    cfg = load_config()
    from .llm import get_llm
    from .resume_parser import find_resume

    ok = True
    def check(label, good, hint=""):
        nonlocal ok
        c.print(f"  {'[green]✓[/]' if good else '[red]✗[/]'} {label}" + (f"  [dim]{hint}[/]" if not good and hint else ""))
        ok = ok and good

    c.print("\n[bold]Checks[/]")
    try:
        llm = get_llm()
        up = llm.is_up()
    except Exception as e:  # noqa: BLE001
        llm, up = None, False
        c.print(f"  [yellow]LLM client error: {e}[/]")
    check("Ollama reachable", up, "start it with: ollama serve")
    if up and llm:
        for m, present in llm.ensure_models().items():
            check(f"model {m}", present, f"ollama pull {m}")
    r = find_resume(cfg)
    check(f"resume found{f' ({r.name})' if r else ''}", bool(r), f"put a .pdf/.docx in {cfg.resume_dir}")
    check("resume PDF for uploads", bool(cfg.resume_pdf), f"set resume.upload_pdf in config.yaml")
    check("phone number set", bool(cfg.profile.phone), "most application forms require it")
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        check("playwright installed", True)
    except Exception:
        check("playwright installed", False, "python -m playwright install chromium")
    c.print(f"\n{'[green]Ready to go.[/]' if ok else '[yellow]Fix the above, then run: jobagent doctor[/]'}\n")


def main():
    app()


if __name__ == "__main__":
    main()
