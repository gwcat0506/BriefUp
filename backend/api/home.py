"""
홈 화면 집계 엔드포인트 — 7개 쿼리를 병렬로 처리해 단 1회 왕복으로 반환
"""
import asyncio
from fastapi import APIRouter
from core.supabase import supabase
from datetime import date, timedelta

router = APIRouter()


# ── 동기 DB 헬퍼 (asyncio.to_thread 로 병렬 실행) ───────────────

def _q_streak_and_status(user_id: str):
    from api.user import MILESTONES
    res = supabase.table("streaks").select("*").eq("user_id", user_id).execute()
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if not res.data:
        streak = {
            "current_streak": 0, "longest_streak": 0, "freeze_available": 1,
            "milestone": None, "next_milestone": 7, "days_to_next": 7,
        }
        status = {"status": "new", "message": "오늘 첫 학습을 시작해봐요! 🌱"}
        return streak, status

    row = res.data[0]
    current = row.get("current_streak", 0)
    last = row.get("last_active_date")
    freeze = row.get("freeze_available", 0)

    milestone = None
    for days, info in sorted(MILESTONES.items()):
        if current == days:
            milestone = {"days": days, **info}
            break
    next_ms = next((d for d in sorted(MILESTONES.keys()) if d > current), None)
    next_ms_reward = MILESTONES[next_ms]["reward"] if next_ms else None
    streak = {**row, "milestone": milestone, "next_milestone": next_ms,
              "days_to_next": (next_ms - current) if next_ms else None,
              "next_milestone_reward": next_ms_reward}

    if str(last) == today:
        status = {"status": "done", "message": f"오늘 학습 완료! 🔥 {current}일 연속", "current_streak": current}
    elif str(last) == yesterday:
        status = {"status": "pending", "message": f"오늘 아직 학습 안 했어요! 🔥 {current}일 스트릭 위험",
                  "current_streak": current, "freeze_available": freeze}
    elif freeze > 0 and current > 0:
        status = {"status": "freezeable", "message": f"스트릭이 끊길 위기! 프리즈 사용할까요? ({freeze}개 남음)",
                  "current_streak": current, "freeze_available": freeze}
    else:
        status = {"status": "broken", "message": "스트릭이 끊겼어요. 오늘부터 다시 시작! 💪", "current_streak": 0}

    return streak, status


def _q_xp(user_id: str):
    from api.user import get_xp_info
    res = supabase.table("users").select("xp").eq("id", user_id).execute()
    total_xp = (res.data[0] if res.data else {}).get("xp") or 0
    return get_xp_info(total_xp)


def _q_levels(user_id: str):
    res = supabase.table("concept_levels").select("*").eq("user_id", user_id).order("level", desc=True).execute()
    return res.data or []


async def _q_contents(user_id: str):
    today = date.today().isoformat()
    topics_res = await asyncio.to_thread(
        lambda: supabase.table("topics").select("name, category")
            .eq("user_id", user_id).eq("is_active", True).execute()
    )
    topics = topics_res.data or []
    if not topics:
        return []

    lookup_keys: list[str] = []
    seen_keys: set[str] = set()
    for topic in topics:
        for key in (topic["name"], topic["category"]):
            if key and key not in seen_keys:
                seen_keys.add(key)
                lookup_keys.append(key)

    async def _fetch(key: str):
        return await asyncio.to_thread(
            lambda: supabase.table("contents").select("*")
                .eq("topic_category", key).eq("collected_at", today)
                .order("created_at", desc=True).limit(3).execute()
        )

    results = await asyncio.gather(*[_fetch(k) for k in lookup_keys])

    all_contents = []
    seen_ids: set[str] = set()
    for res in results:
        for item in (res.data or []):
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                all_contents.append(item)
    return all_contents


def _q_review_count(user_id: str):
    weak = (supabase.table("concept_levels").select("concept")
            .eq("user_id", user_id).lt("level", 50).gt("total_attempts", 0)
            .limit(5).execute())
    if not weak.data:
        return 0
    weak_concepts = [row["concept"] for row in weak.data]
    answered_today = (supabase.table("quiz_results").select("quiz_id")
                      .eq("user_id", user_id).gte("answered_at", date.today().isoformat()).execute())
    answered_ids = [r["quiz_id"] for r in answered_today.data]
    q = supabase.table("quizzes").select("id").in_("concept", weak_concepts).limit(2)
    if answered_ids:
        q = q.not_.in_("id", answered_ids)
    return len((q.execute()).data or [])


# ── 집계 엔드포인트 ──────────────────────────────────────────────

@router.get("/summary/{user_id}")
async def home_summary(user_id: str):
    """홈 화면 데이터를 병렬 조회해 단 1회 HTTP 왕복으로 반환"""
    from api.progress import get_user_curricula

    streak_status_task = asyncio.to_thread(_q_streak_and_status, user_id)
    xp_task            = asyncio.to_thread(_q_xp,            user_id)
    levels_task        = asyncio.to_thread(_q_levels,         user_id)
    contents_task      = _q_contents(user_id)
    review_task        = asyncio.to_thread(_q_review_count,   user_id)
    curricula_task     = get_user_curricula(user_id)

    (streak_status_pair, xp_info, levels,
     contents, review_count, curricula) = await asyncio.gather(
        streak_status_task, xp_task, levels_task,
        contents_task, review_task, curricula_task,
        return_exceptions=True,
    )

    def safe(val, default=None):
        return default if isinstance(val, Exception) else val

    streak, streak_status = safe(streak_status_pair, (None, None))

    return {
        "streak":        streak,
        "streak_status": streak_status,
        "xp_info":       safe(xp_info),
        "levels":        safe(levels, []),
        "contents":      safe(contents, []),
        "review_count":  safe(review_count, 0),
        "curricula":     safe(curricula, []),
    }
