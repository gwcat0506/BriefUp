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
    res = supabase.table("quizzes").select("*, contents(title, source, original_url)").eq("content_id", content_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="이 콘텐츠의 퀴즈가 아직 없어요.")
    return res.data


@router.get("/review/{user_id}")
async def get_review_quizzes(user_id: str):
    """
    틀린 개념 자동 재출제 (말해보카 핵심 기능)
    오답 개념 중 아직 마스터 안 된 것 우선 출제
    """
    # 틀린 개념 찾기 (정답률 50% 미만)
    weak = supabase.table("concept_levels")\
        .select("concept, level, total_attempts, correct_attempts")\
        .eq("user_id", user_id)\
        .lt("level", 50)\
        .gt("total_attempts", 0)\
        .order("level")\
        .limit(5)\
        .execute()

    if not weak.data:
        return []

    weak_concepts = [row["concept"] for row in weak.data]

    # 해당 개념의 퀴즈 가져오기 (오늘 이미 푼 것 제외)
    answered_today = supabase.table("quiz_results")\
        .select("quiz_id")\
        .eq("user_id", user_id)\
        .gte("answered_at", date.today().isoformat())\
        .execute()
    answered_ids = [r["quiz_id"] for r in answered_today.data]

    quizzes_q = supabase.table("quizzes")\
        .select("*, contents(title, source, original_url)")\
        .in_("concept", weak_concepts)\
        .limit(5)

    if answered_ids:
        quizzes_q = quizzes_q.not_.in_("id", answered_ids)

    quizzes = quizzes_q.execute()

    # 복습 퀴즈임을 표시
    for q in quizzes.data:
        q["is_review"] = True
        q["review_reason"] = f"'{q['concept']}' 개념을 다시 연습해봐요 💪"

    return quizzes.data


@router.get("/today/{user_id}")
async def get_today_quizzes(user_id: str):
    """오늘의 퀴즈 반환 (토픽당 2문제, 최대 10문제)"""
    # 유저 관심사 토픽명 가져오기 (contents.topic_category = topic_name으로 저장됨)
    topics = supabase.table("topics").select("name").eq("user_id", user_id).eq("is_active", True).execute()
    if not topics.data:
        raise HTTPException(status_code=404, detail="관심사 없음. 마이페이지에서 관심사를 설정해주세요.")

    topic_names = [t["name"] for t in topics.data]

    # 오늘 날짜 콘텐츠 가져오기
    today = date.today().isoformat()
    contents = supabase.table("contents").select("id").in_("topic_category", topic_names).eq("collected_at", today).execute()

    if not contents.data:
        raise HTTPException(status_code=404, detail="오늘의 콘텐츠가 아직 없어요.")

    content_ids = [c["id"] for c in contents.data]

    # 이미 푼 퀴즈 제외
    answered = supabase.table("quiz_results").select("quiz_id").eq("user_id", user_id).execute()
    answered_ids = [r["quiz_id"] for r in answered.data]

    # 토픽별 2문제씩, 최대 10문제 (난이도 균형: difficulty 오름차순)
    import random
    result = []
    seen_content_ids: set = set()
    for topic in topic_names:
        topic_contents = supabase.table("contents").select("id").eq("topic_category", topic).eq("collected_at", today).execute()
        topic_content_ids = [c["id"] for c in topic_contents.data]
        if not topic_content_ids:
            continue
        q = supabase.table("quizzes").select("*, contents(title, source, original_url)") \
            .in_("content_id", topic_content_ids) \
            .order("difficulty") \
            .limit(2)
        if answered_ids:
            q = q.not_.in_("id", answered_ids)
        rows = q.execute().data
        result.extend(rows)
        if len(result) >= 10:
            break

    random.shuffle(result)
    return result[:10]

@router.post("/answer")
async def submit_answer(body: QuizAnswer):
    """퀴즈 답 제출 + 레벨 업데이트"""
    # 정답 확인 (contents 조인으로 topic_category 가져오기)
    quiz = supabase.table("quizzes").select("*, contents(topic_category)").eq("id", body.quiz_id).single().execute()
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
    category = (quiz.data.get("contents") or {}).get("topic_category", "")
    _update_concept_level(body.user_id, concept, category, is_correct)

    # 스트릭 업데이트
    _update_streak(body.user_id)

    # XP 지급 (정답 시)
    xp_data = None
    if is_correct:
        from api.user import add_xp, XP_QUIZ_CORRECT
        try:
            xp_data = add_xp(body.user_id, XP_QUIZ_CORRECT)
        except Exception as e:
            print(f"[XP 오류] {e}")

    return {
        "is_correct": is_correct,
        "answer": quiz.data["answer"],
        "explanation": quiz.data["explanation"],
        "concept": concept,
        "xp_gained": (xp_data["xp_gained"] if xp_data else 0),
        "xp_info": xp_data,
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
        try:
            from api.user import add_xp, XP_STREAK_DAY
            add_xp(user_id, XP_STREAK_DAY)
        except Exception:
            pass
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
