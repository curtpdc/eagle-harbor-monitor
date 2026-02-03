# Eagle Harbor Data Center Monitor - Setup Guide

## Prerequisites

- Azure subscription
- Python 3.11+
- Node.js 18+
- PostgreSQL (or use Azure PostgreSQL)
- Anthropic API key
- SendGrid API key

## Step 1: Azure Infrastructure Setup

### 1.1 Create PostgreSQL Database

```bash
# Create Azure PostgreSQL Flexible Server
az postgres flexible-server create \
  --name eagle-harbor-db \
  --resource-group xigusa-rg \
  --location eastus \
  --admin-user adminuser \
  --admin-password <YourPassword> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15

# Create database
az postgres flexible-server db create \
  --resource-group xigusa-rg \
  --server-name eagle-harbor-db \
  --database-name eagle_harbor_monitor

# Allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group xigusa-rg \
  --name eagle-harbor-db \
  --rule-name AllowAzure \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 1.2 Run Database Migrations

```bash
cd database
psql "postgresql://adminuser@eagle-harbor-db:password@eagle-harbor-db.postgres.database.azure.com:5432/eagle_harbor_monitor?sslmode=require" -f schema.sql
```

### 1.3 Create Storage Account (for documents)

```bash
az storage account create \
  --name eagleharbordata \
  --resource-group xigusa-rg \
  --location eastus \
  --sku Standard_LRS

az storage container create \
  --name documents \
  --account-name eagleharbordata
```

## Step 2: Backend Deployment

### 2.1 Configure Environment Variables

Create `.env` file in `backend/`:

```env
DATABASE_URL=postgresql://adminuser:password@eagle-harbor-db.postgres.database.azure.com:5432/eagle_harbor_monitor?sslmode=require
ANTHROPIC_API_KEY=your_key_here
SENDGRID_API_KEY=your_key_here
FROM_EMAIL=alerts@eagleharbormonitor.org
APP_URL=https://eagleharbormonitor.org
```

### 2.2 Deploy to Azure App Service

```bash
cd backend

# Create requirements.txt is already present
pip install -r requirements.txt

# Deploy to existing App Service
az webapp up \
  --resource-group xigusa-webapp \
  --name eagle-harbor-api \
  --runtime "PYTHON:3.11" \
  --sku B1

# Configure environment variables
az webapp config appsettings set \
  --resource-group xigusa-webapp \
  --name eagle-harbor-api \
  --settings DATABASE_URL="postgresql://..." \
             ANTHROPIC_API_KEY="..." \
             SENDGRID_API_KEY="..."
```

## Step 3: Azure Functions Deployment

### 3.1 Create Function App

```bash
az functionapp create \
  --resource-group xigusa-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name eagle-harbor-functions \
  --storage-account eagleharbordata
```

### 3.2 Deploy Functions

```bash
cd functions

# Install dependencies locally
pip install -r requirements.txt

# Deploy
func azure functionapp publish eagle-harbor-functions

# Configure environment variables
az functionapp config appsettings set \
  --resource-group xigusa-rg \
  --name eagle-harbor-functions \
  --settings DATABASE_URL="postgresql://..." \
             ANTHROPIC_API_KEY="..."
```

## Step 4: Frontend Deployment

### 4.1 Create Static Web App

```bash
# Using Azure Portal or CLI
az staticwebapp create \
  --name eagle-harbor-monitor \
  --resource-group xigusa-rg \
  --location eastus2 \
  --source https://github.com/yourusername/eagle-harbor-monitor \
  --branch main \
  --app-location "/frontend" \
  --api-location "" \
  --output-location "out"
```

### 4.2 Build and Deploy Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build
npm run build

# Deploy (automated via GitHub Actions or manual)
# The Static Web App will auto-deploy from your GitHub repo
```

## Step 5: Configure Custom Domain (Optional)

```bash
# Add custom domain to Static Web App
az staticwebapp hostname set \
  --name eagle-harbor-monitor \
  --hostname www.eagleharbormonitor.org
```

## Step 6: Testing

### 6.1 Test Backend API

```bash
# Health check
curl https://eagle-harbor-api.azurewebsites.net/api/health

# Subscribe
curl -X POST https://eagle-harbor-api.azurewebsites.net/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

### 6.2 Test Functions

```bash
# Check function logs
az functionapp log tail \
  --name eagle-harbor-functions \
  --resource-group xigusa-rg
```

## Step 7: Monitoring

### 7.1 Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app eagle-harbor-insights \
  --location eastus \
  --resource-group xigusa-rg

# Link to App Service
az webapp config appsettings set \
  --resource-group xigusa-webapp \
  --name eagle-harbor-api \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="..."
```

## Costs Summary

- PostgreSQL B1ms: ~$12/month
- App Service B1: ~$13/month (use existing)
- Function App (Consumption): ~$5/month
- Storage Account: ~$2/month
- Static Web App: FREE
- **Total Azure: ~$32/month**

Plus external services:
- Anthropic API: ~$50-100/month
- SendGrid: FREE (up to 100 emails/day)

## Troubleshooting

### Database Connection Issues
```bash
# Test connection
psql "postgresql://adminuser@eagle-harbor-db:password@eagle-harbor-db.postgres.database.azure.com:5432/eagle_harbor_monitor?sslmode=require"
```

### Function Not Running
```bash
# Check logs
az functionapp log tail --name eagle-harbor-functions --resource-group xigusa-rg

# Restart function app
az functionapp restart --name eagle-harbor-functions --resource-group xigusa-rg
```

### API Not Responding
```bash
# Check App Service logs
az webapp log tail --name eagle-harbor-api --resource-group xigusa-webapp
```

## Next Steps

1. Obtain API keys from Anthropic and SendGrid
2. Configure DNS for custom domain
3. Set up GitHub Actions for CI/CD
4. Invite beta testers
5. Monitor system performance
