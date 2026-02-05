# Production Readiness Test Script
# Run this before deploying to verify everything works

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Eagle Harbor Monitor - Production Test" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check Backend Files
Write-Host "✓ Checking backend files..." -ForegroundColor Yellow
$backendFiles = @(
    "backend\app\services\ai_service.py",
    "backend\app\api\routes.py",
    "backend\app\main.py"
)

foreach ($file in $backendFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file missing!" -ForegroundColor Red
        exit 1
    }
}

# Test 2: Check Frontend Files
Write-Host "`n✓ Checking frontend files..." -ForegroundColor Yellow
$frontendFiles = @(
    "frontend\src\app\page.tsx",
    "frontend\src\components\AskQuestion.tsx",
    "frontend\src\app\globals.css",
    "frontend\next.config.js"
)

foreach ($file in $frontendFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file missing!" -ForegroundColor Red
        exit 1
    }
}

# Test 3: Check Next.js Config
Write-Host "`n✓ Checking Next.js configuration..." -ForegroundColor Yellow
$nextConfig = Get-Content "frontend\next.config.js" -Raw
if ($nextConfig -match "output: 'export'") {
    Write-Host "  ✓ Static export configured" -ForegroundColor Green
} else {
    Write-Host "  ✗ Static export NOT configured!" -ForegroundColor Red
    exit 1
}

# Test 4: Check GitHub Workflow
Write-Host "`n✓ Checking GitHub workflow..." -ForegroundColor Yellow
if (Test-Path ".github\workflows\azure-static-web-apps.yml") {
    $workflow = Get-Content ".github\workflows\azure-static-web-apps.yml" -Raw
    if ($workflow -match 'output_location: "out"') {
        Write-Host "  ✓ Workflow configured correctly" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Workflow output_location incorrect!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✗ Workflow file missing!" -ForegroundColor Red
    exit 1
}

# Test 5: Check for timeout configurations
Write-Host "`n✓ Checking timeout configurations..." -ForegroundColor Yellow
$aiService = Get-Content "backend\app\services\ai_service.py" -Raw
if ($aiService -match "timeout=30.0" -and $aiService -match "@async_timeout") {
    Write-Host "  ✓ AI service timeouts configured" -ForegroundColor Green
} else {
    Write-Host "  ✗ Timeout configurations missing!" -ForegroundColor Red
    exit 1
}

# Test 6: Check Backend Dependencies
Write-Host "`n✓ Checking backend dependencies..." -ForegroundColor Yellow
if (Test-Path "backend\requirements.txt") {
    $requirements = Get-Content "backend\requirements.txt" -Raw
    $requiredPackages = @("fastapi", "openai", "sqlalchemy", "azure-communication-email")
    $allFound = $true
    foreach ($pkg in $requiredPackages) {
        if ($requirements -match $pkg) {
            Write-Host "  ✓ $pkg found" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $pkg missing!" -ForegroundColor Red
            $allFound = $false
        }
    }
    if (-not $allFound) { exit 1 }
} else {
    Write-Host "  ✗ requirements.txt missing!" -ForegroundColor Red
    exit 1
}

# Test 7: Check Frontend Dependencies
Write-Host "`n✓ Checking frontend dependencies..." -ForegroundColor Yellow
if (Test-Path "frontend\package.json") {
    $package = Get-Content "frontend\package.json" -Raw | ConvertFrom-Json
    $requiredPackages = @("next", "react", "axios", "tailwindcss")
    $allFound = $true
    foreach ($pkg in $requiredPackages) {
        if ($package.dependencies.$pkg -or $package.devDependencies.$pkg) {
            Write-Host "  ✓ $pkg found" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $pkg missing!" -ForegroundColor Red
            $allFound = $false
        }
    }
    if (-not $allFound) { exit 1 }
} else {
    Write-Host "  ✗ package.json missing!" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "✓ ALL CHECKS PASSED!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ready for production deployment!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test locally: Run backend and frontend servers" -ForegroundColor White
Write-Host "   Backend:  cd backend && uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "   Frontend: cd frontend && npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Deploy to Azure: git push origin main" -ForegroundColor White
Write-Host ""
Write-Host "3. Monitor: Check GitHub Actions and Azure Portal" -ForegroundColor White
Write-Host ""
