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

# ── Amendment Watchlist keywords — any matter matching these gets auto-watched ─
WATCHLIST_AUTO_DETECT_KEYWORDS = [
    'zoning text amendment', 'zoning amendment', 'data center',
    'qualified data center', 'ar zone', 're zone', 'eagle harbor',
    'chalk point', 'cr-98-2025', 'eo 42-2025', 'moratorium',
    'special exception', 'landover mall',
]

# Milestone action keywords — these trigger is_milestone=True in history tracking
MILESTONE_ACTIONS = [
    'introduced', 'referred', 'public hearing', 'hearing scheduled',
    'amended', 'approved', 'denied', 'passed', 'failed', 'enacted',
    'signed', 'vetoed', 'withdrawn', 'tabled', 'adopted',
    'first reading', 'second reading', 'third reading',
    'committee report', 'transmitted', 'effective date',
]

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
    matters_cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%dT00:00:00")

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

                # ── Auto-detect watchlist candidates ─────────────────
                watch_text = f"{m_title} {m_name} {m_file} {m_type}".lower()
                if any(kw in watch_text for kw in WATCHLIST_AUTO_DETECT_KEYWORDS):
                    existing_watch = db.execute(
                        text("SELECT 1 FROM watched_matters WHERE matter_id = :mid"),
                        {"mid": m_id}
                    ).first()
                    if not existing_watch:
                        try:
                            db.execute(
                                text("""
                                INSERT INTO watched_matters
                                    (matter_id, matter_file, matter_type, title, body_name,
                                     current_status, legistar_url, watch_reason, auto_detected, is_active, priority)
                                VALUES (:mid, :mfile, :mtype, :title, :body,
                                        :status, :url, :reason, TRUE, TRUE, 'high')
                                """),
                                {
                                    "mid": m_id, "mfile": m_file, "mtype": m_type,
                                    "title": (m_name or m_title)[:500], "body": m_body,
                                    "status": m_status, "url": matter_url,
                                    "reason": f"Auto-detected: matched watchlist keywords in '{m_type}: {m_file}'"
                                },
                            )
                            logging.info(f"Auto-watched matter {m_id}: {m_file} - {m_name or m_title[:60]}")
                        except Exception as ew:
                            logging.warning(f"Could not auto-watch matter {m_id}: {ew}")

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


# ── Amendment Watchlist Tracker ──────────────────────────────────────────────

@app.function_name(name="AmendmentWatchlistTracker")
@app.schedule(schedule="0 15 */4 * * *", arg_name="timer", run_on_startup=False)
def amendment_watchlist_tracker(timer: func.TimerRequest) -> None:
    """Track active watched matters for status changes, new attachments, and votes.

    Polls three Legistar API endpoints for each active watched matter:
      1. /matters/{id}/histories   — status transitions (Introduced → Referred → etc.)
      2. /matters/{id}/attachments — draft text, staff reports, memos
      3. /matters/{id}/votes       — roll-call votes with individual Aye/Nay

    Runs every 4 hours (offset 15 min from other scrapers).
    New findings are stored in dedicated tables and flagged for notification.
    """

    logging.info('Amendment Watchlist Tracker started')

    LEGISTAR_BASE = "https://webapi.legistar.com/v1/princegeorgescountymd"
    API_HEADERS = {"Accept": "application/json"}

    try:
        db = SessionLocal()

        # Get all active watched matters
        watched = db.execute(
            text("SELECT matter_id, current_status, title FROM watched_matters WHERE is_active = TRUE")
        ).fetchall()

        if not watched:
            logging.info('No active watched matters — nothing to track')
            db.close()
            return

        logging.info(f'Tracking {len(watched)} active watched matters')

        new_histories = 0
        new_attachments = 0
        new_votes = 0
        status_changes = 0

        for row in watched:
            mid = row[0]
            prev_status = row[1] or ""
            matter_title = row[2] or ""

            # ── 1. Histories (status transitions) ────────────────────
            try:
                resp = requests.get(
                    f"{LEGISTAR_BASE}/matters/{mid}/histories",
                    headers=API_HEADERS,
                    timeout=20,
                )
                resp.raise_for_status()
                histories = resp.json()
            except Exception as e:
                logging.warning(f"History fetch failed for matter {mid}: {e}")
                histories = []

            latest_status = prev_status
            latest_action_date = None

            for hist in histories:
                hist_id = hist.get("MatterHistoryId")
                if not hist_id:
                    continue

                # Dedup check
                exists = db.execute(
                    text("SELECT 1 FROM matter_histories WHERE legistar_history_id = :hid"),
                    {"hid": hist_id}
                ).first()
                if exists:
                    continue

                action_date_str = hist.get("MatterHistoryActionDate", "")
                action_date = None
                if action_date_str:
                    try:
                        action_date = datetime.fromisoformat(action_date_str.replace("Z", "+00:00").split("+")[0])
                    except (ValueError, TypeError):
                        pass

                action_text = hist.get("MatterHistoryActionName", "")
                action_body = hist.get("MatterHistoryActionBodyName", "")
                result_text = hist.get("MatterHistoryPassedFlagName", "")
                vote_info = hist.get("MatterHistoryTally", "")
                minutes_note = hist.get("MatterHistoryMinutesNote", "")

                # Detect milestone actions
                is_milestone = any(
                    ma in action_text.lower() for ma in MILESTONE_ACTIONS
                )

                # Track status progression
                new_status = action_text or result_text or prev_status

                db.execute(
                    text("""
                    INSERT INTO matter_histories
                        (matter_id, legistar_history_id, action_date, action_text,
                         action_body, result, vote_info, minutes_note,
                         previous_status, new_status, is_milestone, notified, discovered_date)
                    VALUES (:mid, :hid, :adate, :atext,
                            :abody, :result, :vinfo, :mnote,
                            :pstatus, :nstatus, :milestone, FALSE, :now)
                    """),
                    {
                        "mid": mid, "hid": hist_id, "adate": action_date,
                        "atext": action_text[:500], "abody": action_body[:200],
                        "result": result_text[:100], "vinfo": vote_info[:200],
                        "mnote": minutes_note,
                        "pstatus": prev_status[:200], "nstatus": new_status[:200],
                        "milestone": is_milestone, "now": datetime.now(),
                    },
                )
                new_histories += 1

                if action_date and (latest_action_date is None or action_date > latest_action_date):
                    latest_action_date = action_date
                    latest_status = new_status

                if is_milestone:
                    logging.info(
                        f"[MILESTONE] Matter {mid}: {action_text} ({result_text}) on {action_date}"
                    )

            # Update matter's current status if changed
            if latest_status != prev_status:
                db.execute(
                    text("""
                    UPDATE watched_matters
                    SET current_status = :status, last_action_date = :adate, updated_date = :now
                    WHERE matter_id = :mid
                    """),
                    {"status": latest_status[:200], "adate": latest_action_date, "now": datetime.now(), "mid": mid},
                )
                status_changes += 1
                logging.info(f"Status change for matter {mid}: '{prev_status}' → '{latest_status}'")

            # ── 2. Attachments (draft text, staff reports) ───────────
            try:
                resp = requests.get(
                    f"{LEGISTAR_BASE}/matters/{mid}/attachments",
                    headers=API_HEADERS,
                    timeout=20,
                )
                resp.raise_for_status()
                attachments = resp.json()
            except Exception as e:
                logging.warning(f"Attachment fetch failed for matter {mid}: {e}")
                attachments = []

            for att in attachments:
                att_id = att.get("MatterAttachmentId")
                if not att_id:
                    continue

                exists = db.execute(
                    text("SELECT 1 FROM matter_attachments WHERE legistar_attachment_id = :aid"),
                    {"aid": att_id}
                ).first()
                if exists:
                    continue

                att_name = att.get("MatterAttachmentName", "")
                att_link = att.get("MatterAttachmentHyperlink", "")
                att_filename = att.get("MatterAttachmentFileName", "")
                file_ext = att_filename.rsplit(".", 1)[-1].lower() if "." in att_filename else ""

                # Try to scrape text content from non-PDF attachments
                content_text = ""
                if att_link and not att_link.lower().endswith(".pdf"):
                    content_text = scrape_article_content(att_link)

                db.execute(
                    text("""
                    INSERT INTO matter_attachments
                        (matter_id, legistar_attachment_id, name, hyperlink,
                         file_type, content_text, analyzed, notified, discovered_date)
                    VALUES (:mid, :aid, :name, :link,
                            :ftype, :content, FALSE, FALSE, :now)
                    """),
                    {
                        "mid": mid, "aid": att_id, "name": att_name[:500],
                        "link": att_link, "ftype": file_ext[:50],
                        "content": content_text, "now": datetime.now(),
                    },
                )
                new_attachments += 1
                logging.info(f"New attachment for matter {mid}: {att_name[:80]}")

            # ── 3. Votes (roll calls) ────────────────────────────────
            try:
                resp = requests.get(
                    f"{LEGISTAR_BASE}/matters/{mid}/votes",
                    headers=API_HEADERS,
                    timeout=20,
                )
                resp.raise_for_status()
                votes = resp.json()
            except Exception as e:
                logging.warning(f"Vote fetch failed for matter {mid}: {e}")
                votes = []

            for vote in votes:
                vote_id = vote.get("VoteId")
                if not vote_id:
                    continue

                exists = db.execute(
                    text("SELECT 1 FROM matter_votes WHERE legistar_vote_id = :vid"),
                    {"vid": vote_id}
                ).first()
                if exists:
                    continue

                vote_date_str = vote.get("VoteDate", "")
                vote_date = None
                if vote_date_str:
                    try:
                        vote_date = datetime.fromisoformat(vote_date_str.replace("Z", "+00:00").split("+")[0])
                    except (ValueError, TypeError):
                        pass

                body_name = vote.get("VoteEventItemBodyName", "")
                result_text = vote.get("VoteResult", "")
                person_name = vote.get("VotePersonName", "")
                vote_value = vote.get("VoteValueName", "")  # Aye, Nay, Abstain

                # Votes API returns one row per person — aggregate into roll_call
                # Store individual vote record; aggregation happens at API layer
                tally = f"{person_name}: {vote_value}" if person_name else ""
                roll_call_entry = [{"person": person_name, "vote": vote_value}] if person_name else []

                db.execute(
                    text("""
                    INSERT INTO matter_votes
                        (matter_id, legistar_vote_id, vote_date, body_name,
                         result, tally, roll_call, notified, discovered_date)
                    VALUES (:mid, :vid, :vdate, :body,
                            :result, :tally, :roll_call, FALSE, :now)
                    """),
                    {
                        "mid": mid, "vid": vote_id, "vdate": vote_date,
                        "body": body_name[:200], "result": result_text[:100],
                        "tally": tally[:50],
                        "roll_call": json.dumps(roll_call_entry),
                        "now": datetime.now(),
                    },
                )
                new_votes += 1

            if new_votes > 0:
                logging.info(f"New votes for matter {mid}: {new_votes} records")

        db.commit()
        db.close()

        logging.info(
            f'Amendment Watchlist Tracker completed: '
            f'{new_histories} new histories, {new_attachments} new attachments, '
            f'{new_votes} new votes, {status_changes} status changes'
        )

    except Exception as e:
        logging.error(f'Amendment Watchlist Tracker error: {str(e)}')


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


# ── Instant Alert Sender ─────────────────────────────────────────────────────

@app.function_name(name="InstantAlertSender")
@app.schedule(schedule="0 */10 * * * *", arg_name="timer", run_on_startup=False)
def instant_alert_sender(timer: func.TimerRequest) -> None:
    """Send instant email alerts for high-priority articles and watchlist milestones.

    Checks for:
      1. Analyzed articles with priority_score >= 8 that haven't been notified
      2. Watchlist milestone history entries that haven't been notified
      3. New watchlist attachments that haven't been notified

    Runs every 10 minutes (same cadence as ArticleAnalyzer).
    """
    logging.info('Instant Alert Sender started')

    try:
        db = SessionLocal()

        # Get verified active subscribers
        subscribers = db.execute(
            text("SELECT email FROM subscribers WHERE verified = TRUE AND is_active = TRUE")
        ).fetchall()

        if not subscribers:
            logging.info('No active subscribers — skipping alerts')
            db.close()
            return

        sub_emails = [row[0] for row in subscribers]
        logging.info(f'{len(sub_emails)} active subscribers')

        alerts_sent = 0

        # ── 1. High-priority articles (priority >= 8, analyzed, not notified)
        high_priority = db.execute(
            text("""
            SELECT id, title, url, summary, source, priority_score
            FROM articles
            WHERE analyzed = TRUE AND notified = FALSE AND priority_score >= 8
            ORDER BY priority_score DESC
            LIMIT 5
            """)
        ).fetchall()

        for art in high_priority:
            art_id, title, url, summary, source, priority = art
            logging.info(f"Sending alert for article {art_id}: {title[:60]} (priority={priority})")

            try:
                from azure.communication.email import EmailClient
                comm_conn = os.environ.get("AZURE_COMM_CONNECTION_STRING")
                from_email = os.environ.get("FROM_EMAIL", "")

                if comm_conn and from_email:
                    email_client = EmailClient.from_connection_string(comm_conn)
                    badge = "🚨 CRITICAL" if priority >= 9 else "⚠️ URGENT"

                    for email_addr in sub_emails:
                        html = f"""
                        <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background: #dc3545; color: white; padding: 20px; text-align: center;">
                            <h1>{badge}: Data Center Alert</h1>
                        </div>
                        <div style="padding: 30px; background: #f9fafb;">
                            <h2>{title}</h2>
                            <p><strong>Source:</strong> {source} | <strong>Priority:</strong> {priority}/10</p>
                            <div style="background: white; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0;">
                                {summary or 'Click through to read the full article.'}
                            </div>
                            <div style="text-align: center; margin: 20px 0;">
                                <a href="{url}" style="background: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Read Full Article</a>
                            </div>
                        </div>
                        </body></html>
                        """
                        msg = {
                            "senderAddress": from_email,
                            "recipients": {"to": [{"address": email_addr}]},
                            "content": {
                                "subject": f"{badge}: {title[:80]}",
                                "html": html,
                            },
                        }
                        try:
                            poller = email_client.begin_send(msg)
                            poller.result()
                            alerts_sent += 1
                        except Exception as se:
                            logging.error(f"Email send error for {email_addr}: {se}")

                    db.execute(
                        text("UPDATE articles SET notified = TRUE WHERE id = :id"),
                        {"id": art_id}
                    )
                else:
                    logging.warning("Azure Comm Services not configured — skipping email send")
                    db.execute(
                        text("UPDATE articles SET notified = TRUE WHERE id = :id"),
                        {"id": art_id}
                    )
            except ImportError:
                logging.warning("azure-communication-email not installed — skipping email send")
                db.execute(
                    text("UPDATE articles SET notified = TRUE WHERE id = :id"),
                    {"id": art_id}
                )

        # ── 2. Watchlist milestone changes (not yet notified)
        try:
            milestones = db.execute(
                text("""
                SELECT mh.id, mh.matter_id, mh.action_text, mh.result, mh.action_date,
                       wm.title, wm.legistar_url
                FROM matter_histories mh
                JOIN watched_matters wm ON wm.matter_id = mh.matter_id
                WHERE mh.is_milestone = TRUE AND mh.notified = FALSE
                ORDER BY mh.discovered_date DESC
                LIMIT 10
                """)
            ).fetchall()

            for ms in milestones:
                ms_id, mid, action_text, result, action_date, matter_title, legistar_url = ms
                detail = f"{action_text}"
                if result:
                    detail += f" — {result}"
                if action_date:
                    detail += f" (on {str(action_date)[:10]})"

                logging.info(f"Watchlist milestone alert: matter {mid} - {detail}")

                try:
                    from azure.communication.email import EmailClient
                    comm_conn = os.environ.get("AZURE_COMM_CONNECTION_STRING")
                    from_email = os.environ.get("FROM_EMAIL", "")

                    if comm_conn and from_email:
                        email_client = EmailClient.from_connection_string(comm_conn)
                        for email_addr in sub_emails:
                            html = f"""
                            <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <div style="background: #f59e0b; color: white; padding: 20px; text-align: center;">
                                <h1>📋 Amendment Watchlist Update</h1>
                            </div>
                            <div style="padding: 30px; background: #f9fafb;">
                                <h2>{matter_title}</h2>
                                <div style="background: white; padding: 15px; border-left: 4px solid #f59e0b; margin: 15px 0;">
                                    <p><strong>Change:</strong> {detail}</p>
                                </div>
                                {"<div style='text-align: center; margin: 20px 0;'><a href='" + legistar_url + "' style='background: #1e40af; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;'>View on Legistar</a></div>" if legistar_url else ""}
                            </div>
                            </body></html>
                            """
                            msg = {
                                "senderAddress": from_email,
                                "recipients": {"to": [{"address": email_addr}]},
                                "content": {
                                    "subject": f"📋 Watchlist: {matter_title[:60]} — {action_text[:40]}",
                                    "html": html,
                                },
                            }
                            try:
                                poller = email_client.begin_send(msg)
                                poller.result()
                                alerts_sent += 1
                            except Exception as se:
                                logging.error(f"Watchlist email error for {email_addr}: {se}")
                except (ImportError, Exception) as ex:
                    logging.warning(f"Could not send watchlist email: {ex}")

                db.execute(
                    text("UPDATE matter_histories SET notified = TRUE WHERE id = :id"),
                    {"id": ms_id}
                )

        except Exception as e:
            logging.warning(f"Watchlist milestone check failed (tables may not exist yet): {e}")

        # ── 3. New watchlist attachments (not yet notified)
        try:
            new_atts = db.execute(
                text("""
                SELECT ma.id, ma.matter_id, ma.name, wm.title, wm.legistar_url
                FROM matter_attachments ma
                JOIN watched_matters wm ON wm.matter_id = ma.matter_id
                WHERE ma.notified = FALSE
                ORDER BY ma.discovered_date DESC
                LIMIT 10
                """)
            ).fetchall()

            for att in new_atts:
                att_id = att[0]
                db.execute(
                    text("UPDATE matter_attachments SET notified = TRUE WHERE id = :id"),
                    {"id": att_id}
                )

        except Exception as e:
            logging.warning(f"Attachment notification check failed: {e}")

        db.commit()
        db.close()
        logging.info(f'Instant Alert Sender completed: {alerts_sent} emails sent')

    except Exception as e:
        logging.error(f'Instant Alert Sender error: {str(e)}')


# ── Weekly Digest Sender ─────────────────────────────────────────────────────

@app.function_name(name="WeeklyDigestSender")
@app.schedule(schedule="0 0 15 * * 5", arg_name="timer", run_on_startup=False)
def weekly_digest_sender(timer: func.TimerRequest) -> None:
    """Send weekly digest every Friday at 3 PM.

    Collects:
      - Top articles from the past 7 days (sorted by priority)
      - Watchlist changes from the past 7 days
      - Upcoming events in the next 14 days
    """
    logging.info('Weekly Digest Sender started')

    try:
        db = SessionLocal()
        week_ago = datetime.now() - timedelta(days=7)
        two_weeks = datetime.now() + timedelta(days=14)

        # Get subscribers
        subscribers = db.execute(
            text("""
            SELECT email, unsubscribe_token
            FROM subscribers WHERE verified = TRUE AND is_active = TRUE
            """)
        ).fetchall()

        if not subscribers:
            logging.info('No active subscribers — skipping digest')
            db.close()
            return

        # Top articles
        articles = db.execute(
            text("""
            SELECT title, url, summary, priority_score, category, source
            FROM articles
            WHERE analyzed = TRUE AND discovered_date >= :cutoff
              AND (relevance_score >= 4 OR relevance_score IS NULL)
            ORDER BY priority_score DESC, discovered_date DESC
            LIMIT 15
            """),
            {"cutoff": week_ago}
        ).fetchall()

        article_list = [
            {"title": a[0], "url": a[1], "summary": a[2],
             "priority_score": a[3], "category": a[4], "source": a[5]}
            for a in articles
        ]

        # Watchlist changes
        watchlist_changes = []
        try:
            changes = db.execute(
                text("""
                SELECT mh.action_text, mh.result, mh.action_date, wm.title
                FROM matter_histories mh
                JOIN watched_matters wm ON wm.matter_id = mh.matter_id
                WHERE mh.discovered_date >= :cutoff
                ORDER BY mh.action_date DESC
                LIMIT 10
                """),
                {"cutoff": week_ago}
            ).fetchall()

            for c in changes:
                detail = c[0] or ""
                if c[1]:
                    detail += f" — {c[1]}"
                if c[2]:
                    detail += f" ({str(c[2])[:10]})"
                watchlist_changes.append({
                    "matter_title": c[3],
                    "change_type": "status_change",
                    "detail": detail,
                })
        except Exception:
            logging.warning("Could not fetch watchlist changes for digest")

        # Upcoming events
        upcoming = []
        try:
            events = db.execute(
                text("""
                SELECT title, event_date, location, event_type
                FROM events
                WHERE event_date >= :now AND event_date <= :end
                  AND is_cancelled = FALSE
                ORDER BY event_date
                LIMIT 10
                """),
                {"now": datetime.now(), "end": two_weeks}
            ).fetchall()

            for e in events:
                upcoming.append({
                    "title": e[0],
                    "event_date": str(e[1])[:16] if e[1] else "TBD",
                    "location": e[2] or "",
                    "event_type": e[3] or "",
                })
        except Exception:
            logging.warning("Could not fetch upcoming events for digest")

        # Send digest to each subscriber
        digests_sent = 0
        try:
            from azure.communication.email import EmailClient
            comm_conn = os.environ.get("AZURE_COMM_CONNECTION_STRING")
            from_email = os.environ.get("FROM_EMAIL", "")

            if not comm_conn or not from_email:
                logging.warning("Azure Comm Services not configured — skipping digest")
                db.close()
                return

            email_client = EmailClient.from_connection_string(comm_conn)
            today = datetime.now().strftime("%B %d, %Y")

            for row in subscribers:
                email_addr, unsub_token = row[0], row[1]

                # Build article rows
                article_rows = ""
                for a in article_list:
                    p = a.get("priority_score", 0)
                    badge = "🚨" if p and p >= 8 else "⚠️" if p and p >= 6 else "📰"
                    article_rows += f"""<tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                            {badge} <a href="{a['url']}" style="color:#1e40af;">{a['title'][:100]}</a>
                        </td>
                        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align:center;">{a.get('category','')}</td>
                    </tr>"""

                articles_html = ""
                if article_list:
                    articles_html = f"""<h3>📰 Top Articles This Week ({len(article_list)})</h3>
                    <table style="width:100%;border-collapse:collapse;"><thead><tr>
                        <th style="padding:8px;text-align:left;border-bottom:2px solid #d1d5db;">Article</th>
                        <th style="padding:8px;text-align:center;border-bottom:2px solid #d1d5db;">Category</th>
                    </tr></thead><tbody>{article_rows}</tbody></table>"""

                watchlist_html = ""
                if watchlist_changes:
                    items = "".join(
                        f"<li><strong>{c['matter_title']}</strong>: {c['detail']}</li>"
                        for c in watchlist_changes
                    )
                    watchlist_html = f"<h3>📋 Amendment Watchlist Updates</h3><ul>{items}</ul>"

                events_html = ""
                if upcoming:
                    items = "".join(
                        f"<li><strong>{e['event_date']}</strong> — {e['title']}"
                        f"{' @ ' + e['location'] if e.get('location') else ''}</li>"
                        for e in upcoming
                    )
                    events_html = f"<h3>📅 Upcoming Events</h3><ul>{items}</ul>"

                unsub_url = f"{os.environ.get('APP_URL', 'https://eagleharbormonitor.org')}/unsubscribe/{unsub_token}"

                html = f"""<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#1e40af;color:white;padding:20px;text-align:center;">
                    <h1>Weekly Digest</h1>
                    <p style="margin:5px 0 0;">Eagle Harbor Data Center Monitor — {today}</p>
                </div>
                <div style="padding:30px;background:#f9fafb;">
                    {articles_html}{watchlist_html}{events_html}
                    {"<p style='color:#9ca3af;'>No notable updates this week.</p>" if not article_list and not watchlist_changes and not upcoming else ""}
                </div>
                <div style="padding:20px;text-align:center;color:#6b7280;font-size:12px;">
                    <a href="{unsub_url}" style="color:#6b7280;">Unsubscribe</a>
                </div>
                </body></html>"""

                msg = {
                    "senderAddress": from_email,
                    "recipients": {"to": [{"address": email_addr}]},
                    "content": {
                        "subject": f"Weekly Digest — Eagle Harbor Monitor ({today})",
                        "html": html,
                    },
                }
                try:
                    poller = email_client.begin_send(msg)
                    poller.result()
                    digests_sent += 1
                except Exception as se:
                    logging.error(f"Digest send error for {email_addr}: {se}")

        except ImportError:
            logging.warning("azure-communication-email not installed")

        db.close()
        logging.info(f'Weekly Digest completed: {digests_sent} digests sent')

    except Exception as e:
        logging.error(f'Weekly Digest error: {str(e)}')
