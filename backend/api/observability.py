"""
파이프라인 관측 API
실행 이력, 단계 로그, 품질 지표 조회
"""

import asyncio
from fastapi import APIRouter, HTTPException
from core.supabase import supabase

router = APIRouter()


@router.get("/runs")
async def list_runs(limit: int = 20):
    """최근 파이프라인 실행 목록 + 품질 요약"""
    try:
        res = await asyncio.to_thread(
            lambda: supabase.table("pipeline_runs")
                .select("id, status, categories, started_at, finished_at, stats")
                .order("started_at", desc=True)
                .limit(limit)
                .execute()
        )
        runs = []
        for row in (res.data or []):
            stats = row.get("stats") or {}
            skipped = stats.get("skipped", {})
            runs.append({
                "run_id":          row["id"],
                "status":          row["status"],
                "categories":      row.get("categories", []),
                "started_at":      row["started_at"],
                "finished_at":     row.get("finished_at"),
                "iterations":      stats.get("iterations"),
                "total_contents":  stats.get("total_contents", 0),
                "total_quizzes":   stats.get("total_quizzes", 0),
                "total_failed":    stats.get("total_failed", 0),
                "run_quality":     stats.get("run_quality", row["status"]),
                "quiz_pass_rate":  stats.get("quiz_pass_rate"),
                "avg_faithfulness": stats.get("avg_faithfulness"),
                "cost_usd":        stats.get("cost_usd"),
                "skipped": {
                    "by_agent":        skipped.get("by_agent", 0),
                    "by_faithfulness": skipped.get("by_faithfulness", 0),
                    "total_collected": skipped.get("total_collected", 0),
                    "total_saved":     skipped.get("total_saved", 0),
                },
            })
        return {"runs": runs, "count": len(runs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}")
async def get_run_detail(run_id: str):
    """특정 실행의 단계 로그 + 실패 유형 분석"""
    try:
        run_res, logs_res = await asyncio.gather(
            asyncio.to_thread(
                lambda: supabase.table("pipeline_runs")
                    .select("*")
                    .eq("id", run_id)
                    .single()
                    .execute()
            ),
            asyncio.to_thread(
                lambda: supabase.table("pipeline_logs")
                    .select("step_order, tool_name, category, status, duration_ms, error_message, output, inputs")
                    .eq("run_id", run_id)
                    .order("step_order")
                    .execute()
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not run_res.data:
        raise HTTPException(status_code=404, detail="run not found")

    logs = logs_res.data or []

    # 실패 유형별 집계
    failure_counts: dict[str, int] = {}
    for log in logs:
        output = log.get("output") or {}
        ft = output.get("failure_type")
        if ft:
            failure_counts[ft] = failure_counts.get(ft, 0) + 1

    # 계층 구조: parent_step_order 기준으로 자식 스텝 연결
    step_map = {log["step_order"]: log for log in logs}
    for log in logs:
        output = log.get("output") or {}
        parent_order = output.get("parent_step_order")
        if parent_order and parent_order in step_map:
            parent = step_map[parent_order]
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(log["step_order"])

    return {
        "run": run_res.data,
        "steps": logs,
        "failure_analysis": {
            "counts": failure_counts,
            "total_steps": len(logs),
            "failed_steps": sum(1 for l in logs if l["status"] == "failed"),
        },
    }


@router.get("/runs/{run_id}/failures")
async def get_run_failures(run_id: str):
    """실패한 스텝만 필터링 — 실패 유형별 그룹화"""
    try:
        res = await asyncio.to_thread(
            lambda: supabase.table("pipeline_logs")
                .select("step_order, tool_name, category, error_message, output, duration_ms")
                .eq("run_id", run_id)
                .eq("status", "failed")
                .order("step_order")
                .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    failures = res.data or []
    grouped: dict[str, list] = {}
    for f in failures:
        ft = (f.get("output") or {}).get("failure_type", "unknown")
        grouped.setdefault(ft, []).append({
            "step_order":    f["step_order"],
            "tool_name":     f["tool_name"],
            "category":      f["category"],
            "error_message": f["error_message"],
            "duration_ms":   f["duration_ms"],
        })

    return {"run_id": run_id, "by_failure_type": grouped, "total": len(failures)}
