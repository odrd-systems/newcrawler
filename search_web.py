import re
import time
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str | None = None
    engine: str = "duckduckgo"
    domain: str | None = None


@dataclass
class SearchResponse:
    query: str
    engine: str
    results: list[SearchResult]
    metadata: dict = field(default_factory=dict)


def clean_text(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_domain(url: str) -> str:
    match = re.search(r"^https?://([^/]+)", url)
    return match.group(1).lower() if match else ""


async def search_duckduckgo(
    query: str,
    limit: int = 10,
    user_agent: str = "FoundationCrawlerAI/0.2",
) -> SearchResponse:
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": user_agent},
    ) as client:
        response = await client.get(search_url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []

    for block in soup.select(".result"):
        link = block.select_one(".result__title a.result__a")
        snippet_el = block.select_one(".result__snippet")
        if not link:
            continue

        url = link.get("href", "").strip()
        title = clean_text(link.get_text(" ", strip=True))
        snippet = clean_text(snippet_el.get_text(" ", strip=True)) if snippet_el else None

        if not url or not title:
            continue

        results.append(
            SearchResult(
                title=title,
                url=url,
                snippet=snippet,
                engine="duckduckgo",
                domain=extract_domain(url),
            )
        )

        if len(results) >= limit:
            break

    return SearchResponse(
        query=query,
        engine="duckduckgo",
        results=results,
        metadata={
            "timestamp": time.time(),
            "result_count": len(results),
            "search_url": search_url,
        },
    )
