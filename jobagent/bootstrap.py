"""Cross-platform installer.

All the real setup work lives here rather than in the shell scripts, so
Windows, macOS and Linux stay in sync by construction. The launchers
(start.sh / start.ps1 / start.bat) only find a Python, make a venv, and hand
over to this module.

Safe to run repeatedly — every step is idempotent.
"""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IS_WIN = os.name == "nt"

# ---------------------------------------------------------------------------
#  console
# ---------------------------------------------------------------------------
def _supports_colour() -> bool:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return False
    if not IS_WIN:
        return True
    # Windows Terminal sets WT_SESSION. Old conhost needs VT mode turning on,
    # which is available on Windows 10+ — try it and believe the return code.
    if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
        return True
    try:
        import ctypes

        k = ctypes.windll.kernel32
        return bool(k.SetConsoleMode(k.GetStdHandle(-11), 7))
    except Exception:
        return False


_C = _supports_colour()
G = "\033[0;32m" if _C else ""
B = "\033[0;34m" if _C else ""
Y = "\033[1;33m" if _C else ""
R = "\033[0;31m" if _C else ""
D = "\033[2m" if _C else ""
N = "\033[0m" if _C else ""

# conhost can't render ✓/▸ reliably; fall back to ASCII.
_UNI = True
try:
    "✓▸✗".encode(sys.stdout.encoding or "utf-8")
except Exception:
    _UNI = False

TICK = "✓" if _UNI else "[ok]"
ARROW = "▸" if _UNI else ">"
CROSS = "✗" if _UNI else "[!]"


def say(m):  print(f"{B}{ARROW}{N} {m}", flush=True)
def ok(m):   print(f"{G}{TICK}{N} {m}", flush=True)
def warn(m): print(f"{Y}!{N} {m}", flush=True)
def err(m):  print(f"{R}{CROSS}{N} {m}", flush=True)


def banner():
    print()
    print(f"  {B}+------------------------------------------+{N}")
    print(f"  {B}|{N}  {G}LocalJobAgent{N}                             {B}|{N}")
    print(f"  {B}|{N}  {D}fully local - nothing leaves your machine{N}  {B}|{N}")
    print(f"  {B}+------------------------------------------+{N}")
    print()


# ---------------------------------------------------------------------------
#  helpers
# ---------------------------------------------------------------------------
def run(cmd, check=True, quiet=False, **kw):
    """Run a command list. Returns CompletedProcess; never raises unless check."""
    try:
        return subprocess.run(
            cmd,
            check=check,
            stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.STDOUT if quiet else None,
            **kw,
        )
    except FileNotFoundError:
        if check:
            raise
        return subprocess.CompletedProcess(cmd, 1)
    except subprocess.CalledProcessError:
        if check:
            raise
        return subprocess.CompletedProcess(cmd, 1)


def which(name: str) -> str | None:
    return shutil.which(name) or (shutil.which(name + ".exe") if IS_WIN else None)


def ask_yes(prompt: str, default: bool = True) -> bool:
    if not sys.stdin.isatty():
        return default
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        a = input(f"    {prompt} {suffix} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not a:
        return default
    return a.startswith("y")


# ---------------------------------------------------------------------------
#  steps
# ---------------------------------------------------------------------------
def install_python_deps() -> None:
    say("Installing Python packages")
    pip = [sys.executable, "-m", "pip"]
    run(pip + ["install", "--upgrade", "pip", "-q"], check=False, quiet=True)

    req = ROOT / "requirements.txt"
    r = run(pip + ["install", "-q", "-r", str(req)], check=False)
    if r.returncode != 0:
        err("Package install failed. Scroll up for the pip error.")
        sys.exit(1)
    ok("packages installed")

    # python-snappy needs a C toolchain and routinely fails on Windows. It is
    # only used to read Apple .pages resumes, so it is strictly optional.
    say("Optional: .pages resume support")
    r = run(pip + ["install", "-q", "python-snappy"], check=False, quiet=True)
    if r.returncode == 0:
        ok("Apple .pages resumes supported")
    else:
        warn("skipped python-snappy (needs a C compiler) — export .pages resumes to PDF")


def install_browser() -> None:
    say("Installing the browser Playwright drives")
    r = run([sys.executable, "-m", "playwright", "install", "chromium"], check=False, quiet=True)
    if r.returncode != 0:
        warn("chromium install had trouble — retry later with:")
        warn(f"    {sys.executable} -m playwright install chromium")
        return
    if platform.system() == "Linux":
        run([sys.executable, "-m", "playwright", "install-deps", "chromium"],
            check=False, quiet=True)
    ok("browser ready")


# ---------------------------------------------------------------------------
#  ollama
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434"


def ollama_up(timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=timeout):
            return True
    except Exception:
        return False


def start_ollama() -> bool:
    if ollama_up():
        return True
    exe = which("ollama")
    if not exe:
        return False
    say("Starting Ollama in the background")
    kw = {}
    if IS_WIN:
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0) | \
                              getattr(subprocess, "DETACHED_PROCESS", 0)
    else:
        kw["start_new_session"] = True
    try:
        subprocess.Popen([exe, "serve"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, **kw)
    except Exception:
        return False
    for _ in range(20):
        time.sleep(1)
        if ollama_up():
            return True
    return False


def ensure_ollama() -> bool:
    if which("ollama"):
        ok("ollama found")
    else:
        warn("Ollama is not installed — the agent needs it to score jobs.")
        system = platform.system()
        if system == "Windows":
            print("    Download it from https://ollama.com/download/windows")
            print("    Install, then run start.bat again.")
            return False
        if system == "Darwin":
            print("    Download it from https://ollama.com/download")
            print("    Install, then run ./start.sh again.")
            return False
        if ask_yes("Install Ollama now?", True):
            r = run(["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"], check=False)
            if r.returncode != 0 or not which("ollama"):
                err("Ollama install failed. See https://ollama.com/download")
                return False
        else:
            return False

    if not start_ollama():
        warn("Could not reach Ollama on localhost:11434.")
        if platform.system() == "Windows":
            print("    Open the Ollama app from the Start menu, then re-run start.bat.")
        else:
            print("    Run `ollama serve` in another terminal, then re-run.")
        return False
    ok("ollama running")
    return True


def detect_memory_mb() -> int:
    """GPU VRAM if we can see a GPU, otherwise total system RAM."""
    exe = which("nvidia-smi")
    if exe:
        try:
            out = subprocess.run(
                [exe, "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=15)
            vals = [int(x) for x in re.findall(r"\d+", out.stdout)]
            if vals:
                return max(vals)
        except Exception:
            pass
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                 capture_output=True, text=True, timeout=10)
            return int(out.stdout.strip()) // (1024 * 1024)
        if system == "Linux":
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                if line.startswith("MemTotal:"):
                    return int(re.findall(r"\d+", line)[0]) // 1024
        if system == "Windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            st = MEMORYSTATUSEX()
            st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
            return int(st.ullTotalPhys) // (1024 * 1024)
    except Exception:
        pass
    return 0


def suggest_model(mb: int) -> str | None:
    if mb <= 0:
        return None
    # qwen2.5:32b lands around 20 GB at q4_K_M, so 22 GB is the honest floor.
    if mb >= 22000:
        return "qwen2.5:32b-instruct"
    if mb >= 11000:
        return "qwen2.5:14b-instruct"
    return "llama3.1:8b-instruct-q4_K_M"


def read_models() -> tuple[str, str]:
    chat, emb = "qwen2.5:14b-instruct", "nomic-embed-text"
    cfg = ROOT / "config.yaml"
    if cfg.exists():
        t = cfg.read_text(encoding="utf-8")
        m = re.search(r"^\s*chat_model:\s*[\"']?([^\"'\n#]+)", t, re.M)
        if m:
            chat = m.group(1).strip()
        m = re.search(r"^\s*embed_model:\s*[\"']?([^\"'\n#]+)", t, re.M)
        if m:
            emb = m.group(1).strip()
    return chat, emb


def write_chat_model(name: str) -> None:
    cfg = ROOT / "config.yaml"
    t = cfg.read_text(encoding="utf-8")
    t = re.sub(r"^(\s*chat_model:\s*).*$", rf'\g<1>"{name}"', t, count=1, flags=re.M)
    cfg.write_text(t, encoding="utf-8")


def pull_models() -> None:
    chat, emb = read_models()
    mb = detect_memory_mb()
    sug = suggest_model(mb)
    if sug and sug != chat:
        kind = "GPU VRAM" if which("nvidia-smi") else "system RAM"
        print(f"  {D}detected ~{mb} MB {kind} -> suggests {sug}{N}")
        if ask_yes(f"Use {sug} instead of {chat}?", False):
            write_chat_model(sug)
            chat = sug
            ok(f"chat model set to {chat}")

    exe = which("ollama")
    if not exe:
        return
    say(f"Downloading models: {emb}, then {chat}")
    print(f"  {D}this is the slow part - several GB{N}")
    for m in (emb, chat):
        if run([exe, "pull", m], check=False).returncode != 0:
            warn(f"could not pull {m} — retry later with: ollama pull {m}")
    ok("models ready")


# ---------------------------------------------------------------------------
#  project files
# ---------------------------------------------------------------------------
RESUME_EXT = (".pdf", ".docx", ".txt", ".md", ".pages")


def find_resume() -> Path | None:
    d = ROOT / "resume"
    if not d.exists():
        return None
    files = [p for p in d.iterdir()
             if p.is_file() and p.suffix.lower() in RESUME_EXT and not p.name.startswith(".")]
    if not files:
        return None
    order = {".pdf": 0, ".docx": 1, ".txt": 2, ".md": 3, ".pages": 4}
    files.sort(key=lambda p: (order.get(p.suffix.lower(), 9), -p.stat().st_mtime))
    return files[0]


def prepare_files() -> None:
    for d in ("resume", "data", "logs"):
        (ROOT / d).mkdir(exist_ok=True)
    env, example = ROOT / ".env", ROOT / ".env.example"
    if example.exists() and not env.exists():
        shutil.copyfile(example, env)
    from .db import init_db

    init_db()
    ok("database initialised")


def check_resume() -> bool:
    r = find_resume()
    if r:
        ok(f"resume: {r.name}")
        return True
    print()
    warn("No resume found.")
    print()
    print(f"    Drop your resume into the resume folder, then run this again:")
    if IS_WIN:
        print(f"      {D}copy %USERPROFILE%\\Downloads\\MyResume.pdf \"{ROOT / 'resume'}\"{N}")
    else:
        print(f"      {D}cp ~/Downloads/MyResume.pdf \"{ROOT / 'resume'}\"{N}")
    print()
    print("    PDF works best. .docx, .txt and .pages also work.")
    print()
    return False


# ---------------------------------------------------------------------------
#  entry points
# ---------------------------------------------------------------------------
STAMP = ROOT / "data" / ".install_complete"


def install(force: bool = False) -> int:
    """Full first-run install. Idempotent."""
    banner()
    if STAMP.exists() and not force:
        return 0

    say("First run — setting everything up. This takes a few minutes.")
    print()
    ok(f"python {platform.python_version()} ({platform.system()})")

    install_python_deps()
    install_browser()
    prepare_files()

    if not ensure_ollama():
        print()
        err("Setup stopped: Ollama is required.")
        return 1
    pull_models()

    STAMP.parent.mkdir(parents=True, exist_ok=True)
    STAMP.write_text(platform.platform(), encoding="utf-8")  # noqa: E501
    print()
    ok("Install complete.")
    print()
    return 0


def preflight() -> int:
    """Runs on every start: make sure Ollama is up and a resume exists."""
    if not start_ollama() and which("ollama"):
        warn("Ollama isn't responding — starting it may take a moment.")
    if not check_resume():
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    cmd = argv[0] if argv else "install"
    if cmd == "install":
        return install(force="--force" in argv)
    if cmd == "preflight":
        return preflight()
    if cmd == "doctor-deps":
        print(f"python  {platform.python_version()}  {sys.executable}")
        print(f"os      {platform.platform()}")
        print(f"ollama  {'yes' if which('ollama') else 'no'}  (running: {ollama_up()})")
        print(f"memory  {detect_memory_mb()} MB")
        print(f"resume  {find_resume() or 'none'}")
        return 0
    err(f"unknown bootstrap command: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
