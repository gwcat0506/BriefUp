"""
STEP 1 — 콘텐츠 수집
신뢰도 높은 공식 API/RSS만 사용
수집 후 품질 필터 적용 (길이, 키워드, 중복)
"""

import httpx
import feedparser
from datetime import date
from core.supabase import supabase

# ── 관심사별 소스 매핑 ──────────────────────────────────────────
SOURCES = {
    "AI/ML": [
        {"type": "arxiv",  "query": "RAG retrieval augmented generation agent LLM"},
        {"type": "arxiv",  "query": "agentic AI multi-agent framework"},
        {"type": "rss",    "url": "https://huggingface.co/blog/feed.xml", "name": "HuggingFace"},
        {"type": "rss",    "url": "https://tldr.tech/ai/rss",             "name": "TLDR AI"},
    ],
    "철학": [
        {"type": "rss", "url": "https://philosophybites.com/atom.xml",        "name": "Philosophy Bites"},
        {"type": "rss", "url": "https://www.philosophersmag.com/feed",        "name": "Philosophers Mag"},
    ],
    "경제": [
        {"type": "rss", "url": "https://feeds.feedburner.com/typepad/krMN",  "name": "Freakonomics"},
        {"type": "rss", "url": "https://www.economist.com/finance-and-economics/rss.xml", "name": "Economist"},
    ],
    "심리학": [
        {"type": "rss", "url": "https://www.psychologytoday.com/intl/front-page/feed", "name": "Psychology Today"},
    ],
}

# 카테고리별 품질 키워드 (관련성 검증)
QUALITY_KEYWORDS = {
    "AI/ML":  ["RAG", "agent", "LLM", "embedding", "transformer", "inference", "fine-tuning", "retrieval"],
    "철학":   ["philosophy", "ethics", "logic", "epistemology", "consciousness", "존재", "윤리", "철학"],
    "경제":   ["economy", "market", "GDP", "inflation", "investment", "경제", "시장", "금리"],
    "심리학": ["psychology", "behavior", "cognitive", "mental", "emotion", "심리", "인지", "행동"],
}


async def collect_for_category(category: str) -> list[dict]:
    """카테고리 콘텐츠 수집 + 품질 필터"""
    sources = SOURCES.get(category, [])
    raw_items = []

    async with httpx.AsyncClient(timeout=20) as client:
        for source in sources:
            try:
                if source["type"] == "arxiv":
                    items = await _fetch_arxiv(client, source["query"])
                elif source["type"] == "rss":
                    items = await _fetch_rss(source["url"])
                else:
                    continue

                for item in items:
                    item["source"] = source.get("name", source["type"])
                    item["topic_category"] = category
                raw_items.extend(items)

            except Exception as e:
                print(f"  [수집 오류] {source}: {e}")

    # 품질 필터 적용
    filtered = [item for item in raw_items if _is_quality_content(item, category)]
    print(f"  [{category}] 수집 {len(raw_items)}개 → 필터 후 {len(filtered)}개")
    return filtered[:5]  # 카테고리당 최대 5개


def _is_quality_content(item: dict, category: str) -> bool:
    """품질 필터 3단계"""
    text = item.get("text", "")
    title = item.get("title", "")

    # 1. 길이 체크 — 너무 짧으면 요약/퀴즈 생성 불가
    if len(text) < 150:
        return False

    # 2. 관련성 체크 — 카테고리 키워드 포함 여부
    keywords = QUALITY_KEYWORDS.get(category, [])
    combined = (title + " " + text).lower()
    if not any(kw.lower() in combined for kw in keywords):
        return False

    # 3. 중복 체크 — 오늘 이미 수집된 URL
    url = item.get("url", "")
    if url:
        existing = supabase.table("contents").select("id").eq("original_url", url).execute()
        if existing.data:
            return False

    return True


async def _fetch_arxiv(client: httpx.AsyncClient, query: str) -> list[dict]:
    """arxiv 공식 API"""
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query=all:{query}"
        f"&max_results=5"
        f"&sortBy=submittedDate&sortOrder=descending"
    )
    res = await client.get(url)
    feed = feedparser.parse(res.text)

    return [
        {
            "title": entry.title.replace("\n", " ").strip(),
            "url":   entry.link,
            "text":  entry.summary.replace("\n", " ").strip()[:2000],
        }
        for entry in feed.entries
    ]


async def _fetch_rss(url: str) -> list[dict]:
    """RSS 피드"""
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:5]:
        text = entry.get("summary", "") or entry.get("description", "")
        results.append({
            "title": entry.get("title", "").strip(),
            "url":   entry.get("link", ""),
            "text":  text[:2000],
        })
    return results
