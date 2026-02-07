"""Test AI chat integration with a real question"""

import asyncio
import re
import logging
from datetime import datetime, timedelta
from sqlalchemy import or_, desc
from app.database import SessionLocal
from app.models import Article, Event
from app.services.ai_service import AIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ask():
    question = "What is the latest on the Data Center Task Force in Prince George's County?"
    print(f"\n{'='*80}")
    print(f"QUESTION: {question}")
    print(f"{'='*80}\n")

    db = SessionLocal()
    ai_service = AIService()
    print(f"AI service enabled: {ai_service.enabled}")

    question_lower = question.lower()

    # Domain phrase detection (same logic as routes.py)
    domain_phrases = []
    phrase_map = {
        "data center": "data center", "task force": "task force",
        "planning board": "planning board", "eagle harbor": "eagle harbor",
        "chalk point": "chalk point", "zoning amendment": "zoning amendment",
    }
    for phrase in phrase_map:
        if phrase in question_lower:
            domain_phrases.append(phrase_map[phrase])

    stopwords = {
        "the", "a", "an", "and", "or", "but", "if", "then", "to", "of", "in", "on", "for", "with",
        "is", "are", "was", "were", "be", "been", "being", "it", "this", "that", "these", "those",
        "what", "when", "where", "why", "how", "about", "from", "by", "as", "at", "into", "over",
        "do", "does", "did", "can", "could", "should", "would", "will", "may", "might",
        "data", "center", "centers", "county", "maryland", "prince", "george", "charles",
    }
    tokens = [t for t in re.findall(r"[a-z0-9']+", question_lower) if t not in stopwords and len(t) > 2]

    print(f"Domain phrases: {domain_phrases}")
    print(f"Search tokens: {tokens}")

    cutoff = datetime.now() - timedelta(days=180)

    # Keyword search
    conditions = []
    for phrase in domain_phrases:
        like = f"%{phrase}%"
        conditions.extend([Article.title.ilike(like), Article.summary.ilike(like), Article.content.ilike(like)])
    for token in tokens:
        like = f"%{token}%"
        conditions.extend([Article.title.ilike(like), Article.summary.ilike(like), Article.content.ilike(like)])

    keyword_articles = db.query(Article).filter(
        Article.analyzed == True,
        Article.discovered_date >= cutoff,
        or_(*conditions)
    ).order_by(desc(Article.priority_score), desc(Article.discovered_date)).limit(10).all()

    print(f"\nKeyword matches: {len(keyword_articles)}")
    for a in keyword_articles:
        print(f"  [{a.priority_score}/10] {a.title[:80]}")

    # Backfill with high-priority articles
    seen_ids = {a.id for a in keyword_articles}
    articles = list(keyword_articles)
    if len(articles) < 10:
        recent_top = db.query(Article).filter(
            Article.analyzed == True, Article.discovered_date >= cutoff
        ).order_by(desc(Article.priority_score), desc(Article.discovered_date)).limit(15).all()
        for a in recent_top:
            if a.id not in seen_ids:
                articles.append(a)
                seen_ids.add(a.id)
            if len(articles) >= 10:
                break

    print(f"\nTotal articles for context: {len(articles)}")

    # Build context for AI (matches routes.py logic)
    article_context = []
    for a in articles:
        ctx = {"title": a.title, "url": a.url, "priority_score": a.priority_score}
        if a.summary:
            ctx["summary"] = a.summary
        if a.content:
            ctx["content"] = a.content[:500]
        if a.category:
            ctx["category"] = a.category
        article_context.append(ctx)

    print(f"\nCalling AI service (answer_question)...")
    answer = await ai_service.answer_question(question, article_context)
    
    print(f"\n{'='*80}")
    print(f"AI ANSWER:")
    print(f"{'='*80}")
    print(answer)
    print(f"{'='*80}")

    # Show source articles used
    print(f"\nSOURCES ({len(articles)} articles provided as context):")
    for a in articles[:5]:
        print(f"  - [{a.priority_score}/10] {a.title[:70]}")
        print(f"    {a.url}")

    db.close()

if __name__ == "__main__":
    asyncio.run(test_ask())
