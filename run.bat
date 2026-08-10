@echo off
REM ===========================================================================
REM  LocalJobAgent CLI  (Windows)
REM
REM    run.bat                 start the dashboard + background agent
REM    run.bat discover        run one job search now
REM    run.bat apply           apply to everything you've approved
REM    run.bat profile         show your parsed skill library
REM    run.bat login linkedin  log into a board once
REM    run.bat doctor          check the setup
REM    run.bat status          quick pipeline snapshot
REM ===========================================================================
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
exit /b %ERRORLEVEL%
