# Quick Start Script for Local Development

Write-Host "🚀 Starting Eagle Harbor Data Center Monitor Setup..." -ForegroundColor Green

# Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Setup Backend
Write-Host "`n🔧 Setting up backend..." -ForegroundColor Cyan
Set-Location backend

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "✓ Backend setup complete!" -ForegroundColor Green

# Setup Frontend
Set-Location ..\frontend
Write-Host "`n🎨 Setting up frontend..." -ForegroundColor Cyan

Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

Write-Host "✓ Frontend setup complete!" -ForegroundColor Green

# Setup Database (if local PostgreSQL is available)
Set-Location ..\database
Write-Host "`n🗄️ Database setup..." -ForegroundColor Cyan

$dbUrl = Read-Host "Enter your PostgreSQL connection string (or press Enter to skip)"
if ($dbUrl) {
    Write-Host "Running migrations..." -ForegroundColor Yellow
    psql $dbUrl -f schema.sql
    Write-Host "✓ Database setup complete!" -ForegroundColor Green
} else {
    Write-Host "⚠ Skipping database setup. You'll need to run migrations manually." -ForegroundColor Yellow
}

# Create .env file
Set-Location ..
Write-Host "`n📝 Creating environment file..." -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file. Please update with your API keys!" -ForegroundColor Green
} else {
    Write-Host "⚠ .env file already exists" -ForegroundColor Yellow
}

# Summary
Write-Host "`n✨ Setup Complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your API keys"
Write-Host "2. Start backend:  cd backend && uvicorn app.main:app --reload"
Write-Host "3. Start frontend: cd frontend && npm run dev"
Write-Host "4. Visit: http://localhost:3000"
Write-Host "`n🎉 Happy monitoring!" -ForegroundColor Magenta
