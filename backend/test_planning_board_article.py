"""Test script to add Planning Board article and analyze it"""
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Article
from app.services.ai_service import AIService
from app.config import settings

# Ensure database exists
Base.metadata.create_all(bind=engine)

async def test_planning_board_article():
    db = SessionLocal()
    ai_service = AIService()
    
    article_content = """Greetings District 9 residents and beyond,

While I was digging myself out to attend a court hearing on a development case on January 29th, the Planning Board voted to start the process to change the County's zoning ordinance to allow data centers in rural, agricultural and residential areas, which can primarily be District 9, but will encompass the entire County.

Here's the key excerpt from the Planning Board's January 29th meeting:

"The next item on the agenda is item 3A, legislative updates. My favorite person, Ms. Gomez. Your favorite, Ms. Bartender or Ms. Gomez? Good morning, Chairman and members of the Planning Board.

For the record, Natalia Gomez with the Planning Director's Office. Item 3A is a legislative amendment. Before I start, pursuant Section 27-30C01C1, a legislative amendment shall be initiated only by a member of the District Council or the Chair of the Council at the request of the Planning Board.

And the reason I'm here today is for the latter one. I respectfully request the Planning Board to initiate a legislative amendment to amend the principal use table to permit qualified data centers in a specific rural and agricultural and residential based zones and set forward for requirements for qualified data centers in the agricultural AR zone and residential estate zone. Are there any questions for Ms. Gomez? I have none.

Seeing none, is there a motion? Move approval. Mr. Chair? Second, Mr. Chair. All right, it's been properly moved and seconded.

I will now call the roll. Vice Chair Geraldo? Vote aye. Commissioner Okoye? Aye.

And I vote aye as well. Thank you so much."

Key Takeaways:
The Planning Board voted to amend the Principal Use Table to permit "qualified data centers" in certain rural/agricultural and residential-based zones and set requirements for qualified data centers in the Agricultural (AR) zone and Residential Estate (RE) zone.

What Happens Next:
The next fight shifts to definitions and guardrails. The words "qualified data center," "permit," "specific zones," and "set forward requirements" will do all the work.

What Do We Need to Do:
Contact your Councilmember and request the draft legislative amendment language. Track the zoning changes to the Principal Use Table edits plus any new standards section for AR and RE."""

    article_data = {
        "title": "Planning Board Votes to Allow Data Centers in AR and RE Zones",
        "url": "https://pgccouncil.us/planning-board-jan-29-2026",
        "content": article_content,
        "source": "District 9 Community Alert",
        "discovered_date": datetime(2026, 1, 29)
    }
    
    print("\n" + "="*80)
    print("TESTING PLANNING BOARD ARTICLE ANALYSIS")
    print("="*80)
    
    # Run AI analysis
    print("\n🤖 Running AI Analysis...")
    analysis = await ai_service.analyze_article(article_data)
    
    print("\n📊 ANALYSIS RESULTS:")
    print(f"  Relevance Score: {analysis.get('relevance_score')}/10")
    print(f"  Priority Score: {analysis.get('priority_score')}/10")
    print(f"  Category: {analysis.get('category')}")
    print(f"  County: {analysis.get('county')}")
    
    print(f"\n📝 Summary:")
    print(f"  {analysis.get('summary')}")
    
    print(f"\n🔑 Key Points:")
    for point in analysis.get('key_points', []):
        print(f"  • {point}")
    
    # Create article in database
    article = Article(
        title=article_data['title'],
        url=article_data['url'],
        content=article_data['content'],
        summary=analysis.get('summary'),
        source=article_data['source'],
        discovered_date=article_data['discovered_date'],
        analyzed=True,
        priority_score=analysis.get('priority_score'),
        category=analysis.get('category'),
        county=analysis.get('county')
    )
    
    db.add(article)
    db.commit()
    db.refresh(article)
    
    print(f"\n✅ Article #{article.id} saved to database")
    print("\n" + "="*80)
    print("TEST COMPLETE - Article ready for display and email alerts")
    print("="*80 + "\n")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_planning_board_article())
