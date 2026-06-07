"""
collector.py 단독 테스트
  python test_collector.py                  # 기본 (RAG / AI/ML)
  python test_collector.py "LangGraph" "AI/ML"
  python test_collector.py "사르트르" "철학"
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

from agent.collector import (
    collect_for_topic,
    collect_for_category,
    _is_quality_content,
    RSS_SOURCES,
)


# ── 단위 테스트 (네트워크/DB 불필요) ─────────────────────────────

def test_keyword_split():
    """topic_name 키워드 분리 동작 확인"""
    import re

    cases = [
        ("RAG",             ["rag"]),
        ("AI/ML",           ["ai", "ml"]),
        ("LangGraph",       ["langgraph"]),
        ("사르트르",         ["사르트르"]),
        ("multi-agent",     ["multi-agent"]),  # 하이픈은 분리 안 함 — 검색 정밀도 유지
    ]

    print("=== 키워드 분리 테스트 ===")
    passed = 0
    for topic, expected in cases:
        result = [kw.lower() for kw in re.split(r"[\s/,]+", topic) if len(kw) > 1]
        ok = result == expected
        passed += ok
        mark = "✅" if ok else "❌"
        print(f"  {mark} '{topic}' → {result}  (기대 {expected})")
    print(f"결과: {passed}/{len(cases)} 통과\n")


def test_quality_filter_length():
    """길이 필터 확인 (DB 없이)"""
    print("=== 길이 필터 테스트 ===")
    short = {"title": "짧은 글", "text": "너무 짧아요", "url": ""}
    long  = {"title": "RAG 논문", "text": "RAG " + "x" * 200, "url": ""}

    # url 빈 문자열이면 중복 체크 스킵됨
    print(f"  짧은 글 (text={len(short['text'])}자): {'통과' if _is_quality_content(short, 'RAG') else '필터됨'} → 기대: 필터됨")
    print(f"  긴 글   (text={len(long['text'])}자):  {'통과' if _is_quality_content(long, 'RAG') else '필터됨'} → 기대: 통과\n")


def test_rss_sources():
    """RSS_SOURCES에 arxiv 쿼리가 없는지 확인"""
    print("=== RSS_SOURCES 구조 확인 ===")
    has_arxiv = False
    for category, sources in RSS_SOURCES.items():
        for s in sources:
            if s.get("type") == "arxiv" or "query" in s:
                has_arxiv = True
                print(f"  ❌ arxiv 쿼리 발견: {category} / {s}")
        print(f"  ✅ {category}: RSS {len(sources)}개")
    if not has_arxiv:
        print("  ✅ arxiv 쿼리 없음 — topic_name 동적 사용으로 변경 확인\n")


# ── 실제 수집 테스트 (네트워크 + DB 필요) ────────────────────────

async def test_collect_topic(topic_name: str, category: str):
    print(f"=== 수집 테스트: topic='{topic_name}' / category='{category}' ===")
    results = await collect_for_topic(topic_name, category)

    if not results:
        print("  결과 없음 (네트워크 또는 필터 확인)\n")
        return

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r['source']}")
        print(f"      제목: {r['title'][:65]}")
        print(f"      URL:  {r['url'][:70]}")
        print(f"      텍스트 {len(r['text'])}자")
    print()


async def test_collect_category_compat():
    """collect_for_category 하위 호환 확인"""
    print("=== 하위 호환 테스트: collect_for_category('AI/ML') ===")
    results = await collect_for_category("AI/ML")
    print(f"  결과 {len(results)}개\n")


if __name__ == "__main__":
    # API/DB 없이 돌아가는 단위 테스트
    test_keyword_split()
    test_quality_filter_length()
    test_rss_sources()

    # 실제 수집 테스트 (네트워크 + Supabase 필요)
    topic    = sys.argv[1] if len(sys.argv) > 1 else "RAG"
    category = sys.argv[2] if len(sys.argv) > 2 else "AI/ML"

    asyncio.run(test_collect_topic(topic, category))
    asyncio.run(test_collect_category_compat())
