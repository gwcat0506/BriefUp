from agent.collector import collect_for_category
from agent.summarizer import summarize_and_generate_quiz
from core.supabase import supabase
from datetime import date

# 지원하는 카테고리 목록
SUPPORTED_CATEGORIES = ["AI/ML", "철학", "경제", "심리학"]

async def run_daily_pipeline():
    """
    매일 새벽 5시 자동 실행
    1. 카테고리별 콘텐츠 수집
    2. Claude로 요약 + 퀴즈 생성
    3. Supabase에 저장
    """
    print(f"[파이프라인 시작] {date.today()}")

    # 오늘 유저들이 설정한 카테고리만 수집
    topics = supabase.table("topics").select("category").eq("is_active", True).execute()
    categories = list(set([t["category"] for t in topics.data]))

    if not categories:
        categories = ["AI/ML"]  # 기본값

    for category in categories:
        print(f"[수집 중] {category}")
        try:
            raw_contents = await collect_for_category(category)

            for raw in raw_contents[:3]:  # 카테고리당 최대 3개
                try:
                    result = await summarize_and_generate_quiz(
                        title=raw["title"],
                        raw_text=raw["raw_text"],
                        category=category
                    )

                    # 콘텐츠 저장
                    content_res = supabase.table("contents").insert({
                        "topic_category": category,
                        "source": raw["source"],
                        "title": raw["title"],
                        "original_url": raw["original_url"],
                        "summary": result["summary"],
                        "collected_at": date.today().isoformat()
                    }).execute()

                    content_id = content_res.data[0]["id"]

                    # 퀴즈 저장
                    for quiz in result["quizzes"]:
                        supabase.table("quizzes").insert({
                            "content_id": content_id,
                            "question": quiz["question"],
                            "options": quiz["options"],
                            "answer": quiz["answer"],
                            "explanation": quiz["explanation"],
                            "concept": quiz["concept"],
                            "difficulty": quiz.get("difficulty", 1)
                        }).execute()

                    print(f"  ✅ 저장 완료: {raw['title'][:40]}")

                except Exception as e:
                    print(f"  ❌ 요약/저장 오류: {e}")

        except Exception as e:
            print(f"[카테고리 오류] {category}: {e}")

    print(f"[파이프라인 완료] {date.today()}")
