"""
Seed database with critical Planning Board January 29, 2026 meeting information
Run this to immediately populate the knowledge base with key data center policy updates
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment or use default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://adminuser:EagleHarbor2026!@eagle-harbor-db.postgres.database.azure.com/eagle_harbor_db?sslmode=require")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Critical Planning Board meeting article
planning_board_article = {
    "title": "Planning Board Votes to Allow Data Centers in Rural, Agricultural, and Residential Zones - January 29, 2026",
    "url": "https://pgccouncil.us/planning-board/2026-01-29-meeting",
    "content": """
Planning Board January 29, 2026 Meeting - Data Center Zoning Amendment Initiated

KEY VOTE: The Planning Board voted to initiate a legislative amendment to permit qualified data centers in rural, agricultural, and residential zones throughout Prince George's County.

MEETING EXCERPT:
Natalia Gomez, Planning Director's Office: "I respectfully request the Planning Board to initiate a legislative amendment to amend the principal use table to permit qualified data centers in a specific rural and agricultural and residential based zones and set forward for requirements for qualified data centers in the agricultural AR zone and residential estate zone."

VOTE RESULTS:
- Vice Chair Geraldo: Aye
- Commissioner Okoye: Aye  
- Chairman: Aye
Motion passed unanimously with no debate or public comment.

WHAT THIS MEANS:
1. POLICY SHIFT: The conversation is no longer hypothetical. A text amendment is being prepared to change where data centers are allowed countywide.

2. ZONE EXPANSION: Rural and estate-residential zones (AR and RE zones) become part of the data center siting pipeline, particularly affecting District 9 but applicable countywide.

3. "QUALIFIED DATA CENTER" DEFINITION: The amendment will define what constitutes a "qualified data center" - this definition is critical and will determine:
   - Size limits (MW capacity)
   - Building type requirements
   - "Edge" vs. hyperscale distinctions
   - Tenancy requirements
   - Grid interconnection thresholds

ZONES AFFECTED:
- AR Zone (Agricultural-Rural)
- RE Zone (Residential Estate)  
- Potentially other rural/agricultural/residential zones countywide

NEXT STEPS IN PROCESS:
1. Draft legislative amendment language will be prepared
2. Language submitted to District Council (County Council sitting as zoning authority)
3. Public hearing process
4. District Council vote

CRITICAL AREAS TO MONITOR:
- Principal Use Table amendments
- Definition of "qualified data center"
- Approval pathway: permitted by right, limited use, or special exception
- On-site power generation limits and emissions controls
- Infrastructure requirements (PJM interconnection, substation upgrades)
- Compatibility standards: setbacks, buffering, noise limits, lighting, building height
- Water use disclosure requirements
- Truck routing and construction hours
- Community impact assessments

RESIDENT ACTION ITEMS:
1. Contact your Councilmember to request draft amendment language when introduced
2. Track Principal Use Table edits for AR and RE zones
3. Submit comments keyed to specific line edits and measurable standards
4. Push for tight definitions and enforceable conditions early
5. Pre-register for public hearings under new participation rules
6. Organize community response before draft becomes baseline

CONTEXT:
This vote represents a directional signal from County leadership (County Council and County Executive who appoints Planning Board members) supporting data center development in District 9 and throughout the County, despite ongoing community protests and environmental concerns.

The lack of debate or public comment at the Planning Board meeting indicates this was a procedural vote to initiate the amendment process. The substantive policy debate will occur during the District Council review process.

RELATED POLICIES:
- CR-98-2025: County Resolution establishing Data Center Task Force
- Executive Order 42-2025: State-level data center evaluation requirements
- Prince George's County Data Center Moratorium (enacted January 26, 2021)
- Chalk Point Power Plant site evaluation for data center conversion

SIGNIFICANCE:
This is the most significant policy development in Prince George's County data center policy since the 2021 moratorium. It represents a fundamental shift from restricting data center development to actively creating pathways for it in previously protected zones.
""",
    "source": "Prince George's County Planning Board",
    "discovered_date": datetime.now(),
    "published_date": datetime(2026, 1, 29),
    "analyzed": False,
    "priority_score": 10,
    "category": "legislation",
    "county": "prince_georges"
}

# Related articles
related_articles = [
    {
        "title": "CR-98-2025: Data Center Task Force Resolution Analysis",
        "url": "https://pgccouncil.us/CR-98-2025",
        "content": """
County Resolution CR-98-2025 establishes a Data Center Task Force to study impacts of data center development in Prince George's County, Maryland. 

KEY PROVISIONS:
- Evaluation of zoning amendments including AR (Agricultural-Rural) and RE (Residential Estate) zones
- Assessment of environmental impacts: grid capacity, water usage, heat island effects
- Community concerns investigation
- Review of potential data center sites including Chalk Point Power Plant area

TASK FORCE MANDATE:
The task force is charged with providing recommendations on:
1. Appropriate zoning classifications for data center development
2. Environmental impact mitigation requirements
3. Infrastructure capacity assessments (electrical grid, water, wastewater)
4. Community compatibility standards
5. Economic impact analysis

RELATIONSHIP TO PLANNING BOARD ACTION:
The January 29, 2026 Planning Board vote to initiate zoning amendments appears to be moving forward with recommendations from the Task Force process, specifically targeting AR and RE zones for "qualified data center" development.

TIMELINE:
Resolution passed in early 2025, with Task Force work continuing through 2025-2026. The Planning Board's January 2026 action suggests the County is moving from study phase to implementation phase.
""",
        "source": "Prince George's County Council",
        "discovered_date": datetime.now(),
        "published_date": datetime(2025, 3, 15),
        "analyzed": False,
        "priority_score": 9,
        "category": "policy",
        "county": "prince_georges"
    },
    {
        "title": "Chalk Point Power Plant Site: Prime Data Center Conversion Candidate",
        "url": "https://mncppc.org/chalk-point-evaluation",
        "content": """
The retired Chalk Point Power Plant in Prince George's County has emerged as a primary candidate for data center development due to existing electrical grid infrastructure.

SITE ADVANTAGES:
- Existing electrical grid infrastructure and transmission capacity
- Large industrial-zoned parcel suitable for hyperscale data centers
- Proximity to PJM interconnection points
- Waterfront location with potential cooling water access

COMMUNITY CONCERNS:
- Traffic impacts on surrounding residential areas
- Environmental effects on Patuxent River waterfront
- Conversion of industrial site to intensive data center use
- Noise, lighting, and heat island effects on nearby communities

ZONING REVIEW:
The Maryland-National Capital Park and Planning Commission (MNCPPC) is reviewing zoning implications of data center conversion. The January 29, 2026 Planning Board action on AR and RE zones may facilitate development of Chalk Point and similar sites.

CURRENT STATUS:
Site is under evaluation for data center suitability. The Planning Board's initiation of zoning amendments for rural and agricultural zones suggests movement toward enabling development at Chalk Point and other potential sites in District 9.
""",
        "source": "MNCPPC",
        "discovered_date": datetime.now(),
        "published_date": datetime(2025, 11, 10),
        "analyzed": False,
        "priority_score": 8,
        "category": "development",
        "county": "prince_georges"
    }
]

def seed_database():
    """Insert seed articles into database"""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding database with Planning Board information...")
        
        # Insert main Planning Board article
        db.execute(
            text("""
                INSERT INTO articles 
                (title, url, content, source, discovered_date, published_date, analyzed, priority_score, category, county)
                VALUES (:title, :url, :content, :source, :discovered, :published, :analyzed, :priority, :category, :county)
                ON CONFLICT (url) DO NOTHING
            """),
            planning_board_article
        )
        print("✅ Added: Planning Board January 29, 2026 meeting")
        
        # Insert related articles
        for article in related_articles:
            db.execute(
                text("""
                    INSERT INTO articles 
                    (title, url, content, source, discovered_date, published_date, analyzed, priority_score, category, county)
                    VALUES (:title, :url, :content, :source, :discovered_date, :published_date, :analyzed, :priority_score, :category, :county)
                    ON CONFLICT (url) DO NOTHING
                """),
                article
            )
            print(f"✅ Added: {article['title'][:60]}...")
        
        db.commit()
        
        # Get article count
        result = db.execute(text("SELECT COUNT(*) FROM articles")).fetchone()
        total_articles = result[0] if result else 0
        
        print(f"\n✅ Database seeded successfully!")
        print(f"📊 Total articles in database: {total_articles}")
        print("\n🤖 Next: ArticleAnalyzer function will process these articles automatically")
        print("⏰ AI chat will be knowledgeable about Planning Board meeting within 5-10 minutes")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
