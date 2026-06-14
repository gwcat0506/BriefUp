"""
기존 파이프라인 수집 콘텐츠(plain text summary)를 카드 JSON 형식으로 변환.

실행:
  cd backend && source .venv/bin/activate
  python -m scripts.backfill_cards [--dry-run]
"""
import asyncio
import json
import sys
import os

from openai import AsyncOpenAI
from core.supabase import supabase
from core.config import GPT_4O_MINI_MODEL
from core.utils import extract_json

dry_run = "--dry-run" in sys.argv

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CONVERT_PROMPT = """아래 [기존 요약]은 한 글의 핵심을 정리한 텍스트입니다.
이를 4장의 학습 카드로 재구성하세요. 내용은 요약에 있는 것만 사용하고 추가하지 마세요.

[글 제목]
{title}

[기존 요약]
{summary}

JSON으로만 응답:
{{
  "cards": [
    {{"type": "hook", "emoji": "🔍", "title": "핵심 발견 제목", "content": "2~3문장 (\\n으로 단락 구분)"}},
    {{"type": "insight", "emoji": "💡", "title": "왜 이게 중요한가", "content": "2~3문장 (\\n으로 단락 구분)"}},
    {{"type": "example", "emoji": "🎯", "title": "이렇게 씁니다", "content": "1~2문장"}},
    {{"type": "summary", "emoji": "📌", "title": "이것만 기억하세요", "points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"]}}
  ]
}}"""


async def convert_one(row: dict) -> dict | None:
    """기존 plain text summary → cards JSON. 실패 시 None 반환."""
    try:
        response = await client.chat.completions.create(
            model=GPT_4O_MINI_MODEL,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": CONVERT_PROMPT.format(
                    title=row["title"],
                    summary=row["summary"][:3000],
                ),
            }],
        )
        raw = response.choices[0].message.content.strip()
        parsed = extract_json(raw)
        if parsed and isinstance(parsed.get("cards"), list) and len(parsed["cards"]) > 0:
            return parsed
        return None
    except Exception as e:
        print(f"  [오류] {row['id'][:8]}… : {e}")
        return None


async def main():
    res = supabase.table("contents").select("id, title, summary, source").execute()
    rows = [r for r in (res.data or []) if not (r.get("source") or "").startswith("chapter:")]

    # 이미 카드 형식인 것 제외
    to_convert = []
    for r in rows:
        try:
            parsed = json.loads(r["summary"])
            if isinstance(parsed.get("cards"), list):
                continue
        except Exception:
            pass
        to_convert.append(r)

    print(f"변환 대상: {len(to_convert)}개 (전체 파이프라인 콘텐츠: {len(rows)}개)")
    if dry_run:
        print("[dry-run] 실제 변환 없이 종료")
        return

    ok = 0
    fail = 0
    for i, row in enumerate(to_convert, 1):
        print(f"  [{i}/{len(to_convert)}] {row['title'][:50]}...")
        cards_data = await convert_one(row)
        if cards_data:
            supabase.table("contents").update({
                "summary": json.dumps(cards_data, ensure_ascii=False)
            }).eq("id", row["id"]).execute()
            ok += 1
            print(f"    ✅ 변환 완료")
        else:
            fail += 1
            print(f"    ❌ 변환 실패 (원본 유지)")
        await asyncio.sleep(0.3)  # rate limit 여유

    print(f"\n완료: 성공 {ok}개 / 실패 {fail}개")


if __name__ == "__main__":
    asyncio.run(main())
