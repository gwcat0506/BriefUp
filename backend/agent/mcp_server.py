"""
BrefUp MCP 수집 서버
fastmcp 기반 — Claude Desktop 또는 MCP 호환 클라이언트에서 직접 연결 가능

실행:
  python agent/mcp_server.py          # stdio MCP 서버
"""

import httpx
from fastmcp import FastMCP
from core.supabase import supabase
from agent.collector import _fetch_arxiv, _fetch_rss, _is_quality_content, RSS_SOURCES
from agent.web_search import search_web

mcp = FastMCP("BrefUp Collector")


@mcp.tool()
async def get_topics() -> list[dict]:
    """
    Supabase topics 테이블에서 활성 관심사 조회.
    동일 name+category를 구독한 유저 수를 집계해 user_count로 반환.
    user_count 높은 순 정렬 — 많이 구독된 관심사를 우선 수집할 수 있도록.
    """
    res = supabase.table("topics").select("name, category").eq("is_active", True).execute()

    counts: dict[tuple, int] = {}
    for row in (res.data or []):
        key = (row["name"], row["category"])
        counts[key] = counts.get(key, 0) + 1

    return sorted(
        [
            {"name": name, "category": cat, "user_count": cnt}
            for (name, cat), cnt in counts.items()
        ],
        key=lambda x: x["user_count"],
        reverse=True,
    )


@mcp.tool()
async def collect_arxiv(topic_name: str, category: str) -> list[dict]:
    """
    arxiv에서 topic_name으로 논문 검색.
    품질 필터(길이·관련성·중복) 적용 후 반환.

    Args:
        topic_name: 검색 키워드 (topics.name 값)
        category:   소속 카테고리 (topic_category 필드에 저장됨)
    """
    async with httpx.AsyncClient(timeout=20) as client:
        items = await _fetch_arxiv(client, topic_name)

    for item in items:
        item["source"] = "arxiv"
        item["topic_category"] = category

    filtered = [item for item in items if _is_quality_content(item, topic_name)]
    print(f"  [arxiv] '{topic_name}' → {len(items)}개 → 필터 후 {len(filtered)}개")
    return filtered


@mcp.tool()
async def collect_rss(topic_name: str, category: str) -> list[dict]:
    """
    카테고리 RSS 소스에서 수집 후 topic_name 키워드 필터.
    RSS_SOURCES에 등록된 카테고리만 지원.

    Args:
        topic_name: 관련성 필터에 사용할 키워드 (topics.name 값)
        category:   RSS 소스 선택 기준 (AI/ML, 철학, 경제, 심리학)
    """
    sources = RSS_SOURCES.get(category, [])
    if not sources:
        print(f"  [RSS] '{category}' 카테고리에 등록된 소스 없음")
        return []

    raw: list[dict] = []
    for source in sources:
        try:
            items = await _fetch_rss(source["url"])
            for item in items:
                item["source"] = source["name"]
                item["topic_category"] = category
            raw.extend(items)
        except Exception as e:
            print(f"  [RSS 오류] {source['name']}: {e}")

    filtered = [item for item in raw if _is_quality_content(item, topic_name)]
    print(f"  [RSS] '{category}/{topic_name}' → {len(raw)}개 → 필터 후 {len(filtered)}개")
    return filtered


@mcp.tool()
async def collect_web(topic_name: str, category: str) -> list[dict]:
    """
    웹 검색 후 신뢰도 필터(0.65+) 적용.
    반환 결과는 이후 verifier.py에서 재검증.

    Args:
        topic_name: 검색 키워드 (SEARCH_SUFFIX 자동 추가됨)
        category:   topic_category 필드에 저장될 카테고리명
    """
    items = await search_web(topic_name)
    for item in items:
        item["topic_category"] = category
    return items


if __name__ == "__main__":
    mcp.run()
