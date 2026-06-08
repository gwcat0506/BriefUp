"""
챕터 기반 학습 API
챕터 선택 → GPT가 설명 즉시 생성 → DB 캐시 → 퀴즈 생성
"""

import asyncio
import json
import os
from datetime import date

from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI

from core.supabase import supabase

router = APIRouter()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LEARN_PROMPT = """
당신은 {track} 분야 전문가입니다. 아래 챕터를 학습 카드 5장으로 만드세요.
독자가 읽고 나서 "이걸 알면 실제로 뭔가 달라지겠다"고 느껴야 합니다.

챕터: {chapter_title} ({level})
핵심 개념: {concepts}

## 카드 구성 및 기준

**카드 1 — hook (문제 제기)**
- 독자가 이미 겪었거나 곧 겪을 현실적인 문제 상황 제시
- "혹시 이런 상황 있지 않나요?" 수준이 아니라, 실제로 이 개념 없이 생기는 구체적 문제

**카드 2 — concept (핵심 원리)**
- 개념의 본질과 작동 원리를 설명 — 비유 OK, 하지만 비유만으로 끝내지 말 것
- "왜 이렇게 설계됐는지" 이유까지 포함

**카드 3 — example (실제 적용)**
- 현실 서비스/상황에서 이 개념이 어떻게 쓰이는지 구체적 사례
- 수치나 맥락 포함 권장 ("ChatGPT는 이 원리로 ~를 처리한다")

**카드 4 — pitfall (흔한 오해 또는 주의사항)**
- 이 개념을 처음 배울 때 많이 하는 오해 또는 실수
- "~라고 생각하기 쉽지만, 실제로는 ~이다" 형식

**카드 5 — summary (핵심 정리)**
- 기억해야 할 핵심 포인트 3가지 — 구체적이고 실용적으로

규칙:
- 각 카드 content는 3~5문장, 밀도 있게 작성
- 이모지 활용, 한국어 작성 (전문용어 영어 병기 가능)
- 뻔한 도입부 금지: "오늘은 ~에 대해 알아보겠습니다" 형식 금지

JSON 형식으로만 응답:
{{
  "chapter_title": "{chapter_title}",
  "cards": [
    {{
      "type": "hook",
      "emoji": "🤔",
      "title": "이런 문제, 겪어보셨나요?",
      "content": "이 개념 없이 생기는 현실적인 문제 상황"
    }},
    {{
      "type": "concept",
      "emoji": "💡",
      "title": "핵심 개념명 — 왜 이렇게 동작하는가",
      "content": "원리 + 왜 이렇게 설계됐는지 이유"
    }},
    {{
      "type": "example",
      "emoji": "🎯",
      "title": "실제로는 이렇게 씁니다",
      "content": "구체적 서비스/수치/맥락 포함 사례"
    }},
    {{
      "type": "pitfall",
      "emoji": "⚠️",
      "title": "이건 오해하기 쉬워요",
      "content": "흔한 오해 또는 주의사항 — ~라고 생각하기 쉽지만 실제로는 ~"
    }},
    {{
      "type": "summary",
      "emoji": "📌",
      "title": "기억할 것 3가지",
      "points": ["구체적 포인트 1", "구체적 포인트 2", "구체적 포인트 3"]
    }}
  ]
}}
"""

QUIZ_FROM_CHAPTER_PROMPT = """
다음 학습 내용을 바탕으로 난이도가 다른 퀴즈 3개를 만들어주세요.

[학습 내용]
{content}

## 난이도별 기준
- difficulty 1: 개념의 본질/존재 이유를 묻는 문제 (단순 정의 암기 ❌)
- difficulty 2: 두 개념 비교, 어떤 상황에서 무엇을 선택하는지
- difficulty 3: 실제 상황에서 트레이드오프 판단, 현업 수준 적용

## 공통 원칙
- 오답 보기는 그럴 듯하지만 틀린 것으로 (명백히 틀린 보기 ❌)
- 해설은 정답 이유 + 대표 오답 이유까지 포함
- 단순 "이름은?", "정의는?" 형식 금지

JSON 형식으로만 응답:
{{
  "quizzes": [
    {{
      "question": "개념 본질을 묻는 질문",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "1",
      "explanation": "정답 이유 + 핵심 오답 이유",
      "concept": "핵심개념",
      "difficulty": 1
    }},
    {{
      "question": "비교·선택 질문",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "2",
      "explanation": "정답 이유 + 핵심 오답 이유",
      "concept": "핵심개념2",
      "difficulty": 2
    }},
    {{
      "question": "실제 적용·트레이드오프 질문",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "3",
      "explanation": "정답 이유 + 왜 이 판단이 중요한지",
      "concept": "핵심개념3",
      "difficulty": 3
    }}
  ]
}}
"""


@router.get("/list")
async def get_all_chapters():
    """전체 챕터 목록 반환 (topic_curricula DB 기반)"""
    res = await asyncio.to_thread(
        lambda: supabase.table("topic_curricula").select("topic_key, topic_name, chapters").execute()
    )
    return {
        row["topic_key"]: {
            "title": row["topic_name"],
            "chapters": row.get("chapters") or [],
        }
        for row in (res.data or [])
    }


@router.get("/{chapter_id}")
async def get_chapter_content(chapter_id: str):
    """
    챕터 학습 콘텐츠 반환.
    DB에 캐시된 것 있으면 반환, 없으면 GPT로 즉시 생성.
    """
    # 캐시 확인
    cached = supabase.table("contents")\
        .select("*")\
        .eq("source", f"chapter:{chapter_id}")\
        .execute()

    if cached.data:
        row = cached.data[0]
        try:
            cards_data = json.loads(row["summary"])
        except Exception:
            cards_data = None
        return {"content": row, "cards": cards_data, "from_cache": True}

    # topic_curricula DB에서 챕터 메타데이터 찾기
    chapter_meta, topic_key, topic_name = await _find_chapter_from_db(chapter_id)
    if not chapter_meta:
        raise HTTPException(status_code=404, detail=f"챕터 {chapter_id}를 찾을 수 없어요.")

    # GPT로 학습 카드 즉시 생성
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": LEARN_PROMPT.format(
                track=topic_name,
                chapter_title=chapter_meta["title"],
                level=chapter_meta["level"],
                concepts=", ".join(chapter_meta.get("concepts", [])),
            )
        }]
    )
    raw = response.choices[0].message.content.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    cards_data = json.loads(raw)
    summary_json = json.dumps(cards_data, ensure_ascii=False)

    # DB 저장 (캐시)
    saved = supabase.table("contents").insert({
        "topic_category": topic_key.upper(),
        "source": f"chapter:{chapter_id}",
        "title": chapter_meta["title"],
        "original_url": "",
        "summary": summary_json,
        "collected_at": date.today().isoformat(),
    }).execute()

    content_id = saved.data[0]["id"]

    plain_text = " ".join(
        c.get("content", "") + " " + " ".join(c.get("points", []))
        for c in cards_data.get("cards", [])
    )
    await _generate_and_save_quizzes(plain_text, content_id)

    return {"content": saved.data[0], "cards": cards_data, "from_cache": False}


async def _generate_and_save_quizzes(explanation: str, content_id: str):
    """챕터 설명 기반 퀴즈 생성 + 저장"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": QUIZ_FROM_CHAPTER_PROMPT.format(content=explanation[:2000])
            }]
        )
        raw = response.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        data = json.loads(raw)
        for quiz in data.get("quizzes", []):
            supabase.table("quizzes").insert({
                "content_id": content_id,
                "question": quiz["question"],
                "options": quiz["options"],
                "answer": quiz["answer"],
                "explanation": quiz["explanation"],
                "concept": quiz["concept"],
                "difficulty": quiz.get("difficulty", 1),
            }).execute()
    except Exception as e:
        print(f"[퀴즈 생성 오류] {e}")


async def _find_chapter_from_db(chapter_id: str) -> tuple[dict | None, str, str]:
    """topic_curricula DB에서 chapter_id로 챕터 메타데이터 + topic_key + topic_name 반환"""
    res = await asyncio.to_thread(
        lambda: supabase.table("topic_curricula")
            .select("topic_key, topic_name, chapters")
            .execute()
    )
    for row in (res.data or []):
        for ch in (row.get("chapters") or []):
            if ch.get("id") == chapter_id:
                return ch, row["topic_key"], row["topic_name"]
    return None, "", ""
