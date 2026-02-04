from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import secrets
from datetime import datetime

from app.database import get_db
from app.models import Subscriber, Article
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
    
    # Get relevant articles (simple keyword search for MVP)
    keywords = request.question.lower().split()
    articles = db.query(Article).filter(
        Article.analyzed == True
    ).order_by(desc(Article.priority_score)).limit(10).all()
    
    # Generate answer using AI
    answer_data = await ai_service.answer_question(request.question, articles)
    
    return QuestionResponse(**answer_data)


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
