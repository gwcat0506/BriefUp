"""
OpenAI Tool Use 기반 에이전트 파이프라인
GPT가 도구를 직접 선택/호출하며 전체 파이프라인을 오케스트레이션
"""

import asyncio
import json
import os
from openai import AsyncOpenAI
from core.logger import PipelineLogger
from agent.mcp_tools import TOOL_SCHEMAS, get_active_topics, run_pipeline_for_topic

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """당신은 BrefUp 학습 콘텐츠 생성 에이전트입니다.

매일 새벽 5시에 실행되어 사용자들의 학습 콘텐츠를 자동으로 준비합니다.

작업 순서:
1. get_active_topics를 호출해 처리할 토픽 목록(name, category)을 확인합니다
2. 각 토픽에 대해 순서대로 run_pipeline_for_topic을 호출합니다
3. 모든 토픽 처리가 완료되면 결과를 한국어로 간략히 요약합니다

주의사항:
- 한 토픽에서 오류가 발생해도 나머지 토픽은 반드시 처리합니다
- 모든 토픽을 빠짐없이 처리한 후에만 종료합니다
"""

MAX_ITERATIONS = 20  # 무한 루프 방지


async def run_agent_pipeline(topics: list[dict] | None = None) -> dict:
    """
    Tool Use 에이전트 파이프라인 실행

    Args:
        topics: 지정 시 get_active_topics 없이 해당 토픽만 실행
                형식: [{"name": "RAG", "category": "AI/ML"}, ...]
    Returns:
        {run_id, total_contents, total_quizzes, total_failed}
    """
    logger = PipelineLogger()
    logger.start_run([t["name"] for t in topics] if topics else [])

    if topics:
        topic_list = ", ".join(f"{t['name']}({t['category']})" for t in topics)
        user_message = f"다음 토픽으로 파이프라인을 실행하세요: {topic_list}"
    else:
        user_message = "오늘의 파이프라인을 실행하세요."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    total_stats = {"total_contents": 0, "total_quizzes": 0, "total_failed": 0}
    iteration = 0

    try:
        while iteration < MAX_ITERATIONS:
            iteration += 1

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                messages=messages,
            )

            msg = response.choices[0].message
            messages.append(msg)

            # 도구 호출 없이 텍스트 응답 → 에이전트 완료
            if not msg.tool_calls:
                if msg.content:
                    print(f"\n[Agent 완료]\n{msg.content}")
                break

            # 도구 실행
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")

                print(f"[Agent] {name}({', '.join(f'{k}={v}' for k, v in args.items())})")

                try:
                    if name == "get_active_topics":
                        result = await get_active_topics()

                    elif name == "run_pipeline_for_topic":
                        result = await run_pipeline_for_topic(
                            args["topic_name"], args["category"], logger
                        )
                        total_stats["total_contents"] += result.get("contents_saved", 0)
                        total_stats["total_quizzes"] += result.get("quizzes_saved", 0)
                        total_stats["total_failed"] += result.get("failed", 0)

                    else:
                        result = {"error": f"알 수 없는 도구: {name}"}

                except Exception as e:
                    result = {"error": str(e)}
                    print(f"[Agent] 도구 오류 ({name}): {e}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        logger.finish_run(status="success", stats=total_stats)

    except Exception as e:
        print(f"[Agent] 파이프라인 오류: {e}")
        logger.finish_run(status="failed", stats={"error": str(e)})
        raise

    total_stats["run_id"] = logger.run_id
    return total_stats
