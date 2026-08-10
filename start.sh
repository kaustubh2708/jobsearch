#!/usr/bin/env bash
# =============================================================================
#  LocalJobAgent — THE ONE COMMAND
#
#    git clone <repo> && cd Jobsearch
#    cp ~/my_resume.pdf resume/
#    ./start.sh
#
#  Safe to run any time. First run installs everything and walks you through
#  setup; every run after that just starts the agent.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

G='\033[0;32m'; B='\033[0;34m'; Y='\033[1;33m'; R='\033[0;31m'; D='\033[2m'; N='\033[0m'
say()  { echo -e "${B}▸${N} $1"; }
ok()   { echo -e "${G}✓${N} $1"; }
warn() { echo -e "${Y}!${N} $1"; }
die()  { echo -e "${R}✗${N} $1"; exit 1; }

echo ""
echo -e "  ${B}┌────────────────────────────────────────────┐${N}"
echo -e "  ${B}│${N}  ${G}LocalJobAgent${N}                             ${B}│${N}"
echo -e "  ${B}│${N}  ${D}fully local · nothing leaves your machine${N}  ${B}│${N}"
echo -e "  ${B}└────────────────────────────────────────────┘${N}"
echo ""

STAMP=".venv/.setup_complete"

# ============================================================ 1. install ====
if [ ! -f "$STAMP" ]; then
  say "First run — setting everything up. This takes a few minutes."
  echo ""

  # --- python ---
  PY=""
  for cand in python3.12 python3.11 python3.10 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
      V=$("$cand" -c 'import sys;print(f"{sys.version_info.major}{sys.version_info.minor:02d}")' 2>/dev/null || echo 0)
      [ "$V" -ge 310 ] && { PY="$cand"; break; }
    fi
  done
  [ -n "$PY" ] || die "Python 3.10+ required. Install it and re-run ./start.sh"
  ok "$($PY --version)"

  # --- venv + deps ---
  say "Creating virtual environment"
  [ -d .venv ] || "$PY" -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install --upgrade pip -q

  say "Installing Python packages"
  if ! pip install -q -r requirements.txt 2>/dev/null; then
    warn "retrying without python-snappy (only needed to read .pages resumes)"
    grep -v 'python-snappy' requirements.txt > /tmp/_req.txt
    pip install -q -r /tmp/_req.txt || die "pip install failed — see the output above"
  fi
  ok "packages installed"

  say "Installing the browser Playwright drives"
  python -m playwright install chromium >/dev/null 2>&1 || warn "chromium install had trouble; retry: python -m playwright install chromium"
  [[ "$(uname)" == "Linux" ]] && (python -m playwright install-deps chromium >/dev/null 2>&1 || warn "may need: sudo python -m playwright install-deps chromium")
  ok "browser ready"

  # --- ollama ---
  if ! command -v ollama >/dev/null 2>&1; then
    warn "Ollama is not installed — the agent needs it to score jobs."
    if [[ "$(uname)" == "Darwin" ]]; then
      echo "    Get it from https://ollama.com/download, then re-run ./start.sh"
      exit 1
    else
      read -r -p "    Install Ollama now? [Y/n] " a
      [[ "$a" =~ ^[Nn]$ ]] && die "Ollama is required." || curl -fsSL https://ollama.com/install.sh | sh
    fi
  fi
  ok "ollama present"

  pgrep -x ollama >/dev/null 2>&1 || { (ollama serve >/dev/null 2>&1 &); sleep 3; }

  # --- pick a model that fits the machine ---
  CHAT=$(grep -E '^\s*chat_model:' config.yaml | head -1 | sed 's/.*: *//' | tr -d '"'"'"' ')
  EMB=$(grep -E '^\s*embed_model:' config.yaml | head -1 | sed 's/.*: *//' | tr -d '"'"'"' ')
  CHAT=${CHAT:-qwen2.5:14b-instruct}; EMB=${EMB:-nomic-embed-text}

  VRAM=0
  if command -v nvidia-smi >/dev/null 2>&1; then
    VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 || echo 0)
  elif [[ "$(uname)" == "Darwin" ]]; then
    VRAM=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1048576 ))
  fi
  if [ "$VRAM" -gt 0 ]; then
    if   [ "$VRAM" -ge 30000 ]; then SUG="qwen2.5:32b-instruct"
    elif [ "$VRAM" -ge 11000 ]; then SUG="qwen2.5:14b-instruct"
    else                             SUG="llama3.1:8b-instruct-q4_K_M"; fi
    echo -e "  ${D}detected ~${VRAM} MB of GPU/unified memory → suggests ${SUG}${N}"
    if [ "$SUG" != "$CHAT" ]; then
      read -r -p "    Use $SUG instead of $CHAT? [y/N] " a
      if [[ "$a" =~ ^[Yy]$ ]]; then
        python - "$SUG" <<'PY'
import re,sys,pathlib
p=pathlib.Path("config.yaml"); t=p.read_text()
p.write_text(re.sub(r'(chat_model:\s*).*', r'\1"%s"' % sys.argv[1], t, count=1))
PY
        CHAT="$SUG"; ok "chat model set to $CHAT"
      fi
    fi
  fi

  say "Downloading models — $EMB then $CHAT (this is the slow part)"
  ollama pull "$EMB"  || warn "could not pull $EMB"
  ollama pull "$CHAT" || warn "could not pull $CHAT"
  ok "models ready"

  mkdir -p resume data logs
  [ -f .env ] || { [ -f .env.example ] && cp .env.example .env; }
  python -c "from jobagent.db import init_db; init_db()" && ok "database initialised"

  touch "$STAMP"
  echo ""
  ok "Install complete."
  echo ""
fi

# ---------------------------------------------------------------------------
# shellcheck disable=SC1091
source .venv/bin/activate
[ -f .env ] && set -a && . ./.env && set +a
command -v ollama >/dev/null 2>&1 && ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 && { (ollama serve >/dev/null 2>&1 &); sleep 3; }

# ============================================================== 2. resume ===
RESUME=$(find resume -maxdepth 1 -type f \( -name '*.pdf' -o -name '*.docx' -o -name '*.txt' -o -name '*.md' -o -name '*.pages' \) 2>/dev/null | head -1 || true)
if [ -z "$RESUME" ]; then
  echo ""
  warn "No resume found."
  echo ""
  echo "    Drop your resume into the resume/ folder, then run ./start.sh again:"
  echo -e "      ${D}cp ~/Downloads/MyResume.pdf $(pwd)/resume/${N}"
  echo ""
  echo "    PDF works best. .docx, .txt and .pages also work."
  echo ""
  exit 1
fi
ok "resume: $(basename "$RESUME")"

# ============================================================ 3. first-run ===
# Interactive wizard: profile details + skill library. Skipped once complete.
python -m jobagent.cli setup || die "setup failed"

# ============================================================== 4. launch ====
echo ""
say "Starting the agent + dashboard"
echo ""
exec python -m jobagent.cli serve
