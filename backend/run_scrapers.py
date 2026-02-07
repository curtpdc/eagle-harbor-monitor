"""
Comprehensive scraper to populate Eagle Harbor Monitor database.

Mirrors the Azure Functions pipeline (functions/function_app.py) but uses
ORM models for local dev.  Three scrapers:
  1. Legistar JSON API  — events, agenda items, legislation
  2. Planning Board     — pgplanningboard.org news + agendas
  3. RSS feeds (10)     — Maryland news + data-center industry

Run:  cd backend && python run_scrapers.py
"""

import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Article
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# ─── Shared constants ────────────────────────────────────────────────────────

SCRAPER_KEYWORDS = [
    'data center', 'datacenter', 'eagle harbor', 'chalk point',
    'qualified data center', 'CR-98-2025', 'executive order 42-2025',
    'landover mall', 'zoning', 'AR zone', 'RE zone',
    'MNCPPC', 'planning board', 'legislative amendment',
    'prince george', 'charles county',
    'moratorium', 'special exception', 'zoning text amendment',
    'task force', 'environmental justice', 'PEPCO', 'grid capacity',
    'megawatt', 'cooling water', 'patuxent river',
]

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; EagleHarborMonitor/1.0; +https://eagleharbormonitor.org)'
}

LEGISTAR_BASE = "https://webapi.legistar.com/v1/princegeorgescountymd"
API_HEADERS = {"Accept": "application/json"}

ITEM_CHECK_TERMS = ['council', 'planning', 'zoning', 'environment', 'economic']

RSS_FEEDS = [
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


def kw_match(text: str) -> bool:
    """Check if text contains any keyword."""
    t = text.lower()
    return any(kw.lower() in t for kw in SCRAPER_KEYWORDS)


def scrape_article_content(url: str, timeout: int = 15) -> str:
    """Fetch and extract main text from an article URL (up to 5000 chars)."""
    try:
        resp = requests.get(url, timeout=timeout, headers=BROWSER_HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        body = (
            soup.find('article')
            or soup.find('div', class_=lambda c: c and any(
                x in (c if isinstance(c, str) else ' '.join(c))
                for x in ['article-body', 'story-body', 'entry-content', 'post-content']
            ))
            or soup.find('div', {'role': 'article'})
            or soup.find('main')
        )
        if body:
            text = body.get_text(separator=' ', strip=True)
        else:
            text = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))
        return ' '.join(text.split())[:5000]
    except Exception as e:
        logging.warning(f"Could not scrape {url}: {e}")
        return ""


# Track URLs added in the current run to avoid session-level duplicates
_seen_urls: set = set()


def _add_article(db, *, title, url, content, source, published_date=None):
    """Insert article if url not already present. Returns True if added."""
    if url in _seen_urls:
        return False
    existing = db.query(Article).filter(Article.url == url).first()
    if existing:
        _seen_urls.add(url)
        return False
    article = Article(
        title=title[:500],
        url=url,
        content=content or title,
        source=source,
        published_date=published_date,
        discovered_date=datetime.now(),
        analyzed=False,
    )
    db.add(article)
    _seen_urls.add(url)
    return True


# ═════════════════════════════════════════════════════════════════════════════
#  1. LEGISTAR JSON API
# ═════════════════════════════════════════════════════════════════════════════

def scrape_legistar():
    """Query PG County Legistar API for events, agenda items, and legislation."""
    logging.info('🏛️  Starting Legistar API scraper...')

    events_cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    matters_cutoff = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%dT00:00:00")

    db = SessionLocal()
    new_articles = 0

    # ── 1a. Events (meetings) ────────────────────────────────────────────────
    try:
        resp = requests.get(
            f"{LEGISTAR_BASE}/events",
            params={
                "$top": 200,
                "$orderby": "EventDate desc",
                "$filter": f"EventDate ge datetime'{events_cutoff}'",
            },
            headers=API_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        events = resp.json()
        logging.info(f"  Fetched {len(events)} events from Legistar API")
    except Exception as e:
        logging.error(f"  Events fetch failed: {e}")
        events = []

    for event in events:
        try:
            event_id = event.get("EventId")
            body_name = event.get("EventBodyName", "")
            event_date = event.get("EventDate", "")[:10]
            comment = event.get("EventComment", "")
            event_url = event.get("EventInSiteURL", "")
            agenda_file = event.get("EventAgendaFile")

            event_text = f"{body_name} {comment}"
            event_kw_hit = kw_match(event_text)

            # ── 1b. Agenda items for relevant bodies ─────────────────────
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
                    if not kw_match(f"{item_title} {item_matter}"):
                        continue

                    matter_id = item.get("EventItemMatterId")
                    event_item_id = item.get("EventItemId", "")
                    item_url = (
                        f"https://princegeorgescountymd.legistar.com/LegislationDetail.aspx?ID={matter_id}"
                        if matter_id
                        else f"{event_url}#item-{event_item_id}" if event_url
                        else f"{LEGISTAR_BASE}/events/{event_id}#item-{event_item_id}"
                    )

                    title = f"[{body_name} - {event_date}] {item_title or item_matter}"
                    content = (
                        f"Meeting: {body_name}\nDate: {event_date}\n"
                        f"Agenda Item: {item_title}\nMatter: {item_matter}"
                    )
                    if matter_id:
                        detail = scrape_article_content(item_url)
                        if detail:
                            content = f"{content}\n\n{detail}"

                    if _add_article(db, title=title, url=item_url,
                                    content=content, source="PG County Legistar"):
                        new_articles += 1
                        logging.info(f"  ✅ Agenda item: {title[:80]}")

            # Store the meeting itself when it matches keywords
            if event_kw_hit and event_url:
                title = f"[Meeting] {body_name} - {event_date}"
                if comment:
                    title = f"{title}: {comment[:200]}"
                content = f"Meeting: {body_name}\nDate: {event_date}\nComment: {comment}"
                if agenda_file:
                    content += f"\nAgenda: {agenda_file}"

                if _add_article(db, title=title, url=event_url,
                                content=content, source="PG County Legistar"):
                    new_articles += 1
                    logging.info(f"  ✅ Meeting: {title[:80]}")

        except Exception as e:
            logging.error(f"  Event {event.get('EventId')} error: {e}")
            continue

    # ── 1c. Legislation (matters) ────────────────────────────────────────────
    try:
        resp = requests.get(
            f"{LEGISTAR_BASE}/matters",
            params={
                "$top": 200,
                "$orderby": "MatterLastModifiedUtc desc",
                "$filter": f"MatterLastModifiedUtc ge datetime'{matters_cutoff}'",
            },
            headers=API_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        matters = resp.json()
        logging.info(f"  Fetched {len(matters)} matters from Legistar API")
    except Exception as e:
        logging.error(f"  Matters fetch failed: {e}")
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

            if not kw_match(f"{m_title} {m_name} {m_file}"):
                continue

            matter_url = f"https://princegeorgescountymd.legistar.com/LegislationDetail.aspx?ID={m_id}"
            title = f"[{m_type}] {m_file}: {m_name or m_title[:200]}"
            content = (
                f"Type: {m_type}\nFile: {m_file}\nBody: {m_body}\n"
                f"Status: {m_status}\nTitle: {m_title}"
            )
            detail = scrape_article_content(matter_url)
            if detail:
                content = f"{content}\n\n{detail}"

            if _add_article(db, title=title, url=matter_url,
                            content=content, source="PG County Legistar"):
                new_articles += 1
                logging.info(f"  ✅ Legislation: {title[:80]}")

        except Exception as e:
            logging.error(f"  Matter {matter.get('MatterId')} error: {e}")
            continue

    db.commit()
    db.close()
    logging.info(f'🏛️  Legistar API scraper complete. Added {new_articles} new articles.')
    return new_articles


# ═════════════════════════════════════════════════════════════════════════════
#  2. PLANNING BOARD (pgplanningboard.org)
# ═════════════════════════════════════════════════════════════════════════════

def scrape_planning_board():
    """Scrape MNCPPC PG County Planning Board website for news + agendas."""
    logging.info('📋 Starting Planning Board scraper...')

    PB_BASE = "https://pgplanningboard.org"
    db = SessionLocal()
    new_articles = 0

    # ── 2a. News / press-release listing pages ───────────────────────────────
    listing_pages = [
        f"{PB_BASE}/news/",
        f"{PB_BASE}/category/press-release/",
    ]

    for page_url in listing_pages:
        try:
            resp = requests.get(page_url, timeout=30, headers=BROWSER_HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            post_elems = (
                soup.find_all('article')
                or soup.find_all('div', class_=lambda c: c and any(
                    x in str(c) for x in ['post', 'entry', 'news-item']
                ))
            )

            if not post_elems:
                seen = set()
                for a in soup.find_all('a', href=True):
                    h = a['href']
                    if (h.startswith(PB_BASE) and h not in seen
                            and h != page_url
                            and not any(s in h for s in ['/category/', '/page/', '/tag/', '/meetings/'])):
                        seen.add(h)
                        post_elems.append(a)

            for elem in post_elems[:25]:
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
                    if not kw_match(f"{title} {excerpt}"):
                        continue

                    full_content = scrape_article_content(href)
                    if _add_article(db, title=title, url=href,
                                    content=full_content, source="PG Planning Board"):
                        new_articles += 1
                        logging.info(f"  ✅ PB article: {title[:80]}")

                except Exception as e:
                    logging.error(f"  PB element error: {e}")
                    continue

        except Exception as e:
            logging.error(f"  Error scraping {page_url}: {e}")
            continue

    # ── 2b. Meetings page — agendas & minutes ────────────────────────────────
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

            if not kw_match(f"{link_text} {a_tag.get('title', '')}"):
                continue

            if not href.startswith('http'):
                href = f"{PB_BASE}{href}"

            title = f"[PB Agenda] {link_text}"
            content = ""
            if not href.endswith('.pdf'):
                content = scrape_article_content(href)

            if _add_article(db, title=title, url=href,
                            content=content or link_text,
                            source="PG Planning Board Agenda"):
                new_articles += 1
                logging.info(f"  ✅ PB agenda: {title[:80]}")

    except Exception as e:
        logging.error(f"  Meetings page error: {e}")

    db.commit()
    db.close()
    logging.info(f'📋 Planning Board scraper complete. Added {new_articles} new articles.')
    return new_articles


# ═════════════════════════════════════════════════════════════════════════════
#  3. RSS FEEDS (10 sources)
# ═════════════════════════════════════════════════════════════════════════════

def scrape_rss_feeds():
    """Scrape 10 RSS feeds for Maryland data center news."""
    logging.info('📰 Starting RSS feed scraper...')

    db = SessionLocal()
    new_articles = 0

    for feed_url, source in RSS_FEEDS:
        try:
            logging.info(f"  Fetching: {source}")
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:30]:
                try:
                    title = entry.get('title', '')
                    url = entry.get('link', '')
                    summary = entry.get('summary', entry.get('description', ''))

                    if not kw_match(f"{title} {summary}"):
                        continue

                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])

                    full_content = scrape_article_content(url)

                    if _add_article(db, title=title, url=url,
                                    content=full_content or summary or title,
                                    source=source, published_date=pub_date):
                        new_articles += 1
                        logging.info(f"  ✅ {source}: {title[:80]}")

                except Exception as e:
                    logging.error(f"  Entry error: {e}")
                    continue

        except Exception as e:
            logging.error(f"  Feed error {source}: {e}")
            continue

    db.commit()
    db.close()
    logging.info(f'📰 RSS scraper complete. Added {new_articles} new articles.')
    return new_articles


# ═════════════════════════════════════════════════════════════════════════════
#  Main
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("=" * 80)
    print("  EAGLE HARBOR MONITOR — COMPREHENSIVE DATABASE POPULATION")
    print("=" * 80)
    print()

    legistar_count = scrape_legistar()
    pb_count = scrape_planning_board()
    rss_count = scrape_rss_feeds()

    total = legistar_count + pb_count + rss_count

    print()
    print("=" * 80)
    print(f"  ✅ SCRAPING COMPLETE — {total} new articles discovered")
    print("=" * 80)
    print(f"  Legistar API:    {legistar_count}")
    print(f"  Planning Board:  {pb_count}")
    print(f"  RSS feeds:       {rss_count}")
    print()
    print("  Next steps:")
    print("    python analyze_articles.py    # AI classification")
    print("    python extract_events.py      # Populate calendar")
    print("=" * 80)
    print()
