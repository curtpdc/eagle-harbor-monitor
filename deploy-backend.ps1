# Deploy Backend API to Azure App Service
# Run this script to deploy the FastAPI backend

$resourceGroup = "eagleharbor"
$appName = "eagleharbor-api"
$location = "eastus2"

Write-Host "Deploying Eagle Harbor Backend API..." -ForegroundColor Cyan

# Check if App Service exists
Write-Host "Checking if App Service exists..." -ForegroundColor Yellow
$appExists = az webapp show --name $appName --resource-group $resourceGroup 2>$null

if (-not $appExists) {
    Write-Host "Creating App Service Plan and Web App..." -ForegroundColor Yellow
    
    # Create App Service Plan (B1 tier - $13/month)
    az appservice plan create `
        --name "$appName-plan" `
        --resource-group $resourceGroup `
        --location $location `
        --sku B1 `
        --is-linux
    
    # Create Web App with Python 3.11
    az webapp create `
        --name $appName `
        --resource-group $resourceGroup `
        --plan "$appName-plan" `
        --runtime "PYTHON:3.11"
    
    Write-Host "App Service created" -ForegroundColor Green
} else {
    Write-Host "App Service already exists" -ForegroundColor Green
}

# Configure environment variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow

# Read from local .env if exists
$envFile = "backend\.env"
if (Test-Path $envFile) {
    Write-Host "Found .env file, using those values..." -ForegroundColor Cyan
    
    # Parse .env file
    $envVars = @{}
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.+)$') {
            $envVars[$matches[1]] = $matches[2]
        }
    }
    
    # Build settings string
    $settings = @(
        "DATABASE_URL=$($envVars['DATABASE_URL'])",
        "AZURE_OPENAI_API_KEY=$($envVars['AZURE_OPENAI_API_KEY'])",
        "AZURE_OPENAI_ENDPOINT=$($envVars['AZURE_OPENAI_ENDPOINT'])",
        "AZURE_OPENAI_DEPLOYMENT=$($envVars['AZURE_OPENAI_DEPLOYMENT'])",
        "AZURE_COMM_CONNECTION_STRING=$($envVars['AZURE_COMM_CONNECTION_STRING'])",
        "FROM_EMAIL=$($envVars['FROM_EMAIL'])",
        "APP_NAME=Eagle Harbor Data Center Monitor",
        "APP_URL=https://eagleharbormonitor.org",
        "DEBUG=False",
        "SCM_DO_BUILD_DURING_DEPLOYMENT=true"
    )
    
    az webapp config appsettings set `
        --name $appName `
        --resource-group $resourceGroup `
        --settings $settings
        
    Write-Host "Environment variables configured" -ForegroundColor Green
} else {
    Write-Host "No .env file found. You'll need to set environment variables manually." -ForegroundColor Yellow
    Write-Host "Run: az webapp config appsettings set --name $appName --resource-group $resourceGroup --settings KEY=VALUE" -ForegroundColor Yellow
}

# Deploy backend code from local directory
Write-Host "Deploying backend code..." -ForegroundColor Yellow

Push-Location backend

# Create deployment ZIP
Write-Host "Creating deployment package..." -ForegroundColor Cyan
$deployPath = "deploy.zip"
if (Test-Path $deployPath) {
    Remove-Item $deployPath
}

# Compress backend files
Compress-Archive -Path @(
    "app",
    "requirements.txt",
    "function_app.py",
    "host.json"
) -DestinationPath $deployPath -Force

# Deploy ZIP
az webapp deploy `
    --resource-group $resourceGroup `
    --name $appName `
    --src-path $deployPath `
    --type zip `
    --async true

Remove-Item $deployPath

Pop-Location

Write-Host "`nDeployment initiated!" -ForegroundColor Green
Write-Host "`nMonitor deployment status:" -ForegroundColor Cyan
Write-Host "az webapp log tail --name $appName --resource-group $resourceGroup" -ForegroundColor White

Write-Host "`nOnce deployed, test the API:" -ForegroundColor Cyan
Write-Host "curl https://$appName.azurewebsites.net/health" -ForegroundColor White
Write-Host "curl https://$appName.azurewebsites.net/api/articles" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 minutes for deployment to complete"
Write-Host "2. Check deployment logs in Azure Portal"
Write-Host "3. Test the /health endpoint"
Write-Host "4. Test the frontend at https://eagleharbormonitor.org"
