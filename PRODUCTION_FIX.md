# Production Deployment Fixes

## Issues Identified

1. **CORS Blocking**: Backend not allowing frontend origin
2. **Double `/api/` Path**: Frontend environment variable missing `/api` suffix
3. **EventCalendar API Mismatch**: Inconsistent URL construction

## Fixes Applied

### 1. Backend CORS Configuration
✅ Updated [backend/app/main.py](backend/app/main.py) to explicitly allow:
- `https://calm-moss-0bea6ad10.4.azurestaticapps.net` (production frontend)
- `http://localhost:3000` (local development)

### 2. Frontend API URL Consistency
✅ Fixed [frontend/src/components/EventCalendar.tsx](frontend/src/components/EventCalendar.tsx) to use consistent API_BASE pattern

### 3. Azure Static Web App Environment Variable
⚠️ **ACTION REQUIRED**: Update Azure Static Web App configuration

## Deployment Steps

### Step 1: Deploy Updated Backend

```powershell
# Navigate to backend directory
cd backend

# Deploy to Azure App Service
az webapp up --name eagleharbor-api --resource-group eagleharbor --runtime "PYTHON:3.11"
```

**Alternative**: Use existing deployment script:
```powershell
.\deploy-backend.ps1
```

### Step 2: Configure Frontend Environment Variable

Set the correct `NEXT_PUBLIC_API_URL` in Azure Static Web Apps:

```powershell
# Set environment variable for production
az staticwebapp appsettings set `
  --name calm-moss-0bea6ad10 `
  --setting-names NEXT_PUBLIC_API_URL=https://eagleharbor-api.azurewebsites.net/api
```

**Important**: The URL must end with `/api` to match backend routes!

### Step 3: Redeploy Frontend

```powershell
# Navigate to frontend directory
cd frontend

# Build for production
npm run build

# Deploy to Azure Static Web Apps (this happens automatically via GitHub Actions)
# Or manually deploy:
# swa deploy --app-location ./out --env production
```

## Verification

After deployment, test these endpoints:

1. **Email Subscription**:
   ```
   https://calm-moss-0bea6ad10.4.azurestaticapps.net
   ```
   - Enter email and click Subscribe
   - Should see success message (no CORS errors)

2. **AI Chat**:
   ```
   https://calm-moss-0bea6ad10.4.azurestaticapps.net
   ```
   - Use "Ask a Question" feature
   - Should receive AI response (no CORS errors)

3. **Events Calendar**:
   ```
   https://calm-moss-0bea6ad10.4.azurestaticapps.net
   ```
   - Navigate to Events/Calendar section
   - Should load upcoming events (no CORS errors)

4. **Backend Health Check**:
   ```
   https://eagleharbor-api.azurewebsites.net/health
   ```
   Should return: `{"status": "healthy"}`

5. **Backend API Direct**:
   ```
   https://eagleharbor-api.azurewebsites.net/api/articles?limit=5
   ```
   Should return JSON array of articles

## Quick Fix Commands (Copy-Paste Ready)

```powershell
# 1. Deploy backend with CORS fix
cd backend
az webapp up --name eagleharbor-api --resource-group eagleharbor --runtime "PYTHON:3.11"

# 2. Set frontend environment variable
az staticwebapp appsettings set `
  --name calm-moss-0bea6ad10 `
  --setting-names NEXT_PUBLIC_API_URL=https://eagleharbor-api.azurewebsites.net/api

# 3. Verify backend is running
curl https://eagleharbor-api.azurewebsites.net/health

# 4. Test API endpoint
curl https://eagleharbor-api.azurewebsites.net/api/articles?limit=1
```

## Expected Results

After applying these fixes:

- ✅ Email subscription form works without CORS errors
- ✅ AI chat functionality works
- ✅ Events calendar loads data
- ✅ All frontend components can access backend API
- ✅ No more `/api/api/` double path errors

## Troubleshooting

### If CORS errors persist:

1. Check backend logs:
   ```powershell
   az webapp log tail --name eagleharbor-api --resource-group eagleharbor
   ```

2. Verify CORS configuration deployed:
   ```powershell
   # SSH into backend container
   az webapp ssh --name eagleharbor-api --resource-group eagleharbor
   
   # Check main.py CORS settings
   cat /home/site/wwwroot/app/main.py | grep -A 10 "CORS"
   ```

### If frontend still has `/api/api/` paths:

1. Check environment variable is set:
   ```powershell
   az staticwebapp appsettings list --name calm-moss-0bea6ad10
   ```

2. Force redeploy frontend:
   ```powershell
   cd frontend
   npm run build
   # Trigger GitHub Actions or manual deploy
   ```

### If AI chat doesn't work after fixing CORS:

1. Check Azure OpenAI configuration:
   ```powershell
   az webapp config appsettings list --name eagleharbor-api --resource-group eagleharbor
   ```
   
   Should show:
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_DEPLOYMENT`

2. Test AI endpoint directly:
   ```bash
   curl -X POST https://eagleharbor-api.azurewebsites.net/api/ask \
     -H "Content-Type: application/json" \
     -d '{"question":"What is CR-98-2025?"}'
   ```

## Resource Names Reference

- **Backend App Service**: `eagleharbor-api`
- **Frontend Static Web App**: `calm-moss-0bea6ad10`
- **Resource Group**: `eagleharbor`
- **Frontend URL**: `https://calm-moss-0bea6ad10.4.azurestaticapps.net`
- **Backend URL**: `https://eagleharbor-api.azurewebsites.net`

## Next Steps

1. ✅ Code fixes applied (committed to repo)
2. ⏳ Deploy backend with CORS fix
3. ⏳ Set frontend environment variable
4. ⏳ Verify all functionality works
5. ⏳ Monitor logs for any remaining issues

## Notes

- Frontend GitHub Actions may auto-deploy on push to main branch
- Backend requires manual deployment via `az webapp up` or deployment script
- Environment variables in Static Web Apps require rebuild to take effect
- CORS changes in backend take effect immediately after restart
