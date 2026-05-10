import re
from urllib.parse import urlparse

from search_web import SearchResult


DEFAULT_TRUSTED_DOMAINS = [
    "reuters.com",
    "bloomberg.com",
    "cnbc.com",
    "finance.yahoo.com",
    "marketwatch.com",
    "wsj.com",
    "forbes.com",
    "investing.com",
    "moneycontrol.com",
    "economictimes.indiatimes.com",
]


def normalize_domain(domain: str) -> str:
    domain = (domain or "").lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def get_domain(url: str) -> str:
    return normalize_domain(urlparse(url).netloc)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", (text or "").lower())


def score_result(
    result: SearchResult,
    query: str,
    preferred_domains: list[str] | None = None,
) -> float:
    preferred_domains = preferred_domains or []
    preferred_domains = [normalize_domain(d) for d in preferred_domains]

    query_terms = set(tokenize(query))
    title_terms = set(tokenize(result.title))
    snippet_terms = set(tokenize(result.snippet or ""))
    domain = get_domain(result.url)

    score = 0.0

    score += len(query_terms.intersection(title_terms)) * 3.0
    score += len(query_terms.intersection(snippet_terms)) * 1.5

    if domain in [normalize_domain(d) for d in DEFAULT_TRUSTED_DOMAINS]:
        score += 5.0

    if domain in preferred_domains:
        score += 8.0

    if any(word in (result.title or "").lower() for word in ["live", "today", "breaking", "update"]):
        score += 2.0

    return score


def rank_results(
    results: list[SearchResult],
    query: str,
    preferred_domains: list[str] | None = None,
    top_k: int = 3,
) -> list[dict]:
    scored = []
    seen = set()

    for result in results:
        domain = get_domain(result.url)
        key = (result.url or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)

        score = score_result(result, query=query, preferred_domains=preferred_domains)
        scored.append(
            {
                "score": score,
                "result": result,
                "domain": domain,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
