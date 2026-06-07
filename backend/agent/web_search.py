"""
웹 검색 + 신뢰도 필터
Tavily API → 도메인/관련성 기반 필터 → collector.py 동일 형식 반환
신뢰도 통과 결과는 이후 verifier.py에서 재검증
"""

import os
from urllib.parse import urlparse
from tavily import AsyncTavilyClient

TRUST_THRESHOLD = 0.65

# 검색 쿼리 접미사 — 기술 콘텐츠 집중, 약어/사전 결과 배제
SEARCH_SUFFIX = "research OR paper OR guide"

# 신뢰도 점수 0으로 처리 — 약어 사전, 광고성 사이트 등
DOMAIN_BLACKLIST: set[str] = {
    "acronymfinder.com",
    "abbreviations.com",
    "allacronyms.com",
    "acronymsandslang.com",
    "dictionary.com",
    "definitions.net",
    "yourdictionary.com",
    "thefreedictionary.com",
}

# 도메인 신뢰도 점수 (tier 기반)
DOMAIN_SCORES: dict[str, float] = {
    # 학술/공식 연구기관
    "arxiv.org":        1.0,
    "nature.com":       1.0,
    "science.org":      1.0,
    "pnas.org":         1.0,
    "acm.org":          1.0,
    "ieee.org":         1.0,
    # AI 연구소 공식 채널
    "openai.com":       0.9,
    "anthropic.com":    0.9,
    "deepmind.google":  0.9,
    "research.google":  0.9,
    "ai.meta.com":      0.9,
    "huggingface.co":   0.9,
    "mistral.ai":       0.9,
    # 주요 대학
    "mit.edu":          0.85,
    "stanford.edu":     0.85,
    "berkeley.edu":     0.85,
    "cs.cmu.edu":       0.85,
    # 권위 있는 기술/과학 미디어
    "techcrunch.com":   0.8,
    "wired.com":        0.8,
    "theverge.com":     0.8,
    "arstechnica.com":  0.8,
    "technologyreview.com": 0.8,
    # 주요 일반 언론
    "reuters.com":      0.75,
    "apnews.com":       0.75,
    "bbc.com":          0.75,
    "economist.com":    0.75,
    "ft.com":           0.75,
    # UGC / 블로그
    "medium.com":       0.5,
    "substack.com":     0.5,
    "dev.to":           0.5,
    "hashnode.com":     0.5,
}
DEFAULT_DOMAIN_SCORE = 0.4


def _get_domain_score(url: str) -> float:
    """URL에서 도메인 추출 후 점수 반환. 서브도메인도 처리."""
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]  # lstrip("www.") 쓰면 wired.com → ired.com 버그 발생

        if host in DOMAIN_BLACKLIST:
            return 0.0

        if host in DOMAIN_SCORES:
            return DOMAIN_SCORES[host]

        # blog.openai.com → openai.com 형태 처리
        for domain, score in DOMAIN_SCORES.items():
            if host.endswith("." + domain):
                return score

        return DEFAULT_DOMAIN_SCORE
    except Exception:
        return DEFAULT_DOMAIN_SCORE


def compute_trust_score(tavily_score: float, url: str) -> float:
    """신뢰도 점수 = Tavily 관련성 60% + 도메인 점수 40%"""
    domain_score = _get_domain_score(url)
    return round(0.6 * tavily_score + 0.4 * domain_score, 3)


async def search_web(
    topic_name: str,
    max_results: int = 10,
    trust_threshold: float = TRUST_THRESHOLD,
) -> list[dict]:
    """
    웹 검색 후 신뢰도 필터 적용.

    Args:
        topic_name: 수집할 관심사 키워드 (topics.name 값 그대로 사용)
        max_results: Tavily에 요청할 최대 결과 수
        trust_threshold: 이 점수 미만은 제외

    Returns:
        collector.py와 동일한 [{title, url, text, trust_score}] 리스트.
        신뢰도 높은 순 정렬.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY 환경변수가 없습니다.")

    client = AsyncTavilyClient(api_key=api_key)

    try:
        response = await client.search(
            query=f"{topic_name} {SEARCH_SUFFIX}",
            max_results=max_results,
            include_raw_content=True,
            search_depth="advanced",
        )
    except Exception as e:
        print(f"  [웹 검색 오류] '{topic_name}': {e}")
        return []

    raw_results = response.get("results", [])
    filtered = []

    for r in raw_results:
        url = r.get("url", "")
        trust_score = compute_trust_score(r.get("score", 0.0), url)

        if trust_score < trust_threshold:
            continue

        # raw_content(전문) 우선, 없으면 content(스니펫)
        text = (r.get("raw_content") or r.get("content") or "").strip()[:3000]

        # collector.py와 동일한 최소 길이 기준
        if len(text) < 150:
            continue

        filtered.append({
            "title": r.get("title", "").strip(),
            "url":   url,
            "text":  text,
            "trust_score": trust_score,
        })

    filtered.sort(key=lambda x: x["trust_score"], reverse=True)

    print(
        f"  [웹 검색] '{topic_name}' → {len(raw_results)}개 수집 "
        f"→ 신뢰도 {trust_threshold}+ 통과 {len(filtered)}개"
    )
    return filtered
