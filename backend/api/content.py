from fastapi import APIRouter, BackgroundTasks
from core.supabase import supabase
from datetime import date

router = APIRouter()


@router.get("/today/{category}")
async def get_today_content(category: str):
    """오늘의 브리핑 콘텐츠"""
    today = date.today().isoformat()
    res = (
        supabase.table("contents")
        .select("*")
        .eq("topic_category", category)
        .eq("collected_at", today)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    return res.data


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
