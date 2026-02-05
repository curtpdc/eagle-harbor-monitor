# Production Deployment Guide - Eagle Harbor Monitor

## ✅ Pre-Deployment Checklist

### 1. Code Quality & Performance
- [x] **AI Service Timeouts**: Added 30s API timeout, 45s analyze timeout, 60s Q&A timeout
- [x] **Error Handling**: Comprehensive try-catch blocks with proper HTTP status codes
- [x] **Frontend Redesign**: Professional community portal design implemented
- [x] **Chat Interface**: Enhanced UX with typing indicators, better error messages, animations
- [x] **Retry Logic**: Azure OpenAI client configured with max_retries=2
- [x] **CSS Animations**: Smooth transitions and loading states

### 2. Configuration Files

#### Frontend (Next.js)
- [x] **next.config.js**: Configured for static export (`output: 'export'`)
- [x] **staticwebapp.config.json**: Navigation fallback configured
- [x] **Environment Variables**: API_URL properly set in workflow

#### Backend (FastAPI)
- [x] **Timeout Configuration**: All async operations have timeout decorators
- [x] **Connection Pooling**: Azure OpenAI client properly configured
- [x] **Error Responses**: Graceful degradation with user-friendly messages

### 3. Azure Resources Required

#### Backend API (App Service or Container)
```bash
# Resource Group
az group create --name eagle-harbor-prod --location centralus

# App Service Plan
az appservice plan create \
  --name eagle-harbor-plan \
  --resource-group eagle-harbor-prod \
  --sku B1 \
  --is-linux

# Web App
az webapp create \
  --name eagleharbor-api \
  --resource-group eagle-harbor-prod \
  --plan eagle-harbor-plan \
  --runtime "PYTHON:3.11"
```

#### Frontend (Azure Static Web Apps)
```bash
# Create Static Web App
az staticwebapp create \
  --name eagleharbor-frontend \
  --resource-group eagle-harbor-prod \
  --location centralus \
  --source https://github.com/curtpdc/eagle-harbor-monitor \
  --branch main \
  --app-location "frontend" \
  --output-location "out" \
  --login-with-github
```

### 4. Environment Variables

#### Backend (Azure App Service)
```bash
# Set all required environment variables
az webapp config appsettings set \
  --name eagleharbor-api \
  --resource-group eagle-harbor-prod \
  --settings \
    DATABASE_URL="postgresql://..." \
    AZURE_OPENAI_API_KEY="your-key" \
    AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" \
    AZURE_COMM_CONNECTION_STRING="your-connection-string" \
    FROM_EMAIL="curtis.prince@xigusa.com" \
    APP_NAME="Eagle Harbor Data Center Monitor" \
    APP_URL="https://eagleharbormonitor.org" \
    DEBUG="False"
```

#### Frontend (GitHub Secrets)
In GitHub repository settings → Secrets and variables → Actions, add:
- `AZURE_STATIC_WEB_APPS_API_TOKEN` (from Azure Portal → Static Web App → Manage deployment token)

### 5. Database Setup

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --name eagleharbor-db \
  --resource-group eagle-harbor-prod \
  --location centralus \
  --admin-user dbadmin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --version 14

# Create database
az postgres flexible-server db create \
  --resource-group eagle-harbor-prod \
  --server-name eagleharbor-db \
  --database-name eagleharbor

# Run schema
psql -h eagleharbor-db.postgres.database.azure.com \
  -U dbadmin \
  -d eagleharbor \
  -f database/schema.sql
```

## 🚀 Deployment Steps

### Step 1: Deploy Backend API

```bash
cd backend

# Option A: Deploy via Azure CLI (recommended)
az webapp up \
  --name eagleharbor-api \
  --resource-group eagle-harbor-prod \
  --runtime "PYTHON:3.11" \
  --sku B1

# Option B: Deploy via Docker
docker build -t eagleharbor-backend:latest .
docker tag eagleharbor-backend:latest eagleharborregistry.azurecr.io/eagleharbor-backend:latest
docker push eagleharborregistry.azurecr.io/eagleharbor-backend:latest

az webapp config container set \
  --name eagleharbor-api \
  --resource-group eagle-harbor-prod \
  --docker-custom-image-name eagleharborregistry.azurecr.io/eagleharbor-backend:latest
```

### Step 2: Verify Backend

```bash
# Health check
curl https://eagleharbor-api.azurewebsites.net/health

# Test endpoints
curl https://eagleharbor-api.azurewebsites.net/api/articles
```

### Step 3: Deploy Frontend

```bash
# Push to GitHub main branch - workflow will auto-deploy
git add .
git commit -m "Production deployment with redesigned UI and performance fixes"
git push origin main

# Monitor deployment in GitHub Actions
# https://github.com/curtpdc/eagle-harbor-monitor/actions
```

### Step 4: Deploy Azure Functions (Scrapers)

```bash
cd functions

# Create Function App
az functionapp create \
  --name eagleharbor-scrapers \
  --resource-group eagle-harbor-prod \
  --consumption-plan-location centralus \
  --runtime python \
  --runtime-version 3.11 \
  --storage-account eagleharborstore \
  --functions-version 4

# Deploy functions
func azure functionapp publish eagleharbor-scrapers
```

## 🔍 Post-Deployment Testing

### 1. Frontend Tests

```bash
# Visit site
https://eagleharbormonitor.org

# Test each tab:
✓ Event Calendar loads
✓ Latest Updates displays articles
✓ Ask AI chat works (send a question)
✓ Email subscription form works
```

### 2. Backend Tests

```bash
# API health
curl https://eagleharbor-api.azurewebsites.net/health

# Articles endpoint
curl https://eagleharbor-api.azurewebsites.net/api/articles

# AI chat endpoint
curl -X POST https://eagleharbor-api.azurewebsites.net/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CR-98-2025?"}'
```

### 3. Email Tests

```bash
# Subscribe with real email
# Verify email received
# Click verification link
# Confirm welcome email received
```

### 4. Performance Tests

```bash
# Test AI timeout handling (should respond within 60s or timeout gracefully)
# Test concurrent requests (5-10 simultaneous users)
# Monitor Azure Application Insights for errors
```

## 🐛 Common Issues & Fixes

### Issue 1: Workflow Fails to Deploy

**Symptom**: GitHub Actions fails with "AZURE_STATIC_WEB_APPS_API_TOKEN not found"

**Fix**:
```bash
# Get deployment token from Azure Portal
az staticwebapp secrets list \
  --name eagleharbor-frontend \
  --resource-group eagle-harbor-prod

# Add to GitHub Secrets: Settings → Secrets → New repository secret
```

### Issue 2: Backend API Timeouts

**Symptom**: Chat interface hangs or times out

**Fix**: Already implemented!
- AI service has 30s API timeout
- Routes have 60s total timeout
- Frontend has 60s axios timeout
- Error messages guide user to try simpler questions

### Issue 3: Frontend Not Connecting to Backend

**Symptom**: "Network Error" in chat or articles not loading

**Fix**:
```bash
# Verify CORS in backend/app/main.py
# Check environment variable in workflow
env:
  NEXT_PUBLIC_API_URL: "https://eagleharbor-api.azurewebsites.net"

# Rebuild frontend
cd frontend && npm run build
```

### Issue 4: Database Connection Fails

**Symptom**: 500 errors on API calls

**Fix**:
```bash
# Check firewall rules
az postgres flexible-server firewall-rule create \
  --resource-group eagle-harbor-prod \
  --name eagleharbor-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Verify connection string format
postgresql://dbadmin:password@eagleharbor-db.postgres.database.azure.com/eagleharbor
```

## 📊 Monitoring & Maintenance

### Application Insights

```bash
# Enable Application Insights
az monitor app-insights component create \
  --app eagleharbor-insights \
  --location centralus \
  --resource-group eagle-harbor-prod

# Connect to App Service
az webapp config appsettings set \
  --name eagleharbor-api \
  --resource-group eagle-harbor-prod \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=..."
```

### Health Monitoring

Set up Azure Monitor alerts for:
- API response time > 5 seconds
- Error rate > 5%
- Database connection failures
- Function app failures

### Log Streaming

```bash
# View real-time logs
az webapp log tail \
  --name eagleharbor-api \
  --resource-group eagle-harbor-prod
```

## ✅ Final Production Checklist

- [ ] Backend API deployed and responding
- [ ] Frontend deployed to Azure Static Web Apps
- [ ] Azure Functions scrapers running on schedule
- [ ] Database schema created and accessible
- [ ] All environment variables configured
- [ ] Email service verified (send test email)
- [ ] AI chat tested (ask 3-5 questions)
- [ ] Subscription workflow tested (subscribe → verify → welcome)
- [ ] CORS properly configured
- [ ] HTTPS enabled on all endpoints
- [ ] Application Insights monitoring enabled
- [ ] Error alerts configured
- [ ] Backup strategy in place for database
- [ ] Domain name configured (if using custom domain)

## 🎉 Launch Announcement

Once all checks pass:

1. **Test with real users** (5-10 beta testers)
2. **Monitor for 24 hours** (watch for errors)
3. **Announce to community** (email, social media)
4. **Set up weekly monitoring** (review Application Insights)

---

**Need Help?**
- Check logs: `az webapp log tail --name eagleharbor-api --resource-group eagle-harbor-prod`
- Review Application Insights dashboard
- Check GitHub Actions for deployment status
- Verify Azure Static Web Apps build logs in Azure Portal
