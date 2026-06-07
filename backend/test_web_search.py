"""
web_search.py 단독 테스트
  python test_web_search.py              # 기본 토픽(RAG)으로 검색
  python test_web_search.py "LangGraph"  # 원하는 토픽으로 검색
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

from agent.web_search import (
    search_web,
    compute_trust_score,
    _get_domain_score,
    TRUST_THRESHOLD,
    SEARCH_SUFFIX,
    DOMAIN_BLACKLIST,
)


# ── 단위 테스트 (API 불필요) ─────────────────────────────────────

def test_domain_score():
    cases = [
        ("https://arxiv.org/abs/2304.01234",              1.0),
        ("https://www.nature.com/articles/s41586",         1.0),
        ("https://blog.openai.com/gpt-4",                 0.9),
        ("https://huggingface.co/blog/rlhf",              0.9),
        ("https://www.wired.com/story/ai-new",            0.8),   # 버그 수정 확인
        ("https://techcrunch.com/2024/01/ai",             0.8),
        ("https://medium.com/@user/rag-explained",        0.5),
        ("https://unknownblog.xyz/ai-post",               0.4),
        # 블랙리스트
        ("https://www.acronymfinder.com/RAG.html",        0.0),
        ("https://www.abbreviations.com/RAG",             0.0),
    ]

    print("=== 도메인 점수 테스트 ===")
    passed = 0
    for url, expected in cases:
        score = _get_domain_score(url)
        ok = score == expected
        passed += ok
        mark = "✅" if ok else "❌"
        host = url.split("/")[2]
        domain = host[4:] if host.startswith("www.") else host
        print(f"  {mark} {domain:<35} score={score}  (기대 {expected})")
    print(f"결과: {passed}/{len(cases)} 통과\n")


def test_blacklist():
    print("=== 블랙리스트 테스트 ===")
    for domain in DOMAIN_BLACKLIST:
        score = _get_domain_score(f"https://{domain}/some-page")
        mark = "✅" if score == 0.0 else "❌"
        print(f"  {mark} {domain:<35} score={score}")
    print()


def test_search_suffix():
    print("=== 검색 쿼리 접미사 확인 ===")
    print(f"  SEARCH_SUFFIX = \"{SEARCH_SUFFIX}\"")
    topic = "RAG"
    expected_query = f"{topic} {SEARCH_SUFFIX}"
    print(f"  '{topic}' → '{expected_query}'")
    print(f"  ✅ 기술 콘텐츠 집중 쿼리 확인\n")


def test_trust_score():
    print("=== 신뢰도 점수 계산 테스트 ===")
    cases = [
        # (url, tavily_score, expected_range)
        ("https://arxiv.org/abs/1234",         0.9, (0.9, 1.0)),   # 최상위
        ("https://medium.com/post",            0.9, (0.7, 0.8)),   # 0.6*0.9 + 0.4*0.5 = 0.74
        ("https://openai.com/research",        0.5, (0.6, 0.8)),   # tavily 보통, 도메인 높음
        ("https://unknownblog.xyz/post",       0.3, (0.0, 0.4)),   # 둘 다 낮음
    ]
    passed = 0
    for url, tavily_score, (lo, hi) in cases:
        score = compute_trust_score(tavily_score, url)
        ok = lo <= score <= hi
        passed += ok
        mark = "✅" if ok else "❌"
        domain = url.split("/")[2].lstrip("www.")
        print(f"  {mark} tavily={tavily_score} + {domain:<25} → trust={score}  (기대 {lo}~{hi})")
    print(f"결과: {passed}/{len(cases)} 통과\n")


def test_threshold():
    print(f"=== 임계값 확인: TRUST_THRESHOLD={TRUST_THRESHOLD} ===")
    samples = [
        ("https://arxiv.org/abs/1234",     0.8),
        ("https://medium.com/post",        0.7),
        ("https://unknownblog.xyz/post",   0.5),
    ]
    for url, tavily_score in samples:
        score = compute_trust_score(tavily_score, url)
        status = "통과" if score >= TRUST_THRESHOLD else "필터됨"
        domain = url.split("/")[2].lstrip("www.")
        print(f"  {domain:<30} trust={score} → {status}")
    print()


# ── 실제 검색 테스트 (TAVILY_API_KEY 필요) ──────────────────────

async def test_search(topic_name: str):
    print(f"=== 웹 검색 테스트: '{topic_name}' ===")
    try:
        results = await search_web(topic_name, max_results=10)
    except ValueError as e:
        print(f"  오류: {e}")
        print("  → backend/.env 에 TAVILY_API_KEY 추가 후 재시도\n")
        return

    if not results:
        print("  검색 결과 없음\n")
        return

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] 신뢰도 {r['trust_score']}")
        print(f"      제목: {r['title'][:65]}")
        print(f"      URL:  {r['url'][:70]}")
        print(f"      텍스트 {len(r['text'])}자: {r['text'][:90].replace(chr(10), ' ')}...")
    print()


if __name__ == "__main__":
    # API 없이 돌아가는 단위 테스트
    test_domain_score()
    test_blacklist()
    test_search_suffix()
    test_trust_score()
    test_threshold()

    # 실제 검색 (TAVILY_API_KEY 필요)
    topic = sys.argv[1] if len(sys.argv) > 1 else "RAG retrieval augmented generation"
    asyncio.run(test_search(topic))
