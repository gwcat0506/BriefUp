from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os

load_dotenv()

from api import quiz, user, content, chapter, progress, logs, home
from agent.scheduler import run_daily_pipeline

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 매일 새벽 5시 파이프라인 자동 실행
    scheduler.add_job(
        run_daily_pipeline,
        "cron",
        hour=5,
        minute=0,
        id="daily_pipeline"
    )
    scheduler.start()
    print("✅ 스케줄러 시작 — 매일 05:00 파이프라인 실행")
    yield
    scheduler.shutdown()

app = FastAPI(
    title="BrefUp API",
    description="AI 브리핑 학습 Agent",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(content.router, prefix="/api/content", tags=["content"])
app.include_router(chapter.router, prefix="/api/chapter", tags=["chapter"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(home.router, prefix="/api/home", tags=["home"])

@app.get("/")
async def root():
    return {"status": "ok", "service": "BrefUp API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/admin/reseed")
async def admin_reseed():
    """커리큘럼 카탈로그를 DB에 upsert. 배포 후 1회 실행용."""
    import asyncio
    from agent.curriculum_catalog import CURRICULUM_CATALOG
    from core.supabase import supabase

    results = []
    for track_id, track in CURRICULUM_CATALOG.items():
        await asyncio.to_thread(
            lambda t_id=track_id, t=track: supabase.table("topic_curricula").upsert({
                "topic_key":     t_id,
                "topic_name":    t["title"],
                "category":      t.get("topic_names", [t["title"]])[0],
                "topic_aliases": t.get("topic_names", []),
                "emoji":         t.get("emoji", "📚"),
                "color":         t.get("color", "#6366F1"),
                "description":   t.get("description", ""),
                "chapters":      t["chapters"],
            }, on_conflict="topic_key").execute()
        )
        results.append({"track": track_id, "chapters": len(track["chapters"])})

    return {"status": "ok", "upserted": results}
