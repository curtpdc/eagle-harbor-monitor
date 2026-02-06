import azure.functions as func
import logging
import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

app = func.FunctionApp()

# Database setup
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@app.function_name(name="LegistarScraper")
@app.schedule(schedule="0 0 */2 * * *", arg_name="timer", run_on_startup=False)
def legistar_scraper(timer: func.TimerRequest) -> None:
    """Scrape Legistar for meetings and legislation every 2 hours"""
    
    logging.info('Legistar scraper function started')
    
    try:
        url = "https://princegeorgescountymd.legistar.com/Calendar.aspx"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find meetings (this is simplified - actual implementation needs more parsing)
        meetings = soup.find_all('tr', class_='rgRow')
        
        db = SessionLocal()
        new_articles = 0
        
        for meeting in meetings[:10]:  # Limit for testing
            try:
                title_elem = meeting.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')
                
                # Check for data center keywords
                if any(keyword.lower() in title.lower() for keyword in [
                    'data center', 'datacenter', 'planning board', 'zoning'
                ]):
                    article_url = f"https://princegeorgescountymd.legistar.com{href}"
                    
                    # Check if already exists
                    existing = db.execute(
                        "SELECT 1 FROM articles WHERE url = :url",
                        {"url": article_url}
                    ).first()
                    
                    if not existing:
                        # Insert new article
                        db.execute(
                            """
                            INSERT INTO articles (title, url, source, discovered_date, analyzed)
                            VALUES (:title, :url, :source, :discovered, FALSE)
                            """,
                            {
                                "title": title,
                                "url": article_url,
                                "source": "PG County Legistar",
                                "discovered": datetime.now()
                            }
                        )
                        new_articles += 1
                        logging.info(f"New article: {title}")
            
            except Exception as e:
                logging.error(f"Error processing meeting: {e}")
                continue
        
        db.commit()
        db.close()
        
        logging.info(f'Legistar scraper completed. New articles: {new_articles}')
    
    except Exception as e:
        logging.error(f'Legistar scraper error: {str(e)}')


@app.function_name(name="RSSNewsScraper")
@app.schedule(schedule="0 */30 * * * *", arg_name="timer", run_on_startup=False)
def rss_news_scraper(timer: func.TimerRequest) -> None:
    """Scrape RSS feeds every 30 minutes"""
    
    logging.info('RSS news scraper function started')
    
    rss_feeds = [
        ("https://www.marylandmatters.org/feed/", "Maryland Matters"),
        ("https://wtop.com/feed/", "WTOP News"),
        ("https://feeds.washingtonpost.com/rss/local", "Washington Post"),
    ]
    
    try:
        db = SessionLocal()
        new_articles = 0
        
        for feed_url, source in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:20]:  # Limit entries
                    title = entry.get('title', '')
                    url = entry.get('link', '')
                    summary = entry.get('summary', '')
                    
                    # Check for data center keywords
                    content_text = f"{title} {summary}".lower()
                    if any(keyword.lower() in content_text for keyword in [
                        'data center', 'datacenter', 'prince george', 'eagle harbor',
                        'chalk point', 'zoning', 'planning board'
                    ]):
                        # Check if already exists
                        existing = db.execute(
                            "SELECT 1 FROM articles WHERE url = :url",
                            {"url": url}
                        ).first()
                        
                        if not existing:
                            published = entry.get('published_parsed')
                            pub_date = datetime(*published[:6]) if published else None
                            
                            db.execute(
                                """
                                INSERT INTO articles (title, url, summary, source, published_date, discovered_date, analyzed)
                                VALUES (:title, :url, :summary, :source, :published, :discovered, FALSE)
                                """,
                                {
                                    "title": title[:500],
                                    "url": url,
                                    "summary": summary,
                                    "source": source,
                                    "published": pub_date,
                                    "discovered": datetime.now()
                                }
                            )
                            new_articles += 1
                            logging.info(f"New article from {source}: {title}")
            
            except Exception as e:
                logging.error(f"Error scraping {source}: {e}")
                continue
        
        db.commit()
        db.close()
        
        logging.info(f'RSS scraper completed. New articles: {new_articles}')
    
    except Exception as e:
        logging.error(f'RSS scraper error: {str(e)}')


@app.function_name(name="ArticleAnalyzer")
@app.schedule(schedule="0 */10 * * * *", arg_name="timer", run_on_startup=False)
def article_analyzer(timer: func.TimerRequest) -> None:
    """Analyze unanalyzed articles every 10 minutes"""
    
    logging.info('Article analyzer function started')
    
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        db = SessionLocal()
        
        # Get unanalyzed articles
        articles = db.execute(
            """
            SELECT id, title, summary, content, source
            FROM articles
            WHERE analyzed = FALSE
            LIMIT 5
            """
        ).fetchall()
        
        for article in articles:
            try:
                content = f"{article[1]} {article[2] or ''} {article[3] or ''}"[:2000]
                
                prompt = f"""Analyze this article about Prince George's County:

Title: {article[1]}
Source: {article[4]}
Content: {content}

Return JSON with:
- priority_score (1-10)
- category (policy/meeting/legislation/environmental/community)
- county (prince_georges/charles/both)

Focus on data centers, zoning, AR/RE zones, planning board actions."""

                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                analysis = json.loads(response.content[0].text)
                
                db.execute(
                    """
                    UPDATE articles
                    SET priority_score = :priority,
                        category = :category,
                        county = :county,
                        analyzed = TRUE
                    WHERE id = :id
                    """,
                    {
                        "id": article[0],
                        "priority": analysis.get('priority_score', 5),
                        "category": analysis.get('category', 'general'),
                        "county": analysis.get('county', 'unclear')
                    }
                )
                
                logging.info(f"Analyzed article {article[0]}: priority {analysis.get('priority_score')}")
            
            except Exception as e:
                logging.error(f"Error analyzing article {article[0]}: {e}")
                # Mark as analyzed anyway to avoid re-processing
                db.execute(
                    "UPDATE articles SET analyzed = TRUE WHERE id = :id",
                    {"id": article[0]}
                )
        
        db.commit()
        db.close()
        
        logging.info(f'Article analyzer completed. Analyzed: {len(articles)}')
    
    except Exception as e:
        logging.error(f'Article analyzer error: {str(e)}')


@app.function_name(name="HistoricalScan")
@app.route(route="historical-scan", methods=["POST", "GET"], auth_level=func.AuthLevel.ANONYMOUS)
def historical_scan(req: func.HttpRequest) -> func.HttpResponse:
    """
    One-time historical scan to populate knowledge base with past 180 days of articles
    Trigger via: GET https://<function-app>.azurewebsites.net/api/historical-scan?days=180
    """
    
    logging.info('Historical scan triggered')
    
    try:
        # Get days parameter (default 180)
        days_param = req.params.get('days', '180')
        days_back = int(days_param)
        
        if days_back > 365:
            return func.HttpResponse(
                "Maximum 365 days allowed",
                status_code=400
            )
        
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        start_date = datetime.now() - timedelta(days=days_back)
        articles_found = 0
        
        # RSS Feeds to scan
        rss_feeds = [
            ("https://www.marylandmatters.org/feed/", "Maryland Matters"),
            ("https://wtop.com/feed/", "WTOP News"),
            ("https://feeds.washingtonpost.com/rss/local", "Washington Post"),
        ]
        
        keywords = [
            'data center', 'datacenter', 'prince george', 'eagle harbor',
            'chalk point', 'CR-98-2025', 'task force', 'zoning',
            'county council', 'planning board', 'AR zone', 'RE zone'
        ]
        
        db = SessionLocal()
        
        for feed_url, source in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:100]:  # Scan up to 100 entries per feed
                    try:
                        # Check publication date
                        pub_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                        
                        if pub_date and pub_date < start_date:
                            continue
                        
                        title = entry.get('title', '')
                        url = entry.get('link', '')
                        summary = entry.get('summary', entry.get('description', ''))
                        
                        content_text = f"{title} {summary}".lower()
                        if not any(kw.lower() in content_text for kw in keywords):
                            continue
                        
                        # Check if exists
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
                                (title, url, content, source, discovered_date, published_date, analyzed)
                                VALUES (:title, :url, :content, :source, :discovered, :published, FALSE)
                            """),
                            {
                                "title": title,
                                "url": url,
                                "content": summary,
                                "source": source,
                                "discovered": datetime.now(),
                                "published": pub_date or datetime.now()
                            }
                        )
                        articles_found += 1
                        logging.info(f"Historical: {title[:60]}")
                    
                    except Exception as e:
                        logging.error(f"Entry error: {e}")
                        continue
            
            except Exception as e:
                logging.error(f"Feed error for {source}: {e}")
                continue
        
        db.commit()
        db.close()
        
        result = {
            "success": True,
            "articles_found": articles_found,
            "days_scanned": days_back,
            "date_range": f"{start_date.date()} to {datetime.now().date()}",
            "note": "ArticleAnalyzer will process these articles automatically"
        }
        
        logging.info(f'Historical scan complete: {articles_found} articles')
        
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )
    
    except Exception as e:
        logging.error(f'Historical scan error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
