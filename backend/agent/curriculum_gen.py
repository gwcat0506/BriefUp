"""
관심사 추가 시 Claude가 커리큘럼 자동 생성
- 챕터 구조 (기초 → 중급 → 심화) + 챕터별 검색 힌트(arxiv_query, web_query) 포함
- topic_curricula DB에 캐시: 동일 토픽은 재생성 없이 DB에서 조회
"""

import asyncio
import json
import os
import re

import anthropic
from core.supabase import supabase

claude = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CURRICULUM_PROMPT = """당신은 "{topic_name}"({category}) 분야의 전문 커리큘럼 설계자입니다.

이 분야를 체계적으로 학습할 수 있도록 8~10개의 챕터로 구성된 심층 커리큘럼을 만들어주세요.

설계 원칙:
- 챕터 제목: 독자가 진짜 궁금해할 질문 또는 핵심 긴장감을 담은 제목 (예: "Bi-Encoder vs Cross-Encoder: 언제 어떤 걸 써야 할까?")
- 진행 구조: Naive 개념 이해 → 핵심 기법 심화 → 최신 연구/응용 (3단계 흐름)
- concepts: 챕터에서 다룰 구체적인 기법·논문명·알고리즘명 3~5개 (막연한 단어 금지, 예: "HyDE" ✓, "고급 기법" ✗)
- search_hints: 아티클 수집용 영문 검색 쿼리
  - arxiv_query: 학술 논문이 있는 분야면 "기법명 저자 연도" 형식 포함, 없으면 null
  - web_query: 챕터 핵심 기법을 설명하는 영문 웹 검색 쿼리 (최신 연도 포함 권장)

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
      "description": "이 챕터에서 배울 구체적인 내용 (1문장, 기법명 포함)",
      "level": "입문",
      "duration": "7분",
      "concepts": ["구체적기법1", "논문명또는알고리즘", "핵심개념3", "실용적도구4"],
      "search_hints": {{
        "arxiv_query": "기법명 저자 연도 키워드 또는 null",
        "web_query": "챕터 핵심기법 영문 웹검색 쿼리 2024"
      }}
    }}
  ]
}}
"""


def _slugify(name: str) -> str:
    """토픽명 → URL-safe slug. 한글은 유니코드 그대로 유지."""
    slug = name.lower().strip()
    slug = re.sub(r"[\s/,]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


async def get_or_create_curriculum(topic_name: str, category: str) -> dict:
    """
    topic_name에 대한 커리큘럼을 반환.
    DB에 있으면 즉시 반환, 없으면 Claude로 생성 후 저장.
    """
    topic_key = _slugify(topic_name)

    # 1. DB 캐시 확인
    existing = await asyncio.to_thread(
        lambda: supabase.table("topic_curricula")
            .select("*")
            .eq("topic_key", topic_key)
            .execute()
    )
    if existing.data:
        return existing.data[0]

    # 2. alias로도 검색 (예: "주식" → "주식/투자" 커리큘럼)
    alias_match = await asyncio.to_thread(
        lambda: supabase.table("topic_curricula")
            .select("*")
            .contains("topic_aliases", [topic_name])
            .execute()
    )
    if alias_match.data:
        return alias_match.data[0]

    # 3. Claude로 신규 생성
    curriculum = await _generate_curriculum(topic_name, category, topic_key)

    # 4. DB 저장
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


async def _generate_curriculum(topic_name: str, category: str, topic_key: str) -> dict:
    """Claude API로 커리큘럼 생성."""
    print(f"  [커리큘럼 생성] '{topic_name}' ({category}) ...")

    response = await claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
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
    data = json.loads(raw)
    print(f"  [커리큘럼 생성 완료] {len(data.get('chapters', []))}개 챕터")
    return data


def _extract_json(text: str) -> str:
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text
