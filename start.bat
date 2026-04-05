@echo off
REM Windows startup script for Aquatic Invasive Species Platform
REM Usage: start.bat

setlocal enabledelayedexpansion

echo.
echo ====================================================
echo   🌊 水生入侵物种综合平台 - 启动程序
echo ====================================================
echo.

REM Check dependencies
echo [*] 检查依赖环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [✗] 错误：未找到 Python 3.8+
    echo     请访问 https://www.python.org/downloads/
    pause
    exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo [✗] 错误：未找到 Node.js
    echo     请访问 https://nodejs.org/
    pause
    exit /b 1
)

echo [✓] Python 和 Node.js 已就绪
echo.

REM Start backend
echo [*] 启动后端服务（端口 8000）...
start "Backend - 水生入侵物种平台" cmd /k ^
    "cd backend && ^
    echo 正在安装后端依赖... && ^
    pip install -r requirements.txt >nul 2>&1 && ^
    echo [✓] 后端依赖安装完成 && ^
    echo 启动 FastAPI 服务器... && ^
    uvicorn main:app --reload --port 8000 --host 0.0.0.0"

timeout /t 2 /nobreak > nul

REM Start frontend
echo [*] 启动前端服务（端口 5173）...
start "Frontend - 水生入侵物种平台" cmd /k ^
    "cd frontend && ^
    echo 正在安装前端依赖... && ^
    npm install --silent >nul 2>&1 && ^
    echo [✓] 前端依赖安装完成 && ^
    echo 启动开发服务器... && ^
    npm run dev"

timeout /t 2 /nobreak > nul

REM Display info
cls
echo.
echo ====================================================
echo   ✅ 所有服务已启动
echo ====================================================
echo.
echo 📱 前端地址：http://localhost:5173
echo 🔌 后端 API：http://localhost:8000
echo 📖 API 文档：http://localhost:8000/docs
echo.
echo 💡 提示：
echo   - 请在两个新打开的窗口中查看详细输出
echo   - 按 Ctrl+C 可停止对应服务
echo   - 若要关闭所有服务，关闭两个窗口即可
echo.
echo ====================================================
timeout /t 300
