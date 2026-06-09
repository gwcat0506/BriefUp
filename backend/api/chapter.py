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
당신은 {track} 분야의 현업 전문가입니다. 아래 챕터를 학습 카드 5장으로 만드세요.
독자 수준: 해당 분야를 처음 배우지만 논리적 사고 가능한 성인.
목표: 읽고 나서 "이 개념이 왜 필요한지, 실제로 어떻게 쓰이는지" 명확히 알 것.

챕터: {chapter_title} ({level})
다뤄야 할 개념: {concepts}

## 카드별 작성 기준 (엄격하게 따를 것)

**카드 1 — hook**
- 이 개념 없이 실제로 발생하는 구체적인 문제 상황을 묘사
- 상황, 원인, 결과를 포함해 "이 문제가 왜 중요한가"를 느끼게 할 것
- title은 이 챕터의 핵심 긴장감이나 질문을 담아 직접 작성 (고정 문구 ❌)
- "혹시 이런 경험 있나요?" 식의 막연한 질문 ❌

**카드 2 — concept**
- 핵심 원리를 단계적으로 설명 (A → B → C 흐름)
- "왜 이렇게 설계됐는가"의 이유까지 포함
- 비유를 쓰되, 비유 이후 반드시 실제 기술 원리로 연결
- 관련 개념 간 관계와 차이도 설명

**카드 3 — example**
- 실제 서비스(ChatGPT, Google, Netflix, Kakao 등)나 오픈소스 프로젝트에서 이 원리가 쓰이는 방식
- 어떤 문제를 해결했는지, 어떻게 적용했는지 구체적으로 서술
- 확인할 수 없는 통계 수치(%, 배율 등)는 절대 언급하지 말 것 — 사례의 맥락과 방식으로만 설명

**카드 4 — insight**
- 이 개념을 알면 어떤 판단이 달라지는가 — 전문가적 시각
- 흔한 오해와 실제 차이, 또는 트레이드오프
- "~라고 생각하기 쉽지만, 실제로는 ~이기 때문에 ~해야 한다" 형식

**카드 5 — summary**
- 핵심 포인트 3가지 — 각각 한 문장, 행동 가능하거나 기억에 남는 형태
- "~하면 ~이다" 또는 "~할 때 ~를 써야 한다" 형식 권장

공통 규칙:
- 각 카드 content는 3~4문장으로 압축 (모바일 가독성 우선)
- 문장 간 줄바꿈(\n)을 활용해 단락을 나눌 것
- 전문용어는 영어 병기 후 한국어 설명 병행
- "오늘은 ~에 대해 알아보겠습니다" 형식 절대 금지
- 이모지는 의미 있는 것만 사용
- 불확실한 정보는 "~로 알려져 있다", "~라고 보고된다" 형식으로 완화할 것

JSON 형식으로만 응답:
{{
  "chapter_title": "{chapter_title}",
  "cards": [
    {{
      "type": "hook",
      "emoji": "🤔",
      "title": "챕터 핵심 긴장감을 담은 제목 (직접 작성)",
      "content": "구체적 문제 상황 (3~4문장, \\n으로 단락 구분)"
    }},
    {{
      "type": "concept",
      "emoji": "💡",
      "title": "핵심 원리 — 왜 이렇게 동작하는가",
      "content": "단계적 원리 설명 + 설계 이유 (3~4문장, \\n으로 단락 구분)"
    }},
    {{
      "type": "example",
      "emoji": "🎯",
      "title": "실제로 이렇게 씁니다",
      "content": "구체적 사례 + 어떤 문제를 어떻게 해결했는지 (3~4문장, 수치 없이)"
    }},
    {{
      "type": "insight",
      "emoji": "⚡",
      "title": "전문가가 보는 핵심 포인트",
      "content": "오해 교정 + 트레이드오프 + 판단 기준 (3~4문장, \\n으로 단락 구분)"
    }},
    {{
      "type": "summary",
      "emoji": "📌",
      "title": "이것만 기억하세요",
      "points": ["행동 가능한 핵심 포인트 1", "행동 가능한 핵심 포인트 2", "행동 가능한 핵심 포인트 3"]
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
async def get_chapter_content(chapter_id: str, refresh: bool = False):
    """
    챕터 학습 콘텐츠 반환.
    DB에 캐시된 것 있으면 반환, 없으면 GPT로 즉시 생성.
    refresh=true 이면 캐시 무시하고 재생성.
    """
    # 캐시 확인
    cached = supabase.table("contents")\
        .select("*")\
        .eq("source", f"chapter:{chapter_id}")\
        .execute()

    if cached.data and not refresh:
        row = cached.data[0]
        try:
            cards_data = json.loads(row["summary"])
        except Exception:
            cards_data = None
        return {"content": row, "cards": cards_data, "from_cache": True}

    # refresh=True면 이전 캐시 + 연결된 퀴즈 삭제 (중복 방지)
    if cached.data and refresh:
        for old_row in cached.data:
            supabase.table("quizzes").delete().eq("content_id", old_row["id"]).execute()
            supabase.table("contents").delete().eq("id", old_row["id"]).execute()

    # topic_curricula DB에서 챕터 메타데이터 찾기
    chapter_meta, topic_key, topic_name = await _find_chapter_from_db(chapter_id)
    if not chapter_meta:
        raise HTTPException(status_code=404, detail=f"챕터 {chapter_id}를 찾을 수 없어요.")

    # GPT로 학습 카드 즉시 생성
    response = await client.chat.completions.create(
        model="gpt-5",
        max_completion_tokens=3000,
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
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": QUIZ_FROM_CHAPTER_PROMPT.format(content=explanation[:3000])
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


@router.delete("/cache/all")
async def clear_chapter_cache():
    """챕터 캐시 전체 삭제 — 프롬프트 변경 후 재생성용"""
    res = supabase.table("contents")\
        .delete()\
        .like("source", "chapter:%")\
        .execute()
    return {"deleted": len(res.data or [])}


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
