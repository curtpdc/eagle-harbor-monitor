# Quick fix: Deploy using Docker to App Service
# This uses the existing Dockerfile which should work

$resourceGroup = "eagleharbor"
$appName = "eagleharbor-api"
$registryName = "eagleharborregistry"

Write-Host "🚀 Deploying backend using Docker..." -ForegroundColor Cyan

# Build Docker image locally
Write-Host "`n📦 Building Docker image..." -ForegroundColor Yellow
cd backend
docker build -t $appName:latest .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker image built successfully" -ForegroundColor Green

# Tag for Azure Container Registry
Write-Host "`n🏷️  Tagging image..." -ForegroundColor Yellow
docker tag $appName:latest "$registryName.azurecr.io/$appName:latest"

# Login to ACR
Write-Host "`n🔐 Logging into Azure Container Registry..." -ForegroundColor Yellow
az acr login --name $registryName

# Push to ACR
Write-Host "`n⬆️  Pushing image to registry..." -ForegroundColor Yellow
docker push "$registryName.azurecr.io/$appName:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Image pushed to registry" -ForegroundColor Green

# Configure App Service to use the container
Write-Host "`n⚙️  Configuring App Service to use container..." -ForegroundColor Yellow
az webapp config container set `
    --name $appName `
    --resource-group $resourceGroup `
    --docker-custom-image-name "$registryName.azurecr.io/$appName:latest" `
    --docker-registry-server-url "https://$registryName.azurecr.io"

# Restart the app
Write-Host "`n🔄 Restarting app..." -ForegroundColor Yellow
az webapp restart --name $appName --resource-group $resourceGroup 2>&1 | Out-Null

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "`nWaiting 30 seconds for app to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Test the endpoint
Write-Host "`n🧪 Testing API..." -ForegroundColor Yellow
$env:HTTPS_PROXY=''; $env:HTTP_PROXY=''
$result = curl.exe -s https://eagleharbor-api.azurewebsites.net/health 2>&1

if ($result -like "*healthy*" -or $result -like "*status*") {
    Write-Host "✅ SUCCESS! Backend is working!" -ForegroundColor Green
    Write-Host $result -ForegroundColor White
    Write-Host "`n📍 API URL: https://eagleharbor-api.azurewebsites.net" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  App may still be starting up. Response:" -ForegroundColor Yellow
    Write-Host $result -ForegroundColor White
    Write-Host "`nWait another 30-60 seconds and test:" -ForegroundColor Yellow
    Write-Host "  curl https://eagleharbor-api.azurewebsites.net/health" -ForegroundColor White
}

cd ..
