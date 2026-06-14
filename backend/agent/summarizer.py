"""
STEP 2 — 요약 생성
소스 본문 기반으로만 생성 → 할루시네이션 최소화
GPT-4o-mini 사용. 4장 학습 카드 JSON 반환.
"""

import json
import re

from openai import AsyncOpenAI
import os
from core.config import GPT_4O_MINI_MODEL
from core.utils import extract_json

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SUMMARY_PROMPT = """당신은 {category} 분야 전문가입니다.
아래 [원문]을 읽고 학습 카드 4장을 만드세요.
모든 카드는 [원문]에 명시된 내용만 사용하세요. 추론·응용 사례·외부 지식 추가 금지.

[원문 제목]
{title}

[원문 내용]
{text}

## 카드별 작성 기준 (원문 범위 내에서만)

**카드 1 — hook (핵심 주장)**
- 이 글이 말하는 가장 중요한 발견/주장/결과 — 원문에 직접 서술된 것
- title: 핵심 주장을 담은 제목 (직접 작성, 고정 문구 ❌)
- content: 1~2문장

**카드 2 — insight (의의)**
- 원문이 설명하는 기존 방법과의 차이점, 또는 이 접근의 장점/한계
- title: "~이기 때문에 ~가 달라진다" 형식 권장
- content: 1~2문장, 원문 근거 있는 것만

**카드 3 — detail (핵심 근거)**
- 원문이 주장을 뒷받침하기 위해 제시한 방법론·실험 결과·수치·기법 이름
- 원문에 없는 응용 분야나 사례 금지 — 원문에 있는 구체적 내용만
- title: "어떻게 작동하는가" 또는 핵심 기법명
- content: 1~2문장

**카드 4 — summary (핵심 정리)**
- 원문에서 직접 도출 가능한 핵심 포인트 3가지 — 각 한 문장
- "~하면 ~이다" 형식 권장

공통 규칙:
- 전문용어는 영어 그대로 (RAG, LLM, HyDE 등)
- 한국어 작성
- 원문에서 근거 찾을 수 없으면 그 내용은 쓰지 말 것

JSON으로만 응답:
{{
  "cards": [
    {{"type": "hook", "emoji": "🔍", "title": "핵심 주장 제목", "content": "1~2문장"}},
    {{"type": "insight", "emoji": "💡", "title": "무엇이 달라지는가", "content": "1~2문장"}},
    {{"type": "detail", "emoji": "⚙️", "title": "어떻게 작동하는가", "content": "1~2문장"}},
    {{"type": "summary", "emoji": "📌", "title": "이것만 기억하세요", "points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"]}}
  ]
}}"""


def _cards_to_text(cards_data: dict) -> str:
    """충실도 검증용: cards JSON → 평문 텍스트로 변환"""
    parts = []
    for card in cards_data.get("cards", []):
        parts.append(card.get("title", ""))
        if card.get("content"):
            parts.append(card["content"])
        if card.get("points"):
            parts.extend(card["points"])
    return "\n".join(p for p in parts if p)


async def summarize(title: str, text: str, category: str) -> tuple[str, dict]:
    """소스 기반 카드 JSON 생성. (JSON 문자열, {input, output} 토큰) 반환"""
    response = await client.chat.completions.create(
        model=GPT_4O_MINI_MODEL,
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": SUMMARY_PROMPT.format(
                category=category,
                title=title,
                text=text[:6000],
            )
        }]
    )
    usage = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}
    raw = response.choices[0].message.content.strip()
    return raw, usage


def parse_cards(raw: str) -> dict | None:
    """GPT 응답에서 cards JSON 파싱. 실패 시 None 반환."""
    parsed = extract_json(raw)
    if parsed and isinstance(parsed.get("cards"), list) and len(parsed["cards"]) > 0:
        return parsed
    return None
