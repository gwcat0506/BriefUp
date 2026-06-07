"""
mcp_server.py 단독 테스트
  python test_mcp_server.py              # 기본 (RAG / AI/ML)
  python test_mcp_server.py "LangGraph" "AI/ML"
  python test_mcp_server.py "사르트르" "철학"
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()


# ── 서버 임포트 확인 (실행 없이) ─────────────────────────────────

async def test_import():
    print("=== 임포트 및 도구 등록 확인 ===")
    try:
        from agent.mcp_server import mcp
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}
        expected = {"get_topics", "collect_arxiv", "collect_rss", "collect_web"}

        for name in sorted(expected):
            mark = "✅" if name in tool_names else "❌"
            print(f"  {mark} {name}")

        missing = expected - tool_names
        if missing:
            print(f"  ❌ 미등록 도구: {missing}")
        else:
            print(f"  ✅ 도구 {len(expected)}개 모두 등록\n")

    except Exception as e:
        print(f"  ❌ 임포트 오류: {e}\n")
        raise


# ── 실제 도구 호출 테스트 (네트워크 + DB 필요) ───────────────────

async def test_get_topics():
    from agent.mcp_server import get_topics
    print("=== get_topics() ===")
    try:
        topics = await get_topics()
        if not topics:
            print("  결과 없음 (topics 테이블 비어 있거나 is_active=False)\n")
            return
        for t in topics[:5]:
            print(f"  [{t['user_count']}명] {t['category']} / {t['name']}")
        if len(topics) > 5:
            print(f"  ... 외 {len(topics) - 5}개")
    except Exception as e:
        print(f"  오류: {e}")
    print()


async def test_collect_arxiv(topic_name: str, category: str):
    from agent.mcp_server import collect_arxiv
    print(f"=== collect_arxiv('{topic_name}', '{category}') ===")
    try:
        results = await collect_arxiv(topic_name, category)
        _print_results(results)
    except Exception as e:
        print(f"  오류: {e}\n")


async def test_collect_rss(topic_name: str, category: str):
    from agent.mcp_server import collect_rss
    print(f"=== collect_rss('{topic_name}', '{category}') ===")
    try:
        results = await collect_rss(topic_name, category)
        _print_results(results)
    except Exception as e:
        print(f"  오류: {e}\n")


async def test_collect_web(topic_name: str, category: str):
    from agent.mcp_server import collect_web
    print(f"=== collect_web('{topic_name}', '{category}') ===")
    try:
        results = await collect_web(topic_name, category)
        for r in results:
            trust = r.get("trust_score", "-")
            print(f"  [{trust}] {r['title'][:60]}")
            print(f"         {r['url'][:65]}")
        if not results:
            print("  결과 없음 (TAVILY_API_KEY 확인)")
    except Exception as e:
        print(f"  오류: {e}")
    print()


def _print_results(results: list[dict]):
    if not results:
        print("  결과 없음\n")
        return
    for r in results:
        print(f"  [{r.get('source', '?')}] {r['title'][:60]}")
        print(f"         {len(r['text'])}자  {r['url'][:60]}")
    print()


if __name__ == "__main__":
    topic    = sys.argv[1] if len(sys.argv) > 1 else "RAG"
    category = sys.argv[2] if len(sys.argv) > 2 else "AI/ML"

    # 임포트/등록 확인 (네트워크 불필요)
    asyncio.run(test_import())

    # 도구별 실제 호출
    asyncio.run(test_get_topics())
    asyncio.run(test_collect_arxiv(topic, category))
    asyncio.run(test_collect_rss(topic, category))
    asyncio.run(test_collect_web(topic, category))
