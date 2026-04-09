"""
actions.py — Real tool implementations
Uses DuckDuckGo (free, no API key) for search and BeautifulSoup for reading.
"""

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


# ─────────────────────────────────────────
# WEB SEARCH (DuckDuckGo — free, no key)
# ─────────────────────────────────────────
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo. Returns formatted results."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title":   r.get("title", ""),
                    "url":     r.get("href", ""),
                    "snippet": r.get("body", "")
                })

        if not results:
            return f"No results found for: {query}"

        formatted = f"🔍 Web search results for: **{query}**\n\n"
        for i, r in enumerate(results, 1):
            formatted += (
                f"**{i}. {r['title']}**\n"
                f"{r['snippet']}\n"
                f"🔗 {r['url']}\n\n"
            )
        return formatted

    except Exception as e:
        return f"Search failed: {str(e)}"


# ─────────────────────────────────────────
# WEB READ (Read page content)
# ─────────────────────────────────────────
def web_read(url_or_query: str) -> str:
    """
    Read a webpage. If given a URL, reads it directly.
    If given text, searches and reads the top result.
    """
    # Determine URL
    if url_or_query.startswith("http://") or url_or_query.startswith("https://"):
        url = url_or_query
    else:
        # Search first, then read top result
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(url_or_query, max_results=1))
                if results:
                    url = results[0].get("href", "")
                else:
                    return f"Could not find a page to read for: {url_or_query}"
        except Exception as e:
            return f"Search failed while trying to read: {str(e)}"

    # Read the page
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove noise tags
        for tag in soup(["script", "style", "nav", "footer",
                         "header", "aside", "advertisement", "iframe"]):
            tag.decompose()

        # Get meaningful text
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 40]
        content = "\n".join(lines[:60])  # First 60 meaningful lines

        if not content:
            return f"Could not extract readable content from: {url}"

        return f"📄 Content from {url}:\n\n{content}"

    except requests.exceptions.Timeout:
        return f"Timeout reading: {url}"
    except Exception as e:
        return f"Failed to read {url}: {str(e)}"


# ─────────────────────────────────────────
# YOUTUBE SEARCH
# ─────────────────────────────────────────
def youtube_search(query: str, max_results: int = 4) -> str:
    """Search YouTube using DuckDuckGo video search."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.videos(
                query,
                max_results=max_results
            ):
                results.append({
                    "title":       r.get("title", ""),
                    "url":         r.get("content", ""),
                    "description": r.get("description", ""),
                    "duration":    r.get("duration", ""),
                    "publisher":   r.get("publisher", "")
                })

        if not results:
            return f"No YouTube results found for: {query}"

        formatted = f"▶️ YouTube results for: **{query}**\n\n"
        for i, r in enumerate(results, 1):
            desc = r["description"][:100] + "..." if len(r["description"]) > 100 else r["description"]
            formatted += (
                f"**{i}. {r['title']}**\n"
                f"{desc}\n"
                f"⏱ {r['duration']} | 📺 {r['publisher']}\n"
                f"🔗 {r['url']}\n\n"
            )
        return formatted

    except Exception as e:
        return f"YouTube search failed: {str(e)}"


# ─────────────────────────────────────────
# TOOL REGISTRY
# ─────────────────────────────────────────
TOOLS = {
    "search":  web_search,
    "read":    web_read,
    "youtube": youtube_search,
}


def execute_tool(tool: str, tool_input: str) -> str:
    """Execute a tool by name with the given input."""
    func = TOOLS.get(tool)
    if not func:
        return f"Unknown tool: '{tool}'. Available: {list(TOOLS.keys())}"
    try:
        return func(tool_input)
    except Exception as e:
        return f"Tool '{tool}' error: {str(e)}"
