import json

from fastapi import APIRouter, BackgroundTasks, HTTPException
from core.supabase import supabase
from datetime import date

router = APIRouter()

_pipeline_running = False


@router.get("/today/for-user/{user_id}")
async def get_today_content_for_user(user_id: str):
    """유저 활성 토픽 기반 오늘의 브리핑 (토픽별로 최대 3개씩)"""
    today = date.today().isoformat()

    topics_res = (
        supabase.table("topics")
        .select("name, category")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    topics = topics_res.data or []

    if not topics:
        return []

    all_contents = []
    seen_ids: set[str] = set()

    # 조회할 키 수집: topic.name과 topic.category 모두 시도 (기존 데이터 호환)
    lookup_keys: list[str] = []
    seen_keys: set[str] = set()
    for topic in topics:
        for key in (topic["name"], topic["category"]):
            if key and key not in seen_keys:
                seen_keys.add(key)
                lookup_keys.append(key)

    if lookup_keys:
        res = (
            supabase.table("contents")
            .select("*")
            .in_("topic_category", lookup_keys)
            .eq("collected_at", today)
            .order("created_at", desc=True)
            .execute()
        )
        topic_count: dict[str, int] = {}
        for item in (res.data or []):
            cat = item["topic_category"]
            if topic_count.get(cat, 0) < 3 and item["id"] not in seen_ids:
                topic_count[cat] = topic_count.get(cat, 0) + 1
                seen_ids.add(item["id"])
                all_contents.append(item)

    return all_contents


@router.get("/")
async def get_contents(category: str | None = None, limit: int = 10):
    q = supabase.table("contents").select("*")
    if category:
        q = q.eq("topic_category", category)
    res = q.order("collected_at", desc=True).limit(limit).execute()
    return res.data


@router.get("/{content_id}/cards")
async def get_content_cards(content_id: str):
    """
    파이프라인 수집 콘텐츠의 학습 카드 반환.
    summary 필드가 {"cards": [...]} 형식이어야 합니다.
    """
    res = supabase.table("contents").select("*").eq("id", content_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없어요.")
    row = res.data[0]
    try:
        cards_data = json.loads(row["summary"])
        if not isinstance(cards_data.get("cards"), list):
            raise ValueError("cards 필드 없음")
    except Exception:
        raise HTTPException(status_code=422, detail="이 콘텐츠는 카드 형식이 아닙니다.")
    return {"content": row, "cards": cards_data}


@router.post("/run-pipeline")
async def run_pipeline(background_tasks: BackgroundTasks):
    """
    파이프라인 수동 실행 (테스트/개발용)
    백그라운드로 실행되어 즉시 응답 반환
    """
    global _pipeline_running
    if _pipeline_running:
        raise HTTPException(status_code=409, detail="파이프라인이 이미 실행 중입니다.")

    from agent.scheduler import run_daily_pipeline

    async def _run():
        global _pipeline_running
        _pipeline_running = True
        try:
            await run_daily_pipeline()
        finally:
            _pipeline_running = False

    background_tasks.add_task(_run)
    return {"status": "started", "message": "파이프라인 백그라운드 실행 시작. 1~2분 후 콘텐츠가 생성됩니다."}
