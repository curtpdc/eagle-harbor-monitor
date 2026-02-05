"""Extract events from existing articles"""

import asyncio
from app.database import SessionLocal
from app.models import Article, Event
from app.services.ai_service import AIService
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def extract_events_from_articles():
    """Extract events from all articles that don't have associated events yet"""
    
    db = SessionLocal()
    ai_service = AIService()
    
    try:
        # Get all articles that haven't been processed for events
        articles = db.query(Article).filter(Article.analyzed == True).all()
        
        logger.info(f"Found {len(articles)} articles to process for events")
        
        total_events = 0
        
        for article in articles:
            # Check if this article already has events
            existing_events = db.query(Event).filter(Event.article_id == article.id).count()
            
            if existing_events > 0:
                logger.info(f"Article '{article.title[:50]}...' already has {existing_events} events, skipping")
                continue
            
            logger.info(f"\nProcessing article: {article.title[:80]}")
            logger.info(f"URL: {article.url}")
            logger.info(f"Category: {article.category}, Priority: {article.priority_score}")
            
            # Extract events using AI
            try:
                events = await ai_service.extract_events({
                    'title': article.title,
                    'content': article.content,
                    'url': article.url
                })
                
                if events and len(events) > 0:
                    logger.info(f"  Found {len(events)} events!")
                    
                    for event_data in events:
                        # Create Event record
                        event = Event(
                            title=event_data.get('title', ''),
                            event_type=event_data.get('event_type', 'other'),
                            event_date=datetime.fromisoformat(event_data['event_date']) if event_data.get('event_date') else None,
                            end_date=datetime.fromisoformat(event_data['end_date']) if event_data.get('end_date') else None,
                            location=event_data.get('location', ''),
                            description=event_data.get('description', ''),
                            article_id=article.id,
                            county=event_data.get('county', article.county or 'unclear'),
                            is_recurring=event_data.get('is_recurring', False),
                            is_past=event_data.get('event_date', '') < datetime.now().isoformat() if event_data.get('event_date') else False,
                            is_cancelled=False
                        )
                        
                        db.add(event)
                        total_events += 1
                        
                        logger.info(f"  ✓ Event: {event.title}")
                        logger.info(f"    Type: {event.event_type}, Date: {event.event_date}")
                        
                        # Update article with event_date if not set
                        if article.event_date is None and event.event_date:
                            article.event_date = event.event_date
                            logger.info(f"    Updated article event_date: {event.event_date}")
                    
                    db.commit()
                else:
                    logger.info(f"  No events found in this article")
                    
            except Exception as e:
                logger.error(f"  Error extracting events: {str(e)}")
                db.rollback()
                continue
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Event extraction complete!")
        logger.info(f"Total events extracted: {total_events}")
        logger.info(f"{'='*80}")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(extract_events_from_articles())
