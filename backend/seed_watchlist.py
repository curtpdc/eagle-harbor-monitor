"""Seed the Amendment Watchlist with initial tracked items.

Uses SQLAlchemy ORM models directly to avoid column-name mismatches.
Run from backend/ with venv activated:
    python seed_watchlist.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
from app.database import engine, Base, SessionLocal
from app.models import WatchedMatter, MatterHistory


def seed():
    # Ensure tables exist from ORM models (idempotent)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Items to seed — matter_id must be integer (use 900000+ for manually tracked)
    items = [
        {
            "matter_id": 900001,
            "matter_file": "ZTA-2026-001",
            "matter_type": "Zoning Text Amendment",
            "title": "Zoning Text Amendment - Qualified Data Centers in AR and RE Zones",
            "body_name": "Prince George's County Planning Board",
            "current_status": "Initiated by Planning Board",
            "last_action_date": datetime(2026, 1, 29, tzinfo=timezone.utc),
            "watch_reason": (
                "CRITICAL: Jan 29, 2026 Planning Board vote (3-0) formally initiated amendment "
                "to amend the Principal Use Table to permit qualified data centers in "
                "Agricultural Residential (AR) and Residential Estate (RE) zones. "
                "Track draft amendment language for: (1) approval path (by right vs special exception), "
                "(2) definition of 'qualified', (3) on-site power provisions, "
                "(4) infrastructure triggers, (5) compatibility standards."
            ),
            "auto_detected": False,
            "is_active": True,
            "priority": "high",
        },
        {
            "matter_id": 900002,
            "matter_file": "CR-98-2025",
            "matter_type": "Council Resolution",
            "title": "CR-98-2025 - Data Center Task Force and Impact Assessment",
            "body_name": "Prince George's County Council",
            "current_status": "Active - Task Force Convened",
            "last_action_date": datetime(2025, 6, 15, tzinfo=timezone.utc),
            "watch_reason": (
                "County resolution establishing a Data Center Task Force to study "
                "the impact of data center development in PG County. "
                "Companion to ZTA amendment. Task Force findings should inform "
                "the zoning text amendment language."
            ),
            "auto_detected": False,
            "is_active": True,
            "priority": "high",
        },
        {
            "matter_id": 900003,
            "matter_file": "EO-42-2025",
            "matter_type": "Executive Order",
            "title": "Executive Order 42-2025 - State Data Center Zoning and Environmental Evaluation",
            "body_name": "State of Maryland - Governor's Office",
            "current_status": "Active - State Implementation",
            "last_action_date": datetime(2025, 3, 1, tzinfo=timezone.utc),
            "watch_reason": (
                "State-level executive order requiring evaluation of data center zoning "
                "and environmental impact across Maryland. Sets framework for county-level policy."
            ),
            "auto_detected": False,
            "is_active": True,
            "priority": "high",
        },
        {
            "matter_id": 900004,
            "matter_file": "CHALK-POINT",
            "matter_type": "Development Project",
            "title": "Chalk Point Power Plant - Data Center Conversion/Redevelopment",
            "body_name": "Prince George's County Planning Board",
            "current_status": "Pre-Application / Monitoring",
            "last_action_date": None,
            "watch_reason": (
                "Tracking potential conversion of the retired Chalk Point coal-fired power plant "
                "site in Eagle Harbor for data center use. ZTA-2026-001 would directly enable "
                "this project in the AR zone. Track for pre-application conferences, "
                "developer announcements, community meetings, environmental assessments."
            ),
            "auto_detected": False,
            "is_active": True,
            "priority": "high",
        },
        {
            "matter_id": 900005,
            "matter_file": "LANDOVER-MALL",
            "matter_type": "Development Project",
            "title": "Landover Mall Site - Data Center Development Proposal",
            "body_name": "Prince George's County Planning Board",
            "current_status": "Monitoring",
            "last_action_date": None,
            "watch_reason": (
                "Monitoring the Landover Mall redevelopment site for potential data center "
                "components. Secondary tracking item."
            ),
            "auto_detected": False,
            "is_active": True,
            "priority": "medium",
        },
    ]

    try:
        inserted = 0
        skipped = 0

        for item_data in items:
            # Check if already exists
            existing = db.query(WatchedMatter).filter_by(matter_id=item_data["matter_id"]).first()
            if existing:
                print(f"  SKIP (exists): {item_data['matter_file']} - {item_data['title'][:60]}")
                skipped += 1
                continue

            matter = WatchedMatter(**item_data)
            db.add(matter)
            db.flush()  # Get the ID assigned

            # Add initial history entry
            history = MatterHistory(
                matter_id=item_data["matter_id"],
                action_date=item_data.get("last_action_date") or datetime.now(timezone.utc),
                action_text="Added to Eagle Harbor Monitor watchlist",
                action_body=item_data["body_name"],
                is_milestone=True,
                notified=False,
            )
            db.add(history)

            print(f"  ADDED: {item_data['matter_file']} - {item_data['title'][:60]}")
            inserted += 1

        db.commit()

        print(f"\n{'='*60}")
        print(f"Watchlist seeding complete!")
        print(f"  Inserted: {inserted}")
        print(f"  Skipped:  {skipped}")
        print(f"{'='*60}")

        # Show summary
        all_items = db.query(WatchedMatter).filter_by(is_active=True).all()
        print(f"\nActive Watchlist Items ({len(all_items)}):")
        print("-" * 70)
        for m in all_items:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(m.priority, "⚪")
            print(f"  {icon} [{m.matter_file}] {m.title[:65]}")
            print(f"     Status: {m.current_status} | Priority: {m.priority}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Eagle Harbor Monitor - Watchlist Seeding")
    print("=" * 60)
    seed()
