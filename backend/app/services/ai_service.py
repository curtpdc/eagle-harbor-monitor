from openai import AzureOpenAI
from typing import List, Dict
from app.config import settings
from app.models import Article
import json
import asyncio
from functools import wraps


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


class AIService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            timeout=30.0,  # 30 second timeout for API calls
            max_retries=2  # Retry failed requests
        )
    
    @async_timeout(45)  # 45 second total timeout including retries
    async def analyze_article(self, article_data: Dict) -> Dict:
        """Analyze article for relevance and priority using Azure OpenAI"""
        
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
    async def answer_question(self, question: str, articles: List[Article]) -> Dict:
        """Answer user question using RAG with Azure OpenAI"""

        # If no articles, provide general information
        if not articles or len(articles) == 0:
            try:
                prompt = f"""You are an expert on data center policy in Prince George's County and Charles County, Maryland.

The user asks: {question}

Provide a helpful, accurate answer based on your knowledge of:
- Prince George's County data center moratorium (enacted January 26, 2021)
- CR-98-2025 and Executive Order 42-2025 creating a Data Center Task Force
- Planning Board's review of zoning amendments
- Community concerns about environmental impacts
- Current status of AR and RE zoning changes

If you don't know specific recent updates, explain what you know and recommend checking official county sources."""

                response = self.client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": "You are an expert on data center policy in Prince George's County and Charles County, Maryland. Provide clear, factual answers."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2048
                )

                return {
                    'answer': response.choices[0].message.content,
                    'sources': [],
                    'confidence': 0.7
                }
            except Exception as e:
                return {
                    'answer': f"I'm currently setting up my knowledge base. Please try again soon. In the meantime, you can check the Prince George's County Planning Board website for official updates on data center developments.",
                    'sources': [],
                    'confidence': 0.0
                }

        # Build context from recent articles
        context = "\n\n".join([
            f"Article: {a.title}\n"
            f"Source: {a.source}\n"
            f"Date: {a.published_date}\n"
            f"Summary: {a.summary or 'No summary'}\n"
            f"URL: {a.url}"
            for a in articles[:5]
        ])

        prompt = f"""You are an expert on data center policy in Prince George's County and Charles County, Maryland.

Based on this recent information:

{context}

Answer this question:
{question}

Provide a clear, factual answer based on the information provided. If you don't have enough information, say so. Include relevant dates and sources."""

        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are an expert on data center policy in Prince George's County and Charles County, Maryland. Provide clear, factual answers based on the provided information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2048
            )

            return {
                'answer': response.choices[0].message.content,
                'sources': [{'title': a.title, 'url': a.url, 'date': str(a.published_date)} for a in articles[:5]],
                'confidence': 0.85
            }

        except Exception as e:
            return {
                'answer': f"I apologize, but I'm having trouble processing your question right now. Please try again later. Error: {str(e)}",
                'sources': [],
                'confidence': 0.0
            }
    
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

