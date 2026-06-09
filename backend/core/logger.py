"""
파이프라인 실행 로거
Supabase pipeline_runs / pipeline_logs 테이블에 기록
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from core.supabase import supabase


class PipelineLogger:
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or str(uuid.uuid4())
        self._step_order = 0

    def start_run(self, categories: list[str]) -> None:
        """pipeline_runs 테이블에 실행 시작 기록"""
        try:
            supabase.table("pipeline_runs").insert({
                "id": self.run_id,
                "categories": categories,
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
            print(f"[Logger] run 시작 — run_id: {self.run_id}")
        except Exception as e:
            print(f"[Logger] run 시작 기록 실패: {e}")

    def log_step(
        self,
        tool_name: str,
        inputs: dict,
        output: Any = None,
        duration_ms: int = 0,
        status: str = "success",
        error_message: Optional[str] = None,
        category: str = "",
        failure_type: Optional[str] = None,
        parent_step_order: Optional[int] = None,
    ) -> int:
        """pipeline_logs 테이블에 단계별 실행 기록

        failure_type: "technical" | "policy_rejected" | "quality_rejected" | "not_found"
          - technical: API 오류, 네트워크 등 기술적 실패
          - policy_rejected: 검증 기준 미달 (퀴즈 verified=0 등)
          - quality_rejected: 품질 낮아 수집 결과 없음
          - not_found: article_id 등 참조 대상 없음
        parent_step_order: 부모 스텝 번호 (계층 추적용)

        주의: inputs/output에 원문 텍스트 포함 금지 (메타데이터만 기록)
        """
        self._step_order += 1
        current_order = self._step_order
        output_data = dict(output) if output else {}
        if failure_type:
            output_data["failure_type"] = failure_type
        if parent_step_order is not None:
            output_data["parent_step_order"] = parent_step_order
        try:
            supabase.table("pipeline_logs").insert({
                "run_id": self.run_id,
                "step_order": current_order,
                "tool_name": tool_name,
                "category": category,
                "inputs": inputs,
                "output": output_data,
                "duration_ms": duration_ms,
                "status": status,
                "error_message": error_message,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            # 로깅 실패가 파이프라인을 중단시키면 안 됨
            print(f"[Logger] 스텝 기록 실패 ({tool_name}): {e}")
        return current_order

    def finish_run(self, status: str = "success", stats: Optional[dict] = None) -> None:
        """pipeline_runs 테이블에 실행 완료 기록"""
        try:
            supabase.table("pipeline_runs").update({
                "status": status,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "stats": stats or {},
            }).eq("id", self.run_id).execute()
            print(f"[Logger] run 완료 — status: {status}, stats: {stats}")
        except Exception as e:
            print(f"[Logger] run 완료 기록 실패: {e}")
