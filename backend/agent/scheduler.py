"""
STEP 5 — 스케줄러 & 저장
매일 새벽 5시 전체 파이프라인 실행
STEP1(수집) → STEP2(요약) → STEP3(퀴즈생성) → STEP4(검증) → STEP5(저장)
"""

from datetime import date
from agent.collector import collect_for_category, SOURCES
from agent.summarizer import summarize
from agent.quiz_gen import generate_quizzes
from agent.verifier import verify_and_filter
from core.supabase import supabase


async def run_daily_pipeline(categories: list[str] | None = None):
    """
    전체 파이프라인 실행
    categories: None이면 DB에서 활성 유저 관심사 자동 감지
    """
    today = date.today().isoformat()
    print(f"\n{'='*50}")
    print(f"[파이프라인 시작] {today}")
    print(f"{'='*50}")

    # 실행할 카테고리 결정
    if not categories:
        topics = supabase.table("topics").select("category").eq("is_active", True).execute()
        categories = list(set([t["category"] for t in topics.data]))
    if not categories:
        categories = ["AI/ML"]  # 기본값

    report = {
        "date": today,
        "categories": {},
        "total_contents": 0,
        "total_quizzes": 0,
        "total_failed": 0,
    }

    for category in categories:
        print(f"\n[카테고리: {category}]")
        cat_report = {"contents": 0, "quizzes": 0, "failed": 0}

        # ── STEP 1: 수집 ──────────────────────────────
        print("  STEP 1. 콘텐츠 수집 중...")
        try:
            raw_contents = await collect_for_category(category)
        except Exception as e:
            print(f"  [수집 실패] {e}")
            continue

        # ── STEP 2~4: 항목별 요약 + 퀴즈 + 검증 ──────
        for raw in raw_contents:
            print(f"\n  처리 중: {raw['title'][:50]}...")
            try:
                # STEP 2: 요약
                print("  STEP 2. 요약 생성 중...")
                summary = await summarize(raw["title"], raw["text"], category)

                # STEP 3: 퀴즈 생성
                print("  STEP 3. 퀴즈 생성 중...")
                quizzes = await generate_quizzes(raw["title"], raw["text"], category)
                if not quizzes:
                    print("  [스킵] 퀴즈 생성 실패")
                    cat_report["failed"] += 1
                    continue

                # STEP 4: 검증
                print("  STEP 4. 퀴즈 검증 중...")
                verified_quizzes = await verify_and_filter(quizzes, raw["text"])
                if not verified_quizzes:
                    print("  [스킵] 검증 통과 퀴즈 없음")
                    cat_report["failed"] += 1
                    continue

                # STEP 5: 저장
                print("  STEP 5. DB 저장 중...")
                content_id = _save_content(raw, summary, category)
                quiz_count = _save_quizzes(verified_quizzes, content_id)

                cat_report["contents"] += 1
                cat_report["quizzes"] += quiz_count
                print(f"  ✅ 완료 — 퀴즈 {quiz_count}개 저장")

            except Exception as e:
                print(f"  ❌ 오류: {e}")
                cat_report["failed"] += 1

        report["categories"][category] = cat_report
        report["total_contents"] += cat_report["contents"]
        report["total_quizzes"] += cat_report["quizzes"]
        report["total_failed"] += cat_report["failed"]

    # 파이프라인 리포트 출력
    _print_report(report)
    return report


def _save_content(raw: dict, summary: str, category: str) -> str:
    """콘텐츠 저장 후 ID 반환"""
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
    """퀴즈 저장 후 저장 개수 반환"""
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


def _print_report(report: dict):
    print(f"\n{'='*50}")
    print(f"[파이프라인 완료] {report['date']}")
    print(f"  총 콘텐츠: {report['total_contents']}개")
    print(f"  총 퀴즈:   {report['total_quizzes']}개")
    print(f"  실패:      {report['total_failed']}개")
    for cat, r in report["categories"].items():
        print(f"  [{cat}] 콘텐츠 {r['contents']}개, 퀴즈 {r['quizzes']}개")
    print(f"{'='*50}\n")
