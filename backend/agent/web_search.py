"""
웹 검색 + 신뢰도 필터
Tavily API → 도메인/관련성 기반 필터 → collector.py 동일 형식 반환
신뢰도 통과 결과는 이후 verifier.py에서 재검증
"""

import os
from urllib.parse import urlparse
from tavily import AsyncTavilyClient

TRUST_THRESHOLD = 0.65

# 검색 쿼리 접미사 — topic_name 그대로 쓸 때만 붙임 (Claude가 작성한 web_query엔 붙이지 않음)
_FALLBACK_SUFFIX = "explained guide"

# 신뢰도 0으로 처리 — 약어 사전, 광고성 사이트
DOMAIN_BLACKLIST: set[str] = {
    "acronymfinder.com", "abbreviations.com", "allacronyms.com",
    "acronymsandslang.com", "dictionary.com", "definitions.net",
    "yourdictionary.com", "thefreedictionary.com",
}

# 명시적 화이트리스트 점수 (없는 도메인은 TLD/키워드 로직으로 처리)
DOMAIN_SCORES: dict[str, float] = {
    # 학술/공식 연구기관
    "arxiv.org": 1.0, "nature.com": 1.0, "science.org": 1.0,
    "pnas.org": 1.0, "acm.org": 1.0, "ieee.org": 1.0,
    "pubmed.ncbi.nlm.nih.gov": 1.0, "ncbi.nlm.nih.gov": 1.0,
    # AI 연구소
    "openai.com": 0.9, "anthropic.com": 0.9, "deepmind.google": 0.9,
    "research.google": 0.9, "ai.meta.com": 0.9, "huggingface.co": 0.9,
    "mistral.ai": 0.9,
    # 교육 플랫폼
    "khanacademy.org": 0.85, "coursera.org": 0.8, "edx.org": 0.8,
    "brilliant.org": 0.8,
    # 백과사전 / 레퍼런스
    "wikipedia.org": 0.85, "britannica.com": 0.85, "scholarpedia.org": 0.85,
    "plato.stanford.edu": 0.9,
    # 금융 / 투자
    "investopedia.com": 0.8, "wsj.com": 0.8, "ft.com": 0.8,
    "bloomberg.com": 0.8, "marketwatch.com": 0.75, "seekingalpha.com": 0.7,
    "morningstar.com": 0.75, "fool.com": 0.7,
    # 역사 / 인문
    "history.com": 0.75, "smithsonianmag.com": 0.8, "nationalgeographic.com": 0.8,
    "historyhit.com": 0.7,
    # 건강 / 의학
    "healthline.com": 0.8, "webmd.com": 0.75, "mayoclinic.org": 0.9,
    "nih.gov": 0.9, "who.int": 0.9, "medicalnewstoday.com": 0.75,
    "menshealth.com": 0.7, "self.com": 0.7,
    # 과학 / 기술 미디어
    "techcrunch.com": 0.8, "wired.com": 0.8, "theverge.com": 0.8,
    "arstechnica.com": 0.8, "technologyreview.com": 0.8,
    "sciencedaily.com": 0.8, "newscientist.com": 0.8,
    "quantamagazine.org": 0.85,
    # 철학
    "iep.utm.edu": 0.9, "philosophybasics.com": 0.75,
    # 주요 언론
    "reuters.com": 0.75, "apnews.com": 0.75, "bbc.com": 0.75,
    "economist.com": 0.75, "nytimes.com": 0.75, "theguardian.com": 0.75,
    # 스타트업 / 비즈니스
    "hbr.org": 0.85, "mckinsey.com": 0.8, "a16z.com": 0.8,
    "paulgraham.com": 0.8, "ycombinator.com": 0.8,
    # UGC / 블로그
    "medium.com": 0.5, "substack.com": 0.5, "dev.to": 0.5, "hashnode.com": 0.5,
}

# 도메인 키워드 → 점수 (화이트리스트에 없어도 이름으로 신뢰도 판단)
_TRUSTED_KEYWORDS: dict[str, float] = {
    "wikipedia": 0.85, "britannica": 0.85, "khan": 0.82,
    "university": 0.8, "institute": 0.78, "hospital": 0.8,
    "gov": 0.82, "edu": 0.8,
    "investopedia": 0.8, "healthline": 0.78, "mayoclinic": 0.88,
    "nature": 0.9, "science": 0.85, "research": 0.75,
    "quanta": 0.85, "smithsonian": 0.82,
}

# TLD별 기본 점수 (화이트리스트·키워드 모두 미해당 시)
_TLD_SCORES: dict[str, float] = {
    ".edu": 0.80,
    ".gov": 0.85,
    ".org": 0.65,
    ".ac.": 0.78,  # .ac.uk, .ac.jp 등 학술기관
}

DEFAULT_DOMAIN_SCORE = 0.5  # 화이트리스트 밖 일반 도메인 기본값 상향


def _get_domain_score(url: str) -> float:
    """
    URL → 도메인 신뢰도 점수.
    우선순위: 화이트리스트 → 키워드 패턴 → TLD → 기본값
    """
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]

        if host in DOMAIN_BLACKLIST:
            return 0.0

        # 1. 명시적 화이트리스트
        if host in DOMAIN_SCORES:
            return DOMAIN_SCORES[host]

        # 2. 서브도메인 → 루트 도메인 매칭 (blog.openai.com → openai.com)
        for domain, score in DOMAIN_SCORES.items():
            if host.endswith("." + domain):
                return score

        # 3. 도메인 이름에 신뢰 키워드 포함 여부
        for keyword, score in _TRUSTED_KEYWORDS.items():
            if keyword in host:
                return score

        # 4. TLD 기반 기본 점수
        for tld, score in _TLD_SCORES.items():
            if host.endswith(tld) or f".{tld}." in host:
                return score

        return DEFAULT_DOMAIN_SCORE
    except Exception:
        return DEFAULT_DOMAIN_SCORE


def compute_trust_score(tavily_score: float, url: str) -> float:
    """
    신뢰도 점수 = Tavily 관련성 70% + 도메인 점수 30%.
    Tavily의 관련성 판단을 더 신뢰해 미등록 도메인도 유연하게 통과.
    """
    domain_score = _get_domain_score(url)
    return round(0.7 * tavily_score + 0.3 * domain_score, 3)


async def search_web(
    query: str,
    max_results: int = 10,
    trust_threshold: float = TRUST_THRESHOLD,
) -> list[dict]:
    """
    웹 검색 후 신뢰도 필터 적용.

    Args:
        query: 검색 쿼리.
               Claude가 작성한 web_query면 그대로 사용.
               topic_name 그대로 넘어오면 fallback suffix 추가.
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

    # 한국어만 있으면(Claude 쿼리 아님) fallback suffix 추가
    has_korean = any("가" <= c <= "힣" for c in query)
    search_query = f"{query} {_FALLBACK_SUFFIX}" if has_korean else query

    try:
        response = await client.search(
            query=search_query,
            max_results=max_results,
            include_raw_content=True,
            search_depth="advanced",
        )
    except Exception as e:
        print(f"  [웹 검색 오류] '{query}': {e}")
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
        f"  [웹 검색] '{search_query}' → {len(raw_results)}개 수집 "
        f"→ 신뢰도 {trust_threshold}+ 통과 {len(filtered)}개"
    )
    return filtered
