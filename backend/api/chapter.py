"""
챕터 기반 학습 API
챕터 선택 → GPT가 설명 즉시 생성 → DB 캐시 → 퀴즈 생성
"""

from fastapi import APIRouter, HTTPException
from openai import AsyncOpenAI
from core.supabase import supabase
from datetime import date
import os
import json

router = APIRouter()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from agent.curriculum_catalog import CHAPTERS

LEARN_PROMPT = """
당신은 {track} 분야를 처음 배우는 사람에게 설명하는 재미있는 선생님입니다.

챕터: {chapter_title} ({level})
핵심 개념: {concepts}

아래 JSON 형식으로 학습 카드 5장을 만들어주세요.
각 카드는 짧고 (3~5문장), 재미있고, 쉬워야 합니다.

카드 구성:
1. hook: 공감 질문이나 흥미로운 상황으로 시작 ("혹시 이런 경험 있나요?")
2. concept: 핵심 개념을 일상 비유로 설명 (도서관, 넷플릭스, 카카오 등 친숙한 예시)
3. example: 실제 서비스/제품에서 어떻게 쓰이는지 구체적 사례
4. insight: "와, 그렇구나!" 하는 핵심 인사이트 1가지
5. summary: 3가지 핵심 포인트 (짧게, 기억하기 쉽게)

규칙:
- 전문용어 최소화, 꼭 써야 하면 괄호로 설명
- 각 카드는 독립적으로 읽혀야 함
- 이모지 적극 활용
- 한국어로 작성

JSON 형식으로만 응답:
{{
  "chapter_title": "{chapter_title}",
  "cards": [
    {{
      "type": "hook",
      "emoji": "🤔",
      "title": "이런 경험 있나요?",
      "content": "공감 가는 상황이나 질문"
    }},
    {{
      "type": "concept",
      "emoji": "💡",
      "title": "핵심 개념명",
      "content": "일상 비유로 쉽게 설명"
    }},
    {{
      "type": "example",
      "emoji": "🎯",
      "title": "실제로는 이렇게 써요",
      "content": "넷플릭스/카카오/유튜브 같은 실제 사례"
    }},
    {{
      "type": "insight",
      "emoji": "✨",
      "title": "이게 핵심이에요",
      "content": "가장 중요한 인사이트 1가지"
    }},
    {{
      "type": "summary",
      "emoji": "📌",
      "title": "오늘 배운 것",
      "points": ["포인트 1", "포인트 2", "포인트 3"]
    }}
  ]
}}
"""

QUIZ_FROM_CHAPTER_PROMPT = """
다음 학습 내용을 바탕으로 이해도 확인 퀴즈 2개를 만들어주세요.

[학습 내용]
{content}

퀴즈 원칙:
- 외우는 문제 ❌ → 이해 확인 문제 ✅
- 일상적 비유 사용 ("마치 ~처럼")
- 짧고 명확한 질문 (2줄 이내)
- 쉬운 말로 해설

JSON 형식으로만 응답:
{{
  "quizzes": [
    {{
      "question": "질문",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "1",
      "explanation": "왜 정답인지 쉽게 설명",
      "concept": "핵심개념",
      "difficulty": 1
    }},
    {{
      "question": "질문2",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "2",
      "explanation": "왜 정답인지 쉽게 설명",
      "concept": "핵심개념2",
      "difficulty": 2
    }}
  ]
}}
"""


@router.get("/list")
async def get_all_chapters():
    """전체 챕터 목록 반환"""
    return CHAPTERS


@router.get("/{chapter_id}")
async def get_chapter_content(chapter_id: str):
    """
    챕터 학습 콘텐츠 반환
    DB에 캐시된 것 있으면 반환, 없으면 GPT로 즉시 생성
    """
    # 캐시 확인 (오늘 날짜 기준)
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

    # 챕터 메타데이터 찾기
    chapter_meta = _find_chapter(chapter_id)
    if not chapter_meta:
        raise HTTPException(status_code=404, detail=f"챕터 {chapter_id}를 찾을 수 없어요.")

    # GPT로 설명 즉시 생성
    track_key = chapter_id.split("-")[0]
    track_title = CHAPTERS.get(track_key, {}).get("title", "")

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": LEARN_PROMPT.format(
                track=track_title,
                chapter_title=chapter_meta["title"],
                level=chapter_meta["level"],
                concepts=", ".join(chapter_meta["concepts"])
            )
        }]
    )
    raw = response.choices[0].message.content.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    cards_data = json.loads(raw)
    # summary 필드엔 JSON 문자열로 저장 (카드 데이터)
    summary_json = json.dumps(cards_data, ensure_ascii=False)

    # DB에 저장 (캐시)
    saved = supabase.table("contents").insert({
        "topic_category": track_key.upper(),
        "source": f"chapter:{chapter_id}",
        "title": chapter_meta["title"],
        "original_url": "",
        "summary": summary_json,
        "collected_at": date.today().isoformat(),
    }).execute()

    content_id = saved.data[0]["id"]

    # 퀴즈 생성 — 카드 내용 기반
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


def _find_chapter(chapter_id: str) -> dict | None:
    """chapter_id로 챕터 메타데이터 찾기"""
    for track in CHAPTERS.values():
        for ch in track["chapters"]:
            if ch["id"] == chapter_id:
                return ch
    return None
