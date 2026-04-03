@echo off
REM Windows batch script to start both backend and frontend

echo Starting Water Invasive Species Platform...
echo.

REM Check if Node.js and npm are installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo npm not found. Please install Node.js
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Start backend in a new window
echo Starting backend...
start "Backend Server" cmd /k "cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak

REM Start frontend in a new window
echo Starting frontend...
start "Frontend Server" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press Enter to continue...
pause
