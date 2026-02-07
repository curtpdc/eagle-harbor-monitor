"""Manual scraper to populate Eagle Harbor Monitor database"""
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from app.database import SessionLocal
from app.models import Article

logging.basicConfig(level=logging.INFO)

def scrape_legistar():
    """Scrape Prince George's County Legistar for relevant meetings/legislation"""
    logging.info('🔍 Starting Legistar scraper...')
    
    db = SessionLocal()
    new_articles = 0
    
    try:
        # Prince George's County Legistar calendar
        url = "https://princegeorgescountymd.legistar.com/Calendar.aspx"
        logging.info(f'Fetching: {url}')
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find meeting rows
        meetings = soup.find_all('tr', class_=['rgRow', 'rgAltRow'])
        logging.info(f'Found {len(meetings)} meetings')
        
        keywords = ['data center', 'datacenter', 'planning board', 'zoning', 
                   'AR zone', 'RE zone', 'qualified data center', 'Eagle Harbor',
                   'Chalk Point', 'Landover']
        
        for meeting in meetings[:20]:  # Process first 20
            try:
                title_elem = meeting.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')
                
                # Check for data center keywords
                if any(kw.lower() in title.lower() for kw in keywords):
                    article_url = f"https://princegeorgescountymd.legistar.com{href}"
                    
                    # Check if already exists
                    existing = db.query(Article).filter(Article.url == article_url).first()
                    
                    if not existing:
                        # Get date
                        date_elem = meeting.find('span', class_='EventDate')
                        event_date = datetime.now()
                        if date_elem:
                            try:
                                date_str = date_elem.get_text(strip=True)
                                event_date = datetime.strptime(date_str, '%m/%d/%Y')
                            except:
                                pass
                        
                        article = Article(
                            title=title[:500],
                            url=article_url,
                            content=f"Meeting: {title}",
                            source="Prince George's County Legistar",
                            discovered_date=datetime.now(),
                            published_date=event_date,
                            analyzed=False
                        )
                        
                        db.add(article)
                        new_articles += 1
                        logging.info(f'  ✅ Added: {title[:80]}...')
            
            except Exception as e:
                logging.error(f'  ❌ Error processing meeting: {e}')
                continue
        
        db.commit()
        logging.info(f'✅ Legistar scraper complete. Added {new_articles} new articles.')
        
    except Exception as e:
        logging.error(f'❌ Legistar scraper failed: {e}')
        db.rollback()
    finally:
        db.close()
    
    return new_articles


def scrape_news_rss():
    """Scrape news RSS feeds for Maryland data center news"""
    logging.info('🔍 Starting RSS News scraper...')
    
    db = SessionLocal()
    new_articles = 0
    
    # RSS feeds to monitor
    feeds = [
        "https://wtop.com/prince-georges-county/feed/",
        "https://www.marylandmatters.org/feed/",
        "https://www.bizjournals.com/washington/search/results/rss?q=data%20center",
    ]
    
    keywords = ['data center', 'datacenter', 'Prince George', 'Charles County',
               'Maryland', 'Eagle Harbor', 'Chalk Point', 'zoning', 'AR zone']
    
    for feed_url in feeds:
        try:
            logging.info(f'Fetching RSS: {feed_url}')
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:  # First 10 from each feed
                try:
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    summary = entry.get('summary', '')
                    content = summary or entry.get('description', '')
                    
                    # Check for data center keywords
                    full_text = f"{title} {content}".lower()
                    if any(kw.lower() in full_text for kw in keywords):
                        
                        # Check if already exists
                        existing = db.query(Article).filter(Article.url == link).first()
                        
                        if not existing and link:
                            # Get published date
                            pub_date = datetime.now()
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                            
                            article = Article(
                                title=title[:500],
                                url=link,
                                content=content[:5000],
                                source=feed_url.split('/')[2],  # Domain name
                                discovered_date=datetime.now(),
                                published_date=pub_date,
                                analyzed=False
                            )
                            
                            db.add(article)
                            new_articles += 1
                            logging.info(f'  ✅ Added: {title[:80]}...')
                
                except Exception as e:
                    logging.error(f'  ❌ Error processing entry: {e}')
                    continue
            
        except Exception as e:
            logging.error(f'❌ Error fetching feed {feed_url}: {e}')
            continue
    
    db.commit()
    logging.info(f'✅ RSS scraper complete. Added {new_articles} new articles.')
    db.close()
    
    return new_articles


if __name__ == "__main__":
    print("\n" + "="*80)
    print("EAGLE HARBOR MONITOR - WEB SCRAPER")
    print("="*80 + "\n")
    
    # Run scrapers
    legistar_count = scrape_legistar()
    rss_count = scrape_news_rss()
    
    total = legistar_count + rss_count
    
    print("\n" + "="*80)
    print(f"✅ SCRAPING COMPLETE - {total} new articles discovered")
    print("="*80)
    print(f"  Legistar: {legistar_count} articles")
    print(f"  RSS News: {rss_count} articles")
    print("\nNext step: Run AI analysis on unanalyzed articles")
    print("="*80 + "\n")
