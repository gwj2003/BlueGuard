#!/bin/bash

# Linux/macOS startup script for Aquatic Invasive Species Platform
# Usage: ./start.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "===================================================="
echo "  🌊 水生入侵物种综合平台 - 启动程序"
echo "===================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[✗] 错误：未找到 Python 3${NC}"
    echo "    请访问 https://www.python.org/downloads/"
    exit 1
fi
echo -e "${GREEN}[✓]${NC} Python 已就绪"

# Check Node.js
if ! command -v npm &> /dev/null; then
    echo -e "${RED}[✗] 错误：未找到 Node.js${NC}"
    echo "    请访问 https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}[✓]${NC} Node.js 已就绪"
echo ""

# Setup backend
echo -e "${BLUE}[*]${NC} 配置后端环境..."
cd backend

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "  安装后端依赖..."
pip install -r requirements.txt > /dev/null 2>&1
echo -e "  ${GREEN}[✓] 后端依赖安装完成${NC}"

# Start backend
echo -e "${BLUE}[*]${NC} 启动后端服务（端口 8000）..."
uvicorn main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
echo -e "  ${GREEN}[✓] 后端进程 ID: $BACKEND_PID${NC}"

cd ..

# Wait briefly for backend to start
sleep 2

# Setup frontend
echo -e "${BLUE}[*]${NC} 配置前端环境..."
cd frontend

echo "  安装前端依赖..."
npm install --silent > /dev/null 2>&1
echo -e "  ${GREEN}[✓] 前端依赖安装完成${NC}"

# Start frontend
echo -e "${BLUE}[*]${NC} 启动前端服务（端口 5173）..."
npm run dev &
FRONTEND_PID=$!
echo -e "  ${GREEN}[✓] 前端进程 ID: $FRONTEND_PID${NC}"

cd ..

echo ""
echo "===================================================="
echo -e "  ${GREEN}✅ 所有服务已启动${NC}"
echo "===================================================="
echo ""
echo -e "  📱 前端地址：${BLUE}http://localhost:5173${NC}"
echo -e "  🔌 后端 API：${BLUE}http://localhost:8000${NC}"
echo -e "  📖 API 文档：${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "  💡 提示："
echo "    - 按 Ctrl+C 停止所有服务"
echo "    - 或单独停止：kill $BACKEND_PID 或 kill $FRONTEND_PID"
echo ""
echo "===================================================="
echo ""

# Wait for both processes
wait
