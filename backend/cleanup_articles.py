"""One-time cleanup: add relevance_score column and re-queue irrelevant articles.

Run from backend/ with venv active:
    python cleanup_articles.py

This script:
  1. Adds the relevance_score column if it doesn't exist yet
  2. Adds the event_date column if it doesn't exist yet (schema sync)
  3. Marks global-industry articles that have no Maryland keywords as
     relevance_score=0 so they're filtered from Latest Updates immediately
  4. Resets analyzed=FALSE on those articles so the improved ArticleAnalyzer
     can re-classify them with the new prompt (optional — controlled by
     RE_ANALYZE flag below)

Safe to run multiple times — all operations are idempotent.
"""

import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from sqlalchemy import text

# Set True to have the ArticleAnalyzer re-process irrelevant articles
# with the improved prompt. Set False to just hide them immediately.
RE_ANALYZE = False

MARYLAND_TERMS = [
    '%maryland%', '%prince george%', '%charles county%', '%pg county%',
    '%eagle harbor%', '%chalk point%', '%upper marlboro%', '%brandywine%',
    '%bowie%', '%college park%', '%greenbelt%', '%laurel%', '%waldorf%',
    '%mncppc%', '%pepco%', '%patuxent%', '%southern maryland%',
    '%anne arundel%', '%cr-98%', '%eo 42%', '%executive order 42%',
    '%landover%', '%indian head%', '%la plata%',
]

GLOBAL_SOURCES = [
    'Data Center Knowledge',
    'Data Center Dynamics',
]

REGIONAL_SOURCES = [
    'WTOP News',
    'Washington Post',
]


def main():
    db = SessionLocal()

    # ── 1. Add relevance_score column if missing ─────────────────────
    try:
        db.execute(text("SELECT relevance_score FROM articles LIMIT 1"))
        print("✓ relevance_score column already exists")
    except Exception:
        db.rollback()
        print("Adding relevance_score column...")
        db.execute(text("ALTER TABLE articles ADD COLUMN relevance_score INTEGER"))
        db.commit()
        print("✓ relevance_score column added")

    # ── 2. Add event_date column if missing (schema sync) ────────────
    try:
        db.execute(text("SELECT event_date FROM articles LIMIT 1"))
        print("✓ event_date column already exists")
    except Exception:
        db.rollback()
        print("Adding event_date column...")
        db.execute(text("ALTER TABLE articles ADD COLUMN event_date TIMESTAMP"))
        db.commit()
        print("✓ event_date column added")

    # ── 3. Add index on relevance_score if missing ───────────────────
    try:
        db.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_articles_relevance ON articles(relevance_score DESC)"
        ))
        db.commit()
        print("✓ relevance_score index ensured")
    except Exception:
        db.rollback()
        print("  (relevance_score index may already exist)")

    # ── 4. Mark non-Maryland articles from global/regional sources ───
    all_sources = GLOBAL_SOURCES + REGIONAL_SOURCES
    for source in all_sources:
        # Build a NOT (title ILIKE ... OR content ILIKE ...) condition for each MD term
        md_conditions = " AND ".join(
            f"(LOWER(COALESCE(title,'')) NOT LIKE '{term}' AND LOWER(COALESCE(content,'')) NOT LIKE '{term}' AND LOWER(COALESCE(summary,'')) NOT LIKE '{term}')"
            for term in MARYLAND_TERMS
        )

        if RE_ANALYZE:
            sql = f"""
                UPDATE articles
                SET relevance_score = 0, analyzed = FALSE
                WHERE source = :source
                  AND ({md_conditions})
            """
        else:
            sql = f"""
                UPDATE articles
                SET relevance_score = 0
                WHERE source = :source
                  AND ({md_conditions})
            """

        result = db.execute(text(sql), {"source": source})
        count = result.rowcount
        action = "marked relevance=0 + reset for re-analysis" if RE_ANALYZE else "marked relevance=0"
        print(f"  {source}: {count} articles {action}")

    db.commit()

    # ── 5. Summary ───────────────────────────────────────────────────
    total = db.execute(text("SELECT COUNT(*) FROM articles")).scalar()
    analyzed = db.execute(text("SELECT COUNT(*) FROM articles WHERE analyzed = TRUE")).scalar()
    has_relevance = db.execute(text("SELECT COUNT(*) FROM articles WHERE relevance_score IS NOT NULL")).scalar()
    low_relevance = db.execute(text("SELECT COUNT(*) FROM articles WHERE relevance_score <= 3")).scalar()
    high_relevance = db.execute(text("SELECT COUNT(*) FROM articles WHERE relevance_score >= 4")).scalar()
    null_relevance = db.execute(text("SELECT COUNT(*) FROM articles WHERE relevance_score IS NULL")).scalar()

    print(f"\n=== DATABASE SUMMARY ===")
    print(f"Total articles:        {total}")
    print(f"Analyzed:              {analyzed}")
    print(f"With relevance score:  {has_relevance}")
    print(f"  High relevance (≥4): {high_relevance}")
    print(f"  Low relevance (≤3):  {low_relevance}")
    print(f"  Not yet scored:      {null_relevance}")
    print(f"\nArticles with NULL relevance_score will still appear in Latest Updates")
    print(f"until the ArticleAnalyzer re-processes them with the new prompt.")

    db.close()
    print("\n✓ Cleanup complete")


if __name__ == "__main__":
    main()
