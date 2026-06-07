"""
학습 진행 상태 + 북마크 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.supabase import supabase
from datetime import datetime

router = APIRouter()


# ── 챕터 진행 상태 ──────────────────────────────────────────

class ProgressUpdate(BaseModel):
    user_id: str
    chapter_id: str      # "rag-1"
    track: str           # "rag"
    status: str          # "started" | "completed"
    quiz_score: int = 0
    quiz_total: int = 0


@router.post("/chapter")
async def update_chapter_progress(body: ProgressUpdate):
    """챕터 진행 상태 업데이트 (upsert)"""
    data = {
        "user_id": body.user_id,
        "chapter_id": body.chapter_id,
        "track": body.track,
        "status": body.status,
        "quiz_score": body.quiz_score,
        "quiz_total": body.quiz_total,
    }
    if body.status == "completed":
        data["completed_at"] = datetime.utcnow().isoformat()

    try:
        res = supabase.table("chapter_progress").upsert(
            data, on_conflict="user_id,chapter_id"
        ).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"chapter_progress 테이블 미생성: {e}")


@router.get("/chapter/{user_id}")
async def get_user_progress(user_id: str):
    """유저의 전체 챕터 진행 상태"""
    res = supabase.table("chapter_progress")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    # chapter_id → progress 매핑으로 반환
    return {row["chapter_id"]: row for row in res.data}


@router.get("/curricula/{user_id}")
async def get_user_curricula(user_id: str):
    """
    유저 관심사 토픽에 맞는 커리큘럼 목록 + 챕터별 진행 상태 반환
    매칭 토픽 없으면 기본 AI 3트랙(rag/agent/llm) 반환
    """
    from agent.curriculum_catalog import CURRICULUM_CATALOG

    # 유저 토픽 조회
    topics_res = supabase.table("topics").select("name").eq("user_id", user_id).eq("is_active", True).execute()
    topic_names_lower = {t["name"].lower() for t in (topics_res.data or [])}

    # 유저 챕터 진행 상태 조회
    try:
        progress_res = supabase.table("chapter_progress").select("chapter_id,status").eq("user_id", user_id).execute()
        completed_ids = {r["chapter_id"] for r in progress_res.data if r.get("status") == "completed"}
        progress_map = {r["chapter_id"]: r["status"] for r in progress_res.data}
    except Exception:
        completed_ids = set()
        progress_map = {}

    def build_track(track_id: str, track: dict) -> dict:
        chapters_out = []
        for ch in track["chapters"]:
            ch_id = ch["id"]
            order = int(ch_id.split("-")[-1])
            # 잠금 해제 로직: 1번은 항상 가능, N번은 N-1번 완료 시 가능
            if order == 1:
                unlock = "available"
            else:
                prev_id = f"{track_id}-{order - 1}"
                unlock = "available" if prev_id in completed_ids else "locked"
            # 실제 진행 상태 우선
            status = progress_map.get(ch_id, unlock)
            if status not in ("completed", "started") and unlock == "locked":
                status = "locked"
            chapters_out.append({
                "id": order,
                "chapter_id": ch_id,
                "title": ch["title"],
                "description": ch.get("description", ""),
                "level": ch["level"],
                "duration": ch.get("duration", "5분"),
                "status": status,
            })
        return {
            "id": track_id,
            "title": track["title"],
            "emoji": track["emoji"],
            "color": track["color"],
            "description": track["description"],
            "totalChapters": len(track["chapters"]),
            "chapters": chapters_out,
        }

    result = []
    for track_id, track in CURRICULUM_CATALOG.items():
        matched = any(n.lower() in topic_names_lower for n in track["topic_names"])
        if matched:
            result.append(build_track(track_id, track))

    # 매칭 없으면 기본 3트랙
    if not result:
        for track_id in ["rag", "agent", "llm"]:
            result.append(build_track(track_id, CURRICULUM_CATALOG[track_id]))

    return result


@router.get("/chapter/{user_id}/next")
async def get_next_chapter(user_id: str):
    """
    다음에 학습할 챕터 추천
    완료 안 된 챕터 중 가장 앞 챕터
    """
    from agent.curriculum_catalog import CHAPTERS

    # 완료된 챕터 목록 (테이블 없으면 빈 셋으로 처리)
    try:
        completed = supabase.table("chapter_progress")\
            .select("chapter_id")\
            .eq("user_id", user_id)\
            .eq("status", "completed")\
            .execute()
        completed_ids = {row["chapter_id"] for row in completed.data}
    except Exception:
        completed_ids = set()

    # 트랙 순서대로 완료 안 된 첫 번째 챕터 찾기
    for track_key, track in CHAPTERS.items():
        for ch in track["chapters"]:
            if ch["id"] not in completed_ids:
                return {
                    "chapter_id": ch["id"],
                    "track": track_key,
                    "track_title": track["title"],
                    "chapter_title": ch["title"],
                    "level": ch["level"],
                    "duration": ch.get("duration", "5분"),
                }
    return None  # 전부 완료


# ── 북마크 ──────────────────────────────────────────────────

class BookmarkCreate(BaseModel):
    user_id: str
    content_id: str
    note: str = ""


@router.post("/bookmark")
async def add_bookmark(body: BookmarkCreate):
    """북마크 추가"""
    try:
        res = supabase.table("bookmarks").insert({
            "user_id": body.user_id,
            "content_id": body.content_id,
            "note": body.note,
        }).execute()
        return {"bookmarked": True, "id": res.data[0]["id"]}
    except Exception:
        # 이미 북마크된 경우 → 삭제 (토글)
        supabase.table("bookmarks")\
            .delete()\
            .eq("user_id", body.user_id)\
            .eq("content_id", body.content_id)\
            .execute()
        return {"bookmarked": False}


@router.get("/bookmark/{user_id}")
async def get_bookmarks(user_id: str):
    """유저 북마크 목록"""
    res = supabase.table("bookmarks")\
        .select("*, contents(id, title, summary, source, topic_category)")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data


@router.get("/bookmark/{user_id}/check/{content_id}")
async def check_bookmark(user_id: str, content_id: str):
    """특정 콘텐츠 북마크 여부 확인"""
    res = supabase.table("bookmarks")\
        .select("id")\
        .eq("user_id", user_id)\
        .eq("content_id", content_id)\
        .execute()
    return {"bookmarked": len(res.data) > 0}
