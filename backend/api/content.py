from fastapi import APIRouter, BackgroundTasks
from core.supabase import supabase
from datetime import date

router = APIRouter()


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


@router.post("/run-pipeline")
async def run_pipeline(background_tasks: BackgroundTasks):
    """
    파이프라인 수동 실행 (테스트/개발용)
    백그라운드로 실행되어 즉시 응답 반환
    """
    from agent.scheduler import run_daily_pipeline
    background_tasks.add_task(run_daily_pipeline)
    return {"status": "started", "message": "파이프라인 백그라운드 실행 시작. 1~2분 후 콘텐츠가 생성됩니다."}
