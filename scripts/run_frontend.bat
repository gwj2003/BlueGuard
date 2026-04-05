@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0..\frontend"

echo [Frontend] Working directory: %CD%
if not exist node_modules\ (
  echo [Frontend] Installing dependencies...
  npm install
  if errorlevel 1 (
    echo [Frontend][ERROR] npm install failed.
    pause
    exit /b 1
  )
) else (
  echo [Frontend] node_modules exists, skipping npm install.
)

echo [Frontend] Starting Vite on http://localhost:5173 ...
npm run dev

echo [Frontend] Dev server stopped.
pause
