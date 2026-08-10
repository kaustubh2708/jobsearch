# =============================================================================
#  LocalJobAgent CLI  (Windows / PowerShell)
#
#    .\run.ps1                 start the dashboard + background agent
#    .\run.ps1 discover        run one job search now
#    .\run.ps1 apply           apply to everything you've approved
#    .\run.ps1 profile         show your parsed skill library
#    .\run.ps1 login linkedin  log into a board once (session is then reused)
#    .\run.ps1 doctor          check the setup
#    .\run.ps1 status          quick pipeline snapshot
#
#  Or use run.bat, which needs no execution-policy change.
# =============================================================================
$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

$vpy = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $vpy)) {
    Write-Host ''
    Write-Host '  No environment found. Run start.bat first.' -ForegroundColor Red
    Write-Host ''
    exit 1
}

if (Test-Path '.env') {
    foreach ($line in (Get-Content '.env')) {
        if ($line -match '^\s*#') { continue }
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $val = $matches[2].Trim().Trim('"').Trim("'")
            if ($val) { [Environment]::SetEnvironmentVariable($matches[1], $val, 'Process') }
        }
    }
}

# Make sure Ollama is up before we need it.
& $vpy -c 'from jobagent.bootstrap import start_ollama; start_ollama()' 2>$null | Out-Null

$cliArgs = if ($args.Count -gt 0) { $args } else { @('serve') }
& $vpy -m jobagent.cli @cliArgs
exit $LASTEXITCODE
