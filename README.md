# Eagle Harbor Data Center Impact Monitor

A real-time monitoring system that tracks data center developments, policy changes, and environmental impacts in Prince George's County and Charles County, Maryland.

## Features

- 🔍 Automated scraping of government meetings, legislation, and news
- 🤖 AI-powered analysis using Claude Sonnet 4.5
- 📧 Instant email alerts for critical developments
- 💬 Public Q&A interface for community questions
- 📊 Environmental data tracking (air quality, grid capacity, water usage)
- 📱 Mobile-responsive design

## Architecture

- **Frontend**: Next.js (Azure Static Web Apps)
- **Backend**: FastAPI (Azure App Service)
- **Database**: PostgreSQL/SQLite (Azure Database for production)
- **Workers**: Azure Functions (Python)
- **Email**: SendGrid
- **AI**: Azure OpenAI (GPT-4o-mini)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Azure subscription (optional for deployment)
- Azure OpenAI access (or use existing Azure OpenAI resource)
- SendGrid API key

### Setup

1. Clone the repository
2. Set up environment variables
3. Deploy Azure infrastructure
4. Run database migrations
5. Deploy application

See `/docs/setup.md` for detailed instructions.

## Project Structure

```
eagle-harbor-monitor/
├── backend/          # FastAPI application
├── frontend/         # Next.js application
├── functions/        # Azure Functions (scrapers)
├── database/         # SQL scripts and migrations
├── docs/            # Documentation
└── infrastructure/  # Azure deployment configs
```

## License

MIT License - See LICENSE file

## Contact

For questions or contributions, please open an issue on GitHub.
