#!/usr/bin/env bash
# =============================================================================
#  LocalJobAgent launcher
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

[ -d .venv ] || { echo "No virtualenv found. Run ./install.sh first."; exit 1; }
# shellcheck disable=SC1091
source .venv/bin/activate
[ -f .env ] && set -a && . ./.env && set +a

# Make sure Ollama is up before we need it.
if command -v ollama >/dev/null 2>&1 && ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "▸ starting ollama…"
  (ollama serve >/dev/null 2>&1 &)
  sleep 3
fi

exec python -m jobagent.cli "${@:-serve}"
