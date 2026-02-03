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
