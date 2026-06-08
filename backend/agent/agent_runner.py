"""
Anthropic Claude + FastMCP 에이전트
MCP 서버에서 도구 목록을 가져와 Claude가 자율적으로 실행
"""

import asyncio
import json
import os

import anthropic
from fastmcp import Client

from core.logger import PipelineLogger
from agent.mcp_server import mcp, _session, reset_session

claude = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-haiku-4-5-20251001"

# 가격 (per token) — Claude Haiku 4.5, GPT-4o-mini
_HAIKU_IN  = 1.00 / 1_000_000
_HAIKU_OUT = 5.00 / 1_000_000
_GPT_IN    = 0.15 / 1_000_000
_GPT_OUT   = 0.60 / 1_000_000

SYSTEM_PROMPT = """당신은 BrefUp 콘텐츠 큐레이터 에이전트입니다.

목표: 커리큘럼 기반으로 오늘의 학습 콘텐츠를 수집·요약·퀴즈 생성·저장합니다.

## 처리 순서 (중요)
1. get_active_topics — 활성 토픽 목록 조회
2. 모든 토픽의 get_collection_plan 동시 호출 — 오늘 다룰 챕터 + 검색 힌트 확인
3. 모든 토픽의 collect_articles 동시 호출
   - get_collection_plan의 today_chapter.search_hints를 반드시 사용하세요
   - search_hints.arxiv_query → arxiv_query 인자
   - search_hints.web_query → web_query 인자
   - search_hints가 없으면 챕터 title과 concepts를 보고 직접 영문 쿼리를 작성하세요
   - 쿼리는 반드시 영문으로 작성하세요 (한국어 토픽명을 영어로 변환)
4. 아티클별: summarize_article → generate_quizzes → save_content
5. 전체 완료 후 처리 결과를 한국어로 요약하고 종료

## 쿼리 작성 예시
- "양자컴퓨팅" / 챕터 "큐비트란 무엇인가?" → arxiv_query: "qubit quantum computing basics", web_query: "what is qubit quantum computing explained"
- "철학" / 챕터 "실존주의" → arxiv_query: null, web_query: "existentialism Sartre Heidegger introduction"
- "주식/투자" / 챕터 "가치 투자" → arxiv_query: "value investing portfolio returns study", web_query: "value investing Warren Buffett principles"

## 자율 판단 권한
- collect_articles 결과의 title/source/text_length를 보고 품질이 낮거나
  챕터 주제와 관련 없는 아티클은 건너뛰어도 됩니다
- summarize_article 실패(success=false) 시 해당 아티클은 건너뛰세요
- generate_quizzes 결과의 verified_count가 0이면 save_content를 호출하지 마세요
- 수집 아티클이 없는 토픽은 기록하고 다음 토픽으로 넘어가세요

## 병렬 실행 (중요)
- 여러 토픽의 get_collection_plan, collect_articles를 한 응답에서 동시에 호출할 수 있습니다
- 같은 토픽 내 서로 다른 아티클의 summarize_article을 동시에 호출할 수 있습니다
- 같은 아티클 내에서는 summarize_article → generate_quizzes → save_content 순서를 지키세요

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

    if topics:
        topic_list = ", ".join(f"{t['name']}({t['category']})" for t in topics)
        user_message = f"다음 토픽으로 파이프라인을 실행하세요: {topic_list}"
    else:
        user_message = "오늘의 파이프라인을 실행하세요."

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
        print(
            f"\n[비용] Claude {tokens['claude_input']}in/{tokens['claude_output']}out | "
            f"OpenAI {tokens['openai_input']}in/{tokens['openai_output']}out | "
            f"총 ${cost_usd:.4f}"
        )

        status = "success" if stats["total_contents"] > 0 else "failed"
        logger.finish_run(
            status=status,
            stats={**stats, "agent_summary": agent_summary, "iterations": iteration},
        )

    except Exception as e:
        print(f"[Agent] 파이프라인 오류: {e}")
        logger.finish_run(status="failed", stats={"error": str(e)})
        raise

    return {**_session["run_stats"], "run_id": logger.run_id}
