"""Setup PostgreSQL schema and migrate data from SQLite"""
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL connection
PG_CONN = "postgresql://adminuser:EagleHarbor2026!@eagle-harbor-db.postgres.database.azure.com:5432/eagle_harbor_monitor?sslmode=require"

# SQLite connection
SQLITE_CONN = "sqlite:///./eagle_harbor.db"

def setup_schema():
    """Create PostgreSQL schema"""
    print("📊 Setting up PostgreSQL schema...")
    
    conn = psycopg2.connect(PG_CONN)
    cur = conn.cursor()
    
    # Read schema file
    with open('../database/schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Execute schema
    cur.execute(schema_sql)
    conn.commit()
    
    print("✅ Schema created successfully")
    
    cur.close()
    conn.close()

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    print("\n📦 Migrating data from SQLite to PostgreSQL...")
    
    # Connect to both databases
    sqlite_engine = create_engine(SQLITE_CONN)
    pg_engine = create_engine(PG_CONN)
    
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PGSession = sessionmaker(bind=pg_engine)
    
    sqlite_session = SQLiteSession()
    pg_session = PGSession()
    
    try:
        # Migrate articles
        articles = sqlite_session.execute(text("SELECT * FROM articles")).fetchall()
        print(f"  Migrating {len(articles)} articles...")
        
        for article in articles:
            # Check if article already exists
            existing = pg_session.execute(
                text("SELECT id FROM articles WHERE url = :url"),
                {"url": article.url}
            ).fetchone()
            
            if not existing:
                pg_session.execute(text("""
                    INSERT INTO articles 
                    (title, url, summary, content, source, published_date, discovered_date, 
                     priority_score, category, county, notified, analyzed)
                    VALUES 
                    (:title, :url, :summary, :content, :source, :published_date, :discovered_date,
                     :priority_score, :category, :county, :notified, :analyzed)
                """), {
                    "title": article.title,
                    "url": article.url,
                    "summary": article.summary,
                    "content": article.content,
                    "source": article.source,
                    "published_date": article.published_date,
                    "discovered_date": article.discovered_date,
                    "priority_score": article.priority_score,
                    "category": article.category,
                    "county": article.county,
                    "notified": bool(article.notified),
                    "analyzed": bool(article.analyzed)
                })
        
        pg_session.commit()
        print(f"  ✅ Migrated {len(articles)} articles")
        
        # Check subscribers
        subscribers = sqlite_session.execute(text("SELECT * FROM subscribers")).fetchall()
        if subscribers:
            print(f"  Migrating {len(subscribers)} subscribers...")
            for sub in subscribers:
                existing = pg_session.execute(
                    text("SELECT id FROM subscribers WHERE email = :email"),
                    {"email": sub.email}
                ).fetchone()
                
                if not existing:
                    pg_session.execute(text("""
                        INSERT INTO subscribers 
                        (email, verified, verification_token, unsubscribe_token, subscribed_at, is_active)
                        VALUES 
                        (:email, :verified, :verification_token, :unsubscribe_token, :subscribed_at, :is_active)
                    """), {
                        "email": sub.email,
                        "verified": bool(sub.verified),
                        "verification_token": sub.verification_token,
                        "unsubscribe_token": sub.unsubscribe_token,
                        "subscribed_at": sub.subscribed_at,
                        "is_active": bool(sub.is_active)
                    })
            
            pg_session.commit()
            print(f"  ✅ Migrated {len(subscribers)} subscribers")
        
        print("\n✅ Data migration complete!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        pg_session.rollback()
    finally:
        sqlite_session.close()
        pg_session.close()

if __name__ == "__main__":
    try:
        # setup_schema()  # Skip schema - already exists
        migrate_data()
        print("\n🎉 PostgreSQL migration complete! Both apps now share the same database.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
