#!/bin/bash

# Linux/Mac startup script

echo "Starting Water Invasive Species Platform..."
echo ""

# Check if Node.js and npm are installed
if ! command -v npm &> /dev/null; then
    echo "npm not found. Please install Node.js"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Start backend
echo "Starting backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend..."
cd frontend
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for both processes
wait
