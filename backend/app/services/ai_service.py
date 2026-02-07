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
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Fine-tuning data directory ───────────────────────────────────────────────
FINETUNE_DIR = Path(__file__).resolve().parent.parent / "finetune_data"
FINETUNE_DIR.mkdir(exist_ok=True)


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


# ── Scoring rubrics for consistent analysis ──────────────────────────────────

ARTICLE_ANALYSIS_SYSTEM = """You are a senior policy analyst specializing in Maryland data center developments, \
zoning law, environmental impact, and community stakeholder dynamics in Prince George's County and Charles County.

Your task is to analyze news articles and government documents, then return structured JSON assessments.

## Scoring Rubrics

### relevance_score (0–10)
- 0-1: No connection to Maryland data centers (national/tech industry noise)
- 2-3: Tangentially related (general MD energy, unrelated zoning)
- 4-5: Indirectly relevant (statewide data center policy, neighboring county actions)
- 6-7: Directly relevant (PG/Charles County data center discussion, PEPCO grid capacity)
- 8-9: Highly relevant (CR-98-2025, EO 42-2025, Eagle Harbor, Chalk Point, zoning amendments)
- 10: Breaking/critical (Planning Board vote, moratorium action, lawsuit filing)

### priority_score (1–10)
- 1-3: Informational/background (general industry trends, historical context)
- 4-5: Notable (new reports, early-stage proposals, committee formations)
- 6-7: Important (public hearings scheduled, draft legislation, environmental reviews)
- 8-9: Urgent (imminent votes, zoning decisions, legal challenges, emergency meetings)
- 10: Critical/breaking (final votes, moratorium enacted, major facility approved/denied)

### category (choose exactly ONE)
- "policy": Executive orders, regulatory frameworks, state/county policy changes
- "meeting": Planning Board, County Council, task force, public hearing agendas/minutes
- "legislation": Bills, resolutions, zoning text amendments (CR-98-2025, EO 42-2025)
- "environmental": Environmental impact studies, water/air quality, grid capacity, energy
- "community": Resident opposition, town halls, petitions, community group actions
- "development": Site plans, facility proposals, construction updates, corporate announcements

### county (choose exactly ONE)
- "prince_georges": Specific to PG County (Upper Marlboro, Brandywine, Bowie, Eagle Harbor, Chalk Point)
- "charles": Specific to Charles County (Waldorf, La Plata, Indian Head)
- "both": Affects both counties or Southern Maryland corridor
- "maryland_statewide": State-level policy affecting all MD counties
- "unclear": Cannot determine geographic focus

## Critical keywords that INCREASE scores
CR-98-2025, EO 42-2025, Eagle Harbor, Chalk Point, qualified data center, AR zone, RE zone,
MNCPPC, Planning Board, zoning text amendment, moratorium, special exception, PEPCO, grid capacity,
Landover Mall, Brandywine, task force, environmental justice, Patuxent River

Return ONLY valid JSON with keys: relevance_score, priority_score, category, county, summary, key_points."""


CHAT_SYSTEM_TEMPLATE = """You are the Eagle Harbor Monitor AI — an expert analyst on data center \
developments in Prince George's County and Charles County, Maryland. Today is {today}.

## Your expertise
- Maryland zoning law (AR zone, RE zone, planned communities)
- County governance (MNCPPC, PG County Council, Planning Board procedures)
- Key legislation: CR-98-2025 (Data Center Task Force), EO 42-2025 (state evaluation)
- Environmental impacts: grid capacity (PEPCO/Exelon), water usage, heat islands
- Key sites: Chalk Point Power Plant, Landover Mall, Eagle Harbor
- Community stakeholder dynamics and opposition movements

## Rules
1. **Ground answers in provided article/event context.** Cite sources by name and date.
2. When context is insufficient, say so explicitly — suggest the user check back as new \
articles are scraped continuously from government and news sources.
3. **NEVER fabricate facts, dates, vote counts, or meeting outcomes.** If you don't know, say so.
4. For questions about broader Maryland data center trends, provide what you know but \
clearly distinguish between monitored facts (from articles) and general knowledge.
5. When discussing upcoming votes or decisions, note that outcomes are uncertain until official results.
6. Always mention relevant legislation (CR-98-2025, EO 42-2025) when applicable.
7. For meeting/hearing questions, include dates, locations, and how residents can participate.
8. Keep answers concise but thorough. Use bullet points for multi-part answers.
9. If asked about topics completely outside Maryland data centers, briefly redirect to your focus area.

## Source hierarchy (most to least authoritative)
1. PG County Legistar / official government records
2. MNCPPC Planning Board documents
3. Maryland Matters, Baltimore Sun (state-level reporting)
4. WTOP, Washington Post (regional reporting)
5. Patch, local community sources"""


EVENT_EXTRACTION_SYSTEM = """You are an expert at extracting structured event data from government \
documents and news articles about Maryland data center developments.

## Rules
1. Only extract events with SPECIFIC dates/times mentioned in the text.
2. Infer reasonable end times for meetings (typically 2-3 hours) if not stated.
3. For recurring meetings (e.g., "every 2nd Thursday"), set is_recurring=true.
4. Use ISO 8601 format: YYYY-MM-DDTHH:MM:SS
5. Event types: meeting, deadline, hearing, vote, protest, announcement
6. Counties: prince_georges, charles, both
7. If a date is ambiguous or uncertain, skip it — do NOT guess.
8. Return empty array [] if no concrete events are found."""


# ── Amendment / Zoning Text Analysis ─────────────────────────────────────────

AMENDMENT_ANALYSIS_SYSTEM = """You are a senior Maryland zoning and land-use attorney \
analysing a draft zoning text amendment or legislative document related to data center \
development in Prince George's County and/or Charles County, Maryland.

Your job is to extract structured findings that community stakeholders need to evaluate \
the amendment's impact. Be precise — quote specific sections/page numbers when possible.

## Required analysis fields

1. **approval_path**: How would data centers be approved under this text?
   - "by_right" — Permitted by right (no discretionary review)
   - "special_exception" — Requires Special Exception / Conditional Use approval
   - "both" — By-right for some sizes/zones, special exception for others
   - "unclear" — Text does not specify or is ambiguous

2. **qualified_definition**: What does the text define as a "qualified data center"?
   Extract MW thresholds, size limits (sq ft), tier classifications.
   If no explicit definition, say "not defined in this text."

3. **power_provisions**: What does the text say about on-site power generation?
   - Backup generators: fuel type (diesel/natural gas), run-time limits
   - On-site generation (co-gen, solar, fuel cells): allowed? required?
   - Grid interconnection requirements, PJM obligations

4. **infrastructure_triggers**: What infrastructure investments are required?
   - Substation construction / upgrades
   - Road improvements
   - Water / sewer capacity assessments
   - Fiscal impact studies or development impact fees

5. **compatibility_standards**: What protections exist for surrounding communities?
   - Setback distances (from residential, from waterways)
   - Noise limits (dBA at property line)
   - Height restrictions
   - Screening / buffering requirements
   - Water consumption / discharge limits
   - Light pollution / dark-sky provisions

6. **zones_affected**: Which zoning districts does this amendment modify?
   List all zone codes mentioned (AR, RE, M-X-T, etc.)

7. **public_participation**: What public input process does the text contemplate?
   - Required public hearings
   - Comment periods
   - Community benefit agreements
   - Environmental review requirements

8. **risk_assessment**: Rate HIGH / MEDIUM / LOW for each:
   - "environmental_risk": Impact on water, air, and habitat
   - "community_risk": Impact on residential quality of life
   - "grid_risk": Impact on local power reliability
   - "approval_risk": Likelihood of passage without modification

9. **summary**: 2-3 sentence plain-English summary for a concerned resident.

10. **key_concerns**: Array of 3-6 specific items residents should raise in public comment.

Return ONLY valid JSON with these keys."""


class AIServiceError(Exception):
    pass


class AIService:
    def __init__(self):
        # Azure OpenAI client (optional for local dev)
        if settings.AZURE_OPENAI_API_KEY:
            try:
                self.client = AzureOpenAI(
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version="2024-08-01-preview",
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    timeout=30.0,
                    max_retries=2
                )
                self.enabled = True
                self._log_config()
                logger.info("AI service initialized with Azure OpenAI")
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

    # ── Fine-tuning data collection ──────────────────────────────────────────

    def _log_finetune_pair(self, task: str, messages: List[Dict], response_text: str):
        """Save prompt/response pairs in JSONL format for future fine-tuning."""
        try:
            record = {
                "task": task,
                "timestamp": datetime.utcnow().isoformat(),
                "messages": messages,
                "completion": response_text,
            }
            filepath = FINETUNE_DIR / f"{task}.jsonl"
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug(f"Failed to log fine-tune data: {e}")

    # ── Validation helpers ───────────────────────────────────────────────────

    @staticmethod
    def _validate_analysis(analysis: Dict) -> Dict:
        """Clamp scores to valid ranges and normalise category/county values."""
        valid_categories = {"policy", "meeting", "legislation", "environmental", "community", "development"}
        valid_counties = {"prince_georges", "charles", "both", "maryland_statewide", "unclear"}

        analysis["relevance_score"] = max(0, min(10, int(analysis.get("relevance_score", 5))))
        analysis["priority_score"] = max(1, min(10, int(analysis.get("priority_score", 5))))

        cat = str(analysis.get("category", "")).lower().strip()
        analysis["category"] = cat if cat in valid_categories else "policy"

        county = str(analysis.get("county", "")).lower().strip()
        analysis["county"] = county if county in valid_counties else "unclear"

        if not analysis.get("summary"):
            analysis["summary"] = "No summary available"
        if not isinstance(analysis.get("key_points"), list):
            analysis["key_points"] = []

        return analysis

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

    # ── Article Analysis ─────────────────────────────────────────────────────

    @async_timeout(45)
    async def analyze_article(self, article_data: Dict) -> Dict:
        """Analyze article for relevance and priority using Azure OpenAI.
        
        Uses a detailed scoring rubric and domain-specific system prompt for
        consistent, high-quality classification. Results are validated and
        clamped to valid ranges before returning.
        """
        
        if not self.enabled:
            logger.info(f"[DEV MODE] Would analyze article: {article_data.get('title', 'Unknown')}")
            return {
                "relevance_score": 5,
                "priority_score": 5,
                "category": "policy",
                "county": "prince_georges",
                "summary": "AI analysis not available in development mode",
                "key_points": ["Configure AZURE_OPENAI_API_KEY to enable AI analysis"]
            }
        
        # Provide more content to the model for better analysis
        title = article_data.get('title', '')
        source = article_data.get('source', 'unknown')
        content = article_data.get('content', '')[:settings.AI_MAX_CONTENT_CHARS]
        pub_date = article_data.get('published_date', 'unknown')
        
        user_prompt = f"""Analyze this article:

Title: {title}
Source: {source}
Published: {pub_date}
Content:
{title} {content}

Return JSON with keys: relevance_score, priority_score, category, county, summary, key_points (3-5 items)."""

        messages = [
            {"role": "system", "content": ARTICLE_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                temperature=settings.AI_ANALYSIS_TEMPERATURE,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content
            analysis = self._validate_analysis(json.loads(raw))

            # Log for fine-tuning data collection
            self._log_finetune_pair("article_analysis", messages, raw)

            logger.info(
                "Article analyzed: title=%s relevance=%s priority=%s category=%s county=%s",
                title[:60], analysis["relevance_score"], analysis["priority_score"],
                analysis["category"], analysis["county"]
            )
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"AI returned invalid JSON: {e}")
            return self._fallback_analysis(article_data)
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return self._fallback_analysis(article_data)

    def _fallback_analysis(self, article_data: Dict) -> Dict:
        """Enhanced keyword-based analysis when AI is unavailable."""
        content_lower = f"{article_data.get('title', '')} {article_data.get('content', '')}".lower()
        
        # Tiered keyword scoring for priority
        critical_keywords = [
            'vote', 'approval', 'denied', 'moratorium', 'legislative amendment',
            'zoning change', 'cr-98-2025', 'eo 42-2025', 'emergency',
        ]
        high_keywords = [
            'planning board', 'county council', 'task force', 'public hearing',
            'zoning text amendment', 'special exception', 'eagle harbor', 'chalk point',
        ]
        medium_keywords = [
            'data center', 'datacenter', 'PEPCO', 'grid capacity', 'environmental',
            'ar zone', 're zone', 'mncppc', 'qualified data center',
        ]
        
        priority = 4
        relevance = 4
        if any(kw in content_lower for kw in critical_keywords):
            priority = 9
            relevance = 8
        elif any(kw in content_lower for kw in high_keywords):
            priority = 7
            relevance = 7
        elif any(kw in content_lower for kw in medium_keywords):
            priority = 5
            relevance = 5

        # Infer category from keywords
        category = "policy"
        if any(kw in content_lower for kw in ['meeting', 'hearing', 'agenda', 'session']):
            category = "meeting"
        elif any(kw in content_lower for kw in ['bill', 'resolution', 'amendment', 'legislation', 'cr-98']):
            category = "legislation"
        elif any(kw in content_lower for kw in ['environmental', 'water', 'air quality', 'grid', 'energy']):
            category = "environmental"
        elif any(kw in content_lower for kw in ['residents', 'community', 'opposition', 'protest', 'petition']):
            category = "community"
        elif any(kw in content_lower for kw in ['construction', 'facility', 'site plan', 'megawatt', 'campus']):
            category = "development"

        # Infer county
        county = "unclear"
        pg = any(kw in content_lower for kw in ['prince george', 'pg county', 'upper marlboro', 'eagle harbor', 'chalk point', 'brandywine', 'bowie'])
        ch = any(kw in content_lower for kw in ['charles county', 'waldorf', 'la plata', 'indian head'])
        if pg and ch:
            county = "both"
        elif pg:
            county = "prince_georges"
        elif ch:
            county = "charles"
        elif 'maryland' in content_lower:
            county = "maryland_statewide"

        return {
            'relevance_score': relevance,
            'priority_score': priority,
            'category': category,
            'county': county,
            'summary': article_data.get('title', 'No summary available'),
            'key_points': []
        }
    
    @async_timeout(60)
    async def answer_question(self, question: str, articles: List[Article], events: Optional[List[Event]] = None) -> Dict:
        """Answer user question using RAG with Azure OpenAI.
        
        Uses domain-expert persona, structured context injection, and confidence
        scoring calibrated to context coverage.
        """
        
        if not self.enabled:
            logger.info(f"[DEV MODE] Would answer question: {question}")
            return {
                'answer': (
                    "AI Q&A is not available in development mode. Please configure "
                    "AZURE_OPENAI_API_KEY in backend/.env to enable this feature. "
                    "For information about Prince George's County data center developments, "
                    "visit the Planning Board website."
                ),
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

        # ── Build article context ────────────────────────────────────────────
        def _get(obj, key, default=''):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        article_list = articles[:10] if articles else []
        if article_list:
            context = "\n\n---\n".join([
                f"[Article {i+1}] {_get(a, 'title')}\n"
                f"Source: {_get(a, 'source', 'unknown')} | "
                f"Date: {_get(a, 'published_date') or _get(a, 'discovered_date', 'unknown')} | "
                f"Priority: {_get(a, 'priority_score', 'N/A')}/10 | "
                f"Category: {_get(a, 'category', 'N/A')}\n"
                f"Summary: {_get(a, 'summary') or 'No summary'}\n"
                f"Content excerpt: {(_get(a, 'content') or '')[:600]}\n"
                f"URL: {_get(a, 'url')}"
                for i, a in enumerate(article_list)
            ])
        else:
            context = "(No articles matched this query in our database.)"

        # ── Build event context ──────────────────────────────────────────────
        event_context = ""
        if events:
            event_lines = []
            for event in events[:5]:
                event_lines.append(
                    f"Event: {_get(event, 'title')}\n"
                    f"Type: {_get(event, 'event_type')} | "
                    f"Date: {_get(event, 'event_date')} | "
                    f"Location: {_get(event, 'location') or 'TBD'} | "
                    f"County: {_get(event, 'county')}\n"
                    f"Description: {_get(event, 'description') or 'No description'}"
                )
            event_context = "\n\n## Upcoming Events\n" + "\n\n".join(event_lines)

        # ── System prompt from template ──────────────────────────────────────
        system_prompt = CHAT_SYSTEM_TEMPLATE.format(today=today)

        has_context = bool(article_list) or bool(events)

        if has_context:
            user_prompt = f"""## Monitored Articles
{context}
{event_context}

## Question
{question}

Answer using the articles/events above. Cite sources by [Article N] reference and name. \
If the articles only partially answer the question, state what is known and what gaps remain."""
        else:
            user_prompt = f"""The user asked: {question}

Our monitoring database currently has no articles matching this specific query.
Provide a brief, helpful response that:
1. Acknowledges we don't have tracked articles on this specific topic yet
2. Provides relevant general context about data center policy in Prince George's County and Charles County, Maryland
3. Notes that our system continuously scrapes government sources (PG County Legistar, MNCPPC), Maryland news (Maryland Matters, WTOP, Washington Post, Patch, Baltimore Sun), and state government feeds
4. Suggests the user check back or rephrase their question

Keep the response concise and helpful."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            loop = asyncio.get_event_loop()
            response = await self._call_openai_with_retry(
                lambda: loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=settings.AZURE_OPENAI_DEPLOYMENT,
                        messages=messages,
                        temperature=settings.AI_CHAT_TEMPERATURE,
                        max_tokens=2048
                    )
                ),
                "context_answer" if has_context else "no_context_answer"
            )

            answer = response.choices[0].message.content if response else ""

            # Calibrated confidence scoring
            if has_context:
                n_articles = len(article_list)
                n_events = len(events) if events else 0
                # More sources = higher confidence, capped at 0.95
                confidence = min(0.95, 0.5 + 0.05 * n_articles + 0.03 * n_events)
            else:
                confidence = 0.25

            # Log for fine-tuning
            self._log_finetune_pair("chat_qa", messages, answer)

            logger.info(
                "AI answer generated: has_context=%s confidence=%.2f answer_len=%s",
                has_context, confidence, len(answer)
            )

            return {
                'answer': answer,
                'sources': [
                    {
                        'title': _get(a, 'title'),
                        'url': _get(a, 'url'),
                        'date': str(_get(a, 'published_date') or _get(a, 'discovered_date', 'unknown'))
                    }
                    for a in article_list
                ],
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {e}")
            raise AIServiceError("Azure OpenAI call failed") from e
    
    async def extract_events(self, article_data: Dict) -> List[Dict]:
        """Extract event dates and details from article content using structured prompt."""
        
        title = article_data.get('title', '')
        content = article_data.get('content', '')[:settings.AI_MAX_CONTENT_CHARS]
        
        user_prompt = f"""Extract all upcoming events, meetings, deadlines, and important dates from this article.

Article Title: {title}
Content: {title} {content}

Return a JSON object with an "events" key containing an array. Each event:
{{
  "title": "descriptive event title",
  "event_type": "meeting|deadline|hearing|vote|protest|announcement",
  "event_date": "YYYY-MM-DDTHH:MM:SS",
  "end_date": "YYYY-MM-DDTHH:MM:SS or null",
  "location": "venue and address if mentioned",
  "description": "1-2 sentence description of what will happen",
  "county": "prince_georges|charles|both"
}}

Return {{"events": []}} if no specific dates are found."""

        messages = [
            {"role": "system", "content": EVENT_EXTRACTION_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                temperature=settings.AI_EVENT_TEMPERATURE,   # Very low for precise date extraction
                max_tokens=1024,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content
            result = json.loads(raw)
            events = result.get('events', result if isinstance(result, list) else [])

            # Log for fine-tuning
            self._log_finetune_pair("event_extraction", messages, raw)

            return events if isinstance(events, list) else []

        except Exception as e:
            logger.error(f"Event extraction error: {e}")
            return []

    # ── Amendment Text Analysis ──────────────────────────────────────────────

    @async_timeout(90)
    async def analyze_amendment_text(self, matter_title: str, attachment_name: str,
                                     text_content: str) -> Dict:
        """Analyze a zoning text amendment or legislative attachment for community impact.

        Returns structured analysis covering approval path, qualified definition,
        power provisions, infrastructure triggers, compatibility standards, risk
        assessment, and key concerns for public comment.
        """
        if not self.enabled:
            return {
                "summary": "AI analysis not available in development mode",
                "approval_path": "unclear",
                "qualified_definition": "Not analyzed",
                "power_provisions": "Not analyzed",
                "infrastructure_triggers": "Not analyzed",
                "compatibility_standards": "Not analyzed",
                "zones_affected": [],
                "public_participation": "Not analyzed",
                "risk_assessment": {
                    "environmental_risk": "MEDIUM",
                    "community_risk": "MEDIUM",
                    "grid_risk": "MEDIUM",
                    "approval_risk": "MEDIUM",
                },
                "key_concerns": ["Configure AZURE_OPENAI_API_KEY to enable analysis"],
            }

        # Send more content for amendment analysis (these docs are critical)
        content = text_content[:8000]

        user_prompt = f"""Analyze this zoning text amendment / legislative document:

Matter: {matter_title}
Attachment: {attachment_name}

Full Text:
{content}

Return JSON with keys: approval_path, qualified_definition, power_provisions, \
infrastructure_triggers, compatibility_standards, zones_affected, public_participation, \
risk_assessment, summary, key_concerns."""

        messages = [
            {"role": "system", "content": AMENDMENT_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]

        try:
            loop = asyncio.get_event_loop()
            response = await self._call_openai_with_retry(
                lambda: loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=settings.AZURE_OPENAI_DEPLOYMENT,
                        messages=messages,
                        temperature=0.15,  # Very precise for legal/policy analysis
                        max_tokens=2048,
                        response_format={"type": "json_object"},
                    ),
                ),
                "amendment_analysis",
            )

            raw = response.choices[0].message.content if response else "{}"
            analysis = json.loads(raw)

            # Log for fine-tuning
            self._log_finetune_pair("amendment_analysis", messages, raw)

            logger.info(
                "Amendment analyzed: matter=%s approval_path=%s",
                matter_title[:60],
                analysis.get("approval_path", "unknown"),
            )
            return analysis

        except Exception as e:
            logger.error(f"Amendment analysis error: {e}")
            return {
                "summary": f"Analysis failed: {e}",
                "approval_path": "unclear",
                "key_concerns": [],
            }

    # ── Feedback / Evaluation ────────────────────────────────────────────────

    def record_feedback(self, question: str, answer: str, rating: int, comment: str = "") -> bool:
        """Record user feedback for answer quality evaluation.
        
        Args:
            question: The original user question
            answer: The AI-generated answer
            rating: 1-5 star rating (1=poor, 5=excellent)
            comment: Optional free-text feedback
            
        Returns:
            True if recorded successfully
        """
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "question": question,
                "answer": answer[:500],   # Truncate for storage
                "rating": max(1, min(5, rating)),
                "comment": comment,
            }
            filepath = FINETUNE_DIR / "feedback.jsonl"
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.info(f"Feedback recorded: rating={rating}")
            return True
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            return False

    def get_finetune_stats(self) -> Dict:
        """Return counts of collected fine-tuning data and feedback."""
        stats = {}
        for filename in ["article_analysis.jsonl", "chat_qa.jsonl", "event_extraction.jsonl", "feedback.jsonl"]:
            filepath = FINETUNE_DIR / filename
            if filepath.exists():
                with open(filepath, "r") as f:
                    stats[filename.replace(".jsonl", "")] = sum(1 for _ in f)
            else:
                stats[filename.replace(".jsonl", "")] = 0
        return stats

