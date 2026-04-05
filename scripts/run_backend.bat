@echo off
setlocal

cd /d "%~dp0..\backend"

set "PYTHON_CMD=python"
set "LOCAL_PY=%CD%\env\python.exe"
if exist "%LOCAL_PY%" set "PYTHON_CMD=%LOCAL_PY%"

echo [Backend] Python executable: %PYTHON_CMD%

echo [Backend] Working directory: %CD%
echo [Backend] Installing dependencies...
"%PYTHON_CMD%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [Backend][ERROR] pip install failed.
  pause
  exit /b 1
)

echo [Backend] Starting FastAPI on http://localhost:8000 ...
"%PYTHON_CMD%" -m uvicorn main:app --reload --port 8000 --host 0.0.0.0

echo [Backend] Server stopped.
pause
