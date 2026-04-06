@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~1"
set "NEO4J_WAIT_MAX=%~2"

if "%ROOT_DIR%"=="" set "ROOT_DIR=%~dp0..\"
if "%NEO4J_WAIT_MAX%"=="" set "NEO4J_WAIT_MAX=45"

set "NEO4J_STARTER=%ROOT_DIR%scripts\start-neo4j.bat"

call :is_port_listening 7687
if not errorlevel 1 (
  echo [OK] Neo4j is listening on port 7687.
  exit /b 0
)

echo [WARN] Neo4j is not listening on port 7687.
if not exist "%NEO4J_STARTER%" (
  echo [WARN] Neo4j starter not found: %NEO4J_STARTER%
  echo [WARN] Continuing startup. QA graph features may be degraded.
  exit /b 0
)

echo [*] Attempting to start Neo4j in a new window...
start "Neo4j - BlueGuard" "%NEO4J_STARTER%"
if errorlevel 1 (
  echo [WARN] Failed to launch Neo4j starter.
  echo [WARN] Continuing startup. QA graph features may be degraded.
  exit /b 0
)

echo [*] Waiting for Neo4j port 7687...
set /a NEO4J_WAIT_COUNT=0
:wait_neo4j
call :is_port_listening 7687
if not errorlevel 1 (
  echo [OK] Neo4j is now listening on port 7687.
  exit /b 0
)

set /a NEO4J_WAIT_COUNT+=1
if %NEO4J_WAIT_COUNT% GEQ %NEO4J_WAIT_MAX% goto neo4j_timeout
timeout /t 1 /nobreak >nul
goto wait_neo4j

:neo4j_timeout
echo [WARN] Neo4j did not become ready within %NEO4J_WAIT_MAX% seconds.
echo [WARN] Continuing startup. QA graph features may be degraded.
exit /b 0

:is_port_listening
netstat -ano | findstr /r /c:":%~1 .*LISTENING" >nul 2>&1
if errorlevel 1 exit /b 1
exit /b 0
