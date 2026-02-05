# Quick start script for Eagle Harbor Monitor local development (Windows)
# This script starts both the backend and frontend servers

Write-Host "🚀 Starting Eagle Harbor Monitor Local Development Environment" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the project root
if (-not (Test-Path "backend") -or -not (Test-Path "frontend")) {
    Write-Host "❌ Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Start backend
Write-Host "📦 Starting Backend (FastAPI)..." -ForegroundColor Yellow
Set-Location backend

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "   Creating Python virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

# Activate venv
& ".\venv\Scripts\Activate.ps1"

# Install dependencies if needed
if (-not (Test-Path "venv\.installed")) {
    Write-Host "   Installing Python dependencies..." -ForegroundColor Gray
    pip install -r requirements.txt | Out-Null
    New-Item -Path "venv\.installed" -ItemType File | Out-Null
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "   ⚠️  Warning: No .env file found in backend/" -ForegroundColor Yellow
    Write-Host "   Creating from .env.example..." -ForegroundColor Gray
    Copy-Item "../.env.example" ".env"
    Write-Host "   ⚠️  Please edit backend\.env and add your API keys!" -ForegroundColor Yellow
}

# Start backend server in new window
Write-Host "   Starting backend server..." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload" -WindowStyle Normal
Set-Location ..

Start-Sleep -Seconds 5

# Check if backend started successfully
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ Backend running at http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Backend may still be starting..." -ForegroundColor Yellow
}

# Start frontend
Write-Host "📦 Starting Frontend (Next.js)..." -ForegroundColor Yellow
Set-Location frontend

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "   Installing Node.js dependencies..." -ForegroundColor Gray
    npm install | Out-Null
}

# Check for .env.local file
if (-not (Test-Path ".env.local")) {
    Write-Host "   Creating .env.local..." -ForegroundColor Gray
    "NEXT_PUBLIC_API_URL=http://localhost:8000/api" | Out-File -FilePath ".env.local" -Encoding utf8
}

# Start frontend server in new window
Write-Host "   Starting frontend server..." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev" -WindowStyle Normal
Set-Location ..

Start-Sleep -Seconds 5

# Check if frontend started successfully
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ Frontend running at http://localhost:3000" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Frontend may still be starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Eagle Harbor Monitor is starting!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "🔌 Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "📚 API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Both servers are running in separate PowerShell windows." -ForegroundColor Gray
Write-Host "Close those windows to stop the servers." -ForegroundColor Gray
Write-Host ""
Write-Host "If the servers didn't start properly, check the separate windows for error messages." -ForegroundColor Gray
Write-Host ""

# Open browser
Write-Host "Opening browser..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
