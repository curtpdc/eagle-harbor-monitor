"""Simple Subscriber Management Tool
Usage:
    python manage_subscribers.py list              # Show all subscribers
    python manage_subscribers.py show <email>      # Show subscriber details
    python manage_subscribers.py verify <email>    # Manually verify a subscriber
    python manage_subscribers.py delete <email>    # Delete a subscriber
    python manage_subscribers.py stats             # Show subscription statistics
"""

import sys
from datetime import datetime
from app.database import SessionLocal
from app.models import Subscriber, Article, AlertSent
from sqlalchemy import func

def list_subscribers():
    """List all subscribers"""
    db = SessionLocal()
    try:
        subscribers = db.query(Subscriber).order_by(Subscriber.created_at.desc()).all()
        
        print(f"\n{'='*80}")
        print(f"SUBSCRIBERS ({len(subscribers)} total)")
        print(f"{'='*80}\n")
        
        if not subscribers:
            print("No subscribers yet.")
            return
        
        # Headers
        print(f"{'Email':<40} {'Status':<12} {'Joined':<12}")
        print(f"{'-'*40} {'-'*12} {'-'*12}")
        
        for sub in subscribers:
            status = "✓ Verified" if sub.verified else "⏳ Pending"
            joined = sub.created_at.strftime("%Y-%m-%d") if sub.created_at else "N/A"
            print(f"{sub.email:<40} {status:<12} {joined:<12}")
        
        print()
        
    finally:
        db.close()

def show_subscriber(email: str):
    """Show detailed subscriber information"""
    db = SessionLocal()
    try:
        sub = db.query(Subscriber).filter(Subscriber.email == email).first()
        
        if not sub:
            print(f"\n❌ Subscriber not found: {email}\n")
            return
        
        print(f"\n{'='*80}")
        print(f"SUBSCRIBER DETAILS: {email}")
        print(f"{'='*80}\n")
        
        print(f"Email:              {sub.email}")
        print(f"Verified:           {'✓ Yes' if sub.verified else '✗ No'}")
        print(f"Created:            {sub.created_at.strftime('%Y-%m-%d %H:%M:%S') if sub.created_at else 'N/A'}")
        print(f"Verification Token: {sub.verification_token[:20]}..." if sub.verification_token else "N/A")
        print(f"Unsubscribe Token:  {sub.unsubscribe_token[:20]}..." if sub.unsubscribe_token else "N/A")
        
        # Count alerts sent
        alerts_count = db.query(AlertSent).count()
        print(f"\nTotal Alerts Sent:  {alerts_count}")
        print()
        
    finally:
        db.close()

def verify_subscriber(email: str):
    """Manually verify a subscriber"""
    db = SessionLocal()
    try:
        sub = db.query(Subscriber).filter(Subscriber.email == email).first()
        
        if not sub:
            print(f"\n❌ Subscriber not found: {email}\n")
            return
        
        if sub.verified:
            print(f"\n✓ Subscriber already verified: {email}\n")
            return
        
        sub.verified = True
        db.commit()
        
        print(f"\n✓ Subscriber verified: {email}\n")
        
    finally:
        db.close()

def delete_subscriber(email: str):
    """Delete a subscriber"""
    db = SessionLocal()
    try:
        sub = db.query(Subscriber).filter(Subscriber.email == email).first()
        
        if not sub:
            print(f"\n❌ Subscriber not found: {email}\n")
            return
        
        confirm = input(f"⚠️  Delete subscriber {email}? (yes/no): ")
        if confirm.lower() != 'yes':
            print("\n❌ Cancelled\n")
            return
        
        db.delete(sub)
        db.commit()
        
        print(f"\n✓ Subscriber deleted: {email}\n")
        
    finally:
        db.close()

def show_stats():
    """Show subscription statistics"""
    db = SessionLocal()
    try:
        total = db.query(Subscriber).count()
        verified = db.query(Subscriber).filter(Subscriber.verified == True).count()
        pending = total - verified
        
        # Get newest subscriber
        newest = db.query(Subscriber).order_by(Subscriber.created_at.desc()).first()
        
        # Get article stats
        articles = db.query(Article).count()
        articles_analyzed = db.query(Article).filter(Article.analyzed == True).count()
        high_priority = db.query(Article).filter(Article.priority_score >= 7).count()
        
        # Get alert stats
        alerts_sent = db.query(AlertSent).count()
        
        print(f"\n{'='*80}")
        print(f"EAGLE HARBOR MONITOR - STATISTICS")
        print(f"{'='*80}\n")
        
        print("SUBSCRIBERS")
        print(f"  Total:           {total}")
        print(f"  ✓ Verified:      {verified}")
        print(f"  ⏳ Pending:       {pending}")
        if newest:
            print(f"  Newest:          {newest.email} ({newest.created_at.strftime('%Y-%m-%d')})")
        print()
        
        print("CONTENT")
        print(f"  Articles:        {articles}")
        print(f"  Analyzed:        {articles_analyzed}")
        print(f"  High Priority:   {high_priority} (score ≥ 7)")
        print()
        
        print("ALERTS")
        print(f"  Sent:            {alerts_sent}")
        print()
        
    finally:
        db.close()

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_subscribers()
    elif command == "show":
        if len(sys.argv) < 3:
            print("\n❌ Usage: python manage_subscribers.py show <email>\n")
            return
        show_subscriber(sys.argv[2])
    elif command == "verify":
        if len(sys.argv) < 3:
            print("\n❌ Usage: python manage_subscribers.py verify <email>\n")
            return
        verify_subscriber(sys.argv[2])
    elif command == "delete":
        if len(sys.argv) < 3:
            print("\n❌ Usage: python manage_subscribers.py delete <email>\n")
            return
        delete_subscriber(sys.argv[2])
    elif command == "stats":
        show_stats()
    else:
        print(f"\n❌ Unknown command: {command}\n")
        print(__doc__)

if __name__ == "__main__":
    main()
