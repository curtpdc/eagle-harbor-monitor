# Manual Backend Deployment Steps
# Run each command one at a time

Write-Host "Step 1: Create App Service Plan" -ForegroundColor Cyan
az appservice plan create `
    --name eagleharbor-api-plan `
    --resource-group eagleharbor `
    --location eastus2 `
    --sku B1 `
    --is-linux

Write-Host "`nStep 2: Create Web App" -ForegroundColor Cyan
az webapp create `
    --name eagleharbor-api `
    --resource-group eagleharbor `
    --plan eagleharbor-api-plan `
    --runtime "PYTHON:3.11"

Write-Host "`nStep 3: Configure startup command" -ForegroundColor Cyan
az webapp config set `
    --resource-group eagleharbor `
    --name eagleharbor-api `
    --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0:8000"

Write-Host "`nStep 4: Set app settings" -ForegroundColor Cyan
az webapp config appsettings set `
    --resource-group eagleharbor `
    --name eagleharbor-api `
    --settings `
        DATABASE_URL="sqlite:///./eagle_harbor.db" `
        AZURE_OPENAI_ENDPOINT="https://xig-openai-resource.cognitiveservices.azure.com/" `
        AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" `
        FROM_EMAIL="alerts@eagleharbormonitor.org" `
        APP_NAME="Eagle Harbor Data Center Monitor" `
        APP_URL="https://eagleharbormonitor.org" `
        DEBUG="False" `
        SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
        WEBSITES_PORT="8000"

Write-Host "`nStep 5: Deploy code" -ForegroundColor Cyan
cd backend
az webapp up `
    --resource-group eagleharbor `
    --name eagleharbor-api `
    --runtime "PYTHON:3.11" `
    --sku B1

Write-Host "`n✅ Done! Test at: https://eagleharbor-api.azurewebsites.net/health" -ForegroundColor Green
