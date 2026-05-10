import re
import time
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

try:
    from markdownify import markdownify as md
except Exception:
    md = None


@dataclass
class ScrapedPage:
    url: str
    final_url: str
    domain: str
    title: str | None = None
    source: str | None = None
    published_at: str | None = None
    author: str | None = None
    text: str | None = None
    markdown: str | None = None
    summary_candidate: str | None = None
    headings: list[str] = field(default_factory=list)
    important_links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    status_code: int = 0
    metadata: dict = field(default_factory=dict)


def clean_text(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_domain(url: str) -> str:
    return (urlparse(url).netloc or "").lower().replace("www.", "")


def extract_published_at(soup: BeautifulSoup) -> str | None:
    selectors = [
        ('meta[property="article:published_time"]', "content"),
        ('meta[name="pubdate"]', "content"),
        ('meta[name="publish-date"]', "content"),
        ('meta[name="date"]', "content"),
        ("time[datetime]", "datetime"),
    ]
    for selector, attr in selectors:
        el = soup.select_one(selector)
        if el and el.get(attr):
            return clean_text(el.get(attr))
    return None


def extract_author(soup: BeautifulSoup) -> str | None:
    selectors = [
        ('meta[name="author"]', "content"),
        ('meta[property="article:author"]', "content"),
    ]
    for selector, attr in selectors:
        el = soup.select_one(selector)
        if el and el.get(attr):
            return clean_text(el.get(attr))
    return None


def extract_main_content(soup: BeautifulSoup) -> tuple[str, list[str]]:
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    container = (
        soup.find("article")
        or soup.find("main")
        or soup.find("section")
        or soup.body
        or soup
    )

    headings = []
    for h in container.find_all(["h1", "h2", "h3"]):
        text = clean_text(h.get_text(" ", strip=True))
        if text:
            headings.append(text)

    paragraphs = []
    for p in container.find_all(["p", "li"]):
        text = clean_text(p.get_text(" ", strip=True))
        if len(text) >= 40:
            paragraphs.append(text)

    text = "\n\n".join(paragraphs)
    return text, headings[:20]


def extract_important_links(soup: BeautifulSoup, limit: int = 10) -> list[str]:
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("http://", "https://")) and href not in seen:
            seen.add(href)
            links.append(href)
        if len(links) >= limit:
            break
    return links


def extract_images(soup: BeautifulSoup, limit: int = 10) -> list[str]:
    images = []
    seen = set()
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        if src and src not in seen:
            seen.add(src)
            images.append(src)
        if len(images) >= limit:
            break
    return images


async def scrape_url(
    url: str,
    user_agent: str = "FoundationCrawlerAI/0.2",
) -> ScrapedPage:
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": user_agent},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    final_url = str(response.url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    title = clean_text(soup.title.get_text()) if soup.title else None
    text, headings = extract_main_content(soup)
    markdown = md(str(soup.body)) if md and soup.body else None
    summary_candidate = text[:1500] if text else None

    return ScrapedPage(
        url=url,
        final_url=final_url,
        domain=get_domain(final_url),
        title=title,
        source=get_domain(final_url),
        published_at=extract_published_at(soup),
        author=extract_author(soup),
        text=text,
        markdown=markdown,
        summary_candidate=summary_candidate,
        headings=headings,
        important_links=extract_important_links(soup),
        images=extract_images(soup),
        status_code=response.status_code,
        metadata={
            "fetched_at": time.time(),
            "content_type": response.headers.get("content-type"),
            "content_length": response.headers.get("content-length"),
        },
    )
