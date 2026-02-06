# Backend Fix - Final Solution

## Current Status

✅ **Frontend**: Working perfectly at https://eagleharbormonitor.org  
✅ **Backend App Service**: Created and configured at https://eagleharbor-api.azurewebsites.net  
❌ **Backend Runtime**: Failing to start (HTTP 503)

## Root Cause

Azure App Service for Linux Python can't find the `app` module correctly. The Oryx buildpack doesn't set PYTHONPATH properly.

## Quick Fix Solution (5 minutes)

Run this single command to fix the backend:

```powershell
# Fix and test the backend
az webapp config container set --name eagleharbor-api --resource-group eagleharbor --docker-custom-image-name "eagleharborregistry.azurecr.io/eagle-harbor-backend:v3"; az webapp restart --name eagleharbor-api --resource-group eagleharbor; Start-Sleep -Seconds 45; curl https://eagleharbor-api.azurewebsites.net/health
```

**What this does:**
- Uses the pre-built Docker image from your registry (already exists!)
- Restarts the app with the correct configuration
- Tests the health endpoint

## If That Doesn't Work - Manual Portal Fix

1. Go to Azure Portal: https://portal.azure.com
2. Navigate to: Resource Groups → eagleharbor → eagleharbor-api
3. Click "Deployment Center" in left menu
4. Change "Source" to "Container Registry"
5. Select:
   - Registry: eagleharborregistry
   - Image: eagle-harbor-backend
   - Tag: v3
6. Click "Save"
7. Wait 2-3 minutes
8. Test: https://eagleharbor-api.azurewebsites.net/health

## Verify It's Working

```powershell
# Health check
curl https://eagleharbor-api.azurewebsites.net/health

# API docs
curl https://eagleharbor-api.azurewebsites.net/docs

# Test subscribe endpoint
curl -X POST https://eagleharbor-api.azurewebsites.net/api/subscribe -H "Content-Type: application/json" -d '{"email":"test@example.com"}'
```

## Once Backend is Working

The frontend is ALREADY configured to use the backend! Just test your homepage:

1. Go to https://eagleharbormonitor.org
2. Try the email subscription form
3. Try the "Ask a Question" chat feature

Both should work immediately once the backend responds.

## Alternative: Use Azure Portal's Built-in Fix

If CLI commands fail:

1. **Azure Portal** → **eagleharbor-api**
2. **Development Tools** → **SSH** → **Go**
3. Run in SSH terminal:
   ```bash
   cd /home/site/wwwroot
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. If that works, update the startup command in Configuration → General Settings → Startup Command:
   ```
   cd /home/site/wwwroot && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## Missing Environment Variables (Add Later)

For FULL functionality, you still need to add:

```powershell
az webapp config appsettings set --name eagleharbor-api --resource-group eagleharbor --settings AZURE_OPENAI_API_KEY="your-key" AZURE_COMM_CONNECTION_STRING="your-connection"
```

Without these:
- ❌ AI chat will not work
- ❌ Email alerts will not work
- ✅ Everything else works (article listing, events, etc.)

## Summary

**The homepage is live and beautiful!** 🎉

**To make it fully functional:**
1. Fix backend startup (use command above or Azure Portal)
2. Add Azure API keys for AI and email
3. Test subscribe and chat features

Your architecture is sound, the code is deployed, it's just a runtime configuration issue!
