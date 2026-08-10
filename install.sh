#!/usr/bin/env bash
# =============================================================================
#  LocalJobAgent — one-command installer
#  Works on macOS, Linux and WSL. Run:  ./install.sh
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")"
BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
say()  { echo -e "${BLUE}▸${NC} $1"; }
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
die()  { echo -e "${RED}✗${NC} $1"; exit 1; }

echo ""
echo "  ┌──────────────────────────────────────────┐"
echo "  │   LocalJobAgent — setup                  │"
echo "  │   fully local · nothing leaves your box  │"
echo "  └──────────────────────────────────────────┘"
echo ""

# ---------------------------------------------------------------- python ----
say "Checking Python"
PY=""
for cand in python3.12 python3.11 python3.10 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    V=$("$cand" -c 'import sys; print(f"{sys.version_info.major}{sys.version_info.minor:02d}")')
    [ "$V" -ge 310 ] && { PY="$cand"; break; }
  fi
done
[ -n "$PY" ] || die "Python 3.10+ required. Install it, then re-run ./install.sh"
ok "$($PY --version)"

# ------------------------------------------------------------------ venv ----
say "Creating virtual environment"
[ -d .venv ] || "$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip -q
ok "venv ready"

say "Installing Python packages (a couple of minutes)"
if ! pip install -q -r requirements.txt; then
  warn "Full install failed — retrying without python-snappy (only needed for .pages resumes)"
  grep -v 'python-snappy' requirements.txt > /tmp/req_nosnappy.txt
  pip install -q -r /tmp/req_nosnappy.txt || die "pip install failed"
fi
ok "packages installed"

say "Installing the Chromium browser Playwright drives"
python -m playwright install chromium >/dev/null 2>&1 || warn "chromium install had issues — retry later with: python -m playwright install chromium"
if [[ "$(uname)" == "Linux" ]]; then
  python -m playwright install-deps chromium >/dev/null 2>&1 || warn "run: sudo python -m playwright install-deps chromium"
fi
ok "browser ready"

# ---------------------------------------------------------------- ollama ----
say "Checking Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  warn "Ollama is not installed."
  if [[ "$(uname)" == "Darwin" ]]; then
    echo "    Install it from https://ollama.com/download, then re-run ./install.sh"
  else
    read -r -p "    Install Ollama now? [Y/n] " a
    if [[ ! "$a" =~ ^[Nn]$ ]]; then curl -fsSL https://ollama.com/install.sh | sh; fi
  fi
fi

if command -v ollama >/dev/null 2>&1; then
  ok "ollama $(ollama --version 2>/dev/null | head -1 || echo installed)"
  pgrep -x ollama >/dev/null 2>&1 || { (ollama serve >/dev/null 2>&1 &); sleep 3; }

  CHAT=$(grep -E '^\s*chat_model:'  config.yaml | head -1 | sed 's/.*: *//' | tr -d '"'"'"' ')
  EMB=$(grep  -E '^\s*embed_model:' config.yaml | head -1 | sed 's/.*: *//' | tr -d '"'"'"' ')
  CHAT=${CHAT:-qwen2.5:14b-instruct}; EMB=${EMB:-nomic-embed-text}

  echo ""
  echo "    Models to download:"
  echo "      $CHAT   (~9 GB — the reasoning model)"
  echo "      $EMB    (~275 MB — the embedding model)"
  echo ""
  read -r -p "    Download now? [Y/n] " a
  if [[ ! "$a" =~ ^[Nn]$ ]]; then
    say "Pulling $EMB";  ollama pull "$EMB"  || warn "pull failed for $EMB"
    say "Pulling $CHAT"; ollama pull "$CHAT" || warn "pull failed for $CHAT"
    ok "models ready"
  else
    warn "Skipped. Later:  ollama pull $CHAT && ollama pull $EMB"
  fi
else
  warn "Ollama missing — the agent cannot score jobs without it."
fi

# ----------------------------------------------------------------- files ----
mkdir -p resume data logs
[ -f .env ] || { [ -f .env.example ] && cp .env.example .env && ok "created .env (add free API keys there — optional)"; }

python - <<'PY'
from jobagent.db import init_db
init_db()
print("\033[0;32m✓\033[0m database initialised")
PY

chmod +x run.sh 2>/dev/null || true

# ---------------------------------------------------------------- finish ----
RES=$(ls resume/*.pdf resume/*.docx resume/*.txt resume/*.pages 2>/dev/null | head -1 || true)
echo ""
echo "  ────────────────────────────────────────────"
ok "Setup complete."
echo ""
echo "  Next:"
if [ -z "$RES" ]; then
  echo "    1. Put your resume in  ./resume/  (PDF works best)"
else
  echo "    1. ✓ resume found: $(basename "$RES")"
fi
echo "    2. Open config.yaml and fill in your phone number + expected CTC"
echo "    3. Log into the boards once (a browser window opens each time):"
echo "         ./run.sh login linkedin"
echo "         ./run.sh login naukri"
echo "    4. Sanity check:    ./run.sh doctor"
echo "    5. Start the agent: ./run.sh"
echo ""
echo "  The dashboard opens at http://127.0.0.1:8765"
echo "  ────────────────────────────────────────────"
echo ""
