"""Live web search service for Eagle Harbor Monitor.

Uses DuckDuckGo search (no API key required) to fetch real-time web results
that supplement our saved article database. Results are formatted as context
for the AI to blend with database articles.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


async def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search the web for real-time results related to the user's question.

    Returns a list of dicts with keys: title, url, snippet.
    Silently returns empty list on any error so the Q&A flow is never blocked.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("duckduckgo-search not installed — skipping live web search")
        return []

    # Build a targeted search query
    search_query = _build_search_query(query)

    try:
        results: List[Dict[str, str]] = []
        with DDGS() as ddgs:
            for r in ddgs.text(search_query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        logger.info("Web search returned %d results for: %s", len(results), search_query)
        return results
    except Exception as e:
        logger.error("Web search failed (non-blocking): %s", e)
        return []


def _build_search_query(question: str) -> str:
    """Add Maryland data center focus to the user's raw question."""
    q_lower = question.lower()

    # If the question already mentions Maryland / PG County, use as-is with a nudge
    md_terms = [
        "maryland", "prince george", "pg county", "charles county",
        "eagle harbor", "chalk point", "landover", "mncppc",
    ]
    has_md_context = any(t in q_lower for t in md_terms)

    dc_terms = ["data center", "datacenter", "zoning", "ar zone", "re zone"]
    has_dc_context = any(t in q_lower for t in dc_terms)

    if has_md_context and has_dc_context:
        return question
    elif has_md_context:
        return f"{question} data center"
    elif has_dc_context:
        return f"{question} Maryland Prince George's County"
    else:
        return f"{question} Maryland data center Prince George's County"


def format_web_results(results: List[Dict[str, str]]) -> str:
    """Format web search results into a context block for the AI prompt."""
    if not results:
        return ""

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[Web {i}] {r['title']}\n"
            f"URL: {r['url']}\n"
            f"Snippet: {r['snippet']}"
        )
    return "\n\n## Live Web Search Results\n" + "\n\n".join(lines)
