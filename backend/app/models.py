from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.sql import func
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
    category = Column(String(100))  # policy, meeting, legislation, environmental, community
    county = Column(String(100))  # prince_georges, charles, both
    
    # Processing status
    notified = Column(Boolean, default=False)
    analyzed = Column(Boolean, default=False)


class AlertSent(Base):
    __tablename__ = "alerts_sent"
    
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(500))
    sent_to = Column(JSON)  # Array of email addresses (stored as JSON for SQLite)
    article_ids = Column(JSON)  # Array of article IDs (stored as JSON for SQLite)
