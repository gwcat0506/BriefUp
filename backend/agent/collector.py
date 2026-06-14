"""
STEP 1 — 콘텐츠 수집
topics.name을 실제 수집 키워드로 사용 (동적 관심사 기반)
arxiv: topic_name을 쿼리로 직접 사용
RSS: 카테고리별 소스에서 수집 후 topic_name 키워드로 필터
"""

import asyncio
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


async def collect_for_topic(
    topic_name: str,
    category: str,
    arxiv_query: str | None = None,
    use_arxiv: bool = True,
    rss_sources: list[dict] | None = None,
) -> list[dict]:
    """
    topic_name을 실제 수집 키워드로 사용.

    - arxiv: use_arxiv=True이고 arxiv_query 또는 topic_name으로 검색
    - RSS: rss_sources 지정 시 해당 목록 사용, 없으면 RSS_SOURCES[category] 사용
    """
    effective_rss = rss_sources if rss_sources is not None else RSS_SOURCES.get(category, [])
    raw_items: list[dict] = []

    async with httpx.AsyncClient(timeout=20) as client:
        # arxiv — use_arxiv=True일 때만 수집
        if use_arxiv:
            try:
                query = arxiv_query or topic_name
                items = await _fetch_arxiv(client, query)
                for item in items:
                    item["source"] = "arxiv"
                    item["topic_category"] = category
                raw_items.extend(items)
            except Exception as e:
                print(f"  [arxiv 오류] '{topic_name}': {e}")

        # RSS — 카테고리 소스 전체 수집
        for source in effective_rss:
            try:
                items = await _fetch_rss(source["url"])
                for item in items:
                    item["source"] = source["name"]
                    item["topic_category"] = category
                raw_items.extend(items)
            except Exception as e:
                print(f"  [RSS 오류] {source['name']}: {e}")

    # 이미 수집된 URL 조회 — 단일 배치 async 호출 (이벤트 루프 블로킹 방지)
    all_urls = [item.get("url", "") for item in raw_items]
    existing_urls = await _fetch_existing_urls(all_urls)

    effective_query = arxiv_query or topic_name
    filtered = [item for item in raw_items if _is_quality_content(item, effective_query, existing_urls)]
    print(f"  [{category}/{topic_name}] 수집 {len(raw_items)}개 → 필터 후 {len(filtered)}개")
    return filtered[:5]


async def _fetch_existing_urls(urls: list[str]) -> set[str]:
    """오늘 이미 저장된 URL 목록을 한 번의 쿼리로 가져온다."""
    clean = [u for u in urls if u]
    if not clean:
        return set()
    try:
        res = await asyncio.to_thread(
            lambda: supabase.table("contents")
                .select("original_url")
                .in_("original_url", clean)
                .execute()
        )
        return {row["original_url"] for row in (res.data or [])}
    except Exception:
        return set()


def _is_quality_content(item: dict, query: str, existing_urls: set[str]) -> bool:
    """품질 필터"""
    text   = item.get("text", "")
    source = item.get("source", "")

    # 1. 길이 체크
    if len(text) < 150:
        return False

    # 2. 관련성 체크
    # - arxiv: 이미 특정 쿼리로 검색했으므로 스킵
    # - trust_score 있는 항목: Tavily가 관련성 보장했으므로 스킵
    # - RSS/기타: query 키워드로 필터
    is_arxiv = source == "arxiv"
    is_web   = "trust_score" in item
    if not is_arxiv and not is_web:
        keywords = [kw.lower() for kw in re.split(r"[\s/,]+", query) if len(kw) > 1]
        combined = (item.get("title", "") + " " + text).lower()
        if keywords and not any(kw in combined for kw in keywords):
            return False

    # 3. 중복 체크 — 이미 수집된 URL
    url = item.get("url", "")
    if url and url in existing_urls:
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
