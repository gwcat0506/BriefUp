import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from datetime import date
from openai import AsyncOpenAI
from core.supabase import supabase
from agent.curriculum_catalog import CURRICULUM_CATALOG

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT = """당신은 심리학 분야의 현업 전문가입니다. 아래 챕터를 학습 카드 5장으로 만드세요.
챕터: {title} ({level})
개념: {concepts}

JSON으로만 응답:
{{"chapter_title": "{title}", "cards": [
  {{"type": "hook", "emoji": "🤔", "title": "제목", "content": "3~4문장"}},
  {{"type": "concept", "emoji": "💡", "title": "핵심 원리", "content": "3~4문장"}},
  {{"type": "example", "emoji": "🎯", "title": "실제 사례", "content": "3~4문장"}},
  {{"type": "insight", "emoji": "⚡", "title": "전문가 시각", "content": "3~4문장"}},
  {{"type": "summary", "emoji": "📌", "title": "이것만 기억하세요", "points": ["핵심1","핵심2","핵심3"]}}
]}}"""

QUIZ_PROMPT = """다음 학습 내용 기반 퀴즈 3개 (난이도 1~3):
{content}

JSON:
{{"quizzes": [
  {{"question":"개념질문","options":{{"1":"a","2":"b","3":"c","4":"d"}},"answer":"1","explanation":"해설","concept":"개념","difficulty":1}},
  {{"question":"비교질문","options":{{"1":"a","2":"b","3":"c","4":"d"}},"answer":"2","explanation":"해설","concept":"개념2","difficulty":2}},
  {{"question":"적용질문","options":{{"1":"a","2":"b","3":"c","4":"d"}},"answer":"3","explanation":"해설","concept":"개념3","difficulty":3}}
]}}"""

def extract_json(raw):
    if "```json" in raw:
        return raw.split("```json")[1].split("```")[0].strip()
    if "```" in raw:
        return raw.split("```")[1].split("```")[0].strip()
    return raw

async def main():
    ch = CURRICULUM_CATALOG["psych"]["chapters"][2]
    print(f"생성: {ch['id']} — {ch['title']}")

    resp = await client.chat.completions.create(
        model="gpt-5",
        max_completion_tokens=3000,
        messages=[{"role": "user", "content": PROMPT.format(
            title=ch["title"], level=ch["level"],
            concepts=", ".join(ch.get("concepts", []))
        )}]
    )
    raw = extract_json(resp.choices[0].message.content.strip())
    cards_data = json.loads(raw)

    saved = supabase.table("contents").insert({
        "topic_category": "PSYCH",
        "source": "chapter:psych-3",
        "title": ch["title"],
        "original_url": "",
        "summary": json.dumps(cards_data, ensure_ascii=False),
        "collected_at": date.today().isoformat(),
    }).execute()
    content_id = saved.data[0]["id"]

    plain = " ".join(
        c.get("content", "") + " " + " ".join(c.get("points", []))
        for c in cards_data.get("cards", [])
    )
    qresp = await client.chat.completions.create(
        model="gpt-4o-mini", max_tokens=1500,
        messages=[{"role": "user", "content": QUIZ_PROMPT.format(content=plain[:2000])}]
    )
    qraw = extract_json(qresp.choices[0].message.content.strip())
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
    print(f"✓ psych-3 완료 (퀴즈 {len(qdata.get('quizzes', []))}개)")

asyncio.run(main())
