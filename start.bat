@echo off
REM ===========================================================================
REM  LocalJobAgent - THE ONE COMMAND  (Windows)
REM
REM    Double-click this file, or from a terminal:  start.bat
REM
REM  Wraps start.ps1 with -ExecutionPolicy Bypass so you never have to change
REM  your machine's PowerShell policy.
REM ===========================================================================
setlocal
cd /d "%~dp0"

where powershell >nul 2>nul
if errorlevel 1 (
  echo.
  echo   PowerShell was not found on this machine.
  echo   LocalJobAgent needs it to install. Windows 10 and 11 ship with it.
  echo.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
set EXITCODE=%ERRORLEVEL%

REM Keep the window open when double-clicked so errors stay readable.
echo %CMDCMDLINE% | find /i "/c" >nul && pause

exit /b %EXITCODE%
