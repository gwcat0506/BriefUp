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
아래 [원문]을 읽고, 독자가 "이걸 알면 실제로 뭐가 달라지는지" 느낄 수 있는 학습 카드 4장을 만드세요.

[원문 제목]
{title}

[원문 내용]
{text}

## 카드 작성 기준

**카드 1 — hook (핵심 발견)**
- 이 글이 말하는 가장 중요한 한 가지 — 독자가 "오, 이거 몰랐다"할 것
- title: 핵심 긴장감이나 질문 (고정 문구 ❌, 직접 작성)
- content: 2~3문장, 원문에 있는 내용만

**카드 2 — insight (왜 중요한가)**
- 기존 방식과 무엇이 다른지, 어떤 문제를 해결하는지
- title: "~이기 때문에 ~해야 한다" 형식 권장
- content: 2~3문장

**카드 3 — example (실제 적용)**
- 현실에서 어디에 쓰이는지 구체적 사례
- title: 구체적인 적용 상황
- content: 1~2문장

**카드 4 — summary (핵심 정리)**
- 기억해야 할 핵심 포인트 3가지 — 각 한 문장
- "~하면 ~이다" 또는 "~할 때 ~를 써야 한다" 형식 권장

공통 규칙:
- 원문에 없는 내용 추가 금지
- 전문용어는 영어 그대로 (RAG, LLM 등)
- 한국어로 작성
- "이 글은 ~을 다룹니다" 시작 금지

JSON으로만 응답:
{{
  "cards": [
    {{"type": "hook", "emoji": "🔍", "title": "핵심 발견 제목", "content": "2~3문장 (\\n으로 단락 구분)"}},
    {{"type": "insight", "emoji": "💡", "title": "왜 이게 중요한가", "content": "2~3문장 (\\n으로 단락 구분)"}},
    {{"type": "example", "emoji": "🎯", "title": "이렇게 씁니다", "content": "1~2문장"}},
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
