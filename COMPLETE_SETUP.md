# Complete Setup & Deployment Guide

This guide will walk you through setting up and running the Eagle Harbor Data Center Monitor from scratch.

## Prerequisites

- Python 3.11+ 
- Node.js 18+
- PostgreSQL (or use SQLite for local dev)
- Azure Subscription (optional, for cloud deployment)
- Azure OpenAI API Key
- SendGrid API Key

## Step 1: Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/curtpdc/eagle-harbor-monitor.git
cd eagle-harbor-monitor

# Copy environment file and fill in your credentials
cp .env.example .env
```

## Step 2: Setup Backend

### Create Virtual Environment

```bash
cd backend

# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Edit the `.env` file in the root directory with:

```env
# Database (use SQLite for local dev, PostgreSQL for production)
DATABASE_URL=sqlite:///./eagle_harbor.db

# Azure OpenAI (required for AI features)
AZURE_OPENAI_ENDPOINT=https://xig-openai-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# SendGrid (required for email alerts)
SENDGRID_API_KEY=your_key_here
FROM_EMAIL=your-verified-sender@example.com

# Application
APP_URL=http://localhost:3000
APP_PORT=8000
APP_RELOAD=true

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Initialize Database

For SQLite (local development):
```bash
# The database will be auto-created on first run
# But you can manually apply the schema:
cd ../database
sqlite3 eagle_harbor.db < schema.sql
```

For PostgreSQL:
```bash
# Create database
createdb eagle_harbor_monitor

# Apply schema
psql eagle_harbor_monitor < schema.sql

# Update .env:
DATABASE_URL=postgresql://user:password@localhost:5432/eagle_harbor_monitor
```

### Run Backend

```bash
cd ../backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**
API Docs: **http://localhost:8000/docs**

## Step 3: Setup Frontend

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

## Step 4: Test the Application

### Test Subscription

```bash
# Open http://localhost:3000 in your browser
# Submit your email to the subscription form
# Check your email for verification link
# Click verification link to activate subscription
```

### Test Q&A Assistant

```bash
# Navigate to "Ask Questions" tab
# Try one of the example questions
# You should get an AI-powered response
```

### Test API Endpoints

```bash
# Get health status
curl http://localhost:8000/health

# Get articles
curl http://localhost:8000/api/articles

# Ask a question
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CR-98-2025?"}'
```

## Step 5: Configure Azure Functions (Scrapers)

The scrapers automatically run on schedule in Azure. For local testing:

### Install Azure Functions Core Tools

```bash
# Windows
choco install azure-functions-core-tools-4

# Mac
brew tap azure/azure
brew install azure-functions-core-tools@4

# Linux
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/
wget -q https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

### Run Functions Locally

```bash
cd functions
func start
```

This will simulate the scheduled scrapers running locally.

## Step 6: Verify Everything Works

### Checklist

- [ ] Backend running at http://localhost:8000
- [ ] Frontend running at http://localhost:3000
- [ ] Can view Swagger API docs at http://localhost:8000/docs
- [ ] Can subscribe with email
- [ ] Can receive verification email (check SendGrid dashboard if issues)
- [ ] Can ask questions and get AI responses
- [ ] Can view articles in "Latest Updates" tab
- [ ] Health check passes: `curl http://localhost:8000/health`

### Common Issues

**Error: "AZURE_OPENAI_API_KEY not set"**
- Ensure .env file is in root directory
- Check that all Azure OpenAI variables are set correctly
- Verify API key has appropriate permissions

**Error: "SendGrid API Key invalid"**
- Check SendGrid dashboard that API key is correct
- Verify the FROM_EMAIL address is verified in SendGrid
- Check that email verification is enabled

**Error: "Database connection failed"**
- For SQLite: Ensure database directory is writable
- For PostgreSQL: Verify connection string and that server is running
- Check that DATABASE_URL in .env is correct

**No articles showing**
- This is normal on first run
- Azure Functions scrapers need to run (every 2 hours for Legistar, every 30 min for RSS)
- For local testing, you can manually insert test articles into the database

## Deployment to Azure

### Deploy Backend to Azure App Service

```bash
# Login to Azure
az login

# Create resource group
az group create --name eagle-harbor-rg --location eastus

# Create App Service plan
az appservice plan create --name eagle-harbor-plan --resource-group eagle-harbor-rg --sku B2

# Create app
az webapp create --resource-group eagle-harbor-rg --plan eagle-harbor-plan --name eagle-harbor-api --runtime "PYTHON|3.11"

# Deploy code
cd backend
az webapp deployment source config-zip --resource-group eagle-harbor-rg --name eagle-harbor-api --src <zip-file>

# Set environment variables
az webapp config appsettings set --resource-group eagle-harbor-rg --name eagle-harbor-api \
  --settings \
  DATABASE_URL="postgresql://..." \
  AZURE_OPENAI_API_KEY="..." \
  SENDGRID_API_KEY="..." \
  FROM_EMAIL="..."
```

### Deploy Frontend to Azure Static Web Apps

```bash
# Build frontend
cd frontend
npm run build

# Deploy to Static Web Apps
# (Follow Azure portal instructions for connecting your GitHub repo)
```

### Deploy Azure Functions

```bash
cd functions
func azure functionapp publish eagle-harbor-functions
```

## Monitoring & Maintenance

### Check Logs

**Backend Logs:**
```bash
# Azure App Service
az webapp log tail --name eagle-harbor-api --resource-group eagle-harbor-rg
```

**Function Logs:**
```bash
# Azure Functions
az functionapp logs streaming start --resource-group eagle-harbor-rg --name eagle-harbor-functions
```

### Database Backups

```bash
# PostgreSQL
pg_dump eagle_harbor_monitor > backup.sql

# SQLite
cp eagle_harbor.db eagle_harbor.db.backup
```

### Monitor SendGrid

- Visit https://app.sendgrid.com/statistics
- Check bounce rates
- Monitor email delivery

### Monitor Azure OpenAI

- Check Azure Portal > Cognitive Services > Usage + quotas
- Monitor token usage
- Set alerts for quota approaching

## Support & Resources

- Eagle Harbor Monitor Issues: https://github.com/curtpdc/eagle-harbor-monitor/issues
- Azure OpenAI Docs: https://learn.microsoft.com/en-us/azure/cognitive-services/openai/
- SendGrid Docs: https://docs.sendgrid.com/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Next.js Docs: https://nextjs.org/docs

## Next Steps

After successful setup:

1. **Import real data**: Run Azure Functions to scrape government sources
2. **Test email alerts**: Configure subscribers and trigger alerts
3. **Monitor performance**: Set up Azure Monitor dashboards
4. **Customize**: Update prompts, styles, and features as needed
5. **Share**: Invite community members to subscribe and participate
