# Local Development Setup Guide

This guide will help you run the Eagle Harbor Monitor locally on your machine.

## Prerequisites

- **Node.js 18+** - [Download](https://nodejs.org/)
- **Python 3.11+** - [Download](https://www.python.org/)
- **Git** - [Download](https://git-scm.com/)

## Quick Start (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/curtpdc/eagle-harbor-monitor.git
cd eagle-harbor-monitor
```

### Step 2: Set Up Backend (Terminal 1)

```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from template)
cp ../.env.example .env

# Edit .env and add your API keys:
# - AZURE_OPENAI_API_KEY (required for AI features)
# - SENDGRID_API_KEY (required for email alerts)
# - Other settings can use defaults for local dev

# Start the backend server
python -m uvicorn app.main:app --reload
```

The backend will start at **http://localhost:8000**

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 3: Set Up Frontend (Terminal 2)

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start at **http://localhost:3000**

You should see:
```
▲ Next.js 16.1.6 (Turbopack)
- Local:         http://localhost:3000
- Network:       http://10.x.x.x:3000

✓ Starting...
✓ Ready in 432ms
```

### Step 4: Open in Browser

Navigate to **http://localhost:3000** in your web browser.

You should see the Eagle Harbor Monitor homepage with:
- Navigation bar
- Hero section
- Email subscription form
- Latest alerts section
- AI Q&A interface

## Troubleshooting

### Issue: "localhost:3000 doesn't connect"

**Symptoms:**
- Browser shows "This site can't be reached"
- "Connection refused" error

**Solutions:**

1. **Verify the dev server is running:**
   ```bash
   # In the frontend directory, check if npm run dev is active
   # You should see "Ready in XXXms" in the console
   ```

2. **Check if port 3000 is already in use:**
   ```bash
   # On Windows:
   netstat -ano | findstr :3000
   
   # On macOS/Linux:
   lsof -i :3000
   ```
   
   If another process is using port 3000, either stop that process or run Next.js on a different port:
   ```bash
   npm run dev -- -p 3001
   ```

3. **Try accessing via 127.0.0.1 instead of localhost:**
   ```
   http://127.0.0.1:3000
   ```

4. **Clear Next.js cache:**
   ```bash
   rm -rf .next
   npm run dev
   ```

5. **Reinstall dependencies:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   npm run dev
   ```

### Issue: "Module not found" or compilation errors

**Solution:**
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

### Issue: Frontend can't connect to backend API

**Symptoms:**
- Articles don't load
- Subscription form fails
- Console shows network errors

**Solutions:**

1. **Verify backend is running:**
   - Open http://localhost:8000/docs in your browser
   - You should see the Swagger API documentation

2. **Check NEXT_PUBLIC_API_URL:**
   ```bash
   # In frontend/.env.local, verify:
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

3. **Check browser console for CORS errors:**
   - Open Developer Tools (F12)
   - Check Console tab for errors
   - CORS should be configured in backend/app/main.py

### Issue: Google Fonts warnings

**Symptoms:**
```
⚠ Error while requesting resource
Failed to download `Inter` from Google Fonts
```

**This is normal** in restricted environments. The app will use fallback fonts. The site will still work perfectly.

### Issue: Database errors

**Symptoms:**
- "Table not found" errors
- "Database connection failed"

**Solutions:**

1. **Verify DATABASE_URL in backend/.env:**
   ```
   # For local dev, SQLite is easiest:
   DATABASE_URL=sqlite:///./eagle_harbor.db
   ```

2. **Initialize database:**
   ```bash
   cd backend
   python -c "from app.database import init_db; init_db()"
   ```

### Issue: Email features don't work

**This is expected for local development** unless you've configured:
- Azure Communication Services credentials in .env
- Verified sender email address

The app will log email attempts to the console instead of actually sending them during development.

## Environment Variables Reference

### Backend (.env in backend/ directory)

Required for full functionality:
```env
# Database
DATABASE_URL=sqlite:///./eagle_harbor.db

# Azure OpenAI (for AI features)
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Email (Azure Communication Services)
AZURE_COMM_CONNECTION_STRING=your_connection_string
FROM_EMAIL=alerts@yourdomain.com

# Application
APP_URL=http://localhost:3000
DEBUG=true
```

### Frontend (.env.local in frontend/ directory)

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Testing Your Setup

### 1. Test Backend API
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

curl http://localhost:8000/api/articles
# Should return: {"articles": [...], "total": 0, "page": 1}
```

### 2. Test Frontend
- Open http://localhost:3000
- Check that the page loads with styling
- Try subscribing with an email (check backend console for logs)
- Try the AI Q&A feature (requires Azure OpenAI configured)

### 3. Test Integration
- Backend should log incoming requests:
  ```
  INFO: 127.0.0.1:XXXXX - "GET /api/articles HTTP/1.1" 200 OK
  ```
- Frontend console should show successful API calls (no errors in DevTools)

## Development Workflow

1. **Make code changes** - Changes auto-reload thanks to hot module replacement
2. **Backend changes** - Uvicorn auto-reloads when you save Python files
3. **Frontend changes** - Turbopack instantly reflects React/TypeScript changes
4. **Test in browser** - Check http://localhost:3000

## Production vs Development

### Development Mode (Current Setup)
- Next.js dev server with hot reload
- Backend points to localhost
- Detailed error messages
- Source maps enabled

### Production Mode
- Next.js exports static files (`npm run build`)
- Backend points to Azure App Service
- Optimized bundles
- Error tracking via Application Insights

## Next Steps

- Read [QUICK_START.md](../QUICK_START.md) for feature overview
- Read [COMPLETE_SETUP.md](../COMPLETE_SETUP.md) for Azure deployment
- Check [ANALYSIS_REPORT.md](../ANALYSIS_REPORT.md) for architecture details

## Getting Help

If you're still having issues:

1. Check the [GitHub Issues](https://github.com/curtpdc/eagle-harbor-monitor/issues)
2. Review error messages in:
   - Backend terminal console
   - Frontend terminal console  
   - Browser Developer Tools Console (F12)
3. Make sure you're using the required versions:
   - Node.js 18+
   - Python 3.11+

## Common Commands Reference

### Backend
```bash
# Start dev server
cd backend
python -m uvicorn app.main:app --reload

# Run scrapers manually
python run_scrapers.py

# View database
python show_database.py

# Test AI analysis
python analyze_articles.py
```

### Frontend
```bash
# Start dev server
cd frontend
npm run dev

# Build for production
npm run build

# Test production build locally
npm run build && npm run start

# Lint code
npm run lint
```
