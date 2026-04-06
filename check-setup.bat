@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ====================================================
echo   BlueGuard ngrok 配置检查工具
echo ====================================================
echo.

set "CHECK_PASSED=0"
set "CHECK_FAILED=0"

REM 检查 ngrok
echo [*] 检查 ngrok...
ngrok --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] ngrok 未安装或未添加到 PATH
    set /a CHECK_FAILED+=1
) else (
    echo [PASS] ngrok 已安装
    set /a CHECK_PASSED+=1
)

REM 检查 Python
echo [*] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python 未安装或未添加到 PATH
    set /a CHECK_FAILED+=1
) else (
    echo [PASS] Python 已安装
    set /a CHECK_PASSED+=1
)

REM 检查 npm
echo [*] 检查 npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] npm 未安装或未添加到 PATH
    set /a CHECK_FAILED+=1
) else (
    echo [PASS] npm 已安装
    set /a CHECK_PASSED+=1
)

REM 检查 .env 文件
echo [*] 检查 .env 文件...
if exist ".env" (
    echo [PASS] .env 文件存在
    set /a CHECK_PASSED+=1
    
    findstr "ALLOW_ORIGINS" .env >nul 2>&1
    if errorlevel 1 (
        echo [WARN] .env 中未找到 ALLOW_ORIGINS
    ) else (
        echo [PASS] ALLOW_ORIGINS 已配置
    )
) else (
    echo [FAIL] .env 文件不存在
    set /a CHECK_FAILED+=1
)

REM 检查后端 main.py
echo [*] 检查后端配置...
if exist "backend\main.py" (
    findstr "allow_origin_regex" backend\main.py >nul 2>&1
    if errorlevel 1 (
        echo [WARN] backend/main.py 未配置正则表达式 CORS
    ) else (
        echo [PASS] backend/main.py 已配置通配符 CORS
        set /a CHECK_PASSED+=1
    )
) else (
    echo [FAIL] backend/main.py 不存在
    set /a CHECK_FAILED+=1
)

REM 检查前端 vite.config.js
echo [*] 检查前端配置...
if exist "frontend\vite.config.js" (
    findstr "proxy" frontend\vite.config.js >nul 2>&1
    if errorlevel 1 (
        echo [WARN] frontend/vite.config.js 未配置代理
    ) else (
        echo [PASS] frontend/vite.config.js 已配置 API 代理
        set /a CHECK_PASSED+=1
    )
    
    findstr "allowedHosts" frontend\vite.config.js >nul 2>&1
    if errorlevel 1 (
        echo [WARN] frontend/vite.config.js 未配置 allowedHosts
    ) else (
        echo [PASS] frontend/vite.config.js 已配置 ngrok 域名
        set /a CHECK_PASSED+=1
    )
) else (
    echo [FAIL] frontend/vite.config.js 不存在
    set /a CHECK_FAILED+=1
)

REM 检查启动脚本
echo [*] 检查启动脚本...
if exist "start-with-ngrok.bat" (
    findstr "ngrok http 5173" start-with-ngrok.bat >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] start-with-ngrok.bat 命令不正确（应为 ngrok http 5173）
        set /a CHECK_FAILED+=1
    ) else (
        echo [PASS] start-with-ngrok.bat 已正确配置
        set /a CHECK_PASSED+=1
    )
) else (
    echo [FAIL] start-with-ngrok.bat 不存在
    set /a CHECK_FAILED+=1
)

echo.
echo ====================================================
echo   检查结果
echo ====================================================
echo 通过: %CHECK_PASSED%
echo 失败: %CHECK_FAILED%
echo.

if %CHECK_FAILED% equ 0 (
    echo ✅ 所有检查通过！可以开始使用。
    echo.
    echo 下一步：
    echo   1. 启动 Neo4j：start-neo4j.bat
    echo   2. 启动所有服务：start-with-ngrok.bat
    echo   3. 查看 ngrok 输出获取公网 URL
) else (
    echo ❌ 有些检查未通过，请解决后重试。
)

echo.
pause
