import json
import os
import re
import time
from dataclasses import asdict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from rank_results import rank_results
from scrape_web import scrape_url
from search_web import search_duckduckgo

app = FastAPI(title="FoundationCrawlerAI", version="0.2.0")


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class ScrapeRequest(BaseModel):
    url: str


class ResearchRequest(BaseModel):
    query: str
    search_limit: int = 10
    max_sources: int = 3
    preferred_domains: list[str] = Field(default_factory=list)
    save: bool = True
    output_dir: str = "output"


def safe_name(value: str) -> str:
    value = re.sub(r"^https?://", "", value)
    value = re.sub(r"[^a-zA-Z0-9._-]", "_", value)
    return value[:120] or f"item_{int(time.time())}"


def save_json(data: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.get("/")
async def root():
    return {
        "name": "FoundationCrawlerAI",
        "version": "0.2.0",
        "endpoints": ["/search", "/scrape", "/research"],
    }


@app.post("/search")
async def search(request: SearchRequest):
    response = await search_duckduckgo(query=request.query, limit=request.limit)
    return asdict(response)


@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    page = await scrape_url(request.url)
    return asdict(page)


@app.post("/research")
async def research(request: ResearchRequest):
    search_response = await search_duckduckgo(query=request.query, limit=request.search_limit)
    ranked = rank_results(
        search_response.results,
        query=request.query,
        preferred_domains=request.preferred_domains,
        top_k=request.max_sources,
    )

    sources = []
    for item in ranked:
        result = item["result"]
        try:
            page = await scrape_url(result.url)
            source_data = {
                "score": item["score"],
                "search_result": asdict(result),
                "scraped": asdict(page),
            }
            sources.append(source_data)
        except Exception as e:
            sources.append(
                {
                    "score": item["score"],
                    "search_result": asdict(result),
                    "error": str(e),
                }
            )

    response = {
        "query": request.query,
        "search": asdict(search_response),
        "selected_sources": [
            {
                "score": item["score"],
                "domain": item["domain"],
                "result": asdict(item["result"]),
            }
            for item in ranked
        ],
        "sources": sources,
    }

    if request.save:
        filename = safe_name(request.query) + ".json"
        path = os.path.join(request.output_dir, filename)
        save_json(response, path)
        response["saved_path"] = path

    return response
