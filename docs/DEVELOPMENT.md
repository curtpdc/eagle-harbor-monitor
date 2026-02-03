# Development Quick Start

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] PostgreSQL database accessible
- [ ] Anthropic API key obtained
- [ ] SendGrid API key obtained

## Local Development Setup

### Option 1: Automated Setup (Windows PowerShell)

```powershell
# Run the setup script
.\setup.ps1
```

### Option 2: Manual Setup

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env with your values
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

#### 3. Database Setup

```bash
cd database

# Connect to your PostgreSQL instance
psql postgresql://user:password@localhost:5432/eagle_harbor_monitor

# Run migrations
\i schema.sql
```

## Running Locally

### Start Backend (Terminal 1)

```bash
cd backend
# Make sure venv is activated
uvicorn app.main:app --reload --port 8000
```

API will be available at: http://localhost:8000

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Website will be available at: http://localhost:3000

### Test the System

1. **Visit Frontend**: Open http://localhost:3000
2. **Subscribe**: Enter your email and click Subscribe
3. **Check API**: Visit http://localhost:8000/docs for Swagger UI
4. **Test Health**: http://localhost:8000/api/health

## Environment Variables

Update `.env` with these required values:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/eagle_harbor_monitor

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
SENDGRID_API_KEY=SG....

# Email
FROM_EMAIL=alerts@yourdomain.com

# App
APP_URL=http://localhost:3000
DEBUG=true
```

## Project Structure

```
eagle-harbor-monitor/
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── main.py       # App entry point
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database connection
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── api/
│   │   │   └── routes.py # API endpoints
│   │   └── services/
│   │       ├── ai_service.py    # Claude integration
│   │       └── email_service.py # SendGrid integration
│   └── requirements.txt
│
├── frontend/             # Next.js application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx      # Home page
│   │   │   └── layout.tsx    # Root layout
│   │   └── components/
│   │       ├── EmailSubscribe.tsx
│   │       ├── LatestAlerts.tsx
│   │       └── AskQuestion.tsx
│   └── package.json
│
├── functions/           # Azure Functions (scrapers)
│   ├── function_app.py  # All functions
│   └── requirements.txt
│
├── database/           # Database schemas
│   └── schema.sql     # PostgreSQL schema
│
└── docs/              # Documentation
    └── SETUP.md      # Deployment guide
```

## Testing the Scrapers Manually

### Test RSS Scraper

```python
cd functions
python -c "
import feedparser
feed = feedparser.parse('https://www.marylandmatters.org/feed/')
for entry in feed.entries[:5]:
    print(entry.title)
"
```

### Test Legistar Scraper

```python
import requests
from bs4 import BeautifulSoup

url = 'https://princegeorgescountymd.legistar.com/Calendar.aspx'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
meetings = soup.find_all('tr', class_='rgRow')
print(f"Found {len(meetings)} meetings")
```

## Common Issues

### Database Connection Failed

```bash
# Check if PostgreSQL is running
pg_isready

# Test connection
psql postgresql://user:password@localhost:5432/eagle_harbor_monitor
```

### Backend Import Errors

```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt --force-reinstall
```

### Frontend Build Errors

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

## Next Steps

Once local development is working:

1. **Add Test Data**: Manually insert some articles in the database
2. **Test Email**: Subscribe with your email and verify emails work
3. **Test Q&A**: Ask questions to test AI integration
4. **Deploy**: Follow `docs/SETUP.md` for Azure deployment

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Support

For issues or questions:
1. Check `docs/SETUP.md` for deployment guide
2. Review logs in backend and frontend terminals
3. Check Azure Portal for cloud deployment issues
