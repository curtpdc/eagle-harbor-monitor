# Historical Scan - One-time function to populate 180 days of data
# Trigger manually via HTTP: https://<function-app>.azurewebsites.net/api/HistoricalScan

import azure.functions as func
import logging
import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# This will be added to function_app.py as an HTTP-triggered function
def run_historical_scan(days_back: int = 180):
    """
    Scan news and government sources for the past N days
    to populate the knowledge base with historical data
    """
    
    logging.info(f'Starting historical scan for past {days_back} days')
    
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        logging.error("DATABASE_URL not configured")
        return {"error": "Database not configured"}
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    start_date = datetime.now() - timedelta(days=days_back)
    articles_found = 0
    
    # RSS Feeds to scan
    rss_feeds = [
        ("https://www.marylandmatters.org/feed/", "Maryland Matters"),
        ("https://wtop.com/feed/", "WTOP News"),
        ("https://feeds.washingtonpost.com/rss/local", "Washington Post Local"),
    ]
    
    # Keywords to filter for
    keywords = [
        'data center', 'datacenter', 'prince george', 'prince georges',
        'eagle harbor', 'chalk point', 'CR-98-2025', 'task force',
        'zoning', 'data centre', 'county council', 'planning board',
        'environmental impact', 'AR zone', 'RE zone'
    ]
    
    try:
        # Scan RSS feeds
        for feed_url, source in rss_feeds:
            try:
                logging.info(f'Scanning {source}...')
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    try:
                        # Check publication date
                        pub_date = None
                        if hasattr(entry, 'published_parsed'):
                            pub_date = datetime(*entry.published_parsed[:6])
                        elif hasattr(entry, 'updated_parsed'):
                            pub_date = datetime(*entry.updated_parsed[:6])
                        
                        # Skip if too old
                        if pub_date and pub_date < start_date:
                            continue
                        
                        title = entry.get('title', '')
                        url = entry.get('link', '')
                        summary = entry.get('summary', entry.get('description', ''))
                        
                        # Check for keywords
                        content_text = f"{title} {summary}".lower()
                        if not any(kw.lower() in content_text for kw in keywords):
                            continue
                        
                        # Check if already exists
                        existing = db.execute(
                            text("SELECT id FROM articles WHERE url = :url"),
                            {"url": url}
                        ).fetchone()
                        
                        if existing:
                            continue
                        
                        # Insert new article
                        db.execute(
                            text("""
                                INSERT INTO articles 
                                (title, url, content, source, discovered_date, published_date, analyzed, county)
                                VALUES (:title, :url, :content, :source, :discovered, :published, FALSE, :county)
                            """),
                            {
                                "title": title,
                                "url": url,
                                "content": summary,
                                "source": source,
                                "discovered": datetime.now(),
                                "published": pub_date or datetime.now(),
                                "county": "prince_georges" if "prince george" in content_text else "unclear"
                            }
                        )
                        articles_found += 1
                        logging.info(f"Added historical article: {title[:80]}")
                    
                    except Exception as e:
                        logging.error(f"Error processing entry from {source}: {e}")
                        continue
            
            except Exception as e:
                logging.error(f"Error scanning {source}: {e}")
                continue
        
        db.commit()
        logging.info(f'Historical scan complete. Found {articles_found} relevant articles')
        
        return {
            "success": True,
            "articles_found": articles_found,
            "days_scanned": days_back,
            "date_range": f"{start_date.date()} to {datetime.now().date()}"
        }
    
    except Exception as e:
        db.rollback()
        logging.error(f'Historical scan error: {str(e)}')
        return {"error": str(e)}
    
    finally:
        db.close()
