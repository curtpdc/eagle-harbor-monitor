# Deploy Backend API to Azure Container Apps
# Serverless, cost-effective alternative to App Service

$resourceGroup = "eagleharbor"
$appName = "eagleharbor-api"
$location = "eastus2"
$containerAppEnv = "eagleharbor-env"

Write-Host "🚀 Deploying Eagle Harbor Backend to Azure Container Apps..." -ForegroundColor Cyan

# Check if Container Apps extension is installed
Write-Host "Checking Azure CLI extensions..." -ForegroundColor Yellow
az extension add --name containerapp --upgrade 2>$null
az provider register --namespace Microsoft.App --wait 2>$null
az provider register --namespace Microsoft.OperationalInsights --wait 2>$null

# Check if Container App Environment exists
Write-Host "Checking if Container App Environment exists..." -ForegroundColor Yellow
$envExists = az containerapp env show --name $containerAppEnv --resource-group $resourceGroup 2>$null

if (-not $envExists) {
    Write-Host "Creating Container App Environment..." -ForegroundColor Yellow
    az containerapp env create `
        --name $containerAppEnv `
        --resource-group $resourceGroup `
        --location $location
    
    Write-Host "✅ Container App Environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Container App Environment already exists" -ForegroundColor Green
}

# Read environment variables from .env file
Write-Host "Reading environment variables..." -ForegroundColor Yellow
$envFile = "backend\.env"
$envVars = @()

if (Test-Path $envFile) {
    Write-Host "Found .env file" -ForegroundColor Cyan
    
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            
            # Skip empty or comment lines
            if ($key -and -not $key.StartsWith('#')) {
                $envVars += "$key=$value"
            }
        }
    }
    
    Write-Host "✅ Loaded $($envVars.Count) environment variables" -ForegroundColor Green
} else {
    Write-Host "⚠️  No .env file found, using minimal configuration" -ForegroundColor Yellow
}

# Add required environment variables
$envVars += "DATABASE_URL=sqlite:///./data.db"
$envVars += "APP_NAME=Eagle Harbor Data Center Monitor"
$envVars += "APP_URL=https://eagleharbormonitor.org"
$envVars += "DEBUG=False"
$envVars += "PORT=8000"
$envVars += "PYTHONUNBUFFERED=1"

# Build environment variables argument
$envArgsString = ($envVars | ForEach-Object { "--env-vars `"$_`"" }) -join ' '

# Deploy Container App from source code
Write-Host "`nDeploying Container App from source..." -ForegroundColor Yellow
Write-Host "This will:" -ForegroundColor Cyan
Write-Host "  1. Build Docker image from backend/Dockerfile" -ForegroundColor White
Write-Host "  2. Push to Azure Container Registry" -ForegroundColor White
Write-Host "  3. Deploy to Container App" -ForegroundColor White
Write-Host "  4. Configure ingress on port 8000" -ForegroundColor White

# Check if Container App exists
$appExists = az containerapp show --name $appName --resource-group $resourceGroup 2>$null

if ($appExists) {
    Write-Host "`n⚠️  Container App '$appName' already exists. Updating..." -ForegroundColor Yellow
    
    # Update existing app
    $updateCmd = "az containerapp update " +
        "--name $appName " +
        "--resource-group $resourceGroup " +
        "--source backend " +
        "$envArgsString"
    
    Invoke-Expression $updateCmd
} else {
    Write-Host "`nCreating new Container App..." -ForegroundColor Yellow
    
    # Create new app
    $createCmd = "az containerapp up " +
        "--name $appName " +
        "--resource-group $resourceGroup " +
        "--location $location " +
        "--environment $containerAppEnv " +
        "--source backend " +
        "--target-port 8000 " +
        "--ingress external " +
        "$envArgsString"
    
    Invoke-Expression $createCmd
}

# Get the app URL
Write-Host "`nRetrieving app URL..." -ForegroundColor Yellow
$appUrl = az containerapp show `
    --name $appName `
    --resource-group $resourceGroup `
    --query properties.configuration.ingress.fqdn `
    --output tsv

if ($appUrl) {
    $appUrl = "https://$appUrl"
    
    Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
    Write-Host "`n📍 App URL: $appUrl" -ForegroundColor Cyan
    
    # Save URL to file for frontend update
    $appUrl | Out-File -FilePath "container-app-url.txt" -NoNewline
    
    Write-Host "`n🧪 Testing API..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    try {
        $response = Invoke-WebRequest -Uri "$appUrl/health" -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Health check passed!" -ForegroundColor Green
            Write-Host $response.Content -ForegroundColor White
        }
    } catch {
        Write-Host "⚠️  Health check pending... App may still be starting up." -ForegroundColor Yellow
        Write-Host "Wait 30-60 seconds and try: curl $appUrl/health" -ForegroundColor White
    }
    
    Write-Host "`n📊 Quick Test Commands:" -ForegroundColor Yellow
    Write-Host "  curl $appUrl/health" -ForegroundColor White
    Write-Host "  curl $appUrl/api/articles" -ForegroundColor White
    Write-Host "  curl $appUrl/docs" -ForegroundColor White
} else {
    Write-Host "❌ Could not retrieve app URL" -ForegroundColor Red
}
