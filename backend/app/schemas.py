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


class FeedbackRequest(BaseModel):
    question: str
    answer: str
    rating: int   # 1-5
    comment: Optional[str] = ""


class FeedbackResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    database: str
    last_scrape: Optional[datetime]


# ── Amendment Watchlist Schemas ──────────────────────────────────────────────

class WatchedMatterCreate(BaseModel):
    matter_id: int
    title: str
    matter_file: Optional[str] = None
    matter_type: Optional[str] = None
    body_name: Optional[str] = None
    watch_reason: Optional[str] = None
    priority: str = "high"


class MatterHistoryResponse(BaseModel):
    id: int
    action_date: Optional[datetime]
    action_text: Optional[str]
    action_body: Optional[str]
    result: Optional[str]
    vote_info: Optional[str]
    previous_status: Optional[str]
    new_status: Optional[str]
    is_milestone: bool
    discovered_date: Optional[datetime]

    class Config:
        from_attributes = True


class MatterAttachmentResponse(BaseModel):
    id: int
    name: Optional[str]
    hyperlink: Optional[str]
    file_type: Optional[str]
    ai_summary: Optional[str]
    analyzed: bool
    discovered_date: Optional[datetime]

    class Config:
        from_attributes = True


class MatterVoteResponse(BaseModel):
    id: int
    vote_date: Optional[datetime]
    body_name: Optional[str]
    result: Optional[str]
    tally: Optional[str]
    roll_call: Optional[List[dict]]
    discovered_date: Optional[datetime]

    class Config:
        from_attributes = True


class WatchedMatterResponse(BaseModel):
    id: int
    matter_id: int
    matter_file: Optional[str]
    matter_type: Optional[str]
    title: str
    body_name: Optional[str]
    current_status: Optional[str]
    last_action_date: Optional[datetime]
    legistar_url: Optional[str]
    watch_reason: Optional[str]
    is_active: bool
    priority: str
    approval_path: Optional[str]
    qualified_definition: Optional[str]
    power_provisions: Optional[str]
    infrastructure_triggers: Optional[str]
    compatibility_standards: Optional[str]
    created_date: Optional[datetime]
    updated_date: Optional[datetime]

    class Config:
        from_attributes = True


class WatchedMatterDetailResponse(WatchedMatterResponse):
    """Full detail including history, attachments, and votes."""
    histories: List[MatterHistoryResponse] = []
    attachments: List[MatterAttachmentResponse] = []
    votes: List[MatterVoteResponse] = []
