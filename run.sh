#!/usr/bin/env bash
# =============================================================================
#  LocalJobAgent CLI  (macOS / Linux / WSL)   —   Windows: use run.bat
#
#    ./run.sh                 start the dashboard + background agent
#    ./run.sh discover        run one job search now
#    ./run.sh apply           apply to everything you've approved
#    ./run.sh profile         show your parsed skill library
#    ./run.sh login linkedin  log into a board once (session is then reused)
#    ./run.sh doctor          check the setup
#    ./run.sh status          quick pipeline snapshot
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

[ -d .venv ] || { echo "No virtualenv found. Run ./start.sh first."; exit 1; }
VPY=".venv/bin/python"

[ -f .env ] && set -a && . ./.env && set +a

# Make sure Ollama is up before we need it.
"$VPY" - <<'PY' 2>/dev/null || true
from jobagent.bootstrap import start_ollama
start_ollama()
PY

exec "$VPY" -m jobagent.cli "${@:-serve}"
