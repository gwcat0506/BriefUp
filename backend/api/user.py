from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from core.supabase import supabase
from datetime import date, timedelta

router = APIRouter()

# ── XP 시스템 ──────────────────────────────────────────
XP_QUIZ_CORRECT = 20
XP_STREAK_DAY = 10

_CHARACTERS = [
    (1,  3,  "🥚", "알",     "입문자"),
    (4,  7,  "🐣", "병아리", "초보자"),
    (8,  15, "🐥", "새",     "학습자"),
    (16, 25, "🦅", "독수리", "탐구자"),
    (26, 40, "🦉", "올빼미", "학자"),
    (41, 9999, "⭐", "전설", "마스터"),
]

def xp_for_level(level: int) -> int:
    """레벨 n 도달에 필요한 누적 XP (50*(n-1)^2)"""
    return 50 * (level - 1) ** 2

def get_level_from_xp(total_xp: int) -> int:
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    return level

def get_xp_info(total_xp: int) -> dict:
    level = get_level_from_xp(total_xp)
    cur_xp = xp_for_level(level)
    nxt_xp = xp_for_level(level + 1)
    xp_in = total_xp - cur_xp
    xp_need = nxt_xp - cur_xp
    char = next((c for c in _CHARACTERS if c[0] <= level <= c[1]), _CHARACTERS[-1])
    return {
        "level": level,
        "total_xp": total_xp,
        "xp_in_level": xp_in,
        "xp_needed": xp_need,
        "progress_pct": int(xp_in / xp_need * 100) if xp_need > 0 else 100,
        "char_emoji": char[2],
        "char_name": char[3],
        "char_title": char[4],
    }

def add_xp(user_id: str, amount: int) -> dict:
    """XP 추가 후 레벨 정보 반환 (sync)"""
    res = supabase.table("users").select("xp").eq("id", user_id).execute()
    cur = (res.data[0] if res.data else {}).get("xp") or 0
    old_level = get_level_from_xp(cur)
    new_xp = cur + amount
    new_level = get_level_from_xp(new_xp)
    supabase.table("users").update({"xp": new_xp}).eq("id", user_id).execute()
    return {
        **get_xp_info(new_xp),
        "xp_gained": amount,
        "leveled_up": new_level > old_level,
        "old_level": old_level,
    }

# ── 마일스톤 정의 (듀오링고 방식) ──────────────────────
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
    category: str | None = None

class FeedbackCreate(BaseModel):
    user_id: str
    feedback_type: str  # "positive" | "negative" | "suggestion"
    message: str
    content_id: str | None = None
    topic_name: str | None = None


@router.get("/{user_id}/xp")
async def get_user_xp(user_id: str):
    res = supabase.table("users").select("xp").eq("id", user_id).execute()
    total_xp = (res.data[0] if res.data else {}).get("xp") or 0
    return get_xp_info(total_xp)


@router.post("/")
async def create_user(body: UserCreate):
    insert_data: dict = {"email": body.email, "nickname": body.nickname}
    if body.id:
        insert_data["id"] = body.id
    try:
        res = supabase.table("users").insert(insert_data).execute()
        return res.data[0] if res.data else {}
    except Exception:
        pass
    try:
        res = supabase.table("users")\
            .update({"nickname": body.nickname})\
            .eq("id", body.id)\
            .execute()
        return res.data[0] if res.data else {}
    except Exception:
        return {}


@router.get("/{user_id}")
async def get_user(user_id: str):
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="유저 없음")
    return res.data[0]


@router.post("/topic")
async def add_topic(body: TopicCreate, background_tasks: BackgroundTasks):
    # 동일 이름 활성 토픽 중복 방지
    existing = supabase.table("topics").select("*")\
        .eq("user_id", body.user_id).eq("name", body.name).eq("is_active", True).execute()
    if existing.data:
        return existing.data[0]

    category = body.category
    if not category:
        from agent.classifier import classify_topic
        category = await classify_topic(body.name)
    try:
        res = supabase.table("topics").insert({
            "user_id": body.user_id,
            "name": body.name,
            "category": category,
        }).execute()
        topic_row = res.data[0]
    except Exception:
        return {"message": "이미 추가된 관심사예요"}

    # 커리큘럼 생성 → 파이프라인 순서대로 백그라운드 실행 (HTTP 응답 블로킹 방지)
    async def _bg(topic_name: str, cat: str):
        try:
            from agent.curriculum_gen import get_or_create_curriculum
            await get_or_create_curriculum(topic_name, cat)
        except Exception as e:
            print(f"[커리큘럼 생성 오류] {e}")
        try:
            from agent.scheduler import run_daily_pipeline
            await run_daily_pipeline([{"name": topic_name, "category": cat}])
        except Exception as e:
            print(f"[파이프라인 오류] {e}")

    background_tasks.add_task(_bg, body.name, category)

    return topic_row


@router.post("/feedback")
async def submit_feedback(body: FeedbackCreate):
    if body.feedback_type not in ("positive", "negative", "suggestion"):
        raise HTTPException(status_code=400, detail="올바르지 않은 feedback_type")
    insert_data: dict = {
        "user_id": body.user_id,
        "feedback_type": body.feedback_type,
        "message": body.message,
    }
    if body.content_id:
        insert_data["content_id"] = body.content_id
    if body.topic_name:
        insert_data["topic_name"] = body.topic_name
    res = supabase.table("user_feedback").insert(insert_data).execute()
    return res.data[0] if res.data else {"success": True}


@router.delete("/topic/{topic_id}")
async def remove_topic(topic_id: str):
    supabase.table("topics").update({"is_active": False}).eq("id", topic_id).execute()
    return {"removed": topic_id}


@router.get("/{user_id}/topics")
async def get_topics(user_id: str):
    res = supabase.table("topics").select("*").eq("user_id", user_id).eq("is_active", True).execute()
    # 이름 중복 제거 (같은 이름 여러 행 있을 경우 첫 번째만 반환)
    seen: set[str] = set()
    unique = []
    for row in res.data:
        if row["name"] not in seen:
            seen.add(row["name"])
            unique.append(row)
    return unique


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
    next_milestone_reward = MILESTONES[next_milestone]["reward"] if next_milestone else None

    return {
        **streak,
        "milestone": milestone,
        "next_milestone": next_milestone,
        "days_to_next": (next_milestone - current) if next_milestone else None,
        "next_milestone_reward": next_milestone_reward,
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
