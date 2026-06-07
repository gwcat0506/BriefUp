"""
스케줄러 — 매일 새벽 5시 에이전트 파이프라인 실행
agent_runner.run_agent_pipeline()으로 위임
"""

async def run_daily_pipeline(topics: list[dict] | None = None):
    """
    전체 파이프라인 실행 (에이전트 방식)
    topics: None이면 에이전트가 DB에서 활성 토픽 자동 감지
            형식: [{"name": "RAG", "category": "AI/ML"}, ...]
    """
    from agent.agent_runner import run_agent_pipeline
    return await run_agent_pipeline(topics=topics)
