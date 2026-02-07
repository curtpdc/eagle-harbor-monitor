from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Subscriber(Base):
    __tablename__ = "subscribers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    verified = Column(Boolean, default=False)
    verification_token = Column(String(100), unique=True)
    unsubscribe_token = Column(String(100), unique=True, nullable=False)
    subscribed_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    summary = Column(Text)
    content = Column(Text)
    source = Column(String(200), nullable=False)
    published_date = Column(DateTime)
    discovered_date = Column(DateTime, default=func.now(), index=True)
    
    # Classification
    priority_score = Column(Integer)  # 1-10
    relevance_score = Column(Integer)  # 0-10: Maryland relevance (8+ = PG/Charles, 0-1 = not MD)
    category = Column(String(100))  # policy, meeting, legislation, environmental, community
    county = Column(String(100))  # prince_georges, charles, both, maryland_statewide, unclear
    event_date = Column(DateTime, index=True)  # For articles about future events
    
    # Processing status
    notified = Column(Boolean, default=False)
    analyzed = Column(Boolean, default=False)


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    event_type = Column(String(100))  # meeting, deadline, hearing, vote, protest, announcement
    event_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime)  # For multi-day events
    location = Column(String(500))
    description = Column(Text)
    article_id = Column(Integer, ForeignKey('articles.id'))
    county = Column(String(100))  # prince_georges, charles, both
    
    # Event metadata
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(200))  # e.g., "Every 2nd Thursday"
    
    # Status tracking
    is_past = Column(Boolean, default=False)
    is_cancelled = Column(Boolean, default=False)
    
    created_date = Column(DateTime, default=func.now())
    sent_at = Column(DateTime, default=func.now())


class AlertSent(Base):
    __tablename__ = "alerts_sent"
    
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(500))
    sent_to = Column(JSON)  # Array of email addresses (stored as JSON for SQLite)
    article_ids = Column(JSON)  # Array of article IDs (stored as JSON for SQLite)


# ── Amendment Watchlist Models ───────────────────────────────────────────────

class WatchedMatter(Base):
    """A Legistar matter (legislation/resolution/amendment) being actively tracked.

    These are specific pieces of legislation the system monitors for status
    changes, new attachments (draft text, staff reports), and votes.
    """
    __tablename__ = "watched_matters"

    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, unique=True, nullable=False, index=True)  # Legistar MatterId
    matter_file = Column(String(100))       # e.g., "CB-001-2026" or "CZ-001-2026"
    matter_type = Column(String(100))       # e.g., "Zoning Text Amendment", "Resolution"
    title = Column(String(500), nullable=False)
    body_name = Column(String(200))         # Originating body (Planning Board, County Council)
    current_status = Column(String(200))    # Latest Legistar status
    last_action_date = Column(DateTime)
    legistar_url = Column(String(1000))

    # Tracking metadata
    watch_reason = Column(Text)             # Why this is being tracked
    auto_detected = Column(Boolean, default=False)   # True if scraper found it, False if manually added
    is_active = Column(Boolean, default=True)        # Set False when fully resolved
    priority = Column(String(20), default="high")    # high, medium, low

    # Amendment-specific analysis fields (populated by AI)
    approval_path = Column(String(100))     # "by-right" / "special exception" / "unknown"
    qualified_definition = Column(Text)     # What "qualified data center" means in this text
    power_provisions = Column(Text)         # On-site power generation rules
    infrastructure_triggers = Column(Text)  # PJM / substation requirements
    compatibility_standards = Column(Text)  # Setbacks, noise, height, water limits

    created_date = Column(DateTime, default=func.now())
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    histories = relationship("MatterHistory", back_populates="matter", order_by="desc(MatterHistory.action_date)")
    attachments = relationship("MatterAttachment", back_populates="matter", order_by="desc(MatterAttachment.discovered_date)")
    votes = relationship("MatterVote", back_populates="matter", order_by="desc(MatterVote.vote_date)")


class MatterHistory(Base):
    """Status transition log for a watched matter from Legistar /matters/{id}/histories."""
    __tablename__ = "matter_histories"

    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("watched_matters.matter_id"), nullable=False, index=True)
    legistar_history_id = Column(Integer, unique=True)  # Dedup key

    action_date = Column(DateTime, index=True)
    action_text = Column(String(500))       # e.g., "Introduced", "Referred to Committee"
    action_body = Column(String(200))       # Body that took the action
    result = Column(String(100))            # "Pass", "Fail", "Amended", etc.
    vote_info = Column(String(200))         # e.g., "3-0" summary
    minutes_note = Column(Text)             # Clerk/minutes notes

    # Change detection
    previous_status = Column(String(200))
    new_status = Column(String(200))
    is_milestone = Column(Boolean, default=False)  # True for significant transitions

    notified = Column(Boolean, default=False)
    discovered_date = Column(DateTime, default=func.now())

    matter = relationship("WatchedMatter", back_populates="histories")


class MatterAttachment(Base):
    """Attachments (draft text, staff reports, memos) for a watched matter."""
    __tablename__ = "matter_attachments"

    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("watched_matters.matter_id"), nullable=False, index=True)
    legistar_attachment_id = Column(Integer, unique=True)

    name = Column(String(500))              # File name / label
    hyperlink = Column(String(1000))        # Download URL
    file_type = Column(String(50))          # pdf, docx, etc.
    content_text = Column(Text)             # Extracted text (if scrape-able)

    # AI analysis of attachment text
    ai_summary = Column(Text)
    ai_analysis = Column(JSON)              # Structured analysis result
    analyzed = Column(Boolean, default=False)

    discovered_date = Column(DateTime, default=func.now())
    notified = Column(Boolean, default=False)

    matter = relationship("WatchedMatter", back_populates="attachments")


class MatterVote(Base):
    """Roll-call vote records for a watched matter."""
    __tablename__ = "matter_votes"

    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("watched_matters.matter_id"), nullable=False, index=True)
    legistar_vote_id = Column(Integer, unique=True)

    vote_date = Column(DateTime, index=True)
    body_name = Column(String(200))         # Body that voted
    result = Column(String(100))            # "Pass", "Fail"
    tally = Column(String(50))              # e.g., "3-0", "7-2-2"

    # Individual votes as JSON: [{"person": "Name", "vote": "Aye"}, ...]
    roll_call = Column(JSON)

    notified = Column(Boolean, default=False)
    discovered_date = Column(DateTime, default=func.now())

    matter = relationship("WatchedMatter", back_populates="votes")
