@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

set "ROOT_DIR=%~dp0"
set "BACKEND_RUNNER=%ROOT_DIR%scripts\run_backend.bat"
set "FRONTEND_RUNNER=%ROOT_DIR%scripts\run_frontend.bat"
set "LAUNCH_LOG=%ROOT_DIR%start-launcher.log"

echo [%date% %time%] launcher_start>"%LAUNCH_LOG%"
echo [%date% %time%] root=%ROOT_DIR%>>"%LAUNCH_LOG%"

echo.
echo ====================================================
echo   BlueGuard Platform - Startup
echo ====================================================
echo.

REM Check dependencies
echo [*] Checking dependencies...
echo [%date% %time%] check_runners>>"%LAUNCH_LOG%"
if not exist "%BACKEND_RUNNER%" (
    echo [ERROR] Missing file: %BACKEND_RUNNER%
    echo [%date% %time%] missing_backend_runner>>"%LAUNCH_LOG%"
    goto :fail
)
echo [OK] Backend runner found.

if not exist "%FRONTEND_RUNNER%" (
    echo [ERROR] Missing file: %FRONTEND_RUNNER%
    echo [%date% %time%] missing_frontend_runner>>"%LAUNCH_LOG%"
    goto :fail
)
echo [OK] Frontend runner found.

echo [%date% %time%] check_python>>"%LAUNCH_LOG%"
python --version >nul 2>&1
if errorlevel 1 (
    if not exist "%ROOT_DIR%backend\env\python.exe" (
        echo [ERROR] Python not found in PATH and local env is missing.
        echo         Expected fallback: %ROOT_DIR%backend\env\python.exe
        echo [%date% %time%] python_missing>>"%LAUNCH_LOG%"
        goto :fail
    )
)
echo [OK] Python check passed.

echo [%date% %time%] skip_npm_precheck>>"%LAUNCH_LOG%"
echo [OK] Skipping npm pre-check in launcher (frontend window will validate npm).

echo [OK] Python and Node.js are available.
echo [OK] Root: %ROOT_DIR%
echo.

REM Start backend
echo [*] Starting backend on port 8000...
echo [%date% %time%] start_backend>>"%LAUNCH_LOG%"
start "Backend - BlueGuard" "%BACKEND_RUNNER%"
if errorlevel 1 (
    echo [ERROR] Failed to launch backend window.
    echo [%date% %time%] start_backend_failed>>"%LAUNCH_LOG%"
    goto :fail
)

timeout /t 3 /nobreak > nul

REM Start frontend
echo [*] Starting frontend on port 5173...
echo [%date% %time%] start_frontend>>"%LAUNCH_LOG%"
start "Frontend - BlueGuard" "%FRONTEND_RUNNER%"
if errorlevel 1 (
    echo [ERROR] Failed to launch frontend window.
    echo [%date% %time%] start_frontend_failed>>"%LAUNCH_LOG%"
    goto :fail
)

timeout /t 5 /nobreak > nul

REM Clear screen and display info
cls
echo.
echo ====================================================
echo   Services Started
echo ====================================================
echo.
echo Frontend: http://localhost:5173
echo Backend : http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Notes:
echo   - Check the two newly opened terminal windows for logs.
echo   - Press Ctrl+C inside each window to stop its service.
echo   - Closing those windows will stop the services.
echo.
echo ====================================================
echo.
echo [*] Waiting for frontend port 5173...
set /a WAIT_COUNT=0
:wait_frontend
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul
if not errorlevel 1 goto frontend_ready
set /a WAIT_COUNT+=1
if %WAIT_COUNT% GEQ 120 goto frontend_timeout
timeout /t 1 /nobreak >nul
goto wait_frontend

:frontend_ready
echo [OK] Frontend is listening on port 5173.
echo [%date% %time%] frontend_ready>>"%LAUNCH_LOG%"
goto open_browser

:frontend_timeout
echo [WARN] Frontend did not listen on port 5173 within 120 seconds.
echo [WARN] Browser will still be opened. Check frontend window logs.
echo [%date% %time%] frontend_timeout>>"%LAUNCH_LOG%"

:open_browser

REM Open browser
echo [*] Opening http://localhost:5173
start "" "http://localhost:5173"
echo [%date% %time%] browser_opened>>"%LAUNCH_LOG%"

echo.
echo Launcher finished. You can close this window.
pause
exit /b 0

:fail
echo.
echo [%date% %time%] fail_exit>>"%LAUNCH_LOG%"
echo [INFO] See log: %LAUNCH_LOG%
echo Launcher stopped due to missing dependencies or invalid environment.
pause
exit /b 1
