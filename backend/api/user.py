from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.supabase import supabase
from datetime import date, timedelta

router = APIRouter()

# 마일스톤 정의 (듀오링고 방식)
MILESTONES = {
    7:   {"badge": "🔥 일주일 달성!", "reward": "스트릭 프리즈 1개 추가"},
    30:  {"badge": "💎 한 달 달성!", "reward": "스트릭 프리즈 2개 추가"},
    100: {"badge": "👑 100일 달성!", "reward": "스트릭 프리즈 3개 추가 + VIP 뱃지"},
    365: {"badge": "🏆 1년 달성!", "reward": "전설의 학습자!"},
}

class UserCreate(BaseModel):
    id: str | None = None
    email: str
    nickname: str | None = None

class TopicCreate(BaseModel):
    user_id: str
    name: str
    category: str


@router.post("/")
async def create_user(body: UserCreate):
    try:
        insert_data: dict = {"email": body.email, "nickname": body.nickname}
        if body.id:
            insert_data["id"] = body.id
        res = supabase.table("users").insert(insert_data).execute()
        return res.data[0]
    except Exception:
        res = supabase.table("users")\
            .update({"nickname": body.nickname})\
            .eq("email", body.email)\
            .execute()
        return res.data[0] if res.data else {}


@router.get("/{user_id}")
async def get_user(user_id: str):
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="유저 없음")
    return res.data[0]


@router.post("/topic")
async def add_topic(body: TopicCreate):
    try:
        res = supabase.table("topics").insert({
            "user_id": body.user_id,
            "name": body.name,
            "category": body.category
        }).execute()
        return res.data[0]
    except Exception:
        return {"message": "이미 추가된 관심사예요"}


@router.get("/{user_id}/topics")
async def get_topics(user_id: str):
    res = supabase.table("topics").select("*").eq("user_id", user_id).eq("is_active", True).execute()
    return res.data


@router.get("/{user_id}/streak")
async def get_streak(user_id: str):
    """스트릭 + 마일스톤 + 프리즈 정보 반환"""
    res = supabase.table("streaks").select("*").eq("user_id", user_id).execute()
    if not res.data:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "freeze_available": 1,
            "milestone": None,
            "next_milestone": 7,
        }

    streak = res.data[0]
    current = streak.get("current_streak", 0)

    # 마일스톤 확인
    milestone = None
    for days, info in sorted(MILESTONES.items()):
        if current == days:
            milestone = {"days": days, **info}
            break

    # 다음 마일스톤
    next_milestone = next((d for d in sorted(MILESTONES.keys()) if d > current), None)

    return {
        **streak,
        "milestone": milestone,
        "next_milestone": next_milestone,
        "days_to_next": (next_milestone - current) if next_milestone else None,
    }


@router.post("/{user_id}/streak/freeze")
async def use_streak_freeze(user_id: str):
    """스트릭 프리즈 사용 — 어제 학습 못 했을 때"""
    res = supabase.table("streaks").select("*").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="스트릭 데이터 없음")

    streak = res.data[0]
    freeze = streak.get("freeze_available", 0)

    if freeze <= 0:
        raise HTTPException(status_code=400, detail="스트릭 프리즈가 없어요")

    yesterday = (date.today() - timedelta(days=1)).isoformat()

    supabase.table("streaks").update({
        "freeze_available": freeze - 1,
        "last_active_date": yesterday,  # 어제 한 것처럼 설정
    }).eq("user_id", user_id).execute()

    return {
        "success": True,
        "freeze_remaining": freeze - 1,
        "message": f"스트릭 프리즈 사용! 남은 프리즈: {freeze - 1}개"
    }


@router.get("/{user_id}/streak/status")
async def check_streak_status(user_id: str):
    """
    오늘 학습했는지, 스트릭 위험한지 체크
    앱 열 때마다 호출해서 알림 표시용
    """
    res = supabase.table("streaks").select("*").eq("user_id", user_id).execute()
    if not res.data:
        return {"status": "new", "message": "오늘 첫 학습을 시작해봐요! 🌱"}

    streak = res.data[0]
    last = streak.get("last_active_date")
    current = streak.get("current_streak", 0)
    freeze = streak.get("freeze_available", 0)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if str(last) == today:
        return {
            "status": "done",
            "message": f"오늘 학습 완료! 🔥 {current}일 연속",
            "current_streak": current,
        }
    elif str(last) == yesterday:
        return {
            "status": "pending",
            "message": f"오늘 아직 학습 안 했어요! 🔥 {current}일 스트릭 위험",
            "current_streak": current,
            "freeze_available": freeze,
        }
    else:
        if freeze > 0 and current > 0:
            return {
                "status": "freezeable",
                "message": f"스트릭이 끊길 위기! 프리즈 사용할까요? ({freeze}개 남음)",
                "current_streak": current,
                "freeze_available": freeze,
            }
        return {
            "status": "broken",
            "message": "스트릭이 끊겼어요. 오늘부터 다시 시작! 💪",
            "current_streak": 0,
        }
