#!/usr/bin/env python3
"""Local-only server for the Opportunity Desk website."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
WEB = Path(__file__).resolve().parent
DATA = WEB / "data"
STATE = DATA / "dashboard_state.json"
SNAPSHOT = DATA / "dashboard_data.json"
MAX_BODY = 4 * 1024 * 1024
DEFAULT_STATE = {"jobs": {}, "companies": {}, "customCompanies": {}, "customJobs": {},
                 "meta": {"seen": {}, "newOpportunities": {}}}
APP_ROUTES = {"/", "/home", "/apply", "/today", "/hunt", "/vaanya", "/vrinda", "/person"}


URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
CLOSED_PHRASES = ("no longer accepting", "no longer available", "position has been filled", "job not found",
                  "this job has expired", "posting has expired", "job is no longer", "opening has been closed",
                  "no longer open", "page not found", "this position is closed")
HOST_LOCKS: dict[str, threading.Lock] = {}
HOST_LOCKS_GUARD = threading.Lock()


def extract_url(job: dict) -> str:
    match = URL_RE.search(str(job.get("url") or job.get("notes") or ""))
    return match.group(0).rstrip("),.;") if match else ""


def known_urls() -> set[str]:
    """Only URLs already in the dashboard data may be checked, so this is not an open proxy."""
    urls: set[str] = set()
    try:
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        for profile in data.get("profiles", []):
            urls.update(filter(None, (extract_url(j) for j in profile.get("jobs", []))))
    except (OSError, ValueError):
        pass
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        urls.update(filter(None, (extract_url(j) for j in (state.get("customJobs") or {}).values())))
    except (OSError, ValueError):
        pass
    return urls


def check_link(url: str) -> dict:
    """Polite single-URL check: one request at a time per host, 8s timeout, small body read."""
    host = re.sub(r"^https?://([^/]+).*$", r"\1", url).lower()
    if host.endswith("linkedin.com"):
        return {"status": "manual", "note": "LinkedIn listings are checked by you, in your own visible session."}
    with HOST_LOCKS_GUARD:
        lock = HOST_LOCKS.setdefault(host, threading.Lock())
    with lock:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OrbitLinkCheck; local, polite)", "Accept": "text/html,*/*"})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                code = resp.status
                body = resp.read(60000).decode("utf-8", "ignore").lower()
        except urllib.error.HTTPError as exc:
            code, body = exc.code, ""
        except Exception as exc:  # network, TLS, timeout
            return {"status": "error", "note": type(exc).__name__}
    if code in (404, 410):
        return {"status": "dead", "code": code}
    if code in (401, 403, 429, 999) or code >= 500:
        return {"status": "manual", "code": code, "note": "The site blocked an automatic check. Open it to confirm."}
    if any(p in body for p in CLOSED_PHRASES):
        return {"status": "closed", "code": code, "note": "The page says the role is closed."}
    return {"status": "ok", "code": code}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        # Local dev server: always revalidate so edited JS/CSS is never served stale.
        if not any(h.lower().startswith(b"cache-control") for h in getattr(self, "_headers_buffer", [])):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        print("[orbit] " + fmt % args)

    def json_response(self, status: int, data: object):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/data":
            if not SNAPSHOT.exists():
                return self.json_response(404, {"error": "Run website/export_data.py first."})
            return self.json_response(200, json.loads(SNAPSHOT.read_text(encoding="utf-8")))
        if path == "/api/state":
            value = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else DEFAULT_STATE
            return self.json_response(200, value)
        if path in ("/v2", "/v2/"):
            self.path = "/website/v2/index.html"
        elif path in APP_ROUTES:
            self.path = "/website/index.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        size = int(self.headers.get("Content-Length", "0"))
        if size > MAX_BODY:
            return self.json_response(413, {"error": "Request body too large."})
        raw = self.rfile.read(size)
        if path == "/api/state":
            try:
                value = json.loads(raw.decode("utf-8"))
                allowed_maps = ("jobs", "companies", "customCompanies", "customJobs", "meta")
                if not isinstance(value, dict) or any(not isinstance(value.get(key, {}), dict) for key in allowed_maps):
                    raise ValueError("Invalid tracker state.")
                STATE.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
                return self.json_response(200, {"saved": True})
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                return self.json_response(400, {"error": str(exc)})
        if path == "/api/verify":
            try:
                urls = json.loads(raw.decode("utf-8")).get("urls", [])
                if not isinstance(urls, list):
                    raise ValueError("urls must be a list")
                allowed = known_urls()
                urls = [u for u in dict.fromkeys(urls) if isinstance(u, str) and u in allowed][:40]
                with ThreadPoolExecutor(max_workers=4) as pool:
                    results = dict(zip(urls, pool.map(check_link, urls)))
                return self.json_response(200, {"results": results})
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                return self.json_response(400, {"error": str(exc)})
        if path == "/api/refresh":
            try:
                result = subprocess.run([sys.executable, str(WEB / "export_data.py")], cwd=ROOT,
                                        capture_output=True, text=True, timeout=90)
                if result.returncode:
                    return self.json_response(500, {"error": (result.stderr or result.stdout)[-1600:]})
                return self.json_response(200, {"refreshed": True, "output": result.stdout[-800:]})
            except (OSError, subprocess.TimeoutExpired) as exc:
                return self.json_response(500, {"error": str(exc)})
        return self.json_response(404, {"error": "Unknown API route."})


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8766), Handler)
    print("Orbit Opportunity Desk: http://127.0.0.1:8766/website/")
    print("Local-only server. Keep this process running while using the site. Stop with Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
