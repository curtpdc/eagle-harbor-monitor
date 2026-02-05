# Quick Start Guide - Eagle Harbor Monitor

## 5-Minute Quick Start

### Terminal 1: Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # or: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
✅ Backend runs on: http://localhost:8000

### Terminal 2: Frontend  
```bash
cd frontend
npm install
npm run dev
```
✅ Frontend runs on: http://localhost:3000

### Terminal 3: Database Check
```bash
cd database
# Verify schema is set up (optional, auto-created on first backend run)
```

## What To Test

### 1. Open the Application
- Go to **http://localhost:3000**
- You should see the professional landing page

### 2. Test Email Subscription
```
1. Enter your email in the "Subscribe" field on the hero section
2. Click "Subscribe"
3. You should see: "Check your email to verify"
4. If using Gmail: Wait 1-2 minutes, check spam folder
5. Click the verification link in the email
6. You should see: "✅ Email Verified!" page
```

### 3. Test Q&A Assistant
```
1. Click "Ask Questions" tab
2. Try one of the example questions
3. Wait for AI response
4. You should see:
   - Your question in a blue bubble (right side)
   - AI response in gray bubble with emoji (left side)
   - Sources listed below the answer
```

### 4. Test Latest Updates
```
1. Click "Latest Updates" tab
2. If database is empty, you'll see: "No Articles Yet"
   (This is normal - scrapers populate data on schedule)
3. Click "Health Check" link to verify database connection
```

### 5. Test Unsubscribe
- In a test email, click the unsubscribe link
- You should see: "👋 Unsubscribed" confirmation

## Troubleshooting

### Error: "AZURE_OPENAI_API_KEY not set"

**Solution:**
```bash
# Windows PowerShell
$env:AZURE_OPENAI_API_KEY="your_key_here"

# Mac/Linux Bash
export AZURE_OPENAI_API_KEY="your_key_here"

# Or edit .env in the root directory
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://xig-openai-resource.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### Error: "SendGrid API Key invalid"

**Solution:**
```bash
# Check SendGrid dashboard:
# 1. Go to https://app.sendgrid.com/settings/api_keys
# 2. Verify API key is correct
# 3. Verify sender email is verified in Sender Management
# 4. Update .env:
SENDGRID_API_KEY=SG.your_actual_key_here
FROM_EMAIL=your-verified-email@example.com
```

### Error: "Module 'app' not found"

**Solution:**
```bash
# Make sure you're in the backend directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt

# Then run
python -m uvicorn app.main:app --reload
```

### Error: "Port 8000 already in use"

**Solution:**
```bash
# Use a different port
python -m uvicorn app.main:app --reload --port 8001

# Then update frontend's API_URL:
# In frontend/.env or frontend/.env.local:
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### Frontend shows "Unable to get an answer"

**Possible causes:**
1. Azure OpenAI API key not set
2. Backend not running
3. Network connectivity issue

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check API response manually
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'

# Look at browser console for errors (F12 > Console tab)
```

### No articles showing in "Latest Updates"

**This is normal on first run!**

The scrapers run on a schedule in Azure:
- **Legistar scraper**: Every 2 hours  
- **RSS scraper**: Every 30 minutes

To test manually, you can:

```bash
# Insert test article into database
sqlite3 eagle_harbor.db << 'EOF'
INSERT INTO articles (title, url, source, discovered_date, analyzed, priority_score, category, county)
VALUES (
  'Test: CR-98-2025 Data Center Task Force Meeting',
  'https://example.com/test1',
  'Test Source',
  datetime('now'),
  TRUE,
  8,
  'policy',
  'prince_georges'
);
EOF

# Then refresh the frontend
```

## Environment Configuration

### Minimal Setup (Local Dev)
```env
DATABASE_URL=sqlite:///./eagle_harbor.db
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://xig-openai-resource.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
SENDGRID_API_KEY=your_key
FROM_EMAIL=your-email@example.com
APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
DEBUG=true
```

### Production Setup
```env
DATABASE_URL=postgresql://user:pass@server:5432/eagle_harbor
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
SENDGRID_API_KEY=your_key
FROM_EMAIL=noreply@eagleharbormonitor.org
APP_URL=https://eagleharbormonitor.org
NEXT_PUBLIC_API_URL=https://api.eagleharbormonitor.org
DEBUG=false
```

## API Quick Reference

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Articles
```bash
# Get last 10 articles
curl http://localhost:8000/api/articles?limit=10

# Get by category
curl http://localhost:8000/api/articles?category=policy

# Paginate
curl http://localhost:8000/api/articles?page=2&limit=10
```

### Ask Question
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CR-98-2025?"}'
```

### Subscribe
```bash
curl -X POST http://localhost:8000/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

## File Structure for Reference

```
eagle-harbor-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── routes.py               # API endpoints
│   │   ├── models.py               # Database models
│   │   ├── database.py             # DB connection
│   │   ├── config.py               # Settings
│   │   ├── services/
│   │   │   ├── ai_service.py       # Azure OpenAI integration
│   │   │   └── email_service.py    # SendGrid integration
│   │   └── schemas.py              # Pydantic models
│   ├── requirements.txt            # Python dependencies
│   └── function_app.py             # Azure Functions wrapper
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Home page
│   │   │   ├── verify/page.tsx     # Email verification
│   │   │   └── unsubscribe/page.tsx # Unsubscribe
│   │   └── components/
│   │       ├── EmailSubscribe.tsx  # Subscription form
│   │       ├── LatestAlerts.tsx    # Articles list
│   │       └── AskQuestion.tsx     # Q&A chat
│   ├── package.json                # Node dependencies
│   └── tailwind.config.js          # Styling
├── database/
│   └── schema.sql                  # Database schema
├── functions/
│   ├── function_app.py             # Azure Functions scrapers
│   └── requirements.txt            # Python dependencies
├── .env.example                    # Environment template
└── docs/
    ├── SETUP.md                    # Installation guide
    ├── DEVELOPMENT.md              # Development tips
    └── DEPLOYMENT_STATUS.md        # Current status
```

## Next Steps

### After Basic Testing Works:

1. **Add Test Data:**
   - Manually insert articles for testing
   - Or wait for scrapers to run and populate data

2. **Deploy to Azure (Optional):**
   - Follow [COMPLETE_SETUP.md](./COMPLETE_SETUP.md)
   - Create App Service + Static Web Apps

3. **Customize:**
   - Update prompts in `ai_service.py`
   - Add more news feeds to RSS scraper
   - Customize email templates

4. **Share:**
   - Invite friends to subscribe
   - Test email alerts end-to-end
   - Get feedback on Q&A features

## Support

- **API Docs:** http://localhost:8000/docs
- **Frontend Issues:** Check browser console (F12)
- **Backend Issues:** Check terminal output for error logs
- **Email Issues:** Check SendGrid dashboard
- **AI Issues:** Verify Azure OpenAI quota isn't exceeded

---

**Status:** ✅ Ready to test locally  
**Next:** Follow testing steps above, then move to [COMPLETE_SETUP.md](./COMPLETE_SETUP.md) for deployment
