"""Background scheduler — the part that makes this an agent rather than a script.

Runs inside the same process as the dashboard, so `./run.sh` is genuinely the
only command you need.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import load_config
from .db import log as dblog

log = logging.getLogger("jobagent.scheduler")
_sched: BackgroundScheduler | None = None


def _discovery():
    from .pipeline import run_discovery

    try:
        run_discovery()
    except Exception as e:  # noqa: BLE001
        log.exception("scheduled discovery failed")
        dblog("error", f"Scheduled job search failed: {e}")


def _apply():
    from .applier.engine import run_apply_batch
    from .db import Application, AppStatus, get_session
    from sqlmodel import select

    try:
        with get_session() as s:
            waiting = s.exec(
                select(Application).where(Application.status == AppStatus.QUEUED.value)
            ).all()
        if not waiting:
            return
        run_apply_batch()
    except Exception as e:  # noqa: BLE001
        log.exception("scheduled apply failed")
        dblog("error", f"Scheduled apply run failed: {e}")


def _timezone(name: str = "Asia/Kolkata"):
    """Windows has no system tz database. The `tzdata` wheel supplies one, but
    if it's somehow missing we fall back to local time rather than crashing."""
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(name)
    except Exception:
        try:
            import pytz

            return pytz.timezone(name)
        except Exception:
            log.warning("no tz database for %s — using local time. "
                        "Fix with: pip install tzdata", name)
            return None


def start() -> BackgroundScheduler | None:
    global _sched
    cfg = load_config()
    if not cfg.schedule.enabled:
        log.info("scheduler disabled in config")
        return None
    if _sched:
        return _sched

    tz = _timezone()
    _sched = BackgroundScheduler(timezone=tz) if tz else BackgroundScheduler()

    for slot in filter(None, [cfg.schedule.discovery_time, cfg.schedule.discovery_time_2]):
        try:
            h, m = slot.split(":")
            _sched.add_job(_discovery, CronTrigger(hour=int(h), minute=int(m)),
                           id=f"discovery_{slot}", replace_existing=True,
                           misfire_grace_time=3600, max_instances=1)
            log.info("daily job search scheduled for %s IST", slot)
        except Exception as e:  # noqa: BLE001
            log.warning("bad schedule time '%s': %s", slot, e)

    _sched.add_job(_apply, IntervalTrigger(minutes=max(2, cfg.schedule.apply_poll_minutes)),
                   id="apply_poll", replace_existing=True, max_instances=1)
    log.info("apply worker polls every %d min", cfg.schedule.apply_poll_minutes)

    _sched.start()
    dblog("info", "Scheduler started")
    return _sched


def stop() -> None:
    global _sched
    if _sched:
        _sched.shutdown(wait=False)
        _sched = None
