#!/usr/bin/env python3
"""Build the website snapshot from the project's latest tracker workbooks."""
from __future__ import annotations

import importlib.util
import io
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent / "data"


def sheet_ids() -> dict[str, str]:
    """Google Sheet IDs come from website/sheets.config.json (git-ignored) or ORBIT_<NAME>_SHEET_ID env vars."""
    path = Path(__file__).resolve().parent / "sheets.config.json"
    ids = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {name: os.environ.get(f"ORBIT_{name.upper()}_SHEET_ID") or ids.get(name, "") for name in ("vaanya", "vrinda")}


_IDS = sheet_ids()
SHEETS = {
    "vaanya": {
        "id": _IDS["vaanya"],
        "fallback": ROOT / "data" / "Job Search.xlsx",
        "parser": "parse_vaanya",
    },
    "vrinda": {
        "id": _IDS["vrinda"],
        "fallback": ROOT / "data" / "companies.xlsx",
        "parser": "parse_vrinda",
    },
}


def load_project_parser():
    parser_path = ROOT / "scripts" / "export_dashboard_data.py"
    spec = importlib.util.spec_from_file_location("project_dashboard_exporter", parser_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load project workbook parser: {parser_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fetch_live_workbook(sheet_id: str) -> io.BytesIO:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    request = Request(url, headers={"User-Agent": "Orbit local job-search dashboard/1.0"})
    with urlopen(request, timeout=60) as response:
        content_type = response.headers.get_content_type()
        data = response.read(30 * 1024 * 1024 + 1)
    if content_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        raise RuntimeError(f"Google returned {content_type}, not an Excel workbook")
    if len(data) > 30 * 1024 * 1024:
        raise RuntimeError("Google Sheet export exceeded the 30 MB safety limit")
    if not data.startswith(b"PK\x03\x04"):
        raise RuntimeError("Google Sheet export did not contain a valid XLSX file")
    return io.BytesIO(data)


def main() -> None:
    parser = load_project_parser()
    profiles = []
    sources = {}
    warnings = []
    for key, config in SHEETS.items():
        parse = getattr(parser, config["parser"])
        try:
            if not config["id"]:
                raise RuntimeError("no Google Sheet ID configured (see website/sheets.config.example.json)")
            profile = parse(fetch_live_workbook(config["id"]))
            sources[key] = {"kind": "google_sheets", "sheet_id": config["id"]}
        except Exception as exc:
            fallback = config["fallback"]
            if not fallback.exists():
                raise RuntimeError(f"Live Google Sheet {key} could not be read and fallback is missing: {exc}") from exc
            profile = parse(fallback)
            sources[key] = {"kind": "local_workbook_fallback", "file": str(fallback.relative_to(ROOT))}
            warnings.append(f"{key}: live Google Sheet export failed ({exc}); used {fallback.relative_to(ROOT)}")
        profiles.append(profile)
    snapshot = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_mode": "live" if all(source["kind"] == "google_sheets" for source in sources.values()) else "fallback",
        "sources": sources,
        "source_warnings": warnings,
        "profiles": profiles,
    }
    target = DATA / "dashboard_data.json"
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    for profile in profiles:
        linked = sum(bool(job["url"]) for job in profile["jobs"])
        print(f"{profile['candidate']}: {len(profile['companies'])} companies, {len(profile['jobs'])} records, {linked} linked ({sources[profile['candidate'].lower()]['kind']})")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
