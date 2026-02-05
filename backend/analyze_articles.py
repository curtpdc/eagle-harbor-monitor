"""Analyze all unanalyzed articles in the database"""
import asyncio
import logging
from app.database import SessionLocal
from app.models import Article
from app.services.ai_service import AIService

logging.basicConfig(level=logging.INFO)

async def analyze_articles():
    """Run AI analysis on all unanalyzed articles"""
    db = SessionLocal()
    ai_service = AIService()
    
    # Get unanalyzed articles
    articles = db.query(Article).filter(Article.analyzed == False).all()
    
    if not articles:
        print("\n✅ No unanalyzed articles found.")
        db.close()
        return
    
    print(f"\n{'='*80}")
    print(f"ANALYZING {len(articles)} ARTICLES WITH GPT-4O-MINI")
    print(f"{'='*80}\n")
    
    analyzed_count = 0
    
    for idx, article in enumerate(articles, 1):
        try:
            print(f"[{idx}/{len(articles)}] Analyzing: {article.title[:60]}...")
            
            article_data = {
                "title": article.title,
                "content": article.content or article.title,
                "url": article.url,
                "source": article.source
            }
            
            # Run AI analysis
            analysis = await ai_service.analyze_article(article_data)
            
            # Update article
            article.summary = analysis.get('summary')
            article.priority_score = analysis.get('priority_score')
            article.category = analysis.get('category')
            article.county = analysis.get('county')
            article.analyzed = True
            
            db.commit()
            
            print(f"  ✅ Priority: {article.priority_score}/10 | Category: {article.category} | County: {article.county}")
            analyzed_count += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            db.rollback()
            continue
    
    print(f"\n{'='*80}")
    print(f"✅ ANALYSIS COMPLETE - {analyzed_count}/{len(articles)} articles analyzed")
    print(f"{'='*80}\n")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(analyze_articles())
