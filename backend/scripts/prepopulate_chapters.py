"""
5개 사전 선택 토픽의 첫 3챕터를 미리 생성해 DB에 캐시.
챕터 내용(학습 카드) + 퀴즈 3개 세트가 DB에 저장되면 이후 즉시 반환.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from openai import AsyncOpenAI
from core.supabase import supabase
from agent.curriculum_catalog import CURRICULUM_CATALOG

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LEARN_PROMPT = """
당신은 {track} 분야의 현업 전문가입니다. 아래 챕터를 학습 카드 5장으로 만드세요.
독자 수준: 해당 분야를 처음 배우지만 논리적 사고 가능한 성인.
목표: 읽고 나서 "이 개념이 왜 필요한지, 실제로 어떻게 쓰이는지" 명확히 알 것.

챕터: {chapter_title} ({level})
다뤄야 할 개념: {concepts}

JSON 형식으로만 응답:
{{
  "chapter_title": "{chapter_title}",
  "cards": [
    {{"type": "hook", "emoji": "🤔", "title": "핵심 긴장감 제목", "content": "구체적 문제 (3~4문장)"}},
    {{"type": "concept", "emoji": "💡", "title": "핵심 원리", "content": "단계적 원리 + 이유 (3~4문장)"}},
    {{"type": "example", "emoji": "🎯", "title": "실제로 이렇게 씁니다", "content": "실제 사례 (3~4문장)"}},
    {{"type": "insight", "emoji": "⚡", "title": "전문가가 보는 핵심", "content": "오해 + 트레이드오프 (3~4문장)"}},
    {{"type": "summary", "emoji": "📌", "title": "이것만 기억하세요", "points": ["핵심1", "핵심2", "핵심3"]}}
  ]
}}
"""

QUIZ_PROMPT = """
학습 내용 기반 퀴즈 3개 (난이도 1~3):

[학습 내용]
{content}

JSON:
{{
  "quizzes": [
    {{"question": "개념 본질 질문", "options": {{"1":"보기1","2":"보기2","3":"보기3","4":"보기4"}}, "answer": "1", "explanation": "해설", "concept": "개념명", "difficulty": 1}},
    {{"question": "비교 선택 질문", "options": {{"1":"보기1","2":"보기2","3":"보기3","4":"보기4"}}, "answer": "2", "explanation": "해설", "concept": "개념명2", "difficulty": 2}},
    {{"question": "실제 적용 질문", "options": {{"1":"보기1","2":"보기2","3":"보기3","4":"보기4"}}, "answer": "3", "explanation": "해설", "concept": "개념명3", "difficulty": 3}}
  ]
}}
"""


def get_cached_ids():
    res = supabase.table("contents").select("source").like("source", "chapter:%").execute()
    return set(r["source"].replace("chapter:", "") for r in res.data)


async def generate_chapter(chapter_id: str, chapter_meta: dict, topic_key: str, topic_name: str):
    print(f"  생성 중: {chapter_id} — {chapter_meta['title']}")
    try:
        resp = await client.chat.completions.create(
            model="gpt-5",
            max_completion_tokens=3000,
            messages=[{"role": "user", "content": LEARN_PROMPT.format(
                track=topic_name,
                chapter_title=chapter_meta["title"],
                level=chapter_meta["level"],
                concepts=", ".join(chapter_meta.get("concepts", [])),
            )}]
        )
        raw = resp.choices[0].message.content.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        cards_data = json.loads(raw)
        summary_json = json.dumps(cards_data, ensure_ascii=False)

        from datetime import date
        saved = supabase.table("contents").insert({
            "topic_category": topic_key.upper(),
            "source": f"chapter:{chapter_id}",
            "title": chapter_meta["title"],
            "original_url": "",
            "summary": summary_json,
            "collected_at": date.today().isoformat(),
        }).execute()
        content_id = saved.data[0]["id"]

        # 퀴즈 생성
        plain = " ".join(
            c.get("content", "") + " " + " ".join(c.get("points", []))
            for c in cards_data.get("cards", [])
        )
        qresp = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            messages=[{"role": "user", "content": QUIZ_PROMPT.format(content=plain[:2000])}]
        )
        qraw = qresp.choices[0].message.content.strip()
        if "```json" in qraw:
            qraw = qraw.split("```json")[1].split("```")[0].strip()
        elif "```" in qraw:
            qraw = qraw.split("```")[1].split("```")[0].strip()

        qdata = json.loads(qraw)
        for quiz in qdata.get("quizzes", []):
            supabase.table("quizzes").insert({
                "content_id": content_id,
                "question": quiz["question"],
                "options": quiz["options"],
                "answer": quiz["answer"],
                "explanation": quiz["explanation"],
                "concept": quiz["concept"],
                "difficulty": quiz.get("difficulty", 1),
            }).execute()

        print(f"  ✓ {chapter_id} 완료 (퀴즈 {len(qdata.get('quizzes', []))}개)")
    except Exception as e:
        print(f"  ✗ {chapter_id} 실패: {e}")


async def main():
    TARGET_TOPICS = ["agent", "rag", "llm", "invest", "psych"]
    CHAPTERS_PER_TOPIC = 3

    cached = get_cached_ids()
    print(f"이미 캐시된 챕터: {len(cached)}개")

    tasks = []
    for topic_key in TARGET_TOPICS:
        catalog = CURRICULUM_CATALOG[topic_key]
        topic_name = catalog["title"]
        chapters = catalog["chapters"][:CHAPTERS_PER_TOPIC]
        print(f"\n[{topic_name}]")
        for ch in chapters:
            ch_id = ch["id"]
            if ch_id in cached:
                print(f"  스킵 (캐시됨): {ch_id}")
            else:
                tasks.append(generate_chapter(ch_id, ch, topic_key, topic_name))

    if not tasks:
        print("\n모든 챕터가 이미 캐시되어 있습니다!")
        return

    print(f"\n총 {len(tasks)}개 챕터 생성 시작...")
    # 동시 3개씩 처리 (API 부하 제한)
    for i in range(0, len(tasks), 3):
        batch = tasks[i:i+3]
        await asyncio.gather(*batch)

    print("\n사전 생성 완료!")


if __name__ == "__main__":
    asyncio.run(main())
