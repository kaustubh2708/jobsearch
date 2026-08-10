# =============================================================================
#  LocalJobAgent - THE ONE COMMAND  (Windows / PowerShell)
#
#    git clone <repo> Jobsearch
#    cd Jobsearch
#    copy "$env:USERPROFILE\Downloads\MyResume.pdf" resume\
#    .\start.ps1
#
#  If PowerShell blocks the script, run start.bat instead (it needs no policy
#  change), or once:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#
#  Safe to run any time. All the real work happens in jobagent/bootstrap.py so
#  every platform behaves identically.
# =============================================================================

# Continue, not Stop: this script drives native commands and checks their exit
# codes by hand. Under 'Stop', stderr from a native command can raise.
$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot

# Make the console UTF-8 so the tick marks and rupee signs render properly.
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

function Die($msg) {
    Write-Host ""
    Write-Host "  x $msg" -ForegroundColor Red
    Write-Host ""
    exit 1
}

# ---- find a usable python -------------------------------------------------
$pyExe = $null
$pyPre = @()

foreach ($cand in @('python', 'python3', 'py')) {
    $c = Get-Command $cand -ErrorAction SilentlyContinue
    if (-not $c) { continue }

    # 'python' with no Python installed is a Microsoft Store stub that opens
    # the Store instead of running anything. Skip it.
    if ($c.Source -like '*\WindowsApps\*' -and -not (Test-Path (Join-Path (Split-Path $c.Source) 'python3.dll'))) {
        continue
    }

    $pre = if ($cand -eq 'py') { @('-3') } else { @() }
    try {
        $v = & $c.Source @pre '-c' 'import sys;print(sys.version_info.major*100+sys.version_info.minor)' 2>$null
        if ($LASTEXITCODE -eq 0 -and $v -and [int]$v -ge 310) {
            $pyExe = $c.Source
            $pyPre = $pre
            break
        }
    } catch { }
}

if (-not $pyExe) {
    Die @"
Python 3.10 or newer is required.

    Install it from https://www.python.org/downloads/
    IMPORTANT: tick "Add python.exe to PATH" during install.

    Then open a new terminal and run start.bat again.
"@
}

# ---- venv -----------------------------------------------------------------
$vpy = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $vpy)) {
    Write-Host "> Creating virtual environment" -ForegroundColor Blue
    & $pyExe @pyPre -m venv .venv
    if ($LASTEXITCODE -ne 0) { Die 'Could not create the virtualenv.' }
}
if (-not (Test-Path $vpy)) {
    Die 'The .venv folder looks broken. Delete it and run start.bat again.'
}

# ---- load optional API keys from .env -------------------------------------
if (Test-Path '.env') {
    foreach ($line in (Get-Content '.env')) {
        if ($line -match '^\s*#') { continue }
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $val = $matches[2].Trim().Trim('"').Trim("'")
            if ($val) { [Environment]::SetEnvironmentVariable($matches[1], $val, 'Process') }
        }
    }
}

# ---- install (idempotent) -> preflight -> setup wizard -> run -------------
& $vpy -m jobagent.bootstrap install
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $vpy -m jobagent.bootstrap preflight
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $vpy -m jobagent.cli setup
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ''
& $vpy -m jobagent.cli serve
exit $LASTEXITCODE
