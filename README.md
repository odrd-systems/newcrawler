# FoundationCrawlerAI

FoundationCrawlerAI is an AI-ready web research backend.

It is designed for workflows like:

- search the web for a topic
- choose the best links
- scrape the useful content
- return structured data to an AI assistant

Example:
- "today's stock market news"
- "latest NVIDIA earnings news"
- "best Python async tutorials"

## Features

- Web search using DuckDuckGo HTML results
- Result ranking with trusted-domain preference
- URL scraping with article-style extraction
- Structured AI-ready JSON output
- FastAPI endpoints for integration

## Endpoints

### `POST /search`
Search the web and return normalized results.

### `POST /scrape`
Scrape one URL and return structured extracted content.

### `POST /research`
Search, rank, scrape top sources, and return one AI-ready response.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api:app --reload
```

## Docs

Open:

```text
http://127.0.0.1:8000/docs
```

## Example request for `/research`

```json
{
  "query": "today stock market news",
  "search_limit": 10,
  "max_sources": 3,
  "preferred_domains": ["reuters.com", "bloomberg.com", "cnbc.com"],
  "save": true,
  "output_dir": "output"
}
```

## Output

Research responses can be saved into `output/` as JSON files.

## Next upgrades

- Bing / Google / SerpAPI support
- Playwright fallback for dynamic websites
- article extraction upgrades using trafilatura or readability
- summarization and chunking for RAG
