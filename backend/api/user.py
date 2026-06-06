from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.supabase import supabase

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    nickname: str | None = None

class TopicCreate(BaseModel):
    user_id: str
    name: str
    category: str

@router.post("/")
async def create_user(body: UserCreate):
    res = supabase.table("users").insert({
        "email": body.email,
        "nickname": body.nickname
    }).execute()
    return res.data[0]

@router.get("/{user_id}")
async def get_user(user_id: str):
    res = supabase.table("users").select("*").eq("id", user_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="유저 없음")
    return res.data

@router.post("/topic")
async def add_topic(body: TopicCreate):
    res = supabase.table("topics").insert({
        "user_id": body.user_id,
        "name": body.name,
        "category": body.category
    }).execute()
    return res.data[0]

@router.get("/{user_id}/topics")
async def get_topics(user_id: str):
    res = supabase.table("topics").select("*").eq("user_id", user_id).eq("is_active", True).execute()
    return res.data

@router.get("/{user_id}/streak")
async def get_streak(user_id: str):
    res = supabase.table("streaks").select("*").eq("user_id", user_id).single().execute()
    return res.data or {"current_streak": 0, "longest_streak": 0}
