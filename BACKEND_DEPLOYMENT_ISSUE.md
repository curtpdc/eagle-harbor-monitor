# Backend Deployment Status & Fix Instructions

## Current Status (as of Feb 5, 2026)

### ✅ What's Working
- Frontend deployed successfully at https://eagleharbormonitor.org
- Azure App Service `eagleharbor-api` created in `eagleharbor` resource group
- Code successfully uploaded and built (Oryx build logs show no errors)
- Dependencies installed correctly (gunicorn, uvicorn, fastapi all present)

### ❌ What's Broken
- Backend API returns HTTP 503 (Service Unavailable)
- Container starts but application fails to initialize
- Startup command: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Error: Container exits with code 1 after ~90 seconds

## Root Cause

The issue is that Azure App Service for Linux Python is trying to run the FastAPI app from the wrong directory or the module path isn't correct. Azure's Oryx build system unpacks code to `/home/site/wwwroot` but the Python module resolution may be failing.

## Solution Options

### Option 1: Fix Current App Service (Recommended)

1. **Create a proper startup script:**
   - File: `backend/startup.sh`
   - Make it executable
   - Set `PYTHONPATH` correctly
   - Use absolute paths

2. **Update startup command in Azure:**
   ```bash
   az webapp config set --resource-group eagleharbor --name eagleharbor-api \
     --startup-file "bash startup.sh"
   ```

3. **Or use a simpler startup command:**
   ```bash
   # Option A: Direct module import
   az webapp config set --resource-group eagleharbor --name eagleharbor-api \
     --startup-file "cd /home/site/wwwroot && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
   
   # Option B: Set PYTHONPATH
   az webapp config appsettings set --name eagleharbor-api --resource-group eagleharbor \
     --settings PYTHONPATH="/home/site/wwwroot"
   ```

### Option 2: Deploy to Azure Container Apps (Better for FastAPI)

Azure Container Apps is more suited for containerized FastAPI apps:

```bash
# Create Container Apps environment
az containerapp env create \
  --name eagleharbor-env \
  --resource-group eagleharbor \
  --location eastus2

# Deploy from code
az containerapp up \
  --name eagleharbor-api \
  --resource-group eagleharbor \
  --location eastus2 \
  --environment eagleharbor-env \
  --source backend \
  --target-port 8000 \
  --ingress external
```

### Option 3: Use Azure Functions (Already Configured!)

Your code already has `function_app.py` for Azure Functions. This might actually be easier:

```bash
# Deploy as Azure Functions instead
cd backend
func azure functionapp publish eagleharbor-api-func --python
```

## Quick Test Commands

After fixing, test with:

```powershell
# Test health endpoint
curl https://eagleharbor-api.azurewebsites.net/health

# Test API docs
curl https://eagleharbor-api.azurewebsites.net/docs

# Test subscribe endpoint
curl -X POST https://eagleharbor-api.azurewebsites.net/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Immediate Next Steps

1. Try Option 1 first (fix startup command)
2. If that fails after 2 attempts, switch to Option 2 (Container Apps)
3. If time is critical, use Option 3 (Azure Functions)

## Current Environment Variables Set

- DATABASE_URL: sqlite:///./eagle_harbor.db
- AZURE_OPENAI_ENDPOINT: https://xig-openai-resource.cognitiveservices.azure.com/
- AZURE_OPENAI_DEPLOYMENT: gpt-4o-mini
- FROM_EMAIL: alerts@eagleharbormonitor.org
- APP_NAME: Eagle Harbor Data Center Monitor
- APP_URL: https://eagleharbormonitor.org
- DEBUG: False
- SCM_DO_BUILD_DURING_DEPLOYMENT: true
- WEBSITES_PORT: 8000

## Missing (Required for Full Functionality)

- AZURE_OPENAI_API_KEY - ⚠️ REQUIRED for AI chat features
- AZURE_COMM_CONNECTION_STRING - ⚠️ REQUIRED for email subscription

Add these with:
```bash
az webapp config appsettings set \
  --name eagleharbor-api \
  --resource-group eagleharbor \
  --settings \
    AZURE_OPENAI_API_KEY="your-key-here" \
    AZURE_COMM_CONNECTION_STRING="your-connection-string"
```
