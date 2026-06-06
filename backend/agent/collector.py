import httpx
import feedparser
from datetime import date

# ── 관심사별 소스 매핑 ──────────────────────────────
SOURCES = {
    "AI/ML": [
        {"type": "arxiv", "query": "RAG agent LLM"},
        {"type": "rss", "url": "https://huggingface.co/blog/feed.xml"},
        {"type": "rss", "url": "https://tldr.tech/ai/rss"},
    ],
    "철학": [
        {"type": "rss", "url": "https://philosophybites.com/atom.xml"},
    ],
    "경제": [
        {"type": "rss", "url": "https://feeds.bloomberg.com/markets/news.rss"},
    ],
    "심리학": [
        {"type": "rss", "url": "https://www.psychologytoday.com/intl/front-page/feed"},
    ],
}

async def collect_for_category(category: str) -> list[dict]:
    """카테고리에 맞는 콘텐츠 수집"""
    sources = SOURCES.get(category, [])
    results = []

    async with httpx.AsyncClient(timeout=15) as client:
        for source in sources:
            try:
                if source["type"] == "arxiv":
                    items = await _fetch_arxiv(client, source["query"])
                elif source["type"] == "rss":
                    items = await _fetch_rss(source["url"])
                else:
                    continue

                for item in items[:3]:  # 소스당 최대 3개
                    results.append({
                        "topic_category": category,
                        "source": source["type"],
                        "title": item["title"],
                        "original_url": item.get("url", ""),
                        "raw_text": item.get("text", ""),
                        "collected_at": date.today().isoformat()
                    })
            except Exception as e:
                print(f"[수집 오류] {source}: {e}")

    return results

async def _fetch_arxiv(client: httpx.AsyncClient, query: str) -> list[dict]:
    url = f"https://export.arxiv.org/api/query?search_query=all:{query}&max_results=3&sortBy=submittedDate"
    res = await client.get(url)
    feed = feedparser.parse(res.text)
    return [
        {
            "title": entry.title,
            "url": entry.link,
            "text": entry.summary[:1000]
        }
        for entry in feed.entries
    ]

async def _fetch_rss(url: str) -> list[dict]:
    feed = feedparser.parse(url)
    return [
        {
            "title": entry.title,
            "url": entry.link,
            "text": entry.get("summary", "")[:1000]
        }
        for entry in feed.entries[:3]
    ]
