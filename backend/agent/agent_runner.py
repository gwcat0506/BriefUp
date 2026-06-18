"""
Anthropic Claude + FastMCP 에이전트
MCP 서버에서 도구 목록을 가져와 Claude가 자율적으로 실행
"""

import asyncio
import json
import os
import sys

import anthropic
from fastmcp import Client

from core.config import CLAUDE_HAIKU_MODEL as MODEL
from core.logger import PipelineLogger
from agent.mcp_server import mcp, _session, reset_session

claude = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 가격 (per token) — Claude Haiku 4.5, GPT-4o-mini
_HAIKU_IN  = 1.00 / 1_000_000
_HAIKU_OUT = 5.00 / 1_000_000
_GPT_IN    = 0.15 / 1_000_000    # GPT-4o-mini input
_GPT_OUT   = 0.60 / 1_000_000    # GPT-4o-mini output


async def _get_recent_memory() -> str:
    """최근 3회 파이프라인 실행 기록을 조회해 Claude에게 줄 메모리 문자열 생성."""
    from core.supabase import supabase
    try:
        result = await asyncio.to_thread(
            lambda: supabase.table("pipeline_runs")
                .select("stats, status, started_at, categories")
                .order("started_at", desc=True)
                .limit(3)
                .execute()
        )
    except Exception as e:
        print(f"[Memory] 이전 실행 기록 조회 실패: {e}")
        return "이전 실행 기록 조회 실패."

    if not result.data:
        return "이전 실행 기록 없음 (첫 실행)."

    # 유저 피드백 조회 (최근 5개)
    feedback_text = ""
    try:
        fb_result = await asyncio.to_thread(
            lambda: supabase.table("user_feedback")
                .select("feedback_type, message, topic_name, created_at")
                .order("created_at", desc=True)
                .limit(5)
                .execute()
        )
        if fb_result.data:
            fb_lines = ["=== 유저 피드백 (최근 5개) ==="]
            for fb in fb_result.data:
                label = {"positive": "긍정", "negative": "부정", "suggestion": "제안"}.get(fb["feedback_type"], fb["feedback_type"])
                topic_hint = f" [{fb['topic_name']}]" if fb.get("topic_name") else ""
                fb_lines.append(f"  [{label}{topic_hint}] {fb['message']}")
            fb_lines.append("=== 위 피드백을 반영해 콘텐츠 품질을 조정하라 ===")
            feedback_text = "\n".join(fb_lines) + "\n\n"
    except Exception as e:
        print(f"[Memory] 유저 피드백 조회 실패: {e}")

    lines = [feedback_text + "=== 이전 실행 기록 (최근 3회) ==="]
    for i, run in enumerate(result.data):
        s = run.get("stats", {})
        date_str = run.get("started_at", "")[:10]
        lines.append(
            f"[{i+1}회 전 | {date_str}] "
            f"저장 {s.get('total_contents', 0)}개 · "
            f"퀴즈 {s.get('total_quizzes', 0)}개 · "
            f"faithfulness {s.get('avg_faithfulness', 0):.2f} · "
            f"퀴즈통과율 {s.get('quiz_pass_rate', 0):.2f} · "
            f"비용 ${s.get('cost_usd', 0):.3f}"
        )
        if s.get("reflection"):
            lines.append(f"  └ 지난 반성: {s['reflection']}")
        suggs = s.get("next_run_suggestions", [])
        if suggs:
            lines.append(f"  └ 이전 제안: {'; '.join(suggs)}")
    lines.append("=== 위 기록을 참고해 이번 실행 전략을 조정하라 ===")
    memory_text = "\n".join(lines)
    print(f"\n[Memory 주입]\n{memory_text}\n", file=sys.stderr)
    return memory_text

SYSTEM_PROMPT = """당신은 BriefUp 콘텐츠 큐레이터 에이전트입니다.

목표: 각 관심사의 커리큘럼 챕터 순서에 맞춰 오늘의 학습 콘텐츠를 수집·요약·퀴즈 생성·저장합니다.

## 처리 순서 (반드시 이 순서를 지키세요)

### STEP 1 — 토픽 확보
- 유저 메시지에 처리할 토픽이 명시된 경우: 그 토픽만 사용하고 get_active_topics를 건너뜁니다
- 명시된 토픽이 없는 경우: get_active_topics를 호출합니다

### STEP 2 — 수집 계획 (필수)
- 모든 토픽에 대해 get_collection_plan을 동시에 호출합니다
- 반환된 chapter_title, arxiv_query, web_query를 STEP 3에서 그대로 사용합니다
- arxiv_query가 null이면 collect_articles에서도 null로 전달하세요
- collection_strategy가 있으면 use_arxiv, include_domains를 collect_articles에 반드시 전달하세요

### STEP 3 — 아티클 수집
- 모든 토픽의 collect_articles를 동시에 호출합니다
- get_collection_plan에서 받은 arxiv_query, web_query를 반드시 사용하세요
- collection_strategy.use_arxiv → collect_articles의 use_arxiv 파라미터로 전달
- collection_strategy.include_domains → collect_articles의 include_domains 파라미터로 전달
- needs_retry=true이면 더 넓은 쿼리로 1회 재시도하세요

### STEP 4 — 처리 (두 단계로 분리)

**4a. 요약 (병렬 가능)**
- 모든 아티클의 summarize_article을 동시에 호출합니다
- audience_level 결정: 유저 피드백에 "전문가", "어렵게", "expert", "전공자" 등이 있으면 "expert", 그 외 "general"
- 결과에서 success=true인 아티클 ID 목록을 확인합니다

**4b. 퀴즈 생성 + 저장 (4a 완료 후)**
- success=true인 모든 아티클에 대해 generate_quizzes를 동시에 호출합니다
- success=true가 N개면 generate_quizzes를 반드시 N번 호출해야 합니다 (건너뛰기 금지)
- generate_quizzes 결과 verified_count > 0인 아티클만 save_content 호출
- verified_count = 0이면 그 아티클은 save_content 호출 없이 건너뜁니다

**주의**: summarize_article success=true 후 generate_quizzes를 건너뛰는 것은 금지입니다.

### STEP 5 — 반성 (필수 마지막 단계)
모든 save_content 완료 후 save_reflection을 1회 호출합니다:
- quality_assessment: "카테고리별 faithfulness·퀴즈통과율 요약 + 반복된 실패 패턴" 한 문장
- next_run_suggestions: 특정 토픽이 아닌 카테고리/분야 수준의 범용 패턴 제안 최대 3개
  - 나쁜 예) "주식/투자 챕터4에 smart beta 키워드 추가" — 해당 토픽에만 적용 가능
  - 좋은 예) "경제·금융 분야는 arxiv 미스매치 반복 → 사회과학 계열 전체 use_arxiv=false 권장"
  - 좋은 예) "faithfulness 저하 원인 대부분이 HTML 콘텐츠 → web_query에 'research' 또는 'systematic review' 추가"

## 유저 피드백 우선순위
유저 피드백이 서로 상충하면 목록의 첫 번째(가장 최신) 피드백을 우선하세요.

## Cross-run Memory 활용
- 대화 시작 시 주입된 이전 실행 기록을 확인하세요
- 이전 제안이 특정 토픽 언급이어도, 같은 카테고리 분야 전체에 패턴을 적용하세요
- faithfulness 평균 0.75 미만이 반복되는 카테고리는 수집 전략을 전환하세요 (arxiv↔web)

오류가 발생해도 나머지 아티클/토픽은 계속 처리하세요."""

MAX_ITERATIONS = 50  # 토픽 수 × 아티클 수 고려


def _mcp_tools_to_anthropic(mcp_tools) -> list[dict]:
    """FastMCP Tool 목록 → Anthropic tool 스키마 변환"""
    return [
        {
            "name":         t.name,
            "description":  t.description or "",
            "input_schema": t.inputSchema,
        }
        for t in mcp_tools
    ]


async def run_agent_pipeline(topics: list[dict] | None = None) -> dict:
    """
    Claude + MCP 에이전트 파이프라인 실행

    Args:
        topics: 지정 시 해당 토픽만 실행. None이면 DB에서 자동 조회.
    Returns:
        {run_id, total_contents, total_quizzes, total_failed}
    """
    logger = PipelineLogger()
    reset_session(logger)
    logger.start_run([t["name"] for t in topics] if topics else [])

    # 이전 실행 기록 조회 → 초반 user_message에 주입
    memory_context = await _get_recent_memory()

    if topics:
        topic_list = ", ".join(f"{t['name']}({t['category']})" for t in topics)
        user_message = (
            f"{memory_context}\n\n"
            f"다음 토픽으로 파이프라인을 실행하세요: {topic_list}"
        )
    else:
        user_message = f"{memory_context}\n\n오늘의 파이프라인을 실행하세요."

    messages = [{"role": "user", "content": user_message}]
    agent_summary = ""
    iteration = 0

    try:
        async with Client(mcp) as mcp_client:
            # MCP 서버에서 도구 목록 조회 → Anthropic 형식으로 변환
            anthropic_tools = _mcp_tools_to_anthropic(await mcp_client.list_tools())

            while iteration < MAX_ITERATIONS:
                iteration += 1

                response = await claude.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=anthropic_tools,
                    messages=messages,
                )

                _session["run_stats"]["tokens"]["claude_input"] += response.usage.input_tokens
                _session["run_stats"]["tokens"]["claude_output"] += response.usage.output_tokens

                # assistant 응답을 히스토리에 추가
                messages.append({"role": "assistant", "content": response.content})

                if response.stop_reason == "end_turn":
                    text_blocks = [b for b in response.content if b.type == "text"]
                    if text_blocks:
                        agent_summary = text_blocks[-1].text
                        print(f"\n[Agent 완료]\n{agent_summary}")
                    break

                if response.stop_reason != "tool_use":
                    break

                # Claude가 요청한 tool_use 블록 추출
                tool_blocks = [b for b in response.content if b.type == "tool_use"]
                print(f"\n[iteration {iteration}] 도구 {len(tool_blocks)}개 병렬 실행:")
                for b in tool_blocks:
                    print(f"  → {b.name}({json.dumps(b.input, ensure_ascii=False)[:80]})")

                # MCP 클라이언트로 병렬 실행 (Claude가 병렬 요청한 것을 실제로 동시에 처리)
                results = await asyncio.gather(
                    *[mcp_client.call_tool(b.name, b.input) for b in tool_blocks],
                    return_exceptions=True,
                )

                # 결과를 tool_result 형식으로 변환해 다음 메시지에 추가
                tool_results = []
                for block, result in zip(tool_blocks, results):
                    if isinstance(result, Exception):
                        content = json.dumps({"error": str(result)}, ensure_ascii=False)
                    else:
                        content = result.content[0].text if result.content else "{}"
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     content,
                    })

                messages.append({"role": "user", "content": tool_results})

        stats = _session["run_stats"].copy()
        tokens = stats["tokens"]
        cost_usd = round(
            tokens["claude_input"]  * _HAIKU_IN  +
            tokens["claude_output"] * _HAIKU_OUT +
            tokens["openai_input"]  * _GPT_IN    +
            tokens["openai_output"] * _GPT_OUT,
            6,
        )
        stats["cost_usd"] = cost_usd

        quality = stats.get("quality", {})
        faith_scores = quality.get("faithfulness_scores", [])
        avg_faith = round(sum(faith_scores) / len(faith_scores), 3) if faith_scores else 0

        # ── 스킵 추론: collect된 article 중 summary 없으면 Claude가 판단해 스킵 ──
        all_ids = set(_session["articles"].keys())
        summarized_ids = {k for k, v in _session["articles"].items() if "summary" in v}
        saved_ids = {k for k, v in _session["articles"].items() if v.get("quizzes")}
        agent_skipped = len(all_ids - summarized_ids)
        stats["skipped"] = {
            "by_agent":           agent_skipped,
            "by_faithfulness":    quality.get("faithfulness_failures", 0),
            "total_collected":    len(all_ids),
            "total_summarized":   len(summarized_ids),
            "total_saved":        len(saved_ids),
        }

        # ── 퀴즈 통과율 (전체 생성 대비 검증 통과) ──
        total_gen = stats.get("total_generated_quizzes", 0)
        total_ver = stats["total_quizzes"]
        stats["quiz_pass_rate"] = round(total_ver / total_gen, 3) if total_gen > 0 else 0
        stats["avg_faithfulness"] = avg_faith

        # ── run_quality 판정 (success / partial / failed) ──
        total_contents = stats["total_contents"]
        if total_contents == 0:
            run_quality = "failed"
        elif stats["total_failed"] > total_contents or agent_skipped > total_contents * 2:
            run_quality = "partial"
        else:
            run_quality = "success"
        stats["run_quality"] = run_quality

        print(
            f"\n[비용] Claude {tokens['claude_input']}in/{tokens['claude_output']}out | "
            f"GPT-4o-mini {tokens['openai_input']}in/{tokens['openai_output']}out | "
            f"총 ${cost_usd:.4f}"
        )
        print(
            f"[품질] 수집={len(all_ids)} 처리={len(summarized_ids)} 저장={total_contents} "
            f"agent스킵={agent_skipped} 퀴즈통과율={stats['quiz_pass_rate']:.0%} "
            f"faithfulness={avg_faith:.2f} → {run_quality}"
        )

        reflection_data = _session.get("reflection", {})
        # DB status 컬럼은 running/success/failed만 허용 — "partial"은 failed로 매핑
        db_status = run_quality if run_quality in ("success", "failed") else "failed"
        logger.finish_run(
            status=db_status,
            stats={
                **stats,
                "agent_summary": agent_summary,
                "iterations": iteration,
                "reflection": reflection_data.get("quality_assessment", ""),
                "next_run_suggestions": reflection_data.get("next_run_suggestions", []),
            },
        )

    except Exception as e:
        print(f"[Agent] 파이프라인 오류: {e}")
        logger.finish_run(status="failed", stats={"error": str(e)})
        raise

    return {**_session["run_stats"], "run_id": logger.run_id}
