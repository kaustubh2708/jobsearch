#!/usr/bin/env bash
# =============================================================================
#  LocalJobAgent — THE ONE COMMAND  (macOS / Linux / WSL)
#
#    git clone <repo> Jobsearch
#    cd Jobsearch
#    cp ~/MyResume.pdf resume/
#    ./start.sh
#
#  Windows: use start.bat instead.
#  Safe to run any time. All the real work happens in jobagent/bootstrap.py so
#  every platform behaves identically.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

R='\033[0;31m'; N='\033[0m'
die() { echo -e "${R}x${N} $1"; exit 1; }

# ---- find a usable python -------------------------------------------------
PY=""
for cand in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    V=$("$cand" -c 'import sys;print(f"{sys.version_info.major}{sys.version_info.minor:02d}")' 2>/dev/null || echo 0)
    [ "$V" -ge 310 ] 2>/dev/null && { PY="$cand"; break; }
  fi
done
[ -n "$PY" ] || die "Python 3.10+ required. Install it and re-run ./start.sh"

# ---- venv -----------------------------------------------------------------
[ -d .venv ] || "$PY" -m venv .venv || die "could not create the virtualenv"
VPY=".venv/bin/python"
[ -x "$VPY" ] || die "virtualenv looks broken — delete .venv and re-run"

# ---- load optional API keys ----------------------------------------------
[ -f .env ] && set -a && . ./.env && set +a

# ---- install (idempotent), preflight, run --------------------------------
"$VPY" -m jobagent.bootstrap install || exit $?
"$VPY" -m jobagent.bootstrap preflight || exit $?
"$VPY" -m jobagent.cli setup          || exit $?

echo ""
exec "$VPY" -m jobagent.cli serve
