@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ====================================================
echo   BlueGuard - ngrok 启动工具
echo ====================================================
echo.

cd /d "%~dp0"
set "ROOT_DIR=%~dp0"
set "BACKEND_RUNNER=%ROOT_DIR%scripts\run_backend.bat"
set "FRONTEND_RUNNER=%ROOT_DIR%scripts\run_frontend.bat"
set "NEO4J_CHECKER=%ROOT_DIR%scripts\ensure_neo4j.bat"
set "NEO4J_WAIT_MAX=45"

if not exist "%BACKEND_RUNNER%" (
  echo [ERROR] Missing file: %BACKEND_RUNNER%
  pause
  exit /b 1
)

if not exist "%FRONTEND_RUNNER%" (
  echo [ERROR] Missing file: %FRONTEND_RUNNER%
  pause
  exit /b 1
)

REM 检查 ngrok 是否已安装
where ngrok >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] ngrok 未安装或未添加到 PATH
    echo.
    echo 请按以下步骤安装：
    echo   1. 访问 https://ngrok.com/download 下载 ngrok
    echo   2. 将 ngrok.exe 添加到你的 PATH
    echo   3. 或在终端中手动运行：ngrok http 5173
    echo.
    pause
    exit /b 1
)

echo [OK] ngrok 已安装

echo.
echo ====================================================
echo   启动步骤
echo ====================================================
echo.
echo 将使用 3-4 个终端窗口启动以下服务：
echo   1. 终端 1：后端服务（FastAPI，端口 8000）
echo   2. 终端 2：ngrok 隧道（将端口 5173 暴露到公网）
echo   3. 终端 3：前端服务（Vite，端口 5173）
echo   4. Neo4j 未运行时会自动尝试拉起
echo.

pause

call :ensure_neo4j_running
echo.

echo [*] 启动终端 1：后端服务...
start "BlueGuard Backend" "%BACKEND_RUNNER%"

timeout /t 3 /nobreak

echo [*] 启动终端 2：ngrok 隧道...
start "BlueGuard ngrok" cmd /k "ngrok http 5173"

timeout /t 3 /nobreak

echo [*] 启动终端 3：前端服务...
start "BlueGuard Frontend" "%FRONTEND_RUNNER%"

timeout /t 2 /nobreak

echo.
echo ====================================================
echo   服务启动完成
echo ====================================================
echo.
echo 请查看 ngrok 终端窗口获取公网 URL，格式如：
echo   https://xxxx-xxxx-xxxx.ngrok.io
echo.
echo 本地访问：http://localhost:5173
echo.
echo 故障排查：
echo   - 如果 ngrok 报错，检查是否已登录：ngrok authtoken <your-token>
echo   - 如果后端启动失败，检查 Neo4j 是否正在运行
echo   - 如果前端启动失败，确保已运行 npm install
echo.

pause
exit /b 0

:ensure_neo4j_running
if not exist "%NEO4J_CHECKER%" (
  echo [WARN] Neo4j checker not found: %NEO4J_CHECKER%
  echo [WARN] Continuing startup. QA graph features may be degraded.
  exit /b 0
)

call "%NEO4J_CHECKER%" "%ROOT_DIR%" "%NEO4J_WAIT_MAX%"
exit /b 0
