# Eagle Harbor Monitor - AI Agent Instructions

## Project Overview

A real-time monitoring system tracking **data center developments in Prince George's and Charles Counties, Maryland** using:
- **Backend**: FastAPI (Azure App Service)
- **Frontend**: Next.js + React (Azure Static Web Apps)
- **Workers**: Azure Functions (Python scrapers)
- **Database**: PostgreSQL/SQLite
- **AI**: Azure OpenAI (GPT-4o-mini via `AzureOpenAI` client)
- **Notifications**: Azure Communication Services email

## Agent Scope & Capabilities

**Primary Focus**: Monitor and analyze data center developments in Prince George's and Charles Counties, Maryland.

**Question Handling**:
- ✅ **Answer ALL Maryland data center questions**, including:
  - General Maryland data center industry trends and policies
  - Statewide data center legislation and regulations
  - Data centers in other Maryland counties (Montgomery, Anne Arundel, Baltimore, etc.)
  - Maryland energy infrastructure, power grid, and utility providers
  - State-level environmental impact assessments and requirements
  - Comparative analysis with other states (Virginia, Northern Virginia data center alley, etc.)
- ✅ **Prioritize tracking-specific content** (CR-98-2025, Eagle Harbor, Chalk Point) in article analysis
- ✅ **Use web search** when answering broader Maryland data center questions beyond project-specific tracking
- ❌ **Do NOT refuse** questions about Maryland data centers just because they're outside Prince George's/Charles Counties

## Maryland-Specific Domain Context

### Counties & Jurisdictions
- **Prince George's County (PG County)** - Primary focus; home to Chalk Point Power Plant, Landover Mall site, planned data center zones
- **Charles County** - Secondary focus; potential data center expansion zones
- **Key Planning Bodies**: Maryland-National Capital Park and Planning Commission (MNCPPC), County Planning Board, County Executive

### Critical Legislation & Initiatives
- **Executive Order 42-2025** - State initiative requiring evaluation of data center zoning and environmental impact
- **CR-98-2025** - County resolution establishing Data Center Task Force and impact assessment
- **Zoning Classifications**:
  - **AR Zone** - Agricultural/Rural zone (being studied for data center qualification)
  - **RE Zone** - Residential Estate zone (restricted for large facilities)
  - **Planned Community** zones (potential sites near existing infrastructure)

### Key Sites & Facilities
- **Chalk Point Power Plant** - Retired coal facility; potential data center conversion site
- **Landover Mall Site** - Major redevelopment opportunity in central PG County
- **Qualified Data Center** - State designation allowing expedited permitting and tax incentives

### Environmental & Community Concerns
- Grid capacity and power infrastructure (Chalk Point proximity to grid interconnects)
- Water usage and discharge impacts
- Heat island effects and air quality
- Community opposition from residential areas
- Traffic and infrastructure strain

### Important Keywords for Article Analysis
Always flag articles mentioning: "CR-98-2025", "EO 42-2025", "Eagle Harbor", "Chalk Point", "Landover", "qualified data center", "AR zone", "RE zone", "MNCPPC", "Planning Board", "zoning", "task force", "data center amendment"

## Architecture & Key Patterns

### Three-Tier Processing Pipeline

1. **Scraping/Discovery** (Azure Functions) → Articles discovered from government sources
2. **Analysis** (FastAPI AI Service) → `AIService.analyze_article()` classifies by relevance, priority (1-10), and category (policy/meeting/legislation/environmental/community)
3. **Notifications** (EmailService + Subscriber DB) → Verified subscribers receive alerts

### Critical Files to Understand Multi-Component Flows

- [backend/app/main.py](backend/app/main.py) - FastAPI app setup, CORS, router mounting
- [backend/app/api/routes.py](backend/app/api/routes.py) - Email verification/subscription workflow (unsubscribe/verification tokens are critical)
- [backend/app/services/ai_service.py](backend/app/services/ai_service.py) - Azure OpenAI integration with domain-specific prompts for Maryland data center policy
- [backend/app/models.py](backend/app/models.py) - Data schema: `Subscriber` (verified state), `Article` (priority/category/county classification), `AlertSent` (JSON arrays for SQLite compatibility)

### Azure Functions Architecture

**Critical: Two Separate `function_app.py` Files**:
- [backend/function_app.py](backend/function_app.py) - HTTP wrapper for FastAPI deployment on Azure Functions (converts Azure HttpRequest to ASGI via `TestClient`)
- [functions/function_app.py](functions/function_app.py) - Scheduled scrapers (LegistarScraper, RSSNewsScraper)

**Backend Function App** (HTTP trigger):
- Wraps entire FastAPI app for Azure Functions hosting
- Routes all `/api/{*route}` paths through FastAPI via TestClient
- Handles GET/POST/PUT/DELETE methods
- Critical for Azure Functions consumption plan deployment

**Functions App** (Timer triggers):
- `LegistarScraper`: Cron `0 0 */2 * * *` (every 2 hours) - government meeting calendars
- `RSSNewsScraper`: Cron `0 */30 * * * *` (every 30 min) - news feeds
- Direct SQLAlchemy DB access (no FastAPI dependency)

## Essential Workflows & Commands

### Local Development (Backend)

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload      # Runs on http://localhost:8000
```

### Frontend Dev

```bash
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

### Database Setup

Schema in [database/schema.sql](database/schema.sql) defines critical indices on `email`, `discovered_date`, `priority_score` for efficient queries.

### Environment Variables (see [backend/app/config.py](backend/app/config.py))

- `DATABASE_URL` - SQLite/PostgreSQL connection string
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` - GPT-4o-mini configuration
- `AZURE_COMM_CONNECTION_STRING`, `FROM_EMAIL` - Azure Communication Services email credentials

## Developer Workflows & Debugging

### Running Tests
Currently no automated test suite. To manually test:

```bash
# Test backend API locally
cd backend
uvicorn app.main:app --reload --port 8001

# Test endpoints in browser/Postman
GET http://localhost:8001/docs          # Swagger UI
POST http://localhost:8001/api/subscribe
GET http://localhost:8001/api/articles
```

### Utility Scripts for Development
Backend includes several utility scripts in `backend/` for common tasks:
- `show_database.py` - Display all DB records (subscribers, articles, events)
- `show_article.py <id>` - View specific article details
- `manage_subscribers.py` - CLI for subscriber management
- `analyze_articles.py` - Manually trigger AI analysis on unanalyzed articles
- `run_scrapers.py` - Test scrapers locally without Azure Functions
- `test_azure_email.py` - Verify Azure Communication Services email sending
- `test_event_api.py` - Test event/calendar endpoints

Run with activated venv: `python show_database.py`

### Scraper Debugging (Azure Functions)

Functions run on schedules defined in [functions/function_app.py](functions/function_app.py):
- **LegistarScraper** - Every 2 hours (meetings & legislation)
- **RSSNewsScraper** - Every 30 minutes (news feeds)
- Each logs to Azure Function App Logs (`logging.info()`, `logging.error()`)

To test locally:
```bash
# Install Azure Functions Core Tools
func start

# Monitor logs in Azure Portal: Functions > Monitor tab
```

### EmailService Debugging

Test email sending with verified Azure Communication Services account:

```python
# Quick test in Python REPL
from app.services.email_service import EmailService
from app.config import settings

email_service = EmailService()
await email_service.send_verification_email("test@example.com", "test_token_123")
```

Check Azure Portal > Communication Services for delivery status and bounce events. Sender address must be verified domain.

### AI Analysis Debugging

The `AIService.analyze_article()` can fail silently with fallback analysis. To debug:

```python
# In routes.py, temporarily modify analyze_article call
analysis = await ai_service.analyze_article(article_data)
print(f"DEBUG: AI Response = {analysis}")  # Log raw response before JSON parsing
```

Monitor Azure OpenAI API quota and errors in Azure Portal > Cognitive Services > Usage + quotas.

## Project-Specific Patterns

### 1. Event/Calendar Feature (In Development)

The `Event` model in [backend/app/models.py](backend/app/models.py) supports upcoming events tracking:
- `event_date`, `event_type` (meeting/deadline/hearing/vote/protest)
- `is_recurring`, `recurrence_rule` - For regular meetings (e.g., "Every 2nd Thursday")
- `article_id` foreign key - Links events to source articles
- Backend scripts: `extract_events.py`, `test_event_api.py`
- Frontend component: [frontend/src/components/EventCalendar.tsx](frontend/src/components/EventCalendar.tsx)

AI can extract event dates from article content when analyzing. See [docs/CALENDAR_IMPLEMENTATION.md](docs/CALENDAR_IMPLEMENTATION.md) for implementation plan.

### 2. EmailService Integration Patterns

See [backend/app/services/email_service.py](backend/app/services/email_service.py) for three core methods:

**Verification Email** (`send_verification_email()`):
- Called during `subscribe()` route
- Contains one-time verification link with token
- HTML template with branded header
- Token expires only when email is verified via GET `/verify/{token}`

**Welcome Email** (`send_welcome_email()`):
- Sent after email verification succeeds
- Contains unsubscribe link with unsubscribe_token
- Lists alert features (Instant Alerts, Weekly Digest, News Updates)
- Establishes baseline communication expectations

**Instant Alert** (`send_instant_alert()`):
- Batched send to multiple subscribers (Azure Communication Services limits apply)
- Uses article priority_score to determine subject urgency (🚨 URGENT)
- Embeds unsubscribe link in footer (CRITICAL for email compliance)
- Fallback: If sending fails, logs error but doesn't crash route

**Azure Communication Services Configuration**:
- Sender verified in Azure Portal: `FROM_EMAIL` from config
- Domain authentication required for production (DKIM/SPF)
- Monitor delivery status in Azure Portal > Communication Services > Email logs

### 3. Scraper & Data Flow Patterns

Scrapers in [functions/function_app.py](functions/function_app.py) follow standard ETL:
- **Extract**: `LegistarScraper` (Legistar API), `RSSNewsScraper` (RSS feeds)
- **Filter**: Check article against keywords and existing URLs to avoid duplicates
- **Load**: Insert into `articles` table with `analyzed=False` flag
- **Transform**: AI service later calls `analyze_article()` and updates `priority_score`, `category`, `county`

Logging pattern:
```python
logging.info(f'Scraper started')  # Start marker
logging.info(f'New article: {title}')  # Per-article tracking
logging.error(f'Error processing: {e}')  # Failure tracking
logging.info(f'Scraper completed. New articles: {count}')  # Summary
```

Check Azure Functions Monitor tab for these logs after each scheduled run.

### 4. Email Verification Workflow

Two-token system in `Subscriber` model:
- `verification_token` (32-char URL-safe) - Emailed to new subscribers
- `unsubscribe_token` (32-char URL-safe) - Embedded in all alert emails
- Only verified subscribers receive alerts (`verified=True` check before sending)

### 5. Article Classification

AI service returns JSON with exact keys (enforced via prompt):
```python
{
  "relevance_score": 0-10,
  "priority_score": 1-10,
  "category": "policy|meeting|legislation|environmental|community|development",
  "county": "prince_georges|charles|both|unclear",
  "summary": "...",
  "key_points": [...]
}
```

Domain keywords in [backend/app/config.py](backend/app/config.py) include: "CR-98-2025", "EO 42-2025", "Eagle Harbor", "Chalk Point", "AR zone", "RE zone", "Landover Mall".

### 6. SQLite JSON Arrays

In [backend/app/models.py](backend/app/models.py), `AlertSent.sent_to` and `article_ids` use JSON type for SQLite compatibility—store as `json.dumps()` list.

### 7. Async/Await Patterns

- `subscribe()`, `verify_email()`, `unsubscribe()` routes are `async`
- EmailService methods like `send_verification_email()` are `async` 
- AI analysis calls `await` (though service is synchronous)

## New Feature Additions

When adding features:

1. **New Routes**: Add to [backend/app/api/routes.py](backend/app/api/routes.py), include FastAPI `Depends(get_db)` for DB access
2. **New AI Analysis**: Modify `AIService.analyze_article()` prompt template in [backend/app/services/ai_service.py](backend/app/services/ai_service.py); response_format enforces JSON
3. **New Data Fields**: Update [backend/app/models.py](backend/app/models.py) SQLAlchemy models AND [database/schema.sql](database/schema.sql); run migrations
4. **Email Templates**: Update `EmailService` in [backend/app/services/email_service.py](backend/app/services/email_service.py)

## Common Pitfalls to Avoid

- **Subscriber verification**: Don't skip `verified=True` check before sending alerts
- **JSON in SQLite**: Use `json.dumps(list)` for storage, `json.loads()` for retrieval
- **Azure OpenAI API version**: Fixed at `2024-02-15-preview`—update model version in config if needed
- **CORS**: Configured permissively (`allow_origins=["*"]`) for development; tighten for production
- **Async context**: EmailService and AI calls are async; routes must await them

## Deployment

- Backend: Azure App Service (via [backend/Dockerfile](backend/Dockerfile))
- Frontend: Azure Static Web Apps via Next.js build
- Functions: Azure Functions (Python) for web scrapers
- Database: Azure Database for PostgreSQL (or local SQLite for dev)

See [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) and [docs/SETUP.md](docs/SETUP.md) for detailed deploy procedures.

