from fastapi import APIRouter
from core.supabase import supabase
from datetime import date

router = APIRouter()

@router.get("/today/{category}")
async def get_today_content(category: str):
    """오늘의 브리핑 콘텐츠"""
    today = date.today().isoformat()
    res = supabase.table("contents").select("*").eq("topic_category", category).eq("collected_at", today).order("created_at", desc=True).limit(5).execute()
    return res.data

@router.get("/")
async def get_contents(category: str | None = None, limit: int = 10):
    q = supabase.table("contents").select("*")
    if category:
        q = q.eq("topic_category", category)
    res = q.order("collected_at", desc=True).limit(limit).execute()
    return res.data
