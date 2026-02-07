# Eagle Harbor Monitor - Copilot Instructions

## Project Overview

Real-time monitoring of **data center developments in Prince George's and Charles Counties, Maryland**. Three-tier pipeline: scrape → AI-analyze → notify subscribers.

| Component | Tech | Location |
|-----------|------|----------|
| Backend API | FastAPI, Python 3.11 | `backend/app/` |
| Frontend | Next.js 16, React 19, Tailwind CSS | `frontend/src/` |
| Scrapers | Azure Functions (Timer triggers) | `functions/function_app.py` |
| HTTP wrapper | Azure Functions (wraps FastAPI) | `backend/function_app.py` |
| Database | PostgreSQL (prod) / SQLite (dev) | `database/schema.sql` |
| AI | Azure OpenAI GPT-4o-mini, api_version `2024-08-01-preview` | `backend/app/services/ai_service.py` |
| Email | Azure Communication Services | `backend/app/services/email_service.py` |

## Quick Start

```powershell
.\start-dev.ps1          # Windows: auto-setup venv, deps, starts backend(:8000) + frontend(:3000)
```

Azure services are **optional locally** — `AIService` and `EmailService` return mock/dev-mode responses when API keys are unset. See `backend/app/config.py` for all env vars.

## Critical Architecture Decisions

### Two `function_app.py` files (don't confuse them)
- **`backend/function_app.py`** — HTTP wrapper: proxies all requests to FastAPI via `starlette.testclient.TestClient`. Used for Azure Functions consumption plan hosting.
- **`functions/function_app.py`** — Background workers with its own `requirements.txt` (no FastAPI). Uses raw SQLAlchemy `db.execute()` SQL strings, not ORM models. Contains **five functions**:
  - `LegistarScraper` (timer, every 2h) — queries PG County Legistar **JSON API** for events, individual agenda items (`EventItems`), and legislation (`Matters`). Catches specific agenda items (e.g., "Qualified Data Centers — Zoning Text Amendment") even when the meeting title is generic. Only drills into event items for bodies whose name contains council/planning/zoning/environment/economic.
  - `PlanningBoardScraper` (timer, every 2h, offset 30m) — scrapes **pgplanningboard.org** (MNCPPC, a separate body from the County Council) for news articles, press releases, and meeting agendas. Covers the gap where Planning Board actions don't appear in Legistar until transmitted to the Council weeks/months later.
  - `RSSNewsScraper` (timer, every 30m) — scrapes 10 RSS feeds: Maryland Matters, WTOP, Washington Post, Patch (Bowie/Upper Marlboro/College Park), MD Dept of Environment, PG Planning Board, Data Center Knowledge, Data Center Dynamics. Also fetches full article body text via `scrape_article_content()`.
  - `ArticleAnalyzer` (timer, every 10m) — classifies unanalyzed articles using **Anthropic Claude** (not Azure OpenAI); requires `ANTHROPIC_API_KEY` env var
  - `HistoricalScan` (HTTP trigger, `GET/POST /api/historical-scan?days=180`) — one-time backfill of articles from RSS feeds

### Database schema divergence
- `database/schema.sql` uses PostgreSQL types (`SERIAL`, `TEXT[]`, GIN full-text index)
- `backend/app/models.py` uses `JSON` column type for `AlertSent.sent_to` and `article_ids` (SQLite compat: store via `json.dumps()`, read via `json.loads()`)
- When adding columns: update **both** `models.py` and `schema.sql`

### Frontend static export
`next.config.js` conditionally sets `output: 'export'` only in production (for Azure Static Web Apps). Dev server runs normally. API URL comes from `NEXT_PUBLIC_API_URL` env var (defaults to `http://localhost:8000/api`).

## Key Patterns to Follow

### AI service patterns (`backend/app/services/ai_service.py`)
- **Graceful degradation**: `self.enabled` flag; returns mock data when API key unset
- **Retry with timing**: `_call_openai_with_retry()` logs duration, retries on 429/5xx
- **Timeouts via decorator**: `@async_timeout(45)` for analysis, `@async_timeout(60)` for Q&A
- **Sync-to-async bridge**: OpenAI SDK is synchronous; wrapped in `loop.run_in_executor()`
- **Structured output**: `response_format={"type": "json_object"}` enforces JSON responses
- **Fallback analysis**: `_fallback_analysis()` uses keyword matching when AI fails silently
- Custom `AIServiceError` maps to HTTP 503; `TimeoutError` maps to 504

### Article classification schema (enforced by AI prompt)
```json
{
  "relevance_score": "0-10", "priority_score": "1-10",
  "category": "policy|meeting|legislation|environmental|community|development",
  "county": "prince_georges|charles|both|unclear",
  "summary": "...", "key_points": ["..."]
}
```

### RAG in `/api/ask` endpoint
`routes.py` builds article context by: detecting multi-word domain phrases ("eagle harbor", "planning board", etc.) → tokenizing remaining words → removing stopwords (including generic terms like "data", "center", "county") → `ILIKE` search across title/summary/content → **always backfills with recent high-priority articles** so the AI never gets zero context → passes up to 10 articles to `answer_question()`. Meeting-related keywords also pull upcoming `Event` records. The AI prompt is grounded on today's date and instructs the model to answer ONLY from provided context, never from training data.

### Email two-token system
- `verification_token` (32-char `secrets.token_urlsafe`) — sent on subscribe, consumed at `GET /api/verify/{token}`
- `unsubscribe_token` — embedded in every alert email footer (required for compliance)
- **Never send alerts to unverified subscribers** — always check `verified=True`

### Route conventions
All routes in `backend/app/api/routes.py`, mounted at `/api` prefix. DB access via `Depends(get_db)`. Pydantic schemas in `backend/app/schemas.py`. All routes are `async`.

## Domain Context (for AI prompts & article analysis)

This section provides the substantive background an AI agent needs to write accurate prompts, classify articles correctly, and answer user questions about Maryland data center policy. All AI prompts in `ai_service.py` reference these concepts.

### Legislative Tracker

| Identifier | Type | What It Does | Status Signals to Watch |
|------------|------|-------------|------------------------|
| **CR-98-2025** | County Council resolution (PG County) | Establishes a **Data Center Task Force** to study zoning, environmental, and infrastructure impacts before allowing large-scale data centers. Also called the "zoning text amendment" — proposes changes to where data centers can be built. | Committee referral → public hearing → work session → Council vote → County Executive signature/veto |
| **EO 42-2025** | Executive Order (PG County Executive) | County Executive directive on data center siting policy. May impose a **moratorium** on new data center permits pending task force findings, or set conditions/incentives. | Issued → implementation guidance → possible extension or expiration |
| **"Qualified Data Center"** | State-level designation (Maryland) | State tax incentive program: facilities meeting size/investment thresholds get expedited permitting and property/sales tax breaks. Governed by Maryland Economic Development Article. | Application → certification → annual compliance |

**Bill lifecycle in PG County**: Introduction → Committee assignment (typically Planning, Housing and Economic Development) → Public hearing (community testimony) → Committee work session → Full Council vote → County Executive signature or veto (veto overridable by supermajority).

### County Governance Structure

- **County Council** (11 districts) — Legislative authority. Passes resolutions (CR-) and bills (CB-). Controls zoning text amendments.
- **County Executive** — Executive authority. Issues executive orders (EO-), can veto Council legislation. Appoints agency heads.
- **MNCPPC (Maryland-National Capital Park and Planning Commission)** — Bi-county agency (PG + Montgomery) that manages land use planning. Its **PG County Planning Board** (5 members, appointed by County Executive) reviews development applications, conducts preliminary plan/site plan reviews, and makes recommendations on zoning changes. Meets regularly in Upper Marlboro.
- **Planning Board vs. Council**: Planning Board recommends; Council has final authority on zoning text amendments. Board can approve/deny individual site plans within existing zoning.

### Zoning Deep Dive

| Zone | Full Name | Current Use | Data Center Relevance |
|------|-----------|-------------|----------------------|
| **AR zone** | Agricultural-Residential | Low-density residential + farming | Data centers are **not currently permitted**. CR-98-2025 proposes amending this zone to allow data centers by special exception or as a permitted use — this is the core controversy. |
| **RE zone** | Rural-Estate / Residential-Estate | Large-lot residential (1–2 acre min) | Similar restrictions. Amendment would open these areas near existing power infrastructure (e.g., Chalk Point). |

**Why data centers need zoning changes**: Data centers are heavy industrial/commercial uses (power draw 20–100+ MW, backup generators, cooling systems, security fencing). They don't fit any existing PG County residential or agricultural zone by-right. Developers must either: (1) get the zoning text amended to permit them, (2) obtain a **special exception** (case-by-case approval with conditions), or (3) build only in already-zoned industrial/commercial areas (limited supply near power infrastructure).

**Special exception vs. rezoning**: Special exception keeps the base zone but allows a specific use with conditions (noise limits, setbacks, landscaping). Rezoning changes the zone designation entirely. CR-98-2025 debate centers on which path is appropriate.

### Key Sites & Why They Matter

- **Eagle Harbor** — Small, historically Black community in Charles County on the Patuxent River. Adjacent to the retired **Chalk Point Power Plant**. Contentious because data center developers target sites near existing power grid interconnects (Chalk Point has high-voltage transmission infrastructure). Community fears industrialization of a rural/residential area, environmental justice concerns given the community's demographics and history of hosting polluting facilities.
- **Chalk Point Power Plant** — Retired coal-fired generating station (PEPCO/Mirant). Attractive to data center developers because of existing grid substation capacity and transmission line access. Conversion proposals would reuse the power interconnect while bringing new industrial activity.
- **Landover Mall Site** — Former shopping center in central PG County. Large cleared parcel near highways and power. Potential data center or mixed-use redevelopment site. Less controversial than rural sites but raises traffic/infrastructure concerns.

### Historical Context & Community Opposition

PG and Charles Counties are watching what happened in **Loudoun County, Virginia** ("Data Center Alley") — rapid buildout brought tax revenue but also noise complaints, aesthetic impacts, water usage conflicts, and community backlash. Opposition groups in PG/Charles County argue:
- **Environmental justice**: Historically Black and low-income communities disproportionately hosting industrial facilities
- **Water & power**: Data centers consume enormous water for cooling and stress the local grid
- **Noise & aesthetics**: Backup diesel generators, 24/7 HVAC, security lighting incompatible with rural character
- **Property values**: Fear of declining home values near industrial operations
- **Process concerns**: Zoning changes being fast-tracked without adequate community input

### Stakeholder Map (for entity recognition in articles)

| Category | Key Entities |
|----------|-------------|
| **Government bodies** | PG County Council, PG County Executive, Charles County Commissioners, MNCPPC, PG County Planning Board, Maryland General Assembly |
| **Elected officials** | Council members (track by district), County Executive (PG), Governor of Maryland |
| **Developer interests** | Data center companies (e.g., QTS, Vantage, CloudHQ, EdgeCore), commercial real estate brokers, Maryland Chamber of Commerce |
| **Opposition groups** | Eagle Harbor community associations, environmental justice organizations, rural preservation groups, Sierra Club Maryland, Patuxent Riverkeeper |
| **Regulatory agencies** | Maryland Dept of Environment (MDE), Public Service Commission (PSC, power grid), Army Corps of Engineers (wetlands) |
| **Utilities** | PEPCO/Exelon (PG County power), SMECO (Charles County power), Washington Suburban Sanitary Commission (WSSC, water) |

### High-Priority Keywords

Defined in `settings.KEYWORDS` (`backend/app/config.py`):
```
"data center", "datacenter", "eagle harbor", "chalk point", "qualified data center",
"CR-98-2025", "Executive Order 42-2025", "Landover Mall", "zoning", "AR zone", "RE zone",
"MNCPPC", "Planning Board", "legislative amendment"
```

Additional terms the AI should flag with high relevance: "moratorium", "special exception", "zoning text amendment", "task force", "environmental justice", "Patuxent River", "PEPCO", "grid capacity", "megawatt", "cooling water".

### Q&A Scope

Answer **all Maryland data center questions** broadly (not just PG/Charles County) — including statewide legislation, other counties, Virginia comparisons, and energy/environmental policy. Use web search for topics beyond tracked articles.

## Adding Features

1. **New route**: Add to `backend/app/api/routes.py` with `Depends(get_db)`, add Pydantic schema to `schemas.py`
2. **New model/column**: Update `backend/app/models.py` AND `database/schema.sql`
3. **New AI prompt**: Modify prompt in `ai_service.py`; keep `response_format={"type": "json_object"}`
4. **New email**: Add method to `EmailService`; always include unsubscribe link in footer
5. **New scraper**: Add timer function in `functions/function_app.py`; use raw SQL inserts, not ORM

## Utility Scripts

Run from `backend/` with venv active (`python <script>.py`): `show_database.py` (view all records), `show_article.py <id>` (single article detail), `run_scrapers.py` (test scrapers locally), `analyze_articles.py` (trigger AI analysis), `manage_subscribers.py` (CLI subscriber mgmt), `extract_events.py` (pull events from articles), `test_azure_email.py` (test email sending), `test_event_api.py` (test calendar API), `seed_planning_board_data.py` (seed dev data)

## Deployment

- **Backend**: Azure App Service via `backend/Dockerfile` (Python 3.11-slim + uvicorn)
- **Frontend**: Azure Static Web Apps (static export from Next.js)
- **Scrapers**: Azure Functions (separate deployment from `functions/`)
- **Deploy scripts**: `deploy-backend.ps1`, `deploy-containerapp.ps1`, `deploy-postgresql.ps1`

