#!/bin/bash
# Quick start script for Eagle Harbor Monitor local development
# This script starts both the backend and frontend servers

echo "🚀 Starting Eagle Harbor Monitor Local Development Environment"
echo ""

# Check if we're in the project root
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "📦 Starting Backend (FastAPI)..."
cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "   Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
if [ ! -f "venv/.installed" ]; then
    echo "   Installing Python dependencies..."
    pip install -r requirements.txt > /dev/null
    touch venv/.installed
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "   ⚠️  Warning: No .env file found in backend/"
    echo "   Creating from .env.example..."
    cp ../.env.example .env
    echo "   ⚠️  Please edit backend/.env and add your API keys!"
fi

# Start backend server in background
python -m uvicorn app.main:app --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ❌ Backend failed to start. Check backend.log for details."
    cat backend.log
    exit 1
fi

echo "   ✅ Backend running at http://localhost:8000"

# Start frontend
echo "📦 Starting Frontend (Next.js)..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   Installing Node.js dependencies..."
    npm install > /dev/null 2>&1
fi

# Check for .env.local file
if [ ! -f ".env.local" ]; then
    echo "   Creating .env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
fi

# Start frontend server in background
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 5

# Check if frontend started successfully
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ❌ Frontend failed to start. Check frontend.log for details."
    cat frontend.log
    exit 1
fi

echo "   ✅ Frontend running at http://localhost:3000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Eagle Harbor Monitor is now running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Frontend:  http://localhost:3000"
echo "🔌 Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for user to interrupt
wait
