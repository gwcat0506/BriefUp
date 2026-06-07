"""
MCP Tool 구현체
OpenAI tool use에 등록되는 함수들 + 단계별 로깅 주입
원문 텍스트는 이 모듈 내부에서만 처리하고 외부(Claude context)로 노출하지 않음
"""

import time
from datetime import date
from core.supabase import supabase
from core.logger import PipelineLogger
from agent.collector import collect_for_topic
from agent.web_search import search_web
from agent.summarizer import summarize
from agent.quiz_gen import generate_quizzes
from agent.verifier import verify_and_filter


# ── OpenAI Function Calling 스키마 ────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_active_topics",
            "description": (
                "DB에서 활성화된 사용자들의 관심 토픽(name, category) 목록을 조회합니다. "
                "파이프라인 시작 시 반드시 먼저 호출하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_pipeline_for_topic",
            "description": (
                "지정된 토픽에 대해 콘텐츠 수집(arxiv/RSS/웹)→중복제거→요약→퀴즈생성→검증→DB저장 "
                "전체 파이프라인을 실행합니다. 각 단계는 자동으로 로깅됩니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_name": {
                        "type": "string",
                        "description": "처리할 토픽명 (예: RAG, LangGraph, 사르트르)"
                    },
                    "category": {
                        "type": "string",
                        "description": "토픽이 속한 카테고리 (예: AI/ML, 철학, 경제, 심리학)"
                    }
                },
                "required": ["topic_name", "category"]
            }
        }
    }
]


# ── Tool 구현체 ───────────────────────────────────────────────

async def get_active_topics() -> dict:
    """활성 사용자 토픽 조회 — 구독자가 많은 순"""
    try:
        res = supabase.table("topics").select("name, category").eq("is_active", True).execute()
        seen: set[tuple] = set()
        topics: list[dict] = []
        for row in (res.data or []):
            key = (row["name"], row["category"])
            if key not in seen:
                seen.add(key)
                topics.append({"name": row["name"], "category": row["category"]})
        if not topics:
            topics = [{"name": "AI/ML", "category": "AI/ML"}]
        return {"topics": topics}
    except Exception as e:
        return {"topics": [{"name": "AI/ML", "category": "AI/ML"}], "error": str(e)}


async def run_pipeline_for_topic(
    topic_name: str, category: str, logger: PipelineLogger
) -> dict:
    """
    토픽별 전체 파이프라인 실행 + 단계별 로깅

    Returns:
        {topic_name, category, contents_saved, quizzes_saved, failed, duration_seconds}
    """
    stats = {
        "topic_name": topic_name,
        "category": category,
        "contents_saved": 0,
        "quizzes_saved": 0,
        "failed": 0,
    }
    pipeline_start = time.monotonic()

    # ── STEP 1: 수집 (arxiv/RSS + 웹) ─────────────────────────
    t = time.monotonic()
    try:
        trad_items = await collect_for_topic(topic_name, category)

        try:
            web_items = await search_web(topic_name)
        except ValueError:
            web_items = []  # TAVILY_API_KEY 없으면 웹 검색 스킵

        for item in web_items:
            item["topic_category"] = category

        # URL 중복 제거
        seen_urls: set[str] = set()
        raw_contents: list[dict] = []
        for item in trad_items + web_items:
            url = item.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            raw_contents.append(item)

        logger.log_step(
            tool_name="collect",
            inputs={"topic_name": topic_name, "category": category},
            output={
                "arxiv_rss": len(trad_items),
                "web": len(web_items),
                "total_after_dedup": len(raw_contents),
            },
            duration_ms=int((time.monotonic() - t) * 1000),
            status="success",
            category=category,
        )
    except Exception as e:
        logger.log_step(
            tool_name="collect",
            inputs={"topic_name": topic_name, "category": category},
            duration_ms=int((time.monotonic() - t) * 1000),
            status="failed",
            error_message=str(e),
            category=category,
        )
        stats["failed"] += 1
        stats["duration_seconds"] = round(time.monotonic() - pipeline_start, 2)
        return stats

    # ── STEP 2~5: 항목별 처리 ─────────────────────────────────
    for raw in raw_contents:
        title_short = raw["title"][:60]

        # STEP 2: 요약
        t = time.monotonic()
        try:
            summary = await summarize(raw["title"], raw["text"], category)
            logger.log_step(
                tool_name="summarize",
                inputs={"title": title_short, "category": category},
                output={"summary_length": len(summary)},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="success",
                category=category,
            )
        except Exception as e:
            logger.log_step(
                tool_name="summarize",
                inputs={"title": title_short},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="failed",
                error_message=str(e),
                category=category,
            )
            stats["failed"] += 1
            continue

        # STEP 3: 퀴즈 생성
        t = time.monotonic()
        try:
            quizzes = await generate_quizzes(raw["title"], raw["text"], category)
            if not quizzes:
                raise ValueError("퀴즈 생성 결과 없음")
            logger.log_step(
                tool_name="quiz_gen",
                inputs={"title": title_short, "category": category},
                output={"quiz_count": len(quizzes)},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="success",
                category=category,
            )
        except Exception as e:
            logger.log_step(
                tool_name="quiz_gen",
                inputs={"title": title_short},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="failed",
                error_message=str(e),
                category=category,
            )
            stats["failed"] += 1
            continue

        # STEP 4: 검증
        t = time.monotonic()
        try:
            verified = await verify_and_filter(quizzes, raw["text"])
            if not verified:
                raise ValueError("검증 통과 퀴즈 없음")
            logger.log_step(
                tool_name="verify",
                inputs={"quiz_count": len(quizzes), "category": category},
                output={"passed": len(verified), "failed": len(quizzes) - len(verified)},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="success",
                category=category,
            )
        except Exception as e:
            logger.log_step(
                tool_name="verify",
                inputs={"quiz_count": len(quizzes) if quizzes else 0},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="failed",
                error_message=str(e),
                category=category,
            )
            stats["failed"] += 1
            continue

        # STEP 5: 저장
        t = time.monotonic()
        try:
            content_id = _save_content(raw, summary, category)
            quiz_count = _save_quizzes(verified, content_id)
            logger.log_step(
                tool_name="save",
                inputs={"category": category, "quiz_count": len(verified)},
                output={"content_id": content_id, "quizzes_saved": quiz_count},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="success",
                category=category,
            )
            stats["contents_saved"] += 1
            stats["quizzes_saved"] += quiz_count
        except Exception as e:
            logger.log_step(
                tool_name="save",
                inputs={"category": category},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="failed",
                error_message=str(e),
                category=category,
            )
            stats["failed"] += 1

    stats["duration_seconds"] = round(time.monotonic() - pipeline_start, 2)
    return stats


# ── DB 저장 헬퍼 ──────────────────────────────────────────────

def _save_content(raw: dict, summary: str, category: str) -> str:
    res = supabase.table("contents").insert({
        "topic_category": category,
        "source": raw.get("source", "unknown"),
        "title": raw["title"],
        "original_url": raw.get("url", ""),
        "summary": summary,
        "collected_at": date.today().isoformat(),
    }).execute()
    return res.data[0]["id"]


def _save_quizzes(quizzes: list[dict], content_id: str) -> int:
    count = 0
    for quiz in quizzes:
        try:
            supabase.table("quizzes").insert({
                "content_id": content_id,
                "question": quiz["question"],
                "options": quiz["options"],
                "answer": quiz["answer"],
                "explanation": quiz["explanation"],
                "concept": quiz["concept"],
                "difficulty": quiz.get("difficulty", 1),
            }).execute()
            count += 1
        except Exception as e:
            print(f"    [퀴즈 저장 오류] {e}")
    return count
