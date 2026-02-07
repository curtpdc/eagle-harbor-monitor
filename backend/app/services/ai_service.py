from openai import AzureOpenAI, APIConnectionError, APIStatusError, RateLimitError
from typing import List, Dict, Optional
from app.config import settings
from app.models import Article, Event
from datetime import datetime
import json
import asyncio
from functools import wraps
import logging
import time

logger = logging.getLogger(__name__)


def async_timeout(seconds):
    """Decorator to add timeout to async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"{func.__name__} timed out after {seconds} seconds")
        return wrapper
    return decorator


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self):
        # Azure OpenAI client (optional for local dev)
        if settings.AZURE_OPENAI_API_KEY:
            try:
                self.client = AzureOpenAI(
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version="2024-08-01-preview",  # Updated for AI Foundry
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    timeout=30.0,  # 30 second timeout for API calls
                    max_retries=2  # Retry failed requests
                )
                self.enabled = True
                self._log_config()
                logger.info("AI service initialized with Azure AI Foundry")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}")
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False
            logger.warning("AI service disabled: AZURE_OPENAI_API_KEY not configured")

    def _log_config(self):
        endpoint = settings.AZURE_OPENAI_ENDPOINT or ""
        endpoint_host = endpoint.split("//")[-1].split("/")[0] if endpoint else ""
        logger.info(
            "Azure OpenAI config: endpoint_host=%s deployment=%s api_version=%s key_set=%s",
            endpoint_host,
            settings.AZURE_OPENAI_DEPLOYMENT,
            "2024-08-01-preview",
            bool(settings.AZURE_OPENAI_API_KEY)
        )

    async def _call_openai_with_retry(self, call_fn, label: str) -> Optional[object]:
        for attempt in range(1, 3):
            try:
                start = time.monotonic()
                response = await call_fn()
                duration = time.monotonic() - start
                logger.info("Azure OpenAI %s completed in %.2fs", label, duration)
                return response
            except (RateLimitError, APIConnectionError, APIStatusError) as e:
                status = getattr(e, "status_code", None)
                retryable = isinstance(e, (RateLimitError, APIConnectionError)) or status in {429, 500, 502, 503, 504}
                logger.warning("Azure OpenAI %s failed (attempt %s): %s", label, attempt, e)
                if retryable and attempt < 2:
                    await asyncio.sleep(1.5 * attempt)
                    continue
                raise
    
    @async_timeout(45)  # 45 second total timeout including retries
    async def analyze_article(self, article_data: Dict) -> Dict:
        """Analyze article for relevance and priority using Azure OpenAI"""
        
        if not self.enabled:
            logger.info(f"[DEV MODE] Would analyze article: {article_data.get('title', 'Unknown')}")
            # Return mock analysis for dev mode
            return {
                "relevance_score": 5,
                "priority_score": 5,
                "category": "policy",
                "county": "prince_georges",
                "summary": "AI analysis not available in development mode",
                "key_points": ["Configure AZURE_OPENAI_API_KEY to enable AI analysis"]
            }
        
        content = f"{article_data.get('title', '')} {article_data.get('content', '')[:2000]}"
        
        prompt = f"""Analyze this article about Prince George's or Charles County, Maryland:

Title: {article_data.get('title')}
Source: {article_data.get('source')}
Content: {content}

Analyze for data center relevance and provide JSON with these exact keys:
1. relevance_score (0-10): How relevant is this to data center development?
2. priority_score (1-10): How urgent/important is this?
3. category: One of [policy, meeting, legislation, environmental, community, development]
4. county: One of [prince_georges, charles, both, unclear]
5. summary: 2-3 sentence summary
6. key_points: List of 3-5 key takeaways

Focus on:
- Zoning changes (AR zone, RE zone)
- Legislative amendments
- Planning Board actions
- Environmental impacts
- Community meetings
- Task Force activities (CR-98-2025, EO 42-2025)"""

        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are an expert analyst for Maryland data center policy and development. Analyze articles and return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)
            return analysis

        except Exception as e:
            print(f"AI analysis error: {e}")
            return self._fallback_analysis(article_data)

    def _fallback_analysis(self, article_data: Dict) -> Dict:
        """Simple keyword-based analysis if AI fails"""
        content_lower = f"{article_data.get('title', '')} {article_data.get('content', '')}".lower()
        
        critical_keywords = ['vote', 'approval', 'legislative amendment', 'zoning change']
        high_keywords = ['planning board', 'county council', 'task force']
        
        priority = 5
        if any(kw in content_lower for kw in critical_keywords):
            priority = 8
        elif any(kw in content_lower for kw in high_keywords):
            priority = 7

        return {
            'relevance_score': 5,
            'priority_score': priority,
            'category': 'general',
            'county': 'unclear',
            'summary': article_data.get('title', 'No summary available'),
            'key_points': []
        }
    
    @async_timeout(60)  # 60 second timeout for Q&A (longer for complex queries)
    async def answer_question(self, question: str, articles: List[Article], events: Optional[List[Event]] = None) -> Dict:
        """Answer user question using RAG with Azure OpenAI.
        
        Always grounds answers on provided article context. When no articles
        are provided the caller should still pass recent high-priority articles
        so we never fall back to stale training-data knowledge.
        """
        
        if not self.enabled:
            logger.info(f"[DEV MODE] Would answer question: {question}")
            return {
                'answer': "AI Q&A is not available in development mode. Please configure AZURE_OPENAI_API_KEY in backend/.env to enable this feature. For information about Prince George's County data center developments, visit the Planning Board website.",
                'sources': [],
                'confidence': 0.0
            }

        today = datetime.now().strftime("%B %d, %Y")

        logger.info(
            "AI Q&A request: question_len=%s articles=%s events=%s",
            len(question),
            len(articles) if articles else 0,
            len(events) if events else 0
        )

        # Build context from articles (use up to 10 for richer answers)
        # Support both ORM objects (attribute access) and dicts (key access)
        def _get(obj, key, default=''):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        article_list = articles[:10] if articles else []
        if article_list:
            context = "\n\n".join([
                f"Article: {_get(a, 'title')}\n"
                f"Source: {_get(a, 'source', 'unknown')}\n"
                f"Date: {_get(a, 'published_date') or _get(a, 'discovered_date', 'unknown')}\n"
                f"Summary: {_get(a, 'summary') or 'No summary'}\n"
                f"Content: {(_get(a, 'content') or '')[:500]}\n"
                f"Priority: {_get(a, 'priority_score', 'N/A')}/10\n"
                f"URL: {_get(a, 'url')}"
                for a in article_list
            ])
        else:
            context = "(No articles matched this query in our database.)"

        event_context = ""
        if events:
            event_lines = []
            for event in events[:5]:
                event_lines.append(
                    f"Event: {_get(event, 'title')}\n"
                    f"Type: {_get(event, 'event_type')}\n"
                    f"Date: {_get(event, 'event_date')}\n"
                    f"Location: {_get(event, 'location') or 'TBD'}\n"
                    f"County: {_get(event, 'county')}\n"
                    f"Description: {_get(event, 'description') or 'No description'}"
                )
            event_context = "\n\nUpcoming events:\n" + "\n\n".join(event_lines)

        system_prompt = (
            f"You are an expert analyst for the Eagle Harbor Data Center Monitor, "
            f"a real-time monitoring system tracking data center developments in "
            f"Prince George's County and Charles County, Maryland. Today is {today}. "
            f"Answer questions using ONLY the provided article context and events below. "
            f"If the provided context does not contain enough information to answer, "
            f"say so clearly and suggest the user check back as new articles are scraped "
            f"continuously from government and news sources. "
            f"NEVER fabricate facts or use information from before 2024 unless it appears "
            f"in the provided articles. Always cite sources by name and date when available."
        )

        has_context = bool(article_list) or bool(events)

        if has_context:
            prompt = f"""Based on the following recent monitored articles and events:

{context}
{event_context}

Answer this question:
{question}

Provide a clear, factual answer grounded in the information above. Cite article sources by name and date. If the articles only partially answer the question, say what is known and what gaps remain."""
        else:
            prompt = f"""The user asked: {question}

Our monitoring database currently has no articles matching this specific query. 
Provide a brief, helpful response that:
1. Acknowledges we don't have tracked articles on this specific topic yet
2. Provides relevant general context about data center policy in Prince George's County and Charles County, Maryland
3. Notes that our system continuously scrapes government sources (PG County Legistar, MNCPPC), Maryland news (Maryland Matters, WTOP, Washington Post, Patch, Baltimore Sun), and state government feeds
4. Suggests the user check back or rephrase their question

Keep the response concise and helpful."""

        try:
            loop = asyncio.get_event_loop()
            response = await self._call_openai_with_retry(
                lambda: loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=settings.AZURE_OPENAI_DEPLOYMENT,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.4,
                        max_tokens=2048
                    )
                ),
                "context_answer" if has_context else "no_context_answer"
            )

            answer = response.choices[0].message.content if response else ""
            confidence = 0.85 if has_context else 0.3
            logger.info(f"AI answer generated (has_context={has_context}): {answer[:100]}...")

            return {
                'answer': answer,
                'sources': [{'title': _get(a, 'title'), 'url': _get(a, 'url'), 'date': str(_get(a, 'published_date') or _get(a, 'discovered_date', 'unknown'))} for a in article_list],
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {e}")
            raise AIServiceError("Azure OpenAI call failed") from e
    
    async def extract_events(self, article_data: Dict) -> List[Dict]:
        """Extract event dates and details from article content"""
        
        content = f"{article_data.get('title', '')} {article_data.get('content', '')}"
        
        prompt = f"""Extract all upcoming events, meetings, deadlines, and important dates from this article about Maryland data centers.

Article Title: {article_data.get('title')}
Content: {content[:3000]}

Return a JSON array of events with this structure:
[
  {{
    "title": "Planning Board Meeting on Data Center Zoning",
    "event_type": "meeting",
    "event_date": "2026-02-15T14:00:00",
    "end_date": "2026-02-15T17:00:00",
    "location": "Planning Board Chambers, Upper Marlboro, MD",
    "description": "Public hearing on AR/RE zone amendment for data centers",
    "county": "prince_georges"
  }}
]

Event types: meeting, deadline, hearing, vote, protest, announcement
Counties: prince_georges, charles, both
Only include specific dates/times mentioned. Return empty array [] if no events found.
Format dates as ISO 8601 (YYYY-MM-DDTHH:MM:SS).
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting event information from government and news articles. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            # Handle both {"events": [...]} and direct array responses
            events = result.get('events', result if isinstance(result, list) else [])
            return events if isinstance(events, list) else []

        except Exception as e:
            print(f"Event extraction error: {e}")
            return []

