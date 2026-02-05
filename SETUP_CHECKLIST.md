  # Eagle Harbor Monitor - Setup Checklist

Use this checklist to ensure you have everything configured before running the application.

## ✅ Prerequisites Installed

- [ ] Python 3.11+ (`python --version`)
- [ ] Node.js 18+ (`node --version` and `npm --version`)
- [ ] Git (`git --version`)
- [ ] A text editor or IDE (VS Code recommended)

## ✅ Azure OpenAI Setup

### Create/Verify Azure OpenAI Resource

- [ ] Azure subscription created
- [ ] Navigate to Azure Portal
- [ ] Create Azure OpenAI resource (or use existing)
- [ ] Go to Resource > Keys and Endpoint
- [ ] Copy the following values:

**From Azure Portal:**
```
Resource Name: _________________ (e.g., "xig-openai-resource")
Endpoint: https://[resource-name].openai.azure.com/
API Key: _________________________ (keep this SECRET!)
API Version: 2024-02-15-preview
```

### Deploy a Model

- [ ] Go to Azure OpenAI > Model deployments
- [ ] Click "+ Create new deployment"
- [ ] Select model: **gpt-4o-mini** or **gpt-4**
- [ ] Name the deployment: `gpt-4o-mini`
- [ ] Note the deployment name for config

**In .env file:**
```env
AZURE_OPENAI_ENDPOINT=https://[your-resource].openai.azure.com/
AZURE_OPENAI_API_KEY=[your-api-key-here]
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

## ✅ SendGrid Email Setup

### Create SendGrid Account

- [ ] Go to https://sendgrid.com
- [ ] Create free account (allows 100 emails/day)
- [ ] Verify email in "Sender Management"

### Get API Key

- [ ] Go to SendGrid Dashboard
- [ ] Navigate to Settings > API Keys
- [ ] Click "Create API Key"
- [ ] Name: `Eagle Harbor Monitor`
- [ ] Select "Restricted Access"
- [ ] Enable only: "Mail Send"
- [ ] Copy the API key (shows only once!)

**In .env file:**
```env
SENDGRID_API_KEY=SG.[long-string-of-characters-here]
FROM_EMAIL=[your-verified-email@domain.com]
```

### Verify Sender Email

- [ ] Go to Settings > Sender Management
- [ ] Click "Create New Sender"
- [ ] Enter your email: `alerts@example.com` or personal email
- [ ] Verify ownership by clicking link in verification email
- [ ] Use this email as `FROM_EMAIL` in .env

## ✅ Database Setup

### For Local Development (SQLite)

- [ ] Create directory: `./eagle_harbor.db` (auto-created)
- [ ] In .env file:
```env
DATABASE_URL=sqlite:///./eagle_harbor.db
```

### For Production (PostgreSQL)

- [ ] Create PostgreSQL database
- [ ] Get connection string format:
```
postgresql://username:password@host:port/database_name
```
- [ ] In .env file:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/eagle_harbor_monitor
```

## ✅ Environment Configuration

### Create .env File

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env  # or use VS Code
```

### Complete .env File

```env
# ===== CRITICAL - MUST SET =====

# Database
DATABASE_URL=sqlite:///./eagle_harbor.db

# Azure OpenAI (for AI features)
AZURE_OPENAI_ENDPOINT=https://[your-resource].openai.azure.com/
AZURE_OPENAI_API_KEY=sk-...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# SendGrid (for email)
SENDGRID_API_KEY=SG.ABC123...
FROM_EMAIL=your-verified-email@example.com

# ===== OPTIONAL - USE DEFAULTS =====

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Application
APP_NAME=Eagle Harbor Data Center Monitor
APP_URL=http://localhost:3000
DEBUG=true

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Email Settings
WEEKLY_DIGEST_DAY=4
WEEKLY_DIGEST_HOUR=15
WEEKLY_DIGEST_TIMEZONE=America/New_York

# Scraping Settings
SCRAPE_INTERVAL_HOURS=2
NEWS_SCRAPE_INTERVAL_MINUTES=30
```

### ⚠️ Security Notes

- **NEVER commit .env file** (add to .gitignore - already done)
- **NEVER share API keys** publicly
- **NEVER use admin/prod keys** in local testing
- **Rotate keys regularly** in production

## ✅ GitHub Repository

- [ ] Fork: https://github.com/curtpdc/eagle-harbor-monitor
- [ ] Clone to your machine:
```bash
git clone https://github.com/[YOUR-USERNAME]/eagle-harbor-monitor.git
cd eagle-harbor-monitor
```

## ✅ Python Dependencies

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

### Install Requirements

```bash
pip install -r requirements.txt
```

**Expected packages:**
- fastapi (web framework)
- uvicorn (server)
- sqlalchemy (database ORM)
- openai (Azure OpenAI client)
- sendgrid (email sending)
- pydantic (validation)
- And others...

## ✅ Node.js Dependencies

```bash
cd frontend
npm install
```

**Expected packages:**
- next (React framework)
- react (UI library)
- axios (HTTP client)
- tailwindcss (styling)

## ✅ Database Schema

### Apply Schema (Optional)

The database schema is auto-created by SQLAlchemy on first run, but you can manually apply it:

```bash
# SQLite
sqlite3 eagle_harbor.db < ../database/schema.sql

# PostgreSQL
psql -U username -d eagle_harbor_monitor < ../database/schema.sql
```

### Verify Schema

```bash
# SQLite
sqlite3 eagle_harbor.db
> .tables
> .schema subscribers

# PostgreSQL
psql -U username -d eagle_harbor_monitor
> \dt
> \d subscribers
```

## ✅ Run Locally

### Terminal 1: Start Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows only
python -m uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

Expected output:
```
> next dev
  ▲ Next.js 16.1.6
  ▲ Ready in 1.2s
```

### Terminal 3: (Optional) Monitor Database

```bash
# If using PostgreSQL
psql -U username -d eagle_harbor_monitor

# If using SQLite
sqlite3 eagle_harbor.db

# Then run queries:
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM subscribers;
```

## ✅ Verify It Works

### Test 1: Backend API

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "last_scrape": null
}
```

### Test 2: Frontend UI

- Open http://localhost:3000 in browser
- Should see professional landing page
- No errors in browser console (F12)

### Test 3: Email Subscription

1. Enter email in subscription form
2. Wait for email verification
3. Click verification link
4. See success page

### Test 4: Q&A Assistant

1. Click "Ask Questions" tab
2. Enter a test question
3. Get AI response with sources

### Test 5: API Documentation

- Open http://localhost:8000/docs
- Try out endpoints in Swagger UI
- Test `/api/ask` endpoint

## ❓ Troubleshooting

### Missing Module Errors

```bash
# Reinstall requirements
pip install --force-reinstall -r requirements.txt

# For frontend
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

```bash
# Use different port for backend
python -m uvicorn app.main:app --reload --port 8001

# Update frontend env:
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### Database Lock (SQLite)

```bash
# Close any open database connections
# Delete eagle_harbor.db and restart
rm eagle_harbor.db
python -m uvicorn app.main:app --reload  # Will create new DB
```

### Email Not Sending

1. Check SendGrid API key in .env
2. Verify FROM_EMAIL is verified in SendGrid
3. Check SendGrid dashboard for failures
4. Look at backend console for error messages

### AI Not Responding

1. Verify Azure OpenAI API key
2. Check Azure Portal > Cognitive Services > Usage
3. Ensure model deployment exists
4. Try manually:
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

## 📋 Checklist Summary

**Before Running:** 
- [ ] Python 3.11+, Node.js 18+
- [ ] Azure OpenAI API key & endpoint
- [ ] SendGrid API key & verified email
- [ ] .env file with all credentials
- [ ] Git repo cloned

**Before Testing:**
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Database configured
- [ ] Backend server running (port 8000)
- [ ] Frontend dev server running (port 3000)

**After Testing:**
- [ ] Subscription form works
- [ ] Email verification works
- [ ] Q&A assistant responds
- [ ] API health check passes
- [ ] Browser console has no errors
- [ ] SendGrid shows email deliveries

---

**Next Step:** Follow [QUICK_START.md](./QUICK_START.md) to test the application!
