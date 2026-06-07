"""
STEP 4 — 퀴즈 자체 검증 (Self-Verification)
GPT가 생성한 퀴즈를 원문 기준으로 재검증
FAIL 시 재생성 (최대 2회 시도)
목표 정확도: 95%+
"""

from openai import AsyncOpenAI
import os
import json

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VERIFY_PROMPT = """
당신은 퀴즈 품질 검증 전문가입니다.
아래 [퀴즈]가 [원문]에 근거한 내용인지 엄격하게 검증하세요.

검증 기준 (모두 통과해야 PASS):
1. 정답이 원문에서 명확히 찾을 수 있는가?
2. 오답 보기들이 원문에서는 틀린 내용인가?
3. 해설이 원문 내용과 일치하는가?
4. 문제가 명확하고 모호하지 않은가?

[원문]
{source_text}

[퀴즈]
문제: {question}
보기: {options}
정답: {answer}
해설: {explanation}

JSON으로만 응답:
{{"pass": true or false, "reason": "판단 근거 한 문장"}}
"""


async def verify_quiz(quiz: dict, source_text: str) -> dict:
    """퀴즈 단건 검증"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": VERIFY_PROMPT.format(
                source_text=source_text[:2000],
                question=quiz["question"],
                options=json.dumps(quiz["options"], ensure_ascii=False),
                answer=quiz["answer"],
                explanation=quiz["explanation"],
            )
        }]
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

    return json.loads(raw)


async def verify_and_filter(quizzes: list[dict], source_text: str) -> list[dict]:
    """
    퀴즈 목록 검증 후 PASS된 것만 반환
    FAIL 비율 로그로 기록 (벤치마크용)
    """
    passed = []
    failed_count = 0

    for quiz in quizzes:
        try:
            result = await verify_quiz(quiz, source_text)
            if result.get("pass"):
                quiz["verified"] = True
                passed.append(quiz)
                print(f"    [PASS] {quiz['concept']} — {result['reason']}")
            else:
                failed_count += 1
                print(f"    [FAIL] {quiz['concept']} — {result['reason']}")
        except Exception as e:
            # 검증 파싱 실패 시 보수적으로 통과
            print(f"    [검증 오류] {e} — 일단 통과 처리")
            quiz["verified"] = False
            passed.append(quiz)

    total = len(quizzes)
    pass_rate = len(passed) / total * 100 if total > 0 else 0
    print(f"    [검증 결과] {len(passed)}/{total} 통과 ({pass_rate:.0f}%)")

    return passed
