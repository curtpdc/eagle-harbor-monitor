# Quick Backend Deployment Script
# This script deploys the backend API in a simplified way

$ErrorActionPreference = "Continue"
$resourceGroup = "eagleharbor"
$appName = "eagleharbor-api"
$location = "eastus2"

Write-Host "`n=== Eagle Harbor Backend Deployment ===" -ForegroundColor Cyan
Write-Host "Resource Group: $resourceGroup" -ForegroundColor Yellow
Write-Host "App Name: $appName" -ForegroundColor Yellow
Write-Host "Location: $location`n" -ForegroundColor Yellow

# Step 1: Check if App Service Plan exists, create if needed
Write-Host "[1/5] Checking App Service Plan..." -ForegroundColor Cyan
$planExists = az appservice plan show -n "$appName-plan" -g $resourceGroup 2>$null
if (-not $planExists) {
    Write-Host "Creating App Service Plan (B1 - Linux)..." -ForegroundColor Yellow
    az appservice plan create `
        --name "$appName-plan" `
        --resource-group $resourceGroup `
        --location $location `
        --sku B1 `
        --is-linux `
        --output none
    Write-Host "✅ App Service Plan created" -ForegroundColor Green
} else {
    Write-Host "✅ App Service Plan exists" -ForegroundColor Green
}

# Step 2: Check if Web App exists, create if needed
Write-Host "`n[2/5] Checking Web App..." -ForegroundColor Cyan
$appExists = az webapp show -n $appName -g $resourceGroup 2>$null
if (-not $appExists) {
    Write-Host "Creating Web App with Python 3.11..." -ForegroundColor Yellow
    az webapp create `
        --name $appName `
        --resource-group $resourceGroup `
        --plan "$appName-plan" `
        --runtime "PYTHON:3.11" `
        --output none
    Write-Host "✅ Web App created" -ForegroundColor Green
} else {
    Write-Host "✅ Web App exists" -ForegroundColor Green
}

# Step 3: Configure app settings
Write-Host "`n[3/5] Configuring app settings..." -ForegroundColor Cyan
az webapp config appsettings set `
    --name $appName `
    --resource-group $resourceGroup `
    --settings `
        DATABASE_URL="sqlite:///./eagle_harbor.db" `
        AZURE_OPENAI_ENDPOINT="https://xig-openai-resource.cognitiveservices.azure.com/" `
        AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" `
        FROM_EMAIL="alerts@eagleharbormonitor.org" `
        APP_NAME="Eagle Harbor Data Center Monitor" `
        APP_URL="https://eagleharbormonitor.org" `
        DEBUG="False" `
        SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
        WEBSITES_PORT="8000" `
    --output none

Write-Host "✅ App settings configured" -ForegroundColor Green

# Step 4: Create deployment package
Write-Host "`n[4/5] Creating deployment package..." -ForegroundColor Cyan
Push-Location backend

if (Test-Path "deploy.zip") {
    Remove-Item "deploy.zip" -Force
}

Compress-Archive -Path app,requirements.txt,function_app.py,host.json -DestinationPath deploy.zip -Force
Write-Host "✅ Package created" -ForegroundColor Green

# Step 5: Deploy code
Write-Host "`n[5/5] Deploying code to Azure..." -ForegroundColor Cyan
Write-Host "(This may take 2-3 minutes...)" -ForegroundColor Yellow

az webapp deploy `
    --resource-group $resourceGroup `
    --name $appName `
    --src-path deploy.zip `
    --type zip `
    --timeout 300 `
    --output none

Write-Host "✅ Code deployed" -ForegroundColor Green

Remove-Item deploy.zip -Force
Pop-Location

# Summary
Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "`nYour API is deployed at:" -ForegroundColor Cyan
Write-Host "https://$appName.azurewebsites.net" -ForegroundColor White

Write-Host "`nTest endpoints:" -ForegroundColor Cyan
Write-Host "Health Check: curl https://$appName.azurewebsites.net/health" -ForegroundColor White
Write-Host "API Docs: https://$appName.azurewebsites.net/docs" -ForegroundColor White

Write-Host "`n⚠️  Important Next Steps:" -ForegroundColor Yellow
Write-Host "1. Add Azure OpenAI API key to app settings (required for AI features)"
Write-Host "2. Add Azure Communication Services connection string (required for emails)"
Write-Host "3. Wait 2-3 minutes for the app to fully start"
Write-Host "4. Check logs if needed: az webapp log tail -n $appName -g $resourceGroup"

Write-Host "`nTo add missing API keys:" -ForegroundColor Cyan
Write-Host "az webapp config appsettings set -n $appName -g $resourceGroup --settings AZURE_OPENAI_API_KEY=your-key AZURE_COMM_CONNECTION_STRING=your-connection-string" -ForegroundColor White
