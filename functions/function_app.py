import azure.functions as func
import logging
import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

app = func.FunctionApp()

# Database setup
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ── Keyword tiers for geographic filtering ────────────────────────────────────
# Keep in sync with backend/app/config.py settings.KEYWORDS

# Keywords that are inherently Maryland-specific — any match is relevant
MARYLAND_SPECIFIC_KEYWORDS = [
    'eagle harbor', 'chalk point', 'qualified data center',
    'CR-98-2025', 'executive order 42-2025', 'EO 42-2025',
    'landover mall', 'AR zone', 'RE zone',
    'MNCPPC', 'patuxent river', 'PEPCO',
    'prince george', 'charles county', 'pg county',
    'upper marlboro', 'brandywine', 'bowie',
]

# Geographic terms that confirm Maryland relevance
GEOGRAPHIC_KEYWORDS = [
    'maryland', 'prince george', 'charles county', 'pg county',
    'eagle harbor', 'chalk point', 'upper marlboro', 'brandywine',
    'bowie', 'college park', 'greenbelt', 'laurel', 'waldorf',
    'indian head', 'la plata', 'MNCPPC', 'PEPCO', 'patuxent',
    'southern maryland', 'anne arundel',
]

# Contextual keywords — only relevant when combined with a geographic match
CONTEXTUAL_KEYWORDS = [
    'data center', 'datacenter', 'zoning', 'planning board',
    'legislative amendment', 'moratorium', 'special exception',
    'zoning text amendment', 'task force', 'environmental justice',
    'grid capacity', 'megawatt', 'cooling water',
]

# Combined list for local/Maryland-scoped feeds (OR logic)
SCRAPER_KEYWORDS = MARYLAND_SPECIFIC_KEYWORDS + CONTEXTUAL_KEYWORDS

# Feeds that publish global/national content — require geographic AND-filter
GLOBAL_FEEDS = {
    'https://www.datacenterknowledge.com/rss.xml',
    'https://www.datacenterdynamics.com/en/rss/',
}

# Regional feeds covering broad DC-metro area — also require geographic match
REGIONAL_FEEDS = {
    'https://wtop.com/feed/',
    'https://feeds.washingtonpost.com/rss/local',
}


def passes_keyword_filter(title: str, summary: str, feed_url: str) -> bool:
    """Check if an article passes the keyword filter for its feed tier.

    - Local/Maryland feeds (Patch, MD Matters, PG Planning Board, MDE): OR logic
      — any SCRAPER_KEYWORDS match is enough.
    - Global industry feeds (DCK, DCD): require a CONTEXTUAL_KEYWORDS match AND
      a GEOGRAPHIC_KEYWORDS match.
    - Regional feeds (WTOP, WaPo): same AND logic as global feeds.
    """
    content_text = f"{title} {summary}".lower()

    if feed_url in GLOBAL_FEEDS or feed_url in REGIONAL_FEEDS:
        # Must match at least one contextual keyword AND one geographic keyword
        has_contextual = any(kw.lower() in content_text for kw in CONTEXTUAL_KEYWORDS)
        has_geographic = any(kw.lower() in content_text for kw in GEOGRAPHIC_KEYWORDS)
        # Also pass if any Maryland-specific keyword appears (they're inherently geo-scoped)
        has_md_specific = any(kw.lower() in content_text for kw in MARYLAND_SPECIFIC_KEYWORDS)
        return (has_contextual and has_geographic) or has_md_specific
    else:
        # Local/Maryland feeds — any keyword match is enough
        return any(kw.lower() in content_text for kw in SCRAPER_KEYWORDS)


def scrape_article_content(url: str, timeout: int = 15) -> str:
    """Fetch and extract the main text content from an article URL.
    
    Returns up to 5000 chars of body text, or empty string on failure.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; EagleHarborMonitor/1.0; +https://eagleharbormonitor.org)'
        }
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Remove script/style/nav elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        # Try common article body selectors
        article_body = (
            soup.find('article') or
            soup.find('div', class_=lambda c: c and any(x in (c if isinstance(c, str) else ' '.join(c)) for x in ['article-body', 'story-body', 'entry-content', 'post-content'])) or
            soup.find('div', {'role': 'article'}) or
            soup.find('main')
        )

        if article_body:
            text = article_body.get_text(separator=' ', strip=True)
        else:
            # Fallback: grab all <p> tags
            paragraphs = soup.find_all('p')
            text = ' '.join(p.get_text(strip=True) for p in paragraphs)

        # Clean up whitespace
        text = ' '.join(text.split())
        return text[:5000]
    except Exception as e:
        logging.warning(f"Could not scrape content from {url}: {e}")
        return ""


@app.function_name(name="LegistarScraper")
@app.schedule(schedule="0 0 */2 * * *", arg_name="timer", run_on_startup=False)
def legistar_scraper(timer: func.TimerRequest) -> None:
    """Scrape PG County Legistar via JSON API for meetings, agenda items, and legislation.

    Uses the official Legistar Web API instead of fragile HTML scraping.
    Three layers of monitoring:
      1. Events     - meetings from all Council bodies
      2. EventItems - individual agenda items per meeting (catches items like
         "Qualified Data Centers - Zoning Text Amendment" even when the meeting
         title is generic)
      3. Matters    - legislation (bills, resolutions, amendments)
    """

    logging.info('Legistar API scraper started')

    LEGISTAR_BASE = "https://webapi.legistar.com/v1/princegeorgescountymd"
    API_HEADERS = {"Accept": "application/json"}
    events_cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    matters_cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00")

    # Only drill into agenda items for bodies that handle zoning / legislation
    ITEM_CHECK_TERMS = ['council', 'planning', 'zoning', 'environment', 'economic']

    try:
        db = SessionLocal()
        new_articles = 0

        # ── 1. Recent events (meetings) ──────────────────────────────
        try:
            resp = requests.get(
                f"{LEGISTAR_BASE}/events",
                params={
                    "$top": 100,
                    "$orderby": "EventDate desc",
                    "$filter": f"EventDate ge datetime'{events_cutoff}'",
                },
                headers=API_HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            events = resp.json()
        except Exception as e:
            logging.error(f"Legistar events fetch failed: {e}")
            events = []

        for event in events:
            try:
                event_id = event.get("EventId")
                body_name = event.get("EventBodyName", "")
                event_date = event.get("EventDate", "")[:10]
                comment = event.get("EventComment", "")
                event_url = event.get("EventInSiteURL", "")
                agenda_file = event.get("EventAgendaFile")

                event_text = f"{body_name} {comment}".lower()
                event_kw_hit = any(kw.lower() in event_text for kw in SCRAPER_KEYWORDS)

                # ── 2. Agenda items for relevant bodies ──────────────
                body_lower = body_name.lower()
                should_check_items = (
                    event_kw_hit
                    or any(t in body_lower for t in ITEM_CHECK_TERMS)
                )

                if should_check_items:
                    try:
                        ir = requests.get(
                            f"{LEGISTAR_BASE}/events/{event_id}/eventitems",
                            headers=API_HEADERS,
                            timeout=15,
                        )
                        ir.raise_for_status()
                        event_items = ir.json()
                    except Exception:
                        event_items = []

                    for item in event_items:
                        item_title = item.get("EventItemTitle", "")
                        item_matter = item.get("EventItemMatterName", "")
                        item_text = f"{item_title} {item_matter}".lower()
                        if not any(kw.lower() in item_text for kw in SCRAPER_KEYWORDS):
                            continue

                        matter_id = item.get("EventItemMatterId")
                        item_url = (
                            f"https://princegeorgescountymd.legistar.com/LegislationDetail.aspx?ID={matter_id}"
                            if matter_id
                            else event_url or f"{LEGISTAR_BASE}/events/{event_id}"
                        )

                        if db.execute(text("SELECT 1 FROM articles WHERE url = :url"), {"url": item_url}).first():
                            continue

                        title = f"[{body_name} - {event_date}] {item_title or item_matter}"
                        content = (
                            f"Meeting: {body_name}\nDate: {event_date}\n"
                            f"Agenda Item: {item_title}\nMatter: {item_matter}"
                        )
                        if matter_id:
                            detail = scrape_article_content(item_url)
                            if detail:
                                content = f"{content}\n\n{detail}"

                        db.execute(
                            text("""
                            INSERT INTO articles (title, url, content, source, discovered_date, analyzed)
                            VALUES (:title, :url, :content, :source, :discovered, FALSE)
                            """),
                            {"title": title[:500], "url": item_url, "content": content,
                             "source": "PG County Legistar", "discovered": datetime.now()},
                        )
                        new_articles += 1
                        logging.info(f"New agenda item: {title[:80]}")

                # Store the meeting itself when it matches keywords
                if event_kw_hit and event_url:
                    if not db.execute(text("SELECT 1 FROM articles WHERE url = :url"), {"url": event_url}).first():
                        title = f"[Meeting] {body_name} - {event_date}"
                        if comment:
                            title = f"{title}: {comment[:200]}"
                        content = f"Meeting: {body_name}\nDate: {event_date}\nComment: {comment}"
                        if agenda_file:
                            content += f"\nAgenda: {agenda_file}"

                        db.execute(
                            text("""
                            INSERT INTO articles (title, url, content, source, discovered_date, analyzed)
                            VALUES (:title, :url, :content, :source, :discovered, FALSE)
                            """),
                            {"title": title[:500], "url": event_url, "content": content,
                             "source": "PG County Legistar", "discovered": datetime.now()},
                        )
                        new_articles += 1

            except Exception as e:
                logging.error(f"Event {event.get('EventId')} error: {e}")
                continue

        # ── 3. Recent legislation (matters) ──────────────────────────
        try:
            resp = requests.get(
                f"{LEGISTAR_BASE}/matters",
                params={
                    "$top": 100,
                    "$orderby": "MatterLastModifiedUtc desc",
                    "$filter": f"MatterLastModifiedUtc ge datetime'{matters_cutoff}'",
                },
                headers=API_HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            matters = resp.json()
        except Exception as e:
            logging.error(f"Legistar matters fetch failed: {e}")
            matters = []

        for matter in matters:
            try:
                m_title = matter.get("MatterTitle", "")
                m_name = matter.get("MatterName", "")
                m_type = matter.get("MatterTypeName", "")
                m_body = matter.get("MatterBodyName", "")
                m_status = matter.get("MatterStatusName", "")
                m_id = matter.get("MatterId")
                m_file = matter.get("MatterFile", "")

                search_text = f"{m_title} {m_name} {m_file}".lower()
                if not any(kw.lower() in search_text for kw in SCRAPER_KEYWORDS):
                    continue

                matter_url = f"https://princegeorgescountymd.legistar.com/LegislationDetail.aspx?ID={m_id}"
                if db.execute(text("SELECT 1 FROM articles WHERE url = :url"), {"url": matter_url}).first():
                    continue

                title = f"[{m_type}] {m_file}: {m_name or m_title[:200]}"
                content = (
                    f"Type: {m_type}\nFile: {m_file}\nBody: {m_body}\n"
                    f"Status: {m_status}\nTitle: {m_title}"
                )
                detail = scrape_article_content(matter_url)
                if detail:
                    content = f"{content}\n\n{detail}"

                db.execute(
                    text("""
                    INSERT INTO articles (title, url, content, source, discovered_date, analyzed)
                    VALUES (:title, :url, :content, :source, :discovered, FALSE)
                    """),
                    {"title": title[:500], "url": matter_url, "content": content,
                     "source": "PG County Legistar", "discovered": datetime.now()},
                )
                new_articles += 1
                logging.info(f"New legislation: {title[:80]}")

            except Exception as e:
                logging.error(f"Matter {matter.get('MatterId')} error: {e}")
                continue

        db.commit()
        db.close()
        logging.info(f'Legistar API scraper completed. New articles: {new_articles}')

    except Exception as e:
        logging.error(f'Legistar API scraper error: {str(e)}')


@app.function_name(name="RSSNewsScraper")
@app.schedule(schedule="0 */30 * * * *", arg_name="timer", run_on_startup=False)
def rss_news_scraper(timer: func.TimerRequest) -> None:
    """Scrape RSS feeds every 30 minutes.
    
    Sources cover Maryland news, PG/Charles County government, and
    regional data center industry coverage.
    """
    
    logging.info('RSS news scraper function started')
    
    rss_feeds = [
        # Maryland news
        ("https://www.marylandmatters.org/feed/", "Maryland Matters"),
        ("https://wtop.com/feed/", "WTOP News"),
        ("https://feeds.washingtonpost.com/rss/local", "Washington Post"),
        # Regional / PG County local
        ("https://patch.com/feeds/maryland/bowie", "Patch Bowie"),
        ("https://patch.com/feeds/maryland/upper-marlboro", "Patch Upper Marlboro"),
        ("https://patch.com/feeds/maryland/college-park", "Patch College Park"),
        # Maryland state government
        ("https://news.maryland.gov/mde/feed/", "MD Dept of Environment"),
        # MNCPPC / Planning Board
        ("https://pgplanningboard.org/feed/", "PG Planning Board"),
        # Data center industry
        ("https://www.datacenterknowledge.com/rss.xml", "Data Center Knowledge"),
        ("https://www.datacenterdynamics.com/en/rss/", "Data Center Dynamics"),
    ]
    
    try:
        db = SessionLocal()
        new_articles = 0
        
        for feed_url, source in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:20]:  # Limit entries per feed
                    title = entry.get('title', '')
                    url = entry.get('link', '')
                    summary = entry.get('summary', '')
                    
                    # Tiered keyword filter: global/regional feeds require geographic match
                    if not passes_keyword_filter(title, summary, feed_url):
                        continue
                    
                    # Check if already exists
                    existing = db.execute(
                        text("SELECT 1 FROM articles WHERE url = :url"),
                        {"url": url}
                    ).first()
                    
                    if not existing:
                        published = entry.get('published_parsed')
                        pub_date = datetime(*published[:6]) if published else None
                        
                        # Scrape full article content
                        full_content = scrape_article_content(url)
                        
                        db.execute(
                            text("""
                            INSERT INTO articles (title, url, summary, content, source, published_date, discovered_date, analyzed)
                            VALUES (:title, :url, :summary, :content, :source, :published, :discovered, FALSE)
                            """),
                            {
                                "title": title[:500],
                                "url": url,
                                "summary": summary,
                                "content": full_content or summary,
                                "source": source,
                                "published": pub_date,
                                "discovered": datetime.now()
                            }
                        )
                        new_articles += 1
                        logging.info(f"New article from {source}: {title[:80]}")
            
            except Exception as e:
                logging.error(f"Error scraping {source}: {e}")
                continue
        
        db.commit()
        db.close()
        
        logging.info(f'RSS scraper completed. New articles: {new_articles}')
    
    except Exception as e:
        logging.error(f'RSS scraper error: {str(e)}')


@app.function_name(name="PlanningBoardScraper")
@app.schedule(schedule="0 30 */2 * * *", arg_name="timer", run_on_startup=False)
def planning_board_scraper(timer: func.TimerRequest) -> None:
    """Scrape MNCPPC PG County Planning Board website for news and agendas.

    The Planning Board (pgplanningboard.org) is a *separate body* from the
    County Council.  It initiates zoning text amendments, reviews development
    applications, and takes actions that won't appear in Legistar until
    transmitted to the Council weeks/months later.

    Scrapes:
      - /news/  and  /category/press-release/  for articles
      - /meetings/  for upcoming meeting agendas and minutes

    Runs every 2 h (offset 30 min from LegistarScraper).
    """

    logging.info('Planning Board scraper started')

    PB_BASE = "https://pgplanningboard.org"
    BROWSER_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (compatible; EagleHarborMonitor/1.0; +https://eagleharbormonitor.org)'
    }

    try:
        db = SessionLocal()
        new_articles = 0

        # ── 1. News / press-release listing pages ────────────────────
        listing_pages = [
            (f"{PB_BASE}/news/", "PG Planning Board"),
            (f"{PB_BASE}/category/press-release/", "PG Planning Board"),
        ]

        for page_url, source_label in listing_pages:
            try:
                resp = requests.get(page_url, timeout=30, headers=BROWSER_HEADERS)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                # WordPress themes wrap posts in <article> or div.post-*
                post_elems = (
                    soup.find_all('article')
                    or soup.find_all('div', class_=lambda c: c and any(
                        x in str(c) for x in ['post', 'entry', 'news-item']
                    ))
                )

                # Fallback: unique article-like links
                if not post_elems:
                    seen = set()
                    for a in soup.find_all('a', href=True):
                        h = a['href']
                        if (h.startswith(PB_BASE) and h not in seen
                                and h != page_url
                                and not any(s in h for s in ['/category/', '/page/', '/tag/', '/meetings/'])):
                            seen.add(h)
                            post_elems.append(a)

                for elem in post_elems[:20]:
                    try:
                        link = elem if elem.name == 'a' else elem.find('a', href=True)
                        if not link:
                            continue
                        href = link.get('href', '')
                        if not href.startswith('http'):
                            continue

                        heading = elem.find(['h1', 'h2', 'h3', 'h4'])
                        title = (heading.get_text(strip=True) if heading
                                 else link.get_text(strip=True))
                        if not title or len(title) < 10:
                            continue

                        excerpt_tag = elem.find('p')
                        excerpt = excerpt_tag.get_text(strip=True) if excerpt_tag else ""
                        combined = f"{title} {excerpt}".lower()
                        if not any(kw.lower() in combined for kw in SCRAPER_KEYWORDS):
                            continue

                        if db.execute(text("SELECT 1 FROM articles WHERE url = :url"), {"url": href}).first():
                            continue

                        full_content = scrape_article_content(href)
                        db.execute(
                            text("""
                            INSERT INTO articles (title, url, content, source, discovered_date, analyzed)
                            VALUES (:title, :url, :content, :source, :discovered, FALSE)
                            """),
                            {"title": title[:500], "url": href,
                             "content": full_content or title,
                             "source": source_label, "discovered": datetime.now()},
                        )
                        new_articles += 1
                        logging.info(f"New PB article: {title[:80]}")

                    except Exception as e:
                        logging.error(f"PB article element error: {e}")
                        continue

            except Exception as e:
                logging.error(f"Error scraping {page_url}: {e}")
                continue

        # ── 2. Meetings page — agendas & minutes ─────────────────────
        try:
            resp = requests.get(f"{PB_BASE}/meetings/", timeout=30, headers=BROWSER_HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                link_text = a_tag.get_text(strip=True)

                if not any(t in link_text.lower() for t in ['agenda', 'minutes', 'meeting']):
                    if not href.endswith('.pdf'):
                        continue

                combined = f"{link_text} {a_tag.get('title', '')}".lower()
                if not any(kw.lower() in combined for kw in SCRAPER_KEYWORDS):
                    continue

                if not href.startswith('http'):
                    href = f"{PB_BASE}{href}"

                if db.execute(text("SELECT 1 FROM articles WHERE url = :url"), {"url": href}).first():
                    continue

                title = f"[PB Agenda] {link_text}"
                content = ""
                if not href.endswith('.pdf'):
                    content = scrape_article_content(href)

                db.execute(
                    text("""
                    INSERT INTO articles (title, url, content, source, discovered_date, analyzed)
                    VALUES (:title, :url, :content, :source, :discovered, FALSE)
                    """),
                    {"title": title[:500], "url": href,
                     "content": content or link_text,
                     "source": "PG Planning Board Agenda", "discovered": datetime.now()},
                )
                new_articles += 1
                logging.info(f"New PB agenda: {title[:80]}")

        except Exception as e:
            logging.error(f"Meetings page error: {e}")

        db.commit()
        db.close()
        logging.info(f'Planning Board scraper completed. New articles: {new_articles}')

    except Exception as e:
        logging.error(f'Planning Board scraper error: {str(e)}')


@app.function_name(name="ArticleAnalyzer")
@app.schedule(schedule="0 */10 * * * *", arg_name="timer", run_on_startup=False)
def article_analyzer(timer: func.TimerRequest) -> None:
    """Analyze unanalyzed articles every 10 minutes"""
    
    logging.info('Article analyzer function started')
    
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        db = SessionLocal()
        
        # Get unanalyzed articles
        articles = db.execute(
            text("""
            SELECT id, title, summary, content, source
            FROM articles
            WHERE analyzed = FALSE
            LIMIT 5
            """)
        ).fetchall()
        
        for article in articles:
            try:
                content = f"{article[1]} {article[2] or ''} {article[3] or ''}"
                # Use more content for better analysis (up to 3000 chars)
                content = content[:3000]
                
                prompt = f"""You are a classification engine for the Eagle Harbor Data Center Monitor,
which tracks data center developments in Prince George's County and Charles County, Maryland.

Analyze the article below and return a JSON object with these fields:

1. "relevance_score" (integer 0-10): How relevant is this to Maryland data center developments?
   - 8-10: Directly about data centers in Prince George's County or Charles County, MD
     (e.g., Eagle Harbor, Chalk Point, CR-98-2025, PG County zoning for data centers)
   - 6-7: About Maryland statewide data center policy, legislation, or energy/grid issues
     affecting data center siting in Maryland
   - 4-5: Adjacent Maryland topic (zoning, environmental review, planning board action)
     that may affect data center development indirectly
   - 2-3: General Maryland news with weak connection to data centers
   - 0-1: Not about Maryland at all, or no connection to data centers

2. "priority_score" (integer 1-10): Urgency/impact for community stakeholders
   - 8-10: New legislation, votes, executive orders, public hearings on data centers
   - 5-7: Policy discussions, task force updates, environmental reviews
   - 1-4: Background info, industry trends, routine meetings

3. "category": One of: policy, meeting, legislation, environmental, community, development

4. "county": One of: prince_georges, charles, both, maryland_statewide, unclear
   Use "maryland_statewide" for state-level policy, "unclear" ONLY if truly indeterminate.

5. "summary": A 1-2 sentence summary focused on the Maryland/local angle.
   If the article is not about Maryland, say so explicitly.

6. "key_points": Array of 2-4 key takeaways relevant to PG/Charles County stakeholders.

Article to analyze:
Title: {article[1]}
Source: {article[4]}
Content: {content}

Return ONLY valid JSON, no markdown formatting."""

                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                raw_text = response.content[0].text.strip()
                # Strip markdown code fences if present
                if raw_text.startswith('```'):
                    raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text[3:]
                    if raw_text.endswith('```'):
                        raw_text = raw_text[:-3].strip()
                
                analysis = json.loads(raw_text)
                
                relevance = analysis.get('relevance_score', 0)
                priority = analysis.get('priority_score', 5)
                category = analysis.get('category', 'general')
                county = analysis.get('county', 'unclear')
                summary = analysis.get('summary', '')
                
                db.execute(
                    text("""
                    UPDATE articles
                    SET relevance_score = :relevance,
                        priority_score = :priority,
                        category = :category,
                        county = :county,
                        summary = CASE WHEN :summary != '' THEN :summary ELSE summary END,
                        analyzed = TRUE
                    WHERE id = :id
                    """),
                    {
                        "id": article[0],
                        "relevance": min(max(int(relevance), 0), 10),
                        "priority": min(max(int(priority), 1), 10),
                        "category": category,
                        "county": county,
                        "summary": (summary or '')[:2000],
                    }
                )
                
                logging.info(
                    f"Analyzed article {article[0]}: relevance={relevance}, "
                    f"priority={priority}, county={county}"
                )
            
            except Exception as e:
                logging.error(f"Error analyzing article {article[0]}: {e}")
                # Mark as analyzed with low relevance so it doesn't block the queue
                db.execute(
                    text("""
                    UPDATE articles
                    SET analyzed = TRUE, relevance_score = 0
                    WHERE id = :id
                    """),
                    {"id": article[0]}
                )
        
        db.commit()
        db.close()
        
        logging.info(f'Article analyzer completed. Analyzed: {len(articles)}')
    
    except Exception as e:
        logging.error(f'Article analyzer error: {str(e)}')


@app.function_name(name="HistoricalScan")
@app.route(route="historical-scan", methods=["POST", "GET"], auth_level=func.AuthLevel.ANONYMOUS)
def historical_scan(req: func.HttpRequest) -> func.HttpResponse:
    """
    One-time historical scan to populate knowledge base with past 180 days of articles
    Trigger via: GET https://<function-app>.azurewebsites.net/api/historical-scan?days=180
    """
    
    logging.info('Historical scan triggered')
    
    try:
        # Get days parameter (default 180)
        days_param = req.params.get('days', '180')
        days_back = int(days_param)
        
        if days_back > 365:
            return func.HttpResponse(
                "Maximum 365 days allowed",
                status_code=400
            )
        
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        start_date = datetime.now() - timedelta(days=days_back)
        articles_found = 0
        
        # RSS Feeds to scan (same as RSSNewsScraper)
        rss_feeds = [
            ("https://www.marylandmatters.org/feed/", "Maryland Matters"),
            ("https://wtop.com/feed/", "WTOP News"),
            ("https://feeds.washingtonpost.com/rss/local", "Washington Post"),
            ("https://patch.com/feeds/maryland/bowie", "Patch Bowie"),
            ("https://patch.com/feeds/maryland/upper-marlboro", "Patch Upper Marlboro"),
            ("https://patch.com/feeds/maryland/college-park", "Patch College Park"),
            ("https://news.maryland.gov/mde/feed/", "MD Dept of Environment"),
            ("https://pgplanningboard.org/feed/", "PG Planning Board"),
            ("https://www.datacenterknowledge.com/rss.xml", "Data Center Knowledge"),
            ("https://www.datacenterdynamics.com/en/rss/", "Data Center Dynamics"),
        ]
        
        db = SessionLocal()
        
        for feed_url, source in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:100]:  # Scan up to 100 entries per feed
                    try:
                        # Check publication date
                        pub_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                        
                        if pub_date and pub_date < start_date:
                            continue
                        
                        title = entry.get('title', '')
                        url = entry.get('link', '')
                        summary = entry.get('summary', entry.get('description', ''))
                        
                        # Use tiered keyword filter (same logic as RSSNewsScraper)
                        if not passes_keyword_filter(title, summary, feed_url):
                            continue
                        
                        # Check if exists
                        existing = db.execute(
                            text("SELECT id FROM articles WHERE url = :url"),
                            {"url": url}
                        ).fetchone()
                        
                        if existing:
                            continue
                        
                        # Scrape full article content
                        full_content = scrape_article_content(url)
                        
                        # Insert new article
                        db.execute(
                            text("""
                                INSERT INTO articles 
                                (title, url, content, source, discovered_date, published_date, analyzed)
                                VALUES (:title, :url, :content, :source, :discovered, :published, FALSE)
                            """),
                            {
                                "title": title,
                                "url": url,
                                "content": full_content or summary,
                                "source": source,
                                "discovered": datetime.now(),
                                "published": pub_date or datetime.now()
                            }
                        )
                        articles_found += 1
                        logging.info(f"Historical: {title[:60]}")
                    
                    except Exception as e:
                        logging.error(f"Entry error: {e}")
                        continue
            
            except Exception as e:
                logging.error(f"Feed error for {source}: {e}")
                continue
        
        db.commit()
        db.close()
        
        result = {
            "success": True,
            "articles_found": articles_found,
            "days_scanned": days_back,
            "date_range": f"{start_date.date()} to {datetime.now().date()}",
            "note": "ArticleAnalyzer will process these articles automatically"
        }
        
        logging.info(f'Historical scan complete: {articles_found} articles')
        
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )
    
    except Exception as e:
        logging.error(f'Historical scan error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
