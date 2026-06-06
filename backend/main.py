from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os

load_dotenv()

from api import quiz, user, content
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
    allow_origins=[
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(content.router, prefix="/api/content", tags=["content"])

@app.get("/")
async def root():
    return {"status": "ok", "service": "BrefUp API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
