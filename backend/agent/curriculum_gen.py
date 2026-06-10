"""
관심사 추가 시 Claude가 커리큘럼 자동 생성
- 챕터 구조 (기초 → 중급 → 심화) + 챕터별 검색 힌트(arxiv_query, web_query) 포함
- topic_curricula DB에 캐시: 동일 토픽은 재생성 없이 DB에서 조회
- 생성 후 구조 검증 + Claude 자기비판으로 품질 보장
"""

import asyncio
import json
import os
import re

import anthropic
from core.supabase import supabase

claude = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CURRICULUM_PROMPT = """당신은 "{topic_name}"({category}) 분야의 전문 커리큘럼 설계자입니다.

이 분야를 체계적으로 학습할 수 있도록 12~14개의 챕터로 구성된 커리큘럼을 만들어주세요.

## 핵심 원칙 (반드시 준수)
- concepts 목록에는 실제로 존재하고 검증 가능한 기법명·논문명·알고리즘명만 포함
  - ✅ 좋은 예: "HyDE (Hypothetical Document Embeddings)", "FAISS", "Attention Is All You Need (Vaswani 2017)"
  - ❌ 금지: "고급 기법", "최신 알고리즘", "다양한 방법론" 같은 막연한 표현
- 존재하지 않는 논문명이나 알고리즘명을 지어내지 마세요
- 확실하지 않은 개념은 포함하지 마세요

## 설계 원칙
- 챕터 제목: 독자가 진짜 궁금해할 질문 또는 핵심 긴장감을 담은 제목
- 실용성 우선: "어떻게 선택하는가", "언제 쓰는가", "왜 실패하는가" 같은 의사결정 중심 챕터 포함
- 놓치기 쉬운 실전 주제 포함: 비용 관리, 도구 비교, 흔한 실수, 선택 기준 등
- 진행 구조: 기초 이해 → 핵심 기법 적용 → 비교·선택 판단 → 고급 주제/실전 설계
- level 분포 기준:
  - "입문": 1~2개 — 사전 지식 없이 읽을 수 있는 배경·동기 챕터
  - "기본": 2~3개 — 핵심 메커니즘을 이해하고 기본 적용 가능한 챕터
  - "중급": 2~3개 — 트레이드오프를 판단하고 비교·선택할 수 있는 챕터
  - "심화": 2~3개 — 최신 연구·복잡한 아키텍처·실전 설계 판단이 필요한 챕터
- description: "이 챕터를 읽으면 ~를 이해하고 ~를 판단할 수 있다" — 학습 결과 중심
- search_hints: 아티클 수집용 영문 검색 쿼리
  - arxiv_query: 학술 논문이 있는 분야면 실제 논문/기법명 포함, 없으면 null
  - web_query: 챕터 핵심 기법을 설명하는 영문 웹 검색 쿼리

아래 JSON 형식으로만 응답하세요:
{{
  "emoji": "분야를 잘 표현하는 이모지 1개",
  "color": "hex 색상코드 (예: #10B981)",
  "description": "이 분야를 한 문장으로 — 핵심 가치와 학습 범위를 담아서",
  "topic_aliases": ["동의어1", "동의어2"],
  "chapters": [
    {{
      "id": "{topic_key}-1",
      "title": "핵심 질문 또는 긴장감을 담은 챕터 제목",
      "description": "이 챕터를 읽으면 ~를 이해하고 ~를 판단할 수 있다 (1문장, 실제 기법명 포함)",
      "level": "입문",
      "duration": "10분",
      "concepts": ["실제존재하는기법1", "검증된논문명또는알고리즘", "구체적개념3"],
      "search_hints": {{
        "arxiv_query": "실제 논문/기법명 키워드 또는 null",
        "web_query": "챕터 핵심기법 영문 웹검색 쿼리 2024"
      }}
    }}
  ]
}}"""

VALIDATE_PROMPT = """당신은 "{topic_name}" 분야 전문가입니다.
아래 커리큘럼을 검토하고, 존재하지 않거나 틀린 개념명·논문명·알고리즘명이 있으면 수정하세요.

## 검토 기준
1. concepts 목록의 각 항목이 실제로 존재하는가?
2. 존재하지 않는 논문명/알고리즘명이 있으면 실제 이름으로 교체하거나 제거
3. 챕터 순서가 난이도 흐름에 맞는가?

[커리큘럼 chapters]
{chapters_json}

JSON으로만 응답:
{{
  "valid": true or false,
  "issues": ["문제점 설명"] or [],
  "chapters": [수정된 chapters 배열 — 수정 없으면 입력과 동일하게 반환]
}}"""


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[\s/,]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def _validate_structure(curriculum: dict) -> list[str]:
    """필수 필드와 챕터 수 등 구조적 유효성 검사."""
    issues = []
    chapters = curriculum.get("chapters", [])
    if len(chapters) < 6:
        issues.append(f"챕터 수 부족: {len(chapters)}개 (최소 6개 필요)")
    for i, ch in enumerate(chapters):
        for field in ("id", "title", "description", "level", "concepts", "search_hints"):
            if not ch.get(field):
                issues.append(f"챕터 {i+1} '{ch.get('title', '?')}': '{field}' 필드 없음")
        if not ch.get("concepts"):
            issues.append(f"챕터 {i+1}: concepts 비어있음")
    return issues


async def _validate_concepts(topic_name: str, chapters: list[dict]) -> list[dict]:
    """Claude로 concepts 실존 여부 검증 + 수정."""
    print(f"  [커리큘럼 검증] '{topic_name}' concepts 실존 여부 확인...")
    try:
        response = await claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": VALIDATE_PROMPT.format(
                    topic_name=topic_name,
                    chapters_json=json.dumps(chapters, ensure_ascii=False, indent=2),
                ),
            }],
        )
        raw = response.content[0].text.strip()
        raw = _extract_json(raw)
        result = json.loads(raw)

        if result.get("issues"):
            print(f"  [커리큘럼 검증 이슈] {result['issues']}")

        corrected = result.get("chapters", chapters)
        if not corrected:
            return chapters
        print(f"  [커리큘럼 검증 완료] valid={result.get('valid')}")
        return corrected

    except Exception as e:
        print(f"  [커리큘럼 검증 오류] {e} — 원본 유지")
        return chapters


def _catalog_to_row(topic_key: str, track: dict, category: str) -> dict:
    return {
        "topic_key":     topic_key,
        "topic_name":    track["title"],
        "category":      category,
        "topic_aliases": track.get("topic_names", []),
        "emoji":         track.get("emoji", "📚"),
        "color":         track.get("color", "#6366F1"),
        "description":   track.get("description", ""),
        "chapters":      track["chapters"],
    }


async def get_or_create_curriculum(topic_name: str, category: str) -> dict:
    """
    topic_name에 대한 커리큘럼을 반환.
    CURRICULUM_CATALOG에 있는 토픽은 항상 카탈로그(최신) 우선 반환.
    없으면 DB 캐시 → Claude 생성 순으로 진행.
    """
    from agent.curriculum_catalog import CURRICULUM_CATALOG

    topic_key = _slugify(topic_name)

    # 1. CURRICULUM_CATALOG 직접 매칭 (항상 최신 데이터)
    if topic_key in CURRICULUM_CATALOG:
        return _catalog_to_row(topic_key, CURRICULUM_CATALOG[topic_key], category)

    # 2. CURRICULUM_CATALOG alias 매칭
    for cat_key, cat_data in CURRICULUM_CATALOG.items():
        if topic_name in cat_data.get("topic_names", []):
            return _catalog_to_row(cat_key, cat_data, category)

    # 3. DB 캐시 확인
    existing = await asyncio.to_thread(
        lambda: supabase.table("topic_curricula")
            .select("*")
            .eq("topic_key", topic_key)
            .execute()
    )
    if existing.data:
        return existing.data[0]

    # 4. DB alias 검색
    alias_match = await asyncio.to_thread(
        lambda: supabase.table("topic_curricula")
            .select("*")
            .contains("topic_aliases", [topic_name])
            .execute()
    )
    if alias_match.data:
        return alias_match.data[0]

    # 5. Claude로 신규 생성 + 검증
    curriculum = await _generate_and_validate_curriculum(topic_name, category, topic_key)

    # 6. DB 저장
    saved = await asyncio.to_thread(
        lambda: supabase.table("topic_curricula").insert({
            "topic_key":    topic_key,
            "topic_name":   topic_name,
            "category":     category,
            "topic_aliases": curriculum.get("topic_aliases", []),
            "emoji":        curriculum.get("emoji", "📚"),
            "color":        curriculum.get("color", "#6366F1"),
            "description":  curriculum.get("description", ""),
            "chapters":     curriculum["chapters"],
        }).execute()
    )
    return saved.data[0]


def _fallback_curriculum(topic_name: str, topic_key: str) -> dict:
    """JSON 파싱 실패 시 최소 구조 반환."""
    steps = [
        ("기초 개념 이해", "입문"), ("핵심 원리", "기본"), ("주요 기법", "기본"),
        ("심화 분석", "중급"), ("실전 적용", "중급"), ("최신 동향", "심화"),
    ]
    return {
        "emoji": "📚",
        "color": "#6366F1",
        "description": f"{topic_name}의 핵심 개념부터 실전 적용까지",
        "topic_aliases": [],
        "chapters": [
            {
                "id": f"{topic_key}-{i}",
                "title": f"{topic_name}: {title}",
                "description": f"{topic_name}의 {title}을 이해하고 적용할 수 있다",
                "level": level,
                "duration": "10분",
                "concepts": [topic_name],
                "search_hints": {"arxiv_query": None, "web_query": f"{topic_name} {title} 2024"},
            }
            for i, (title, level) in enumerate(steps, 1)
        ],
    }


async def _generate_and_validate_curriculum(topic_name: str, category: str, topic_key: str) -> dict:
    """Claude API로 커리큘럼 생성 후 구조 검증 + concepts 실존 검증."""
    print(f"  [커리큘럼 생성] '{topic_name}' ({category}) ...")

    curriculum = None
    used_fallback = False
    for attempt in range(2):
        try:
            response = await claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": CURRICULUM_PROMPT.format(
                        topic_name=topic_name,
                        category=category,
                        topic_key=topic_key,
                    ),
                }],
            )
            raw = response.content[0].text.strip()
            raw = _extract_json(raw)
            curriculum = json.loads(raw)
            break
        except json.JSONDecodeError as e:
            if attempt == 0:
                print(f"  [커리큘럼 생성 재시도] JSON 파싱 오류: {e}")
            else:
                print(f"  [커리큘럼 생성 실패] JSON 파싱 불가 — 폴백 커리큘럼 사용")

    if curriculum is None:
        curriculum = _fallback_curriculum(topic_name, topic_key)
        used_fallback = True

    print(f"  [커리큘럼 생성 완료] {len(curriculum.get('chapters', []))}개 챕터")

    struct_issues = _validate_structure(curriculum)
    if struct_issues:
        print(f"  [구조 검증 이슈] {struct_issues}")

    if not used_fallback:
        validated_chapters = await _validate_concepts(topic_name, curriculum.get("chapters", []))
        curriculum["chapters"] = validated_chapters

    return curriculum


def _extract_json(text: str) -> str:
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text
