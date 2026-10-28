
import json

from ddgs import DDGS
from langchain.tools import tool


def search_web(query: str, max_results: int = 5) -> list:
    """Search DuckDuckGo and return result titles, snippets, and URLs."""
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if len(query) > 500:
        raise ValueError("Search query is too long.")

    results = DDGS().text(query.strip(), max_results=max_results)

    return [
        {
            "title": item.get("title", ""),
            "summary": item.get("body", ""),
            "url": item.get("href", ""),
        }
        for item in (results or [])
    ]


@tool
def web_search(query: str) -> str:
    """Search the web for current information, facts, research, or comparisons.
    Returns result titles, summaries, and source URLs.
    """
    try:
        results = search_web(query)

        if not results:
            return "ERROR: No web search results were returned."

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as exc:
        return f"ERROR: Web search failed: {type(exc).__name__}: {exc}"