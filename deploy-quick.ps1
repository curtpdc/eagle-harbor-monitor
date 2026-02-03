# Quick Deployment Script - Eagle Harbor Monitor
# This uses SQLite locally for immediate testing while PostgreSQL registers

Write-Host "🚀 Eagle Harbor Monitor - Quick Deployment" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get API Keys
Write-Host "Step 1: API Keys Configuration" -ForegroundColor Yellow
Write-Host "You'll need:"
Write-Host "  1. Anthropic API Key (https://console.anthropic.com)"
Write-Host "  2. SendGrid API Key (https://sendgrid.com - free tier)"
Write-Host ""

$anthropicKey = Read-Host "Enter your Anthropic API Key (or press Enter to skip for now)"
$sendgridKey = Read-Host "Enter your SendGrid API Key (or press Enter to skip for now)"

# Step 2: Create Storage Account for Functions
Write-Host ""
Write-Host "Step 2: Creating Azure Storage Account..." -ForegroundColor Yellow

$storageExists = az storage account show --name eagleharbordata --resource-group xigusa-webapp 2>$null
if (-not $storageExists) {
    az storage account create `
        --name eagleharbordata `
        --resource-group xigusa-webapp `
        --location eastus2 `
        --sku Standard_LRS
    Write-Host "✓ Storage account created" -ForegroundColor Green
} else {
    Write-Host "✓ Storage account already exists" -ForegroundColor Green
}

# Step 3: Create Function App
Write-Host ""
Write-Host "Step 3: Creating Azure Function App..." -ForegroundColor Yellow

az functionapp create `
    --resource-group xigusa-webapp `
    --consumption-plan-location eastus2 `
    --runtime python `
    --runtime-version 3.11 `
    --functions-version 4 `
    --name eagle-harbor-functions `
    --storage-account eagleharbordata `
    --os-type Linux

Write-Host "✓ Function App created" -ForegroundColor Green

# Step 4: Create Web App for Backend API
Write-Host ""
Write-Host "Step 4: Creating Web App for Backend API..." -ForegroundColor Yellow

az webapp create `
    --resource-group xigusa-webapp `
    --plan ASP-xigusawebapp-a8da `
    --name eagle-harbor-api `
    --runtime "PYTHON:3.11"

Write-Host "✓ Web App created" -ForegroundColor Green

# Step 5: Configure Backend Environment Variables
Write-Host ""
Write-Host "Step 5: Configuring Backend Environment..." -ForegroundColor Yellow

$settings = @(
    "DATABASE_URL=sqlite:///./eagle_harbor.db"
    "FROM_EMAIL=alerts@eagleharbormonitor.org"
    "APP_URL=https://eagle-harbor-monitor.azurestaticapps.net"
)

if ($anthropicKey) {
    $settings += "ANTHROPIC_API_KEY=$anthropicKey"
}

if ($sendgridKey) {
    $settings += "SENDGRID_API_KEY=$sendgridKey"
}

az webapp config appsettings set `
    --resource-group xigusa-webapp `
    --name eagle-harbor-api `
    --settings $settings

Write-Host "✓ Environment configured" -ForegroundColor Green

# Step 6: Deploy Backend
Write-Host ""
Write-Host "Step 6: Deploying Backend API..." -ForegroundColor Yellow

Set-Location backend

# Create deployment package
Compress-Archive -Path * -DestinationPath ../backend-deploy.zip -Force

# Deploy
az webapp deployment source config-zip `
    --resource-group xigusa-webapp `
    --name eagle-harbor-api `
    --src ../backend-deploy.zip

Set-Location ..
Remove-Item backend-deploy.zip

Write-Host "✓ Backend deployed" -ForegroundColor Green

# Step 7: Deploy Functions
Write-Host ""
Write-Host "Step 7: Deploying Azure Functions..." -ForegroundColor Yellow

Set-Location functions

# Configure Function App settings
$funcSettings = @(
    "DATABASE_URL=sqlite:///./eagle_harbor.db"
)

if ($anthropicKey) {
    $funcSettings += "ANTHROPIC_API_KEY=$anthropicKey"
}

az functionapp config appsettings set `
    --resource-group xigusa-webapp `
    --name eagle-harbor-functions `
    --settings $funcSettings

# Deploy functions
func azure functionapp publish eagle-harbor-functions --python

Set-Location ..

Write-Host "✓ Functions deployed" -ForegroundColor Green

# Step 8: Create Static Web App
Write-Host ""
Write-Host "Step 8: Creating Static Web App for Frontend..." -ForegroundColor Yellow
Write-Host "Note: This requires GitHub integration. You'll need to:"
Write-Host "  1. Push this code to GitHub"
Write-Host "  2. Run the following command with your GitHub repo URL:"
Write-Host ""
Write-Host "az staticwebapp create \" -ForegroundColor Cyan
Write-Host "    --name eagle-harbor-monitor \" -ForegroundColor Cyan
Write-Host "    --resource-group xigusa-webapp \" -ForegroundColor Cyan
Write-Host "    --location eastus2 \" -ForegroundColor Cyan
Write-Host "    --source https://github.com/YOUR_USERNAME/eagle-harbor-monitor \" -ForegroundColor Cyan
Write-Host "    --branch main \" -ForegroundColor Cyan
Write-Host "    --app-location /frontend \" -ForegroundColor Cyan
Write-Host "    --output-location out" -ForegroundColor Cyan
Write-Host ""

# Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ Deployment Summary" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API: " -NoNewline
Write-Host "https://eagle-harbor-api.azurewebsites.net" -ForegroundColor Cyan
Write-Host "Function App: " -NoNewline
Write-Host "https://eagle-harbor-functions.azurewebsites.net" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test backend: https://eagle-harbor-api.azurewebsites.net/api/health"
Write-Host "  2. Push code to GitHub"
Write-Host "  3. Deploy frontend using Static Web Apps command above"
Write-Host "  4. Once PostgreSQL is ready, update DATABASE_URL to PostgreSQL connection string"
Write-Host ""
Write-Host "PostgreSQL Registration Status:" -ForegroundColor Yellow
$regStatus = az provider show -n Microsoft.DBforPostgreSQL --query "registrationState" -o tsv
Write-Host "  Current: $regStatus"
if ($regStatus -eq "Registered") {
    Write-Host "  ✓ PostgreSQL is ready! You can now create the database." -ForegroundColor Green
} else {
    Write-Host "  ⏳ Still registering. Run this again in 5 minutes to create PostgreSQL." -ForegroundColor Yellow
}
