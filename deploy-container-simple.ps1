# Deploy backend to Azure using Container Instances (simpler than App Service)

Write-Host "Eagle Harbor Backend - Container Instances Deployment" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Configuration
$resourceGroup = "eagleharbor"
$location = "centralus"
$containerName = "eagleharbor-api"
$imageName = "eagleharborregistry.azurecr.io/eagle-harbor-backend:latest"
$dnsLabel = "eagleharbor-api"  # Will be accessible at eagleharbor-api.centralus.azurecontainer.io

# Build and push Docker image
Write-Host "`n1. Building Docker image..." -ForegroundColor Yellow
docker build -t $imageName ./backend
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n2. Pushing to Azure Container Registry..." -ForegroundColor Yellow
az acr login --name eagleharborregistry
docker push $imageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker push failed" -ForegroundColor Red
    exit 1
}

# Get ACR credentials
Write-Host "`n3. Getting ACR credentials..." -ForegroundColor Yellow
$acrPassword = az acr credential show --name eagleharborregistry --query "passwords[0].value" -o tsv

# Deploy to Container Instances
Write-Host "`n4. Deploying to Azure Container Instances..." -ForegroundColor Yellow
az container create `
    --resource-group $resourceGroup `
    --name $containerName `
    --image $imageName `
    --dns-name-label $dnsLabel `
    --ports 8000 `
    --os-type Linux `
    --cpu 1 `
    --memory 1 `
    --registry-login-server eagleharborregistry.azurecr.io `
    --registry-username eagleharborregistry `
    --registry-password $acrPassword `
    --environment-variables `
        DATABASE_URL="sqlite:///./eagle_harbor.db" `
        APP_URL="https://eagleharbormonitor.org" `
        FROM_EMAIL="alerts@eagleharbormonitor.org" `
        AZURE_OPENAI_ENDPOINT="https://xig-openai-resource.cognitiveservices.azure.com/" `
        AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Deployment successful!" -ForegroundColor Green
    Write-Host "`nAPI URL: http://$dnsLabel.centralus.azurecontainer.io:8000" -ForegroundColor Cyan
    Write-Host "Health check: http://$dnsLabel.centralus.azurecontainer.io:8000/health" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Deployment failed" -ForegroundColor Red
    exit 1
}
