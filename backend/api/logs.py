"""
파이프라인 로그 관리 API
pipeline_runs / pipeline_logs 테이블 조회 및 관리
"""

from fastapi import APIRouter, HTTPException
from core.supabase import supabase

router = APIRouter()


@router.get("/runs")
def list_runs(limit: int = 20, status: str = None):
    """파이프라인 실행 목록 조회 (최신순)"""
    query = (
        supabase.table("pipeline_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
    )
    if status:
        query = query.eq("status", status)
    return query.execute().data


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    """특정 run 상세 조회 — 단계별 로그 포함"""
    run_res = supabase.table("pipeline_runs").select("*").eq("id", run_id).execute()
    if not run_res.data:
        raise HTTPException(status_code=404, detail="Run을 찾을 수 없습니다")

    steps_res = (
        supabase.table("pipeline_logs")
        .select("*")
        .eq("run_id", run_id)
        .order("step_order")
        .execute()
    )
    return {"run": run_res.data[0], "steps": steps_res.data}


@router.get("/runs/{run_id}/steps")
def get_run_steps(run_id: str, tool_name: str = None, status: str = None):
    """특정 run의 스텝 목록 — tool_name, status로 필터 가능"""
    query = (
        supabase.table("pipeline_logs")
        .select("*")
        .eq("run_id", run_id)
        .order("step_order")
    )
    if tool_name:
        query = query.eq("tool_name", tool_name)
    if status:
        query = query.eq("status", status)
    return query.execute().data


@router.delete("/runs/{run_id}")
def delete_run(run_id: str):
    """run 및 연관 로그 삭제 (DB cascade 적용 시 자동 삭제)"""
    supabase.table("pipeline_runs").delete().eq("id", run_id).execute()
    return {"deleted": run_id}


@router.get("/stats")
def get_stats(limit: int = 7):
    """최근 N개 run 통계 요약"""
    runs = (
        supabase.table("pipeline_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    total = len(runs)
    success = sum(1 for r in runs if r["status"] == "success")
    total_contents = sum(r.get("stats", {}).get("total_contents", 0) for r in runs)
    total_quizzes = sum(r.get("stats", {}).get("total_quizzes", 0) for r in runs)

    return {
        "runs_count": total,
        "success_rate": round(success / total * 100, 1) if total else 0,
        "total_contents_generated": total_contents,
        "total_quizzes_generated": total_quizzes,
        "recent_runs": runs,
    }
