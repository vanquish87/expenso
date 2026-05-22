@echo off
setlocal ENABLEDELAYEDEXPANSION

rem ---- Expenso launcher ---------------------------------------------------
rem Ensures venv exists, deps are installed, then opens the browser and
rem starts uvicorn. Safe to re-run; everything is idempotent.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
  echo [expenso] creating venv with python 3.9...
  where py >nul 2>&1
  if !ERRORLEVEL! EQU 0 (
    py -3.9 -m venv venv || python -m venv venv
  ) else (
    python -m venv venv
  )
)

if not exist "venv\Scripts\python.exe" (
  echo [expenso] failed to create venv — is python 3.9 installed?
  exit /b 1
)

echo [expenso] installing dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip >nul
venv\Scripts\python.exe -m pip install -r requirements.txt

set HOST=127.0.0.1
set PORT=8000
set URL=http://%HOST%:%PORT%/

echo [expenso] opening %URL%
start "" "%URL%"

echo [expenso] starting uvicorn — Ctrl+C to stop
venv\Scripts\python.exe -m uvicorn app.main:app --host %HOST% --port %PORT%

endlocal
