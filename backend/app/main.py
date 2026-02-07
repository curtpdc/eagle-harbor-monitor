from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.database import engine, Base
from app.config import settings
import app.models  # noqa: F401 — register all ORM models with Base
import logging

logger = logging.getLogger(__name__)

# create_all is idempotent — creates any missing tables without affecting existing ones
Base.metadata.create_all(bind=engine)

# SQLite doesn't support ALTER TABLE via create_all, so add missing columns manually
def _migrate_sqlite():
    """Add any missing columns to existing SQLite tables."""
    if "sqlite" not in str(engine.url):
        return
    import sqlite3
    db_path = str(engine.url).replace("sqlite:///", "")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Get existing columns for the articles table
        cursor.execute("PRAGMA table_info(articles)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        migrations = {
            "articles": {
                "relevance_score": "INTEGER",
                "county": "VARCHAR(100)",
                "event_date": "DATETIME",
            },
        }
        for table, columns in migrations.items():
            for col_name, col_type in columns.items():
                if col_name not in existing_cols:
                    sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    logger.info("Migration: added column %s.%s", table, col_name)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("SQLite migration check failed (non-fatal): %s", e)

_migrate_sqlite()

app = FastAPI(
    title=settings.APP_NAME,
    description="Monitor data center developments in Prince George's and Charles County, Maryland",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://calm-moss-0bea6ad10.4.azurestaticapps.net",
        "*"  # Allow all origins - tighten in production if needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
