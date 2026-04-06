@echo off
setlocal EnableExtensions

set "NEO4J_BIN_DIR="
set "NEO4J_BAT_IN_PATH="
set "CFG_NEO4J_BIN=%NEO4J_BIN%"

REM 1) Explicit override via NEO4J_BIN (bin dir or full neo4j.bat path)
if defined CFG_NEO4J_BIN (
  if exist "%CFG_NEO4J_BIN%\neo4j.bat" (
    set "NEO4J_BIN_DIR=%CFG_NEO4J_BIN%"
  ) else if exist "%CFG_NEO4J_BIN%" (
    for %%F in ("%CFG_NEO4J_BIN%") do (
      if /i "%%~nxF"=="neo4j.bat" set "NEO4J_BIN_DIR=%%~dpF"
    )
  )
)

REM 2) NEO4J_HOME/bin
if not defined NEO4J_BIN_DIR if defined NEO4J_HOME (
  if exist "%NEO4J_HOME%\bin\neo4j.bat" set "NEO4J_BIN_DIR=%NEO4J_HOME%\bin"
)

REM 3) Discover from PATH
if not defined NEO4J_BIN_DIR (
  for /f "delims=" %%I in ('where neo4j.bat 2^>nul') do (
    if not defined NEO4J_BAT_IN_PATH set "NEO4J_BAT_IN_PATH=%%~fI"
  )
  if defined NEO4J_BAT_IN_PATH (
    for %%D in ("%NEO4J_BAT_IN_PATH%") do set "NEO4J_BIN_DIR=%%~dpD"
  )
)

REM 4) Common install locations
if not defined NEO4J_BIN_DIR call :pick_common_install

if not defined NEO4J_BIN_DIR (
  echo [ERROR] Cannot find Neo4j launcher (neo4j.bat).
  echo [INFO] Suggested fixes:
  echo [INFO]   1) Add Neo4j bin to PATH, or
  echo [INFO]   2) Set NEO4J_HOME, or
  echo [INFO]   3) Set NEO4J_BIN to Neo4j bin path or neo4j.bat full path.
  pause
  exit /b 1
)

if not exist "%NEO4J_BIN_DIR%\neo4j.bat" (
  echo [ERROR] Resolved Neo4j path is invalid: %NEO4J_BIN_DIR%
  echo [INFO] Ensure neo4j.bat exists in the resolved directory.
  pause
  exit /b 1
)

REM Self-elevate to avoid Program Files permission issues.
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Requesting administrator permission...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo Starting Neo4j in console mode...
echo Using Neo4j bin: %NEO4J_BIN_DIR%
cd /d "%NEO4J_BIN_DIR%"
call neo4j.bat console

endlocal
exit /b 0

:pick_common_install
if defined ProgramFiles (
  if exist "%ProgramFiles%\Neo4j Community\bin\neo4j.bat" (
    set "NEO4J_BIN_DIR=%ProgramFiles%\Neo4j Community\bin"
    exit /b 0
  )

  for /f "delims=" %%D in ('dir /b /ad /o-n "%ProgramFiles%\neo4j-community-*" 2^>nul') do (
    if not defined NEO4J_BIN_DIR if exist "%ProgramFiles%\%%D\bin\neo4j.bat" (
      set "NEO4J_BIN_DIR=%ProgramFiles%\%%D\bin"
    )
  )
)

if not defined NEO4J_BIN_DIR if defined ProgramFiles(x86) (
  if exist "%ProgramFiles(x86)%\Neo4j Community\bin\neo4j.bat" (
    set "NEO4J_BIN_DIR=%ProgramFiles(x86)%\Neo4j Community\bin"
    exit /b 0
  )

  for /f "delims=" %%D in ('dir /b /ad /o-n "%ProgramFiles(x86)%\neo4j-community-*" 2^>nul') do (
    if not defined NEO4J_BIN_DIR if exist "%ProgramFiles(x86)%\%%D\bin\neo4j.bat" (
      set "NEO4J_BIN_DIR=%ProgramFiles(x86)%\%%D\bin"
    )
  )
)

exit /b 0
