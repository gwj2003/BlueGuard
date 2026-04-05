@echo off
setlocal

set "NEO4J_BIN=C:\Program Files\neo4j-community-5.26.20\bin"

if not exist "%NEO4J_BIN%\neo4j.bat" (
  echo [ERROR] Cannot find neo4j.bat at: %NEO4J_BIN%
  pause
  exit /b 1
)

:: Self-elevate to avoid Program Files permission issues.
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Requesting administrator permission...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo Starting Neo4j in console mode...
cd /d "%NEO4J_BIN%"
call neo4j.bat console

endlocal
