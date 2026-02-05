from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
import secrets
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Subscriber, Article, Event
from app.schemas import (
    SubscriberCreate,
    SubscriberResponse,
    ArticleListResponse,
    ArticleResponse,
    QuestionRequest,
    QuestionResponse,
    HealthResponse
)
from app.services.email_service import EmailService
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/subscribe", response_model=SubscriberResponse)
async def subscribe(subscriber: SubscriberCreate, db: Session = Depends(get_db)):
    """Subscribe to email alerts"""
    
    # Check if already subscribed
    existing = db.query(Subscriber).filter(Subscriber.email == subscriber.email).first()
    
    if existing:
        if existing.verified:
            raise HTTPException(status_code=400, detail="Email already subscribed")
        else:
            # Resend verification
            email_service = EmailService()
            await email_service.send_verification_email(existing.email, existing.verification_token)
            return SubscriberResponse(message="Verification email resent. Please check your inbox.")
    
    # Create new subscriber
    verification_token = secrets.token_urlsafe(32)
    unsubscribe_token = secrets.token_urlsafe(32)
    
    new_subscriber = Subscriber(
        email=subscriber.email,
        verification_token=verification_token,
        unsubscribe_token=unsubscribe_token,
        verified=False
    )
    
    db.add(new_subscriber)
    db.commit()

    # Send verification email
    email_service = EmailService()
    await email_service.send_verification_email(subscriber.email, verification_token)
    
    return SubscriberResponse(
        message="Subscription successful! Please check your email to verify your address."
    )


@router.get("/verify/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email address"""
    
    subscriber = db.query(Subscriber).filter(Subscriber.verification_token == token).first()
    
    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid verification token")
    
    if subscriber.verified:
        return {"message": "Email already verified"}
    
    subscriber.verified = True
    db.commit()
    
    # Send welcome email
    email_service = EmailService()
    await email_service.send_welcome_email(subscriber.email, subscriber.unsubscribe_token)
    
    return {"message": "Email verified successfully! You'll now receive alerts."}


@router.get("/unsubscribe/{token}")
async def unsubscribe(token: str, db: Session = Depends(get_db)):
    """Unsubscribe from alerts"""
    
    subscriber = db.query(Subscriber).filter(Subscriber.unsubscribe_token == token).first()
    
    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid unsubscribe token")
    
    subscriber.is_active = False
    db.commit()
    
    return {"message": "You have been unsubscribed. We're sorry to see you go!"}


@router.get("/articles", response_model=ArticleListResponse)
async def get_articles(
    limit: int = Query(10, ge=1, le=50),
    page: int = Query(1, ge=1),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get recent articles"""
    
    query = db.query(Article).filter(Article.analyzed == True)
    
    if category:
        query = query.filter(Article.category == category)
    
    # Count total
    total = query.count()
    
    # Paginate
    offset = (page - 1) * limit
    articles = query.order_by(desc(Article.discovered_date)).offset(offset).limit(limit).all()
    
    return ArticleListResponse(
        articles=articles,
        total=total,
        page=page,
        limit=limit
    )


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """Ask a question about data centers"""
    
    ai_service = AIService()
    
    try:
        # Get relevant articles (simple keyword search for MVP)
        keywords = request.question.lower().split()
        articles = db.query(Article).filter(
            Article.analyzed == True
        ).order_by(desc(Article.priority_score)).limit(10).all()
        
        # Generate answer using AI with timeout handling
        answer_data = await ai_service.answer_question(request.question, articles)
        
        return QuestionResponse(**answer_data)
    
    except TimeoutError as e:
        raise HTTPException(
            status_code=504, 
            detail="Request timed out. Please try a simpler question or try again in a moment."
        )
    except Exception as e:
        logging.error(f"Error in ask_question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Unable to process your question at this time. Please try again later."
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    
    try:
        # Check database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Get last scrape time
    last_article = db.query(Article).order_by(desc(Article.discovered_date)).first()
    last_scrape = last_article.discovered_date if last_article else None
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        last_scrape=last_scrape
    )


@router.get("/events/upcoming")
async def get_upcoming_events(
    days: int = Query(90, description="Number of days ahead to look"),
    county: Optional[str] = Query(None, description="Filter by county (prince_georges, charles, or both)"),
    db: Session = Depends(get_db)
):
    """Get upcoming events for the next N days"""
    
    now = datetime.now()
    end_date = now + timedelta(days=days)
    
    query = db.query(Event).filter(
        Event.event_date >= now,
        Event.event_date <= end_date,
        Event.is_cancelled == False
    )
    
    if county:
        query = query.filter(Event.county == county)
    
    events = query.order_by(Event.event_date).all()
    
    return {
        "events": [
            {
                "id": event.id,
                "title": event.title,
                "event_type": event.event_type,
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "location": event.location,
                "description": event.description,
                "county": event.county,
                "is_recurring": event.is_recurring,
                "article_id": event.article_id
            }
            for event in events
        ],
        "count": len(events),
        "period": f"next {days} days",
        "as_of": now.isoformat()
    }


@router.get("/events/timeline")
async def get_event_timeline(
    days_back: int = Query(180, description="Number of days back to look"),
    county: Optional[str] = Query(None, description="Filter by county (prince_georges, charles, or both)"),
    db: Session = Depends(get_db)
):
    """Get historical event timeline for the past N days"""
    
    now = datetime.now()
    start_date = now - timedelta(days=days_back)
    
    query = db.query(Event).filter(
        Event.event_date >= start_date,
        Event.event_date <= now
    )
    
    if county:
        query = query.filter(Event.county == county)
    
    events = query.order_by(desc(Event.event_date)).all()
    
    return {
        "events": [
            {
                "id": event.id,
                "title": event.title,
                "event_type": event.event_type,
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "location": event.location,
                "description": event.description,
                "county": event.county,
                "is_past": event.is_past,
                "is_cancelled": event.is_cancelled,
                "article_id": event.article_id
            }
            for event in events
        ],
        "count": len(events),
        "period": f"past {days_back} days",
        "as_of": now.isoformat()
    }
