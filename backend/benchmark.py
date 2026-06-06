"""
퀴즈 정확도 벤치마크 테스트
실행: python benchmark.py

수집 → 요약 → 퀴즈생성 → 검증 전체 파이프라인을
소규모로 실행하고 품질 지표를 측정합니다.

목표:
- 퀴즈 검증 통과율: 90% 이상
- 수집 필터 통과율: 30~60% (너무 낮으면 소스 문제)
"""

import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from agent.collector import collect_for_category
from agent.summarizer import summarize
from agent.quiz_gen import generate_quizzes
from agent.verifier import verify_and_filter


async def run_benchmark(category: str = "AI/ML", max_items: int = 3):
    print(f"\n{'='*60}")
    print(f"  BrefUp 퀴즈 벤치마크 — 카테고리: {category}")
    print(f"{'='*60}")

    stats = {
        "collected": 0,
        "quizzes_generated": 0,
        "quizzes_passed": 0,
        "quizzes_failed": 0,
        "errors": 0,
        "samples": []
    }

    # STEP 1: 수집
    print("\n[STEP 1] 콘텐츠 수집")
    contents = await collect_for_category(category)
    stats["collected"] = len(contents)

    if not contents:
        print("수집된 콘텐츠 없음. 소스 확인 필요.")
        return

    # STEP 2~4: 항목별 처리
    for i, raw in enumerate(contents[:max_items]):
        print(f"\n--- 항목 {i+1}/{min(len(contents), max_items)} ---")
        print(f"제목: {raw['title'][:60]}")
        print(f"출처: {raw.get('source', 'unknown')}")
        print(f"본문 길이: {len(raw['text'])}자")

        try:
            # 요약
            print("\n[요약 생성 중...]")
            summary = await summarize(raw["title"], raw["text"], category)
            print(f"요약: {summary[:150]}...")

            # 퀴즈 생성
            print("\n[퀴즈 생성 중...]")
            quizzes = await generate_quizzes(raw["title"], raw["text"], category)
            stats["quizzes_generated"] += len(quizzes)
            print(f"생성된 퀴즈: {len(quizzes)}개")

            # 검증
            print("\n[퀴즈 검증 중...]")
            passed = await verify_and_filter(quizzes, raw["text"])
            stats["quizzes_passed"] += len(passed)
            stats["quizzes_failed"] += len(quizzes) - len(passed)

            # 샘플 저장
            for q in passed[:1]:
                stats["samples"].append({
                    "source_title": raw["title"],
                    "question": q["question"],
                    "answer": q["answer"],
                    "concept": q["concept"],
                    "difficulty": q.get("difficulty", 1),
                    "verified": q.get("verified", False)
                })

        except Exception as e:
            print(f"오류: {e}")
            stats["errors"] += 1

    # 결과 리포트
    _print_benchmark_report(stats, category)


def _print_benchmark_report(stats: dict, category: str):
    total_gen = stats["quizzes_generated"]
    total_pass = stats["quizzes_passed"]
    pass_rate = (total_pass / total_gen * 100) if total_gen > 0 else 0

    print(f"\n{'='*60}")
    print(f"  벤치마크 결과 — {category}")
    print(f"{'='*60}")
    print(f"  수집된 콘텐츠:     {stats['collected']}개")
    print(f"  생성된 퀴즈:       {total_gen}개")
    print(f"  검증 통과 (PASS):  {total_pass}개")
    print(f"  검증 실패 (FAIL):  {stats['quizzes_failed']}개")
    print(f"  오류:              {stats['errors']}개")
    print(f"  통과율:            {pass_rate:.1f}%  {'✅ 목표 달성' if pass_rate >= 90 else '⚠️  90% 미달'}")

    if stats["samples"]:
        print(f"\n  [샘플 퀴즈]")
        for s in stats["samples"][:2]:
            print(f"  출처: {s['source_title'][:40]}")
            print(f"  문제: {s['question']}")
            print(f"  정답: {s['answer']}번  |  개념: {s['concept']}  |  난이도: {s['difficulty']}")
            print()

    print(f"{'='*60}")

    # JSON 저장
    with open("benchmark_result.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"  결과 저장: benchmark_result.json")


if __name__ == "__main__":
    import sys
    category = sys.argv[1] if len(sys.argv) > 1 else "AI/ML"
    asyncio.run(run_benchmark(category=category, max_items=3))
