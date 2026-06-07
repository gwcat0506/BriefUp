"""
STEP 1 — 콘텐츠 수집
topics.name을 실제 수집 키워드로 사용 (동적 관심사 기반)
arxiv: topic_name을 쿼리로 직접 사용
RSS: 카테고리별 소스에서 수집 후 topic_name 키워드로 필터
"""

import re
import httpx
import feedparser
from datetime import date
from core.supabase import supabase

# RSS 소스만 관리 (arxiv 쿼리는 topic_name에서 동적 생성)
RSS_SOURCES: dict[str, list[dict]] = {
    "AI/ML": [
        {"url": "https://huggingface.co/blog/feed.xml", "name": "HuggingFace"},
        {"url": "https://tldr.tech/ai/rss",             "name": "TLDR AI"},
    ],
    "철학": [
        {"url": "https://philosophybites.com/atom.xml",  "name": "Philosophy Bites"},
        {"url": "https://www.philosophersmag.com/feed",  "name": "Philosophers Mag"},
    ],
    "경제": [
        {"url": "https://feeds.feedburner.com/typepad/krMN",                         "name": "Freakonomics"},
        {"url": "https://www.economist.com/finance-and-economics/rss.xml",           "name": "Economist"},
    ],
    "심리학": [
        {"url": "https://www.psychologytoday.com/intl/front-page/feed", "name": "Psychology Today"},
    ],
}


async def collect_for_topic(topic_name: str, category: str) -> list[dict]:
    """
    topic_name을 실제 수집 키워드로 사용.

    - arxiv: topic_name을 쿼리로 직접 검색
    - RSS: 카테고리 소스에서 수집 후 topic_name 키워드 필터
    """
    rss_sources = RSS_SOURCES.get(category, [])
    raw_items = []

    async with httpx.AsyncClient(timeout=20) as client:
        # arxiv — topic_name을 쿼리로 사용
        try:
            items = await _fetch_arxiv(client, topic_name)
            for item in items:
                item["source"] = "arxiv"
                item["topic_category"] = category
            raw_items.extend(items)
        except Exception as e:
            print(f"  [arxiv 오류] '{topic_name}': {e}")

        # RSS — 카테고리 소스 전체 수집
        for source in rss_sources:
            try:
                items = await _fetch_rss(source["url"])
                for item in items:
                    item["source"] = source["name"]
                    item["topic_category"] = category
                raw_items.extend(items)
            except Exception as e:
                print(f"  [RSS 오류] {source['name']}: {e}")

    filtered = [item for item in raw_items if _is_quality_content(item, topic_name)]
    print(f"  [{category}/{topic_name}] 수집 {len(raw_items)}개 → 필터 후 {len(filtered)}개")
    return filtered[:5]


async def collect_for_category(category: str) -> list[dict]:
    """하위 호환용 — category를 topic_name으로 위임."""
    return await collect_for_topic(category, category)


def _is_quality_content(item: dict, topic_name: str) -> bool:
    """품질 필터 3단계"""
    text = item.get("text", "")
    title = item.get("title", "")

    # 1. 길이 체크
    if len(text) < 150:
        return False

    # 2. 관련성 체크 — topic_name을 단어 단위로 분리해 검증
    #    "AI/ML" → ["ai", "ml"], "LangGraph" → ["langgraph"]
    keywords = [kw.lower() for kw in re.split(r"[\s/,]+", topic_name) if len(kw) > 1]
    combined = (title + " " + text).lower()
    if keywords and not any(kw in combined for kw in keywords):
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
