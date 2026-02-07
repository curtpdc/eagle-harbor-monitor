from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, text
from typing import Optional, List
import secrets
import logging
import re
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Subscriber, Article, Event, WatchedMatter, MatterHistory, MatterAttachment, MatterVote
from app.schemas import (
    SubscriberCreate,
    SubscriberResponse,
    ArticleListResponse,
    ArticleResponse,
    QuestionRequest,
    QuestionResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    WatchedMatterCreate,
    WatchedMatterResponse,
    WatchedMatterDetailResponse,
    MatterHistoryResponse,
    MatterAttachmentResponse,
    MatterVoteResponse,
)
from app.config import settings
from app.services.email_service import EmailService
from app.services.ai_service import AIService, AIServiceError

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
    county: Optional[str] = Query(None, description="Filter by county (prince_georges, charles, both, maryland_statewide)"),
    min_relevance: Optional[int] = Query(None, ge=0, le=10, description="Minimum relevance score (0-10). Defaults to MIN_RELEVANCE_DISPLAY setting."),
    min_priority: Optional[int] = Query(None, ge=1, le=10, description="Minimum priority score (1-10)"),
    db: Session = Depends(get_db)
):
    """Get recent articles filtered by relevance to Maryland data center developments."""
    from app.config import settings
    
    query = db.query(Article).filter(Article.analyzed == True)
    
    # Apply relevance filter — default to configured minimum
    effective_min_relevance = min_relevance if min_relevance is not None else settings.MIN_RELEVANCE_DISPLAY
    if effective_min_relevance > 0:
        # Include articles with relevance_score >= threshold, plus legacy articles with NULL (not yet scored)
        query = query.filter(
            or_(
                Article.relevance_score >= effective_min_relevance,
                Article.relevance_score == None  # Legacy articles not yet re-analyzed
            )
        )
    
    if category:
        query = query.filter(Article.category == category)
    
    if county:
        query = query.filter(Article.county == county)
    
    if min_priority:
        query = query.filter(Article.priority_score >= min_priority)
    
    # Count total
    total = query.count()
    
    # Paginate — sort by date, then priority within the same date
    offset = (page - 1) * limit
    articles = query.order_by(
        desc(Article.discovered_date),
        desc(Article.priority_score)
    ).offset(offset).limit(limit).all()
    
    return ArticleListResponse(
        articles=articles,
        total=total,
        page=page,
        limit=limit
    )


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """Ask a question about data centers.
    
    Always provides recent article context to the AI so answers are grounded
    in current monitored sources, never in stale GPT training data.
    """
    
    logging.info(f"Received question: {request.question}")
    
    ai_service = AIService()
    logging.info(f"AI service initialized, enabled={ai_service.enabled}")
    
    try:
        question_text = request.question.strip()
        question_lower = question_text.lower()

        stopwords = {
            "the", "a", "an", "and", "or", "but", "if", "then", "to", "of", "in", "on", "for", "with",
            "is", "are", "was", "were", "be", "been", "being", "it", "this", "that", "these", "those",
            "what", "when", "where", "why", "how", "about", "from", "by", "as", "at", "into", "over",
            "do", "does", "did", "can", "could", "should", "would", "will", "may", "might",
            "data", "center", "centers", "county", "maryland", "prince", "george", "charles",
        }
        tokens = [t for t in re.findall(r"[a-z0-9']+", question_lower) if t not in stopwords and len(t) > 2]

        # Also detect multi-word domain phrases for better matching
        domain_phrases = []
        phrase_map = {
            "data center": "data center", "eagle harbor": "eagle harbor",
            "chalk point": "chalk point", "planning board": "planning board",
            "task force": "task force", "ar zone": "AR zone", "re zone": "RE zone",
            "cr-98": "CR-98", "eo 42": "EO 42", "landover mall": "landover mall",
            "zoning amendment": "zoning amendment", "special exception": "special exception",
        }
        for phrase in phrase_map:
            if phrase in question_lower:
                domain_phrases.append(phrase_map[phrase])

        cutoff = datetime.now() - timedelta(days=180)
        
        # Step 1: Try keyword + phrase matching
        keyword_articles = []
        if tokens or domain_phrases:
            conditions = []
            for phrase in domain_phrases:
                like = f"%{phrase}%"
                conditions.extend([
                    Article.title.ilike(like),
                    Article.summary.ilike(like),
                    Article.content.ilike(like)
                ])
            for token in tokens:
                like = f"%{token}%"
                conditions.extend([
                    Article.title.ilike(like),
                    Article.summary.ilike(like),
                    Article.content.ilike(like)
                ])
            if conditions:
                keyword_articles = db.query(Article).filter(
                    Article.analyzed == True,
                    Article.discovered_date >= cutoff,
                    or_(*conditions)
                ).order_by(desc(Article.priority_score), desc(Article.discovered_date)).limit(10).all()

        # Step 2: ALWAYS backfill with recent high-priority articles so the AI
        # has current context even when keyword search returns few/no matches
        seen_ids = {a.id for a in keyword_articles}
        articles = list(keyword_articles)

        if len(articles) < 10:
            recent_top = db.query(Article).filter(
                Article.analyzed == True,
                Article.discovered_date >= cutoff,
                or_(
                    Article.relevance_score >= 4,
                    Article.relevance_score == None  # Legacy articles not yet scored
                )
            ).order_by(desc(Article.priority_score), desc(Article.discovered_date)).limit(15).all()
            for article in recent_top:
                if article.id not in seen_ids:
                    articles.append(article)
                    seen_ids.add(article.id)
                if len(articles) >= 10:
                    break

        # Step 3: Pull events for meeting-related questions
        meeting_keywords = [
            "meeting", "hearing", "agenda", "planning board", "council",
            "vote", "public hearing", "work session", "town hall"
        ]
        meeting_related = any(keyword in question_lower for keyword in meeting_keywords)
        events = []
        if meeting_related:
            now = datetime.now()
            end_date = now + timedelta(days=90)
            events = db.query(Event).filter(
                Event.event_date >= now,
                Event.event_date <= end_date,
                Event.is_cancelled == False
            ).order_by(Event.event_date).limit(10).all()
        
        logging.info(f"Found {len(keyword_articles)} keyword matches, {len(articles)} total articles, {len(events)} events")
        
        # Generate answer using AI with timeout handling
        logging.info("Calling AI service answer_question...")
        answer_data = await ai_service.answer_question(question_text, articles, events)
        logging.info("AI answer generated successfully")
        
        return QuestionResponse(**answer_data)
    
    except TimeoutError as e:
        logging.error(f"Timeout in ask_question: {str(e)}")
        raise HTTPException(
            status_code=504, 
            detail="Request timed out. Please try a simpler question or try again in a moment."
        )
    except AIServiceError as e:
        logging.error(f"AI service error in ask_question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable. Please try again in a few moments."
        )
    except Exception as e:
        logging.error(f"Error in ask_question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to process your question at this time. Please try again later."
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on an AI answer to improve quality over time."""
    ai_service = AIService()
    ok = ai_service.record_feedback(
        question=request.question,
        answer=request.answer,
        rating=request.rating,
        comment=request.comment or "",
    )
    if ok:
        return FeedbackResponse(success=True, message="Thank you for your feedback!")
    raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/ai/stats")
async def ai_stats():
    """Return fine-tuning data collection statistics."""
    ai_service = AIService()
    return {
        "enabled": ai_service.enabled,
        "model": settings.AZURE_OPENAI_DEPLOYMENT,
        "finetune_data": ai_service.get_finetune_stats(),
    }


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Get last scrape time
    last_article = db.query(Article).order_by(desc(Article.discovered_date)).first()
    last_scrape = last_article.discovered_date if last_article else None

    # Watchlist summary for health
    try:
        active_watches = db.query(WatchedMatter).filter(WatchedMatter.is_active == True).count()
    except Exception:
        active_watches = 0
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        last_scrape=last_scrape
    )


# ── Amendment Watchlist Endpoints ─────────────────────────────────────────────


@router.get("/watchlist", response_model=List[WatchedMatterResponse])
async def get_watchlist(
    active_only: bool = Query(True, description="Only show active watched matters"),
    db: Session = Depends(get_db),
):
    """List all watched matters (amendment / legislation tracking)."""
    query = db.query(WatchedMatter)
    if active_only:
        query = query.filter(WatchedMatter.is_active == True)
    matters = query.order_by(desc(WatchedMatter.updated_date)).all()
    return matters


@router.get("/watchlist/{matter_id}", response_model=WatchedMatterDetailResponse)
async def get_watched_matter_detail(matter_id: int, db: Session = Depends(get_db)):
    """Get full detail for a watched matter including history, attachments, and votes."""
    matter = db.query(WatchedMatter).filter(WatchedMatter.matter_id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail=f"Matter {matter_id} not found in watchlist")

    histories = (
        db.query(MatterHistory)
        .filter(MatterHistory.matter_id == matter_id)
        .order_by(desc(MatterHistory.action_date))
        .all()
    )
    attachments = (
        db.query(MatterAttachment)
        .filter(MatterAttachment.matter_id == matter_id)
        .order_by(desc(MatterAttachment.discovered_date))
        .all()
    )
    votes = (
        db.query(MatterVote)
        .filter(MatterVote.matter_id == matter_id)
        .order_by(desc(MatterVote.vote_date))
        .all()
    )

    # Build response with relationships
    result = WatchedMatterDetailResponse.model_validate(matter)
    result.histories = [MatterHistoryResponse.model_validate(h) for h in histories]
    result.attachments = [MatterAttachmentResponse.model_validate(a) for a in attachments]
    result.votes = [MatterVoteResponse.model_validate(v) for v in votes]
    return result


@router.post("/watchlist", response_model=WatchedMatterResponse)
async def add_to_watchlist(request: WatchedMatterCreate, db: Session = Depends(get_db)):
    """Manually add a Legistar matter to the watchlist.

    Provide the Legistar MatterId (visible in legislation URLs) and a title.
    The tracker will begin polling for status changes, attachments, and votes.
    """
    existing = db.query(WatchedMatter).filter(WatchedMatter.matter_id == request.matter_id).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.watch_reason = request.watch_reason or existing.watch_reason
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=400, detail="Matter already on watchlist")

    legistar_url = (
        f"https://princegeorgescountymd.legistar.com/LegislationDetail.aspx"
        f"?ID={request.matter_id}"
    )

    matter = WatchedMatter(
        matter_id=request.matter_id,
        matter_file=request.matter_file,
        matter_type=request.matter_type,
        title=request.title,
        body_name=request.body_name,
        legistar_url=legistar_url,
        watch_reason=request.watch_reason or "Manually added",
        auto_detected=False,
        is_active=True,
        priority=request.priority,
    )
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return matter


@router.delete("/watchlist/{matter_id}")
async def remove_from_watchlist(matter_id: int, db: Session = Depends(get_db)):
    """Deactivate a matter from the watchlist (soft delete)."""
    matter = db.query(WatchedMatter).filter(WatchedMatter.matter_id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    matter.is_active = False
    db.commit()
    return {"message": f"Matter {matter_id} removed from active watchlist"}


@router.post("/watchlist/{matter_id}/analyze")
async def analyze_watchlist_attachment(
    matter_id: int,
    attachment_id: Optional[int] = Query(None, description="Specific attachment ID to analyze; omit to analyze all unanalyzed"),
    db: Session = Depends(get_db),
):
    """Trigger AI analysis on attachment text for a watched matter.

    Analyzes the amendment text for approval path, qualified definition,
    power provisions, infrastructure triggers, and compatibility standards.
    """
    matter = db.query(WatchedMatter).filter(WatchedMatter.matter_id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    query = db.query(MatterAttachment).filter(MatterAttachment.matter_id == matter_id)
    if attachment_id:
        query = query.filter(MatterAttachment.id == attachment_id)
    else:
        query = query.filter(MatterAttachment.analyzed == False)

    attachments = query.all()
    if not attachments:
        raise HTTPException(status_code=404, detail="No unanalyzed attachments found")

    ai_service = AIService()
    results = []

    for att in attachments:
        if not att.content_text:
            results.append({"attachment_id": att.id, "status": "skipped", "reason": "no text content"})
            continue

        try:
            analysis = await ai_service.analyze_amendment_text(
                matter_title=matter.title,
                attachment_name=att.name or "",
                text_content=att.content_text,
            )

            att.ai_summary = analysis.get("summary", "")
            att.ai_analysis = analysis
            att.analyzed = True

            # Update parent matter with extracted fields
            if analysis.get("approval_path") and analysis["approval_path"] != "unclear":
                matter.approval_path = analysis["approval_path"]
            if analysis.get("qualified_definition"):
                matter.qualified_definition = analysis["qualified_definition"]
            if analysis.get("power_provisions"):
                matter.power_provisions = analysis["power_provisions"]
            if analysis.get("infrastructure_triggers"):
                matter.infrastructure_triggers = analysis["infrastructure_triggers"]
            if analysis.get("compatibility_standards"):
                matter.compatibility_standards = analysis["compatibility_standards"]

            results.append({"attachment_id": att.id, "status": "analyzed", "summary": att.ai_summary[:200]})
        except Exception as e:
            results.append({"attachment_id": att.id, "status": "error", "reason": str(e)})

    db.commit()
    return {"matter_id": matter_id, "analyzed": len(results), "results": results}


@router.get("/watchlist/changes/recent")
async def get_recent_watchlist_changes(
    hours: int = Query(48, description="Look back this many hours"),
    db: Session = Depends(get_db),
):
    """Get recent changes across all watched matters (for dashboard / alerts)."""
    cutoff = datetime.now() - timedelta(hours=hours)

    new_histories = (
        db.query(MatterHistory)
        .filter(MatterHistory.discovered_date >= cutoff)
        .order_by(desc(MatterHistory.discovered_date))
        .all()
    )
    new_attachments = (
        db.query(MatterAttachment)
        .filter(MatterAttachment.discovered_date >= cutoff)
        .order_by(desc(MatterAttachment.discovered_date))
        .all()
    )
    new_votes = (
        db.query(MatterVote)
        .filter(MatterVote.discovered_date >= cutoff)
        .order_by(desc(MatterVote.discovered_date))
        .all()
    )

    # Gather matter titles for context
    matter_ids = set()
    for h in new_histories:
        matter_ids.add(h.matter_id)
    for a in new_attachments:
        matter_ids.add(a.matter_id)
    for v in new_votes:
        matter_ids.add(v.matter_id)

    matter_titles = {}
    if matter_ids:
        matters = db.query(WatchedMatter).filter(WatchedMatter.matter_id.in_(matter_ids)).all()
        matter_titles = {m.matter_id: m.title for m in matters}

    return {
        "period_hours": hours,
        "as_of": datetime.now().isoformat(),
        "histories": [
            {
                "matter_id": h.matter_id,
                "matter_title": matter_titles.get(h.matter_id, ""),
                "action_date": h.action_date.isoformat() if h.action_date else None,
                "action_text": h.action_text,
                "result": h.result,
                "is_milestone": h.is_milestone,
            }
            for h in new_histories
        ],
        "attachments": [
            {
                "matter_id": a.matter_id,
                "matter_title": matter_titles.get(a.matter_id, ""),
                "name": a.name,
                "hyperlink": a.hyperlink,
                "analyzed": a.analyzed,
            }
            for a in new_attachments
        ],
        "votes": [
            {
                "matter_id": v.matter_id,
                "matter_title": matter_titles.get(v.matter_id, ""),
                "vote_date": v.vote_date.isoformat() if v.vote_date else None,
                "result": v.result,
                "tally": v.tally,
            }
            for v in new_votes
        ],
    }


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


# ── Admin / Seed Endpoints ──────────────────────────────────────────────────

@router.post("/admin/seed-watchlist")
async def seed_watchlist(db: Session = Depends(get_db)):
    """Seed initial Amendment Watchlist items (idempotent — skips existing)."""
    from datetime import timezone

    items = [
        {
            "matter_id": 900001,
            "matter_file": "ZTA-2026-001",
            "matter_type": "Zoning Text Amendment",
            "title": "Zoning Text Amendment - Qualified Data Centers in AR and RE Zones",
            "body_name": "Prince George's County Planning Board",
            "current_status": "Initiated by Planning Board",
            "last_action_date": datetime(2026, 1, 29, tzinfo=timezone.utc),
            "watch_reason": "CRITICAL: Jan 29, 2026 Planning Board vote (3-0) formally initiated amendment to permit qualified data centers in AR and RE zones.",
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
            "watch_reason": "County resolution establishing a Data Center Task Force to study impact of data center development.",
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
            "watch_reason": "State-level executive order requiring evaluation of data center zoning and environmental impact across Maryland.",
            "priority": "high",
        },
        {
            "matter_id": 900004,
            "matter_file": "CHALK-POINT",
            "matter_type": "Development Project",
            "title": "Chalk Point Power Plant - Data Center Conversion/Redevelopment",
            "body_name": "Prince George's County Planning Board",
            "current_status": "Pre-Application / Monitoring",
            "watch_reason": "Tracking potential conversion of the retired Chalk Point coal-fired power plant site in Eagle Harbor for data center use.",
            "priority": "high",
        },
        {
            "matter_id": 900005,
            "matter_file": "LANDOVER-MALL",
            "matter_type": "Development Project",
            "title": "Landover Mall Site - Data Center Development Proposal",
            "body_name": "Prince George's County Planning Board",
            "current_status": "Monitoring",
            "watch_reason": "Monitoring the Landover Mall redevelopment site for potential data center components.",
            "priority": "medium",
        },
    ]

    inserted = 0
    skipped = 0
    for item_data in items:
        existing = db.query(WatchedMatter).filter_by(matter_id=item_data["matter_id"]).first()
        if existing:
            skipped += 1
            continue
        matter = WatchedMatter(**item_data)
        db.add(matter)
        db.flush()
        history = MatterHistory(
            matter_id=item_data["matter_id"],
            action_date=item_data.get("last_action_date") or datetime.now(timezone.utc),
            action_text="Added to Eagle Harbor Monitor watchlist",
            action_body=item_data["body_name"],
            is_milestone=True,
            notified=False,
        )
        db.add(history)
        inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped, "total": inserted + skipped}
