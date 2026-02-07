from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class SubscriberCreate(BaseModel):
    email: EmailStr


class SubscriberResponse(BaseModel):
    message: str
    
    
class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    summary: Optional[str]
    source: str
    published_date: Optional[datetime]
    discovered_date: datetime
    priority_score: Optional[int]
    relevance_score: Optional[int]
    category: Optional[str]
    county: Optional[str]
    
    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    page: int
    limit: int


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: str
    sources: List[dict]
    confidence: float


class HealthResponse(BaseModel):
    status: str
    database: str
    last_scrape: Optional[datetime]
