"""Apply Amendment Watchlist schema migration.

Run from the backend/ directory with venv activated:
    python setup_watchlist_schema.py

Creates the watched_matters, matter_histories, matter_attachments, and
matter_votes tables if they don't already exist.
"""

import sys
import os

# Ensure backend/ is on the import path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine
from app.config import settings
from sqlalchemy import text


# PostgreSQL syntax (production)
PG_MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS watched_matters (
    id SERIAL PRIMARY KEY,
    matter_id INTEGER UNIQUE NOT NULL,
    matter_file VARCHAR(100),
    matter_type VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    body_name VARCHAR(200),
    current_status VARCHAR(200),
    last_action_date TIMESTAMP,
    legistar_url VARCHAR(1000),
    watch_reason TEXT,
    auto_detected BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    priority VARCHAR(20) DEFAULT 'high',
    approval_path VARCHAR(100),
    qualified_definition TEXT,
    power_provisions TEXT,
    infrastructure_triggers TEXT,
    compatibility_standards TEXT,
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS matter_histories (
    id SERIAL PRIMARY KEY,
    matter_id INTEGER NOT NULL REFERENCES watched_matters(matter_id),
    legistar_history_id INTEGER UNIQUE,
    action_date TIMESTAMP,
    action_text VARCHAR(500),
    action_body VARCHAR(200),
    result VARCHAR(100),
    vote_info VARCHAR(200),
    minutes_note TEXT,
    previous_status VARCHAR(200),
    new_status VARCHAR(200),
    is_milestone BOOLEAN DEFAULT FALSE,
    notified BOOLEAN DEFAULT FALSE,
    discovered_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS matter_attachments (
    id SERIAL PRIMARY KEY,
    matter_id INTEGER NOT NULL REFERENCES watched_matters(matter_id),
    legistar_attachment_id INTEGER UNIQUE,
    name VARCHAR(500),
    hyperlink VARCHAR(1000),
    file_type VARCHAR(50),
    content_text TEXT,
    ai_summary TEXT,
    ai_analysis JSONB,
    analyzed BOOLEAN DEFAULT FALSE,
    discovered_date TIMESTAMP DEFAULT NOW(),
    notified BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS matter_votes (
    id SERIAL PRIMARY KEY,
    matter_id INTEGER NOT NULL REFERENCES watched_matters(matter_id),
    legistar_vote_id INTEGER UNIQUE,
    vote_date TIMESTAMP,
    body_name VARCHAR(200),
    result VARCHAR(100),
    tally VARCHAR(50),
    roll_call JSONB,
    notified BOOLEAN DEFAULT FALSE,
    discovered_date TIMESTAMP DEFAULT NOW()
);
"""

# SQLite syntax (local development)
SQLITE_MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS watched_matters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matter_id INTEGER UNIQUE NOT NULL,
    matter_file TEXT,
    matter_type TEXT,
    title TEXT NOT NULL,
    body_name TEXT,
    current_status TEXT,
    last_action_date TIMESTAMP,
    legistar_url TEXT,
    watch_reason TEXT,
    auto_detected INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    priority TEXT DEFAULT 'high',
    approval_path TEXT,
    qualified_definition TEXT,
    power_provisions TEXT,
    infrastructure_triggers TEXT,
    compatibility_standards TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matter_histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matter_id INTEGER NOT NULL,
    legistar_history_id INTEGER UNIQUE,
    action_date TIMESTAMP,
    action_text TEXT,
    action_body TEXT,
    result TEXT,
    vote_info TEXT,
    minutes_note TEXT,
    previous_status TEXT,
    new_status TEXT,
    is_milestone INTEGER DEFAULT 0,
    notified INTEGER DEFAULT 0,
    discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (matter_id) REFERENCES watched_matters(matter_id)
);

CREATE TABLE IF NOT EXISTS matter_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matter_id INTEGER NOT NULL,
    legistar_attachment_id INTEGER UNIQUE,
    name TEXT,
    hyperlink TEXT,
    file_type TEXT,
    content_text TEXT,
    ai_summary TEXT,
    ai_analysis TEXT,
    analyzed INTEGER DEFAULT 0,
    discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified INTEGER DEFAULT 0,
    FOREIGN KEY (matter_id) REFERENCES watched_matters(matter_id)
);

CREATE TABLE IF NOT EXISTS matter_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matter_id INTEGER NOT NULL,
    legistar_vote_id INTEGER UNIQUE,
    vote_date TIMESTAMP,
    body_name TEXT,
    result TEXT,
    tally TEXT,
    roll_call TEXT,
    notified INTEGER DEFAULT 0,
    discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (matter_id) REFERENCES watched_matters(matter_id)
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_watched_matters_matter_id ON watched_matters(matter_id);
CREATE INDEX IF NOT EXISTS idx_watched_matters_active ON watched_matters(is_active);
CREATE INDEX IF NOT EXISTS idx_matter_histories_matter_id ON matter_histories(matter_id);
CREATE INDEX IF NOT EXISTS idx_matter_histories_action_date ON matter_histories(action_date DESC);
CREATE INDEX IF NOT EXISTS idx_matter_attachments_matter_id ON matter_attachments(matter_id);
CREATE INDEX IF NOT EXISTS idx_matter_votes_matter_id ON matter_votes(matter_id);
CREATE INDEX IF NOT EXISTS idx_matter_votes_date ON matter_votes(vote_date DESC);
"""


def is_sqlite():
    db_url = str(settings.DATABASE_URL)
    return "sqlite" in db_url.lower()


def main():
    using_sqlite = is_sqlite()
    db_type = "SQLite" if using_sqlite else "PostgreSQL"
    print(f"Applying Amendment Watchlist schema migration ({db_type})...")

    migration_sql = SQLITE_MIGRATION_SQL if using_sqlite else PG_MIGRATION_SQL

    with engine.connect() as conn:
        # Execute table creation
        for statement in migration_sql.strip().split(";"):
            stmt = statement.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"  Warning: {e}")

        # Execute index creation
        for statement in INDEX_SQL.strip().split(";"):
            stmt = statement.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"  Index warning: {e}")

        conn.commit()

    print("✅ Watchlist schema migration complete!")
    print("   Tables: watched_matters, matter_histories, matter_attachments, matter_votes")


if __name__ == "__main__":
    main()
