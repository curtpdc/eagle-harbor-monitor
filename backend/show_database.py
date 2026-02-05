from app.database import SessionLocal
from app.models import Article

db = SessionLocal()
articles = db.query(Article).order_by(Article.discovered_date.desc()).all()

print(f"\n{'='*80}")
print(f"EAGLE HARBOR MONITOR DATABASE STATUS")
print(f"{'='*80}")
print(f"\n📊 Total Articles: {len(articles)}")

analyzed = [a for a in articles if a.analyzed]
print(f"✅ Analyzed: {len(analyzed)}")
print(f"⏳ Pending Analysis: {len(articles) - len(analyzed)}")

print(f"\n📰 Latest Articles:")
print(f"{'='*80}\n")

for idx, article in enumerate(articles[:10], 1):
    status = "✅" if article.analyzed else "⏳"
    priority = f"{article.priority_score or 0}/10" if article.priority_score else "N/A"
    category = article.category or "pending"
    county = article.county or "?"
    
    print(f"{idx}. {status} [{priority}] {article.title[:65]}...")
    print(f"   Category: {category} | County: {county} | Source: {article.source}")
    print()

db.close()
