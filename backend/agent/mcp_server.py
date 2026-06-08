"""
FastMCP 서버 — BrefUp 파이프라인 도구 정의

내부 에이전트: FastMCP Client로 in-process 연결
외부 클라이언트(Claude Desktop 등): `python -m agent.mcp_server` 로 stdio 서버 실행
"""

import asyncio
import time
import uuid
from datetime import date

from fastmcp import FastMCP
from core.supabase import supabase
from core.logger import PipelineLogger
from agent.collector import collect_for_topic
from agent.web_search import search_web
from agent.summarizer import summarize as _summarize
from agent.quiz_gen import generate_quizzes as _quiz_gen
from agent.verifier import verify_and_filter

mcp = FastMCP(
    name="BrefUp Pipeline",
    instructions=(
        "BrefUp 학습 콘텐츠 파이프라인 도구입니다. "
        "collect_articles → summarize_article → generate_quizzes → save_content 순으로 처리하세요. "
        "collect_articles와 summarize_article은 여러 항목을 동시에 호출할 수 있습니다."
    ),
)

# ── 세션 스토어 ───────────────────────────────────────────────
# 에이전트 한 번의 실행 동안 아티클 데이터를 보관.
# 에이전트에는 ID + 메타데이터만 노출하고, 원문 본문은 여기서만 관리한다.

_session: dict = {
    "articles": {},  # article_id → {title, text, source, url, summary?, quizzes?}
    "run_stats": {
        "total_contents": 0, "total_quizzes": 0, "total_failed": 0,
        "tokens": {"claude_input": 0, "claude_output": 0, "openai_input": 0, "openai_output": 0},
    },
    "logger": None,
}


def reset_session(logger: PipelineLogger) -> None:
    _session["articles"].clear()
    _session["run_stats"] = {
        "total_contents": 0, "total_quizzes": 0, "total_failed": 0,
        "tokens": {"claude_input": 0, "claude_output": 0, "openai_input": 0, "openai_output": 0},
    }
    _session["logger"] = logger


def _log() -> PipelineLogger | None:
    return _session["logger"]


# ── Tools ─────────────────────────────────────────────────────

@mcp.tool()
async def get_active_topics() -> dict:
    """
    DB에서 활성화된 토픽(name, category) 목록을 조회합니다.
    파이프라인 시작 시 가장 먼저 호출하세요.
    """
    try:
        res = await asyncio.to_thread(
            lambda: supabase.table("topics")
                .select("name, category")
                .eq("is_active", True)
                .execute()
        )
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


@mcp.tool()
async def collect_articles(topic_name: str, category: str, arxiv_query: str | None = None, web_query: str | None = None) -> dict:
    """
    토픽에 대한 원문 아티클을 수집합니다.
    여러 토픽을 동시에 호출할 수 있습니다.
    반환된 articles의 title/source/text_length를 보고
    품질이 낮거나 관련 없는 아티클은 건너뛰어도 됩니다.

    topic_name을 보고 직접 영문 쿼리를 작성하세요.

    Args:
        topic_name: 토픽명 (예: RAG, 사르트르)
        category: 카테고리 (예: AI/ML, 철학)
        arxiv_query: arxiv 영문 검색 쿼리 (없으면 topic_name 사용)
        web_query: 웹 영문 검색 쿼리 (없으면 topic_name 사용)
    """
    logger = _log()
    t = time.monotonic()
    try:
        trad_items = await collect_for_topic(topic_name, category, arxiv_query=arxiv_query)

        try:
            web_items = await search_web(web_query or topic_name)
        except ValueError:
            web_items = []

        for item in web_items:
            item["topic_category"] = category

        seen_urls: set[str] = set()
        raw_contents: list[dict] = []
        for item in trad_items + web_items:
            url = item.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            raw_contents.append(item)

        prefix = topic_name[:8].lower().replace(" ", "_").replace("/", "_")
        articles_meta = []
        for raw in raw_contents:
            article_id = f"{prefix}_{uuid.uuid4().hex[:6]}"
            _session["articles"][article_id] = {
                "title":  raw["title"],
                "text":   raw["text"],
                "source": raw.get("source", "unknown"),
                "url":    raw.get("url", ""),
            }
            articles_meta.append({
                "id":          article_id,
                "title":       raw["title"][:80],
                "source":      raw.get("source", "unknown"),
                "text_length": len(raw.get("text", "")),
            })

        if logger:
            logger.log_step(
                tool_name="collect",
                inputs={"topic_name": topic_name, "category": category},
                output={"trad": len(trad_items), "web": len(web_items), "total": len(raw_contents)},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="success",
                category=category,
            )
        return {"topic_name": topic_name, "articles": articles_meta}

    except Exception as e:
        if logger:
            logger.log_step(
                tool_name="collect",
                inputs={"topic_name": topic_name, "category": category},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="failed",
                error_message=str(e),
                category=category,
            )
        _session["run_stats"]["total_failed"] += 1
        return {"topic_name": topic_name, "articles": [], "error": str(e)}


@mcp.tool()
async def summarize_article(article_id: str, category: str) -> dict:
    """
    아티클 하나를 요약합니다.
    같은 토픽의 여러 아티클에 대해 동시에 호출할 수 있습니다.
    실패(success=false) 시 해당 아티클은 건너뛰세요.

    Args:
        article_id: collect_articles에서 받은 article ID
        category: 카테고리 (예: AI/ML, 철학)
    """
    logger = _log()
    article = _session["articles"].get(article_id)
    if not article:
        return {"success": False, "error": f"article_id '{article_id}' not found"}

    t = time.monotonic()
    try:
        summary, usage = await _summarize(article["title"], article["text"], category)
        article["summary"] = summary
        _session["run_stats"]["tokens"]["openai_input"] += usage["input"]
        _session["run_stats"]["tokens"]["openai_output"] += usage["output"]
        if logger:
            logger.log_step(
                tool_name="summarize",
                inputs={"article_id": article_id, "category": category},
                output={"summary_length": len(summary)},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="success",
                category=category,
            )
        return {"success": True, "summary_length": len(summary)}

    except Exception as e:
        if logger:
            logger.log_step(
                tool_name="summarize",
                inputs={"article_id": article_id},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="failed",
                error_message=str(e),
                category=category,
            )
        _session["run_stats"]["total_failed"] += 1
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_quizzes(article_id: str, category: str) -> dict:
    """
    아티클에 대한 퀴즈를 생성하고 자동 검증합니다.
    summarize_article 완료 후 호출하세요.
    verified_count가 0이면 save_content를 호출하지 마세요.

    Args:
        article_id: collect_articles에서 받은 article ID
        category: 카테고리
    """
    logger = _log()
    article = _session["articles"].get(article_id)
    if not article:
        return {"verified_count": 0, "error": f"article_id '{article_id}' not found"}
    if "summary" not in article:
        return {"verified_count": 0, "error": "summarize_article을 먼저 호출하세요"}

    t = time.monotonic()
    try:
        quizzes, gen_usage = await _quiz_gen(article["title"], article["text"], category)
        if not quizzes:
            raise ValueError("퀴즈 생성 결과 없음")
        _session["run_stats"]["tokens"]["openai_input"] += gen_usage["input"]
        _session["run_stats"]["tokens"]["openai_output"] += gen_usage["output"]

        verified, ver_usage = await verify_and_filter(quizzes, article["text"])
        _session["run_stats"]["tokens"]["openai_input"] += ver_usage["input"]
        _session["run_stats"]["tokens"]["openai_output"] += ver_usage["output"]
        article["quizzes"] = verified

        if logger:
            logger.log_step(
                tool_name="quiz_gen",
                inputs={"article_id": article_id, "category": category},
                output={"generated": len(quizzes), "verified": len(verified)},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="success",
                category=category,
            )
        return {
            "verified_count": len(verified),
            "total_generated": len(quizzes),
            "concepts": [q.get("concept", "") for q in verified],
        }

    except Exception as e:
        if logger:
            logger.log_step(
                tool_name="quiz_gen",
                inputs={"article_id": article_id},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="failed",
                error_message=str(e),
                category=category,
            )
        _session["run_stats"]["total_failed"] += 1
        return {"verified_count": 0, "error": str(e)}


@mcp.tool()
async def save_content(article_id: str, topic_name: str, category: str) -> dict:
    """
    요약과 퀴즈가 준비된 아티클을 DB에 저장합니다.
    generate_quizzes의 verified_count > 0일 때만 호출하세요.

    Args:
        article_id: article ID
        topic_name: 토픽명
        category: 카테고리
    """
    logger = _log()
    article = _session["articles"].get(article_id)
    if not article:
        return {"error": f"article_id '{article_id}' not found"}
    if "summary" not in article:
        return {"error": "요약 없음. summarize_article을 먼저 호출하세요"}
    if not article.get("quizzes"):
        return {"error": "검증된 퀴즈 없음. generate_quizzes를 먼저 호출하세요"}

    t = time.monotonic()
    try:
        content_id = await asyncio.to_thread(
            lambda: _insert_content(article, topic_name, category)
        )
        quiz_count = await asyncio.to_thread(
            lambda: _insert_quizzes(article["quizzes"], content_id)
        )

        _session["run_stats"]["total_contents"] += 1
        _session["run_stats"]["total_quizzes"] += quiz_count

        if logger:
            logger.log_step(
                tool_name="save",
                inputs={"article_id": article_id, "category": category},
                output={"content_id": content_id, "quizzes_saved": quiz_count},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="success",
                category=category,
            )
        return {"content_id": content_id, "quizzes_saved": quiz_count}

    except Exception as e:
        if logger:
            logger.log_step(
                tool_name="save",
                inputs={"article_id": article_id},
                duration_ms=int((time.monotonic() - t) * 1000),
                status="failed",
                error_message=str(e),
                category=category,
            )
        _session["run_stats"]["total_failed"] += 1
        return {"error": str(e)}


# ── DB 헬퍼 (동기, asyncio.to_thread에서 호출) ────────────────

def _insert_content(article: dict, topic_name: str, category: str) -> str:
    res = supabase.table("contents").insert({
        "topic_category": topic_name,
        "source":         article.get("source", "unknown"),
        "title":          article["title"],
        "original_url":   article.get("url", ""),
        "summary":        article["summary"],
        "collected_at":   date.today().isoformat(),
    }).execute()
    return res.data[0]["id"]


def _insert_quizzes(quizzes: list[dict], content_id: str) -> int:
    count = 0
    for quiz in quizzes:
        try:
            supabase.table("quizzes").insert({
                "content_id":  content_id,
                "question":    quiz["question"],
                "options":     quiz["options"],
                "answer":      quiz["answer"],
                "explanation": quiz["explanation"],
                "concept":     quiz["concept"],
                "difficulty":  quiz.get("difficulty", 1),
            }).execute()
            count += 1
        except Exception as e:
            print(f"    [퀴즈 저장 오류] {e}")
    return count


if __name__ == "__main__":
    # 외부 MCP 클라이언트(Claude Desktop 등)에서 쓸 때 stdio 서버로 실행
    mcp.run()
