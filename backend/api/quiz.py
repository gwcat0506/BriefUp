from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.supabase import supabase
from datetime import date

router = APIRouter()

class QuizAnswer(BaseModel):
    user_id: str
    quiz_id: str
    content_id: str
    selected: str  # "1" | "2" | "3" | "4"

@router.get("/by-content/{content_id}")
async def get_quizzes_by_content(content_id: str):
    """특정 브리핑 콘텐츠의 퀴즈 반환"""
    res = supabase.table("quizzes").select("*").eq("content_id", content_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="이 콘텐츠의 퀴즈가 아직 없어요.")
    return res.data


@router.get("/today/{user_id}")
async def get_today_quizzes(user_id: str):
    """오늘의 퀴즈 2문제 반환"""
    # 유저 관심사 카테고리 가져오기
    topics = supabase.table("topics").select("category").eq("user_id", user_id).eq("is_active", True).execute()
    if not topics.data:
        raise HTTPException(status_code=404, detail="관심사 없음. 마이페이지에서 관심사를 설정해주세요.")

    categories = [t["category"] for t in topics.data]

    # 오늘 날짜 콘텐츠 가져오기
    today = date.today().isoformat()
    contents = supabase.table("contents").select("id").in_("topic_category", categories).eq("collected_at", today).execute()

    if not contents.data:
        raise HTTPException(status_code=404, detail="오늘의 콘텐츠가 아직 없어요.")

    content_ids = [c["id"] for c in contents.data]

    # 이미 푼 퀴즈 제외
    answered = supabase.table("quiz_results").select("quiz_id").eq("user_id", user_id).execute()
    answered_ids = [r["quiz_id"] for r in answered.data]

    # 퀴즈 2문제 가져오기
    quizzes_q = supabase.table("quizzes").select("*, contents(title, source)").in_("content_id", content_ids).limit(2)
    if answered_ids:
        quizzes_q = quizzes_q.not_.in_("id", answered_ids)

    quizzes = quizzes_q.execute()
    return quizzes.data

@router.post("/answer")
async def submit_answer(body: QuizAnswer):
    """퀴즈 답 제출 + 레벨 업데이트"""
    # 정답 확인
    quiz = supabase.table("quizzes").select("*").eq("id", body.quiz_id).single().execute()
    if not quiz.data:
        raise HTTPException(status_code=404, detail="퀴즈 없음")

    is_correct = quiz.data["answer"] == body.selected

    # 결과 저장
    supabase.table("quiz_results").insert({
        "user_id": body.user_id,
        "quiz_id": body.quiz_id,
        "content_id": body.content_id,
        "selected": body.selected,
        "is_correct": is_correct
    }).execute()

    # 개념 레벨 업데이트
    concept = quiz.data["concept"]
    category = quiz.data.get("category", "")
    _update_concept_level(body.user_id, concept, category, is_correct)

    # 스트릭 업데이트
    _update_streak(body.user_id)

    return {
        "is_correct": is_correct,
        "answer": quiz.data["answer"],
        "explanation": quiz.data["explanation"],
        "concept": concept
    }

def _update_concept_level(user_id: str, concept: str, category: str, is_correct: bool):
    existing = supabase.table("concept_levels").select("*").eq("user_id", user_id).eq("concept", concept).execute()

    if existing.data:
        row = existing.data[0]
        new_level = min(row["level"] + 5, 100) if is_correct else row["level"]
        supabase.table("concept_levels").update({
            "level": new_level,
            "total_attempts": row["total_attempts"] + 1,
            "correct_attempts": row["correct_attempts"] + (1 if is_correct else 0),
        }).eq("id", row["id"]).execute()
    else:
        supabase.table("concept_levels").insert({
            "user_id": user_id,
            "concept": concept,
            "category": category,
            "level": 5 if is_correct else 0,
            "total_attempts": 1,
            "correct_attempts": 1 if is_correct else 0,
        }).execute()

def _update_streak(user_id: str):
    from datetime import date
    today = date.today()
    existing = supabase.table("streaks").select("*").eq("user_id", user_id).execute()

    if existing.data:
        row = existing.data[0]
        last = row["last_active_date"]
        if str(last) == str(today):
            return  # 오늘 이미 업데이트

        from datetime import timedelta
        yesterday = (today - timedelta(days=1)).isoformat()
        if str(last) == yesterday:
            new_streak = row["current_streak"] + 1
        else:
            new_streak = 1  # 끊김

        supabase.table("streaks").update({
            "current_streak": new_streak,
            "longest_streak": max(new_streak, row["longest_streak"]),
            "last_active_date": today.isoformat()
        }).eq("user_id", user_id).execute()
    else:
        supabase.table("streaks").insert({
            "user_id": user_id,
            "current_streak": 1,
            "longest_streak": 1,
            "last_active_date": today.isoformat()
        }).execute()

@router.get("/history/{user_id}")
async def get_quiz_history(user_id: str, limit: int = 20):
    """퀴즈 기록"""
    res = supabase.table("quiz_results").select("*, quizzes(question, concept, explanation)").eq("user_id", user_id).order("answered_at", desc=True).limit(limit).execute()
    return res.data

@router.get("/levels/{user_id}")
async def get_concept_levels(user_id: str):
    """개념별 레벨"""
    res = supabase.table("concept_levels").select("*").eq("user_id", user_id).order("level", desc=True).execute()
    return res.data
