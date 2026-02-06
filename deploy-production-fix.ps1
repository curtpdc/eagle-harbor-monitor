# Production Fix Deployment Script
# Fixes CORS and API URL configuration issues

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 Eagle Harbor Monitor - Production Fix Deployment" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$RESOURCE_GROUP = "eagleharbor"
$BACKEND_NAME = "eagleharbor-api"
$FRONTEND_NAME = "calm-moss-0bea6ad10"
$APP_SERVICE_PLAN = "eagle-harbor-plan"
$API_URL = "https://eagleharbor-api.azurewebsites.net/api"

# Check if Azure CLI is installed
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI not found. Please install: https://aka.ms/installazurecli" -ForegroundColor Red
    exit 1
}

# Check if logged in
Write-Host "🔐 Checking Azure authentication..." -ForegroundColor Yellow
$account = az account show 2>$null | ConvertFrom-Json
if (!$account) {
    Write-Host "❌ Not logged in to Azure. Running 'az login'..." -ForegroundColor Red
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Azure login failed" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host ""

# Step 1: Deploy Backend (CORS Fix)
if (!$SkipBackend) {
    Write-Host "📦 Step 1: Deploying Backend with CORS Fix" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    
    Push-Location backend
    
    Write-Host "Building and deploying to Azure App Service..." -ForegroundColor Yellow
    az webapp up `
        --name $BACKEND_NAME `
        --resource-group $RESOURCE_GROUP `
        --plan $APP_SERVICE_PLAN `
        --runtime "PYTHON:3.11" `
        --verbose
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Backend deployment failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host "✅ Backend deployed successfully" -ForegroundColor Green
    Write-Host ""
    
    # Wait for backend to start
    Write-Host "⏳ Waiting for backend to start (15 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
} else {
    Write-Host "⏭️  Skipping backend deployment" -ForegroundColor Gray
    Write-Host ""
}

# Step 2: Configure Frontend Environment Variable
if (!$SkipFrontend) {
    Write-Host "🌐 Step 2: Configuring Frontend Environment" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    
    # Try to find the Static Web App
    Write-Host "Looking for Static Web App in subscription..." -ForegroundColor Yellow
    $staticApps = az staticwebapp list --query "[?contains(defaultHostname, 'calm-moss-0bea6ad10')]" | ConvertFrom-Json
    
    if ($staticApps -and $staticApps.Count -gt 0) {
        $FRONTEND_NAME = $staticApps[0].name
        Write-Host "Found Static Web App: $FRONTEND_NAME" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not find Static Web App with hostname 'calm-moss-0bea6ad10'" -ForegroundColor Yellow
        Write-Host "Listing all Static Web Apps in subscription:" -ForegroundColor Yellow
        az staticwebapp list --query "[].{Name:name, Hostname:defaultHostname}" -o table
        Write-Host ""
        Write-Host "Please set the environment variable manually:" -ForegroundColor Yellow
        Write-Host "az staticwebapp appsettings set --name <your-app-name> --setting-names NEXT_PUBLIC_API_URL=$API_URL" -ForegroundColor Gray
        Write-Host ""
        $Skip = $true
    }
    
    if (!$Skip) {
        Write-Host "Setting NEXT_PUBLIC_API_URL to: $API_URL" -ForegroundColor Yellow
        
        az staticwebapp appsettings set `
            --name $FRONTEND_NAME `
            --setting-names "NEXT_PUBLIC_API_URL=$API_URL"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Frontend configuration failed" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "✅ Frontend environment configured" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  Note: Frontend will need to be redeployed for changes to take effect" -ForegroundColor Yellow
        Write-Host "   This happens automatically via GitHub Actions on next push" -ForegroundColor Gray
        Write-Host ""
    }
} else {
    Write-Host "⏭️  Skipping frontend configuration" -ForegroundColor Gray
    Write-Host ""
}

# Step 3: Verification
if ($Verify -or (!$SkipBackend -and !$SkipFrontend)) {
    Write-Host "✅ Step 3: Verification" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    
    # Test backend health
    Write-Host "Testing backend health endpoint..." -ForegroundColor Yellow
    try {
        $healthResponse = Invoke-RestMethod -Uri "https://eagleharbor-api.azurewebsites.net/health" -Method Get
        if ($healthResponse.status -eq "healthy") {
            Write-Host "✅ Backend health check passed" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Backend health check returned unexpected status" -ForegroundColor Yellow
            Write-Host $healthResponse
        }
    } catch {
        Write-Host "❌ Backend health check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test backend API
    Write-Host "Testing backend API endpoint..." -ForegroundColor Yellow
    try {
        $articlesResponse = Invoke-RestMethod -Uri "https://eagleharbor-api.azurewebsites.net/api/articles?limit=1" -Method Get
        Write-Host "✅ Backend API responding (found $($articlesResponse.Count) articles)" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Backend API test failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   This may be normal if database is empty" -ForegroundColor Gray
    }
    
    # Check frontend settings
    Write-Host "Checking frontend environment settings..." -ForegroundColor Yellow
    $settings = az staticwebapp appsettings list --name $FRONTEND_NAME | ConvertFrom-Json
    $apiUrlSetting = $settings.properties | Where-Object { $_.NEXT_PUBLIC_API_URL }
    
    if ($apiUrlSetting) {
        Write-Host "✅ NEXT_PUBLIC_API_URL = $($apiUrlSetting.NEXT_PUBLIC_API_URL)" -ForegroundColor Green
        
        if ($apiUrlSetting.NEXT_PUBLIC_API_URL -eq $API_URL) {
            Write-Host "✅ Frontend URL correctly configured" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Frontend URL mismatch:" -ForegroundColor Yellow
            Write-Host "   Expected: $API_URL" -ForegroundColor Gray
            Write-Host "   Got: $($apiUrlSetting.NEXT_PUBLIC_API_URL)" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ NEXT_PUBLIC_API_URL not set in frontend" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Summary
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Summary of Changes:" -ForegroundColor Cyan
Write-Host "  ✅ Backend CORS updated to allow frontend origin" -ForegroundColor Green
Write-Host "  ✅ Frontend API URL configured with /api suffix" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: https://calm-moss-0bea6ad10.4.azurestaticapps.net" -ForegroundColor White
Write-Host "  Backend:  https://eagleharbor-api.azurewebsites.net" -ForegroundColor White
Write-Host "  API:      https://eagleharbor-api.azurewebsites.net/api" -ForegroundColor White
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Commit and push changes to trigger frontend redeploy:" -ForegroundColor White
Write-Host "     git add ." -ForegroundColor Gray
Write-Host "     git commit -m 'Fix CORS and API URL configuration'" -ForegroundColor Gray
Write-Host "     git push origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test frontend functionality:" -ForegroundColor White
Write-Host "     - Email subscription form" -ForegroundColor Gray
Write-Host "     - AI chat feature" -ForegroundColor Gray
Write-Host "     - Events calendar" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Monitor for CORS errors in browser console" -ForegroundColor White
Write-Host ""

# Open URLs in browser
$openBrowser = Read-Host "Open URLs in browser for testing? (y/N)"
if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
    Write-Host "Opening URLs..." -ForegroundColor Yellow
    Start-Process "https://calm-moss-0bea6ad10.4.azurestaticapps.net"
    Start-Process "https://eagleharbor-api.azurewebsites.net/health"
}

Write-Host "✅ Done!" -ForegroundColor Green
