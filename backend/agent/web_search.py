"""
웹 검색 + 신뢰도 필터
Tavily API → KDC 중분류 기반 include_domains 필터 → collector.py 동일 형식 반환
include_domains는 get_collection_plan에서 KDC_MIDDLE_DOMAINS 기반으로 결정되어 전달됨.
신뢰도 통과 결과는 이후 verifier.py에서 재검증
"""

import os
import re
from urllib.parse import urlparse
from tavily import AsyncTavilyClient

TRUST_THRESHOLD = 0.65

# 검색 쿼리 접미사 — topic_name 그대로 쓸 때만 붙임 (Claude가 작성한 web_query엔 붙이지 않음)
_FALLBACK_SUFFIX = "explained guide"

# 스팸·광고성 도메인 차단 — 점수 0 처리
DOMAIN_BLACKLIST: set[str] = {
    "acronymfinder.com", "abbreviations.com", "allacronyms.com",
    "acronymsandslang.com", "dictionary.com", "definitions.net",
    "yourdictionary.com", "thefreedictionary.com",
}

# 최소 본문 길이 (클리닝 후 기준)
_MIN_CONTENT_LEN = 300
# 본문 밀도 임계치 — 알파뉴메릭 비율이 이 미만이면 HTML/네비게이션으로 간주
_MIN_ALPHA_DENSITY = 0.45


def _clean_and_extract(raw: str) -> str:
    """
    raw_content에서 실제 본문 텍스트를 추출한다.
    1. HTML 태그 제거
    2. 마크다운 링크 [text](url) → text (URL 제거해 네비게이션 링크 뭉치 정리)
    3. 마크다운 헤딩·불릿 기호 제거
    4. 3단어 미만 짧은 줄(메뉴 항목) 제거
    5. 중복 공백/개행 정리 후 앞 3000자 반환
    """
    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", " ", raw)
    # 마크다운 링크 → 텍스트만 유지 ([Main page](...) → "Main page")
    text = re.sub(r"\[([^\]]+)\]\(.*?\)", r"\1", text)
    # 마크다운 헤딩·불릿 기호 제거
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[*\-]\s+", "", text, flags=re.MULTILINE)
    # 중복 공백 정리
    text = re.sub(r"[ \t]+", " ", text)

    # 줄 단위로 쪼개서 짧은 줄(네비게이션/메뉴) 제거
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) >= 10:  # 10자 미만 줄은 메뉴/버튼 항목으로 간주 (한국어 단문 보존)
            lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned[:3000]


def _is_content_rich(text: str) -> bool:
    """알파뉴메릭 밀도가 낮으면 HTML/트래킹 코드로 간주."""
    if not text:
        return False
    alpha_num = sum(1 for c in text if c.isalnum())
    return alpha_num / len(text) >= _MIN_ALPHA_DENSITY


def compute_trust_score(tavily_score: float, url: str) -> float:
    """
    신뢰도 점수 = Tavily 점수 그대로 사용.
    include_domains가 KDC 중분류 기반으로 이미 신뢰 도메인을 제한하므로
    별도 도메인 점수 불필요. 블랙리스트만 0점 처리.
    """
    try:
        host = urlparse(url).netloc.lower().lstrip("www.")
        if host in DOMAIN_BLACKLIST:
            return 0.0
    except Exception:
        pass
    return round(tavily_score, 3)


async def search_web(
    query: str,
    max_results: int = 10,
    trust_threshold: float = TRUST_THRESHOLD,
    include_domains: list[str] | None = None,
) -> list[dict]:
    """
    웹 검색 후 신뢰도 필터 적용.

    Args:
        query: 검색 쿼리.
               Claude가 작성한 web_query면 그대로 사용.
               topic_name 그대로 넘어오면 fallback suffix 추가.
        max_results: Tavily에 요청할 최대 결과 수
        trust_threshold: 이 점수 미만은 제외
        include_domains: 이 도메인 목록에서만 검색 (None이면 제한 없음)

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

    search_kwargs: dict = dict(
        query=search_query,
        max_results=max_results,
        include_raw_content=True,
        search_depth="advanced",
    )
    if include_domains:
        search_kwargs["include_domains"] = include_domains

    try:
        response = await client.search(**search_kwargs)
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

        # content(Tavily 큐레이션 발췌) 우선 — 실제 본문 집중.
        # raw_content는 페이지 앞부분 네비게이션을 포함하므로 보조용으로만 사용.
        snippet = (r.get("content") or "").strip()
        raw = r.get("raw_content") or ""
        cleaned_raw = _clean_and_extract(raw) if raw else ""

        if len(snippet) >= 150:
            text = snippet
        elif len(cleaned_raw) >= _MIN_CONTENT_LEN and _is_content_rich(cleaned_raw):
            text = cleaned_raw
        else:
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
