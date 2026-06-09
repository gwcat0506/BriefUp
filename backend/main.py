from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from api import quiz, user, content, chapter, progress, logs, home, observability

app = FastAPI(
    title="BrefUp API",
    description="AI 브리핑 학습 Agent",
    version="0.1.0",
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
app.include_router(observability.router, prefix="/api/pipeline", tags=["observability"])

@app.get("/")
async def root():
    return {"status": "ok", "service": "BrefUp API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

