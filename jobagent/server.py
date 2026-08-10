"""FastAPI backend + static dashboard."""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import func, select

from .config import load_config, save_config
from .db import (Application, AppStatus, Job, JobStatus, RunLog, SkillLibrary,
                 get_session, init_db, utcnow)
from .llm import get_llm

log = logging.getLogger("jobagent.server")
WEB = Path(__file__).parent / "web"

app = FastAPI(title="LocalJobAgent", docs_url="/api/docs")

_state: Dict[str, Any] = {"running": None, "last_run": None}


@app.on_event("startup")
def _startup():
    init_db()


# --------------------------------------------------------------------------- #
#  Models
# --------------------------------------------------------------------------- #
class StatusUpdate(BaseModel):
    status: str


class AppStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class AnswersIn(BaseModel):
    answers: Dict[str, str]


class BulkIn(BaseModel):
    ids: List[int]
    status: str


# --------------------------------------------------------------------------- #
#  Jobs — review board
# --------------------------------------------------------------------------- #
@app.get("/api/jobs")
def list_jobs(status: str = "pending", limit: int = 200, sort: str = "score",
              q: str = "", source: str = "", min_score: int = 0):
    with get_session() as s:
        stmt = select(Job)
        if status and status != "all":
            stmt = stmt.where(Job.status == status)
        if source:
            stmt = stmt.where(Job.source == source)
        if min_score:
            stmt = stmt.where(Job.score >= min_score)
        stmt = stmt.order_by(Job.score.desc() if sort == "score" else Job.discovered_at.desc())
        rows = s.exec(stmt.limit(limit)).all()
        out = [r.as_dict() for r in rows]
    if q:
        ql = q.lower()
        out = [j for j in out if ql in (j["title"] + j["company"] + j["location"]).lower()]
    return out


@app.get("/api/jobs/{job_id}")
def get_job(job_id: int):
    with get_session() as s:
        j = s.get(Job, job_id)
        if not j:
            raise HTTPException(404, "job not found")
        d = j.as_dict()
        a = s.exec(select(Application).where(Application.job_id == job_id)).first()
        d["application"] = a.as_dict() if a else None
        return d


@app.patch("/api/jobs/{job_id}")
def set_job_status(job_id: int, body: StatusUpdate):
    valid = {e.value for e in JobStatus}
    if body.status not in valid:
        raise HTTPException(400, f"status must be one of {valid}")
    with get_session() as s:
        j = s.get(Job, job_id)
        if not j:
            raise HTTPException(404, "job not found")
        j.status = body.status
        j.reviewed_at = utcnow()
        s.add(j)
        # approving pushes it straight onto the tracker
        if body.status == JobStatus.APPROVED.value:
            if not s.exec(select(Application).where(Application.job_id == job_id)).first():
                s.add(Application(job_id=job_id, status=AppStatus.QUEUED.value))
        s.commit()
    return {"ok": True, "id": job_id, "status": body.status}


@app.post("/api/jobs/bulk")
def bulk_status(body: BulkIn):
    with get_session() as s:
        for jid in body.ids:
            j = s.get(Job, jid)
            if not j:
                continue
            j.status = body.status
            j.reviewed_at = utcnow()
            s.add(j)
            if body.status == JobStatus.APPROVED.value:
                if not s.exec(select(Application).where(Application.job_id == jid)).first():
                    s.add(Application(job_id=jid, status=AppStatus.QUEUED.value))
        s.commit()
    return {"ok": True, "count": len(body.ids)}


# --------------------------------------------------------------------------- #
#  Applications — tracker board
# --------------------------------------------------------------------------- #
@app.get("/api/applications")
def list_applications(status: str = "all", limit: int = 300):
    with get_session() as s:
        stmt = select(Application)
        if status != "all":
            stmt = stmt.where(Application.status == status)
        rows = s.exec(stmt.order_by(Application.updated_at.desc()).limit(limit)).all()
        out = []
        for a in rows:
            d = a.as_dict()
            j = s.get(Job, a.job_id)
            d["job"] = j.as_dict() if j else None
            out.append(d)
        return out


@app.patch("/api/applications/{app_id}")
def set_app_status(app_id: int, body: AppStatusUpdate):
    valid = {e.value for e in AppStatus}
    if body.status not in valid:
        raise HTTPException(400, f"status must be one of {valid}")
    with get_session() as s:
        a = s.get(Application, app_id)
        if not a:
            raise HTTPException(404, "application not found")
        a.status = body.status
        if body.notes is not None:
            a.notes = body.notes
        a.updated_at = utcnow()
        s.add(a)
        s.commit()
    return {"ok": True}


@app.post("/api/applications/{app_id}/answers")
def submit_answers(app_id: int, body: AnswersIn):
    from .applier.engine import answer_pending

    answer_pending(app_id, body.answers)
    return {"ok": True, "requeued": True}


# --------------------------------------------------------------------------- #
#  Runs
# --------------------------------------------------------------------------- #
def _run_discovery_bg():
    from .pipeline import run_discovery

    _state["running"] = "discovery"
    try:
        _state["last_run"] = run_discovery()
    except Exception as e:  # noqa: BLE001
        log.exception("discovery failed")
        _state["last_run"] = {"error": str(e)}
    finally:
        _state["running"] = None


def _run_apply_bg():
    from .applier.engine import run_apply_batch

    _state["running"] = "apply"
    try:
        _state["last_run"] = run_apply_batch()
    except Exception as e:  # noqa: BLE001
        log.exception("apply batch failed")
        _state["last_run"] = {"error": str(e)}
    finally:
        _state["running"] = None


@app.post("/api/run/discovery")
def trigger_discovery():
    if _state["running"]:
        raise HTTPException(409, f"{_state['running']} already running")
    threading.Thread(target=_run_discovery_bg, daemon=True).start()
    return {"ok": True, "started": "discovery"}


@app.post("/api/run/apply")
def trigger_apply():
    if _state["running"]:
        raise HTTPException(409, f"{_state['running']} already running")
    threading.Thread(target=_run_apply_bg, daemon=True).start()
    return {"ok": True, "started": "apply"}


@app.post("/api/run/reparse-resume")
def reparse():
    from .resume_parser import ingest

    try:
        row = ingest()
        return {"ok": True, "skills": len(row.data().get("hard_skills", []))}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, str(e))


# --------------------------------------------------------------------------- #
#  Meta
# --------------------------------------------------------------------------- #
@app.get("/api/stats")
def stats():
    with get_session() as s:
        def count(model, **where):
            stmt = select(func.count()).select_from(model)
            for k, v in where.items():
                stmt = stmt.where(getattr(model, k) == v)
            return s.exec(stmt).one()

        today = (datetime.now(timezone.utc) - timedelta(hours=24)).replace(tzinfo=None)
        week = (datetime.now(timezone.utc) - timedelta(days=7)).replace(tzinfo=None)

        found_today = s.exec(
            select(func.count()).select_from(Job).where(Job.discovered_at >= today)
        ).one()
        applied_week = s.exec(
            select(func.count()).select_from(Application)
            .where(Application.submitted_at >= week)
        ).one()
        avg = s.exec(
            select(func.avg(Job.score)).where(Job.status == JobStatus.PENDING.value)
        ).one() or 0

        by_source = {}
        for r in s.exec(select(Job.source, func.count()).group_by(Job.source)).all():
            by_source[r[0] or "unknown"] = r[1]

        return {
            "pending": count(Job, status=JobStatus.PENDING.value),
            "approved": count(Job, status=JobStatus.APPROVED.value),
            "rejected": count(Job, status=JobStatus.REJECTED.value),
            "archived": count(Job, status=JobStatus.ARCHIVED.value),
            "found_today": found_today,
            "applied_total": count(Application, status=AppStatus.APPLIED.value),
            "applied_week": applied_week,
            "queued": count(Application, status=AppStatus.QUEUED.value),
            "needs_input": count(Application, status=AppStatus.NEEDS_INPUT.value),
            "interview": count(Application, status=AppStatus.INTERVIEW.value),
            "offer": count(Application, status=AppStatus.OFFER.value),
            "avg_score": round(float(avg), 1),
            "by_source": by_source,
            "running": _state["running"],
            "last_run": _state["last_run"],
        }


@app.get("/api/profile")
def profile():
    with get_session() as s:
        row = s.exec(
            select(SkillLibrary).where(SkillLibrary.is_active == True)  # noqa: E712
            .order_by(SkillLibrary.created_at.desc())
        ).first()
    if not row:
        return {"exists": False}
    d = row.data()
    d["exists"] = True
    d["source_file"] = row.source_file
    d["created_at"] = row.created_at.isoformat()
    return d


@app.get("/api/logs")
def logs(limit: int = 80):
    with get_session() as s:
        rows = s.exec(select(RunLog).order_by(RunLog.ts.desc()).limit(limit)).all()
        return [{"ts": r.ts.isoformat(), "kind": r.kind, "message": r.message} for r in rows]


@app.get("/api/health")
def health():
    cfg = load_config()
    try:
        llm = get_llm()
        up = llm.is_up()
        models = llm.ensure_models() if up else {}
    except Exception as e:  # noqa: BLE001
        log.warning("llm health check failed: %s", e)
        up, models = False, {}
    return {
        "ollama": up,
        "models_present": models,
        "chat_model": cfg.llm.chat_model,
        "embed_model": cfg.llm.embed_model,
        "resume_pdf": str(cfg.resume_pdf) if cfg.resume_pdf else None,
        "auto_submit": cfg.apply.auto_submit,
        "daily_cap": cfg.apply.daily_apply_cap,
    }


@app.get("/api/config")
def get_cfg():
    return load_config(reload=True).model_dump(mode="json")


@app.put("/api/config")
def put_cfg(body: Dict[str, Any]):
    from .config import Config

    try:
        cfg = Config(**body)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"invalid config: {e}")
    save_config(cfg)
    return {"ok": True}


# --------------------------------------------------------------------------- #
#  Static
# --------------------------------------------------------------------------- #
if WEB.exists():
    app.mount("/static", StaticFiles(directory=str(WEB)), name="static")


@app.get("/")
def index():
    return FileResponse(str(WEB / "index.html"))


def serve():
    import uvicorn

    cfg = load_config()
    init_db()
    if cfg.server.open_browser_on_start:
        import webbrowser

        threading.Timer(1.5, lambda: webbrowser.open(
            f"http://{cfg.server.host}:{cfg.server.port}")).start()
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, log_level="info")
