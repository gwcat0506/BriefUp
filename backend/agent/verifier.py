"""
STEP 4 — 퀴즈 자체 검증 (Self-Verification)
GPT가 생성한 퀴즈를 원문 기준으로 재검증
목표 정확도: 95%+
"""

from openai import AsyncOpenAI
import os
import json

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VERIFY_PROMPT = """
당신은 퀴즈 품질 검증 전문가입니다.
아래 [퀴즈]를 [원문] 기준으로 엄격하게 검증하세요.

## PASS 조건 (모두 충족해야 함)
1. 정답이 원문에서 명확히 근거를 찾을 수 있는가?
2. 오답 보기들이 그럴 듯하지만 원문 기준으로 틀린 내용인가? (명백히 틀린 보기는 감점)
3. 해설이 원문 내용과 일치하며 오답 이유도 설명하는가?
4. 문제가 명확하고 모호하지 않은가?
5. 단순 정의·이름 암기 문제가 아닌가? ("이 개념의 이름은?", "~란 무엇인가?" 형식은 FAIL)

## FAIL 조건 (하나라도 해당하면 FAIL)
- 정답 근거를 원문에서 찾을 수 없음
- 오답 보기 중 명백히 말이 안 되는 것이 포함됨 (함정이 너무 쉬움)
- "~의 이름은?", "~를 무엇이라 하는가?" 같은 단순 정의 암기 문제
- 보기 4개 중 실질적으로 구분이 안 되는 보기가 있음

[원문]
{source_text}

[퀴즈] (difficulty: {difficulty})
문제: {question}
보기: {options}
정답: {answer}
해설: {explanation}

JSON으로만 응답:
{{"pass": true or false, "reason": "판단 근거 한 문장"}}
"""


async def verify_quiz(quiz: dict, source_text: str) -> tuple[dict, dict]:
    """퀴즈 단건 검증. (결과 dict, {input, output} 토큰) 반환. JSON 파싱 실패 시 예외를 올린다."""
    # 원문 앞뒤를 고르게 사용해 긴 원문에서도 검증 품질 유지
    text = source_text[:1500] + source_text[-500:] if len(source_text) > 2000 else source_text

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": VERIFY_PROMPT.format(
                source_text=text,
                question=quiz["question"],
                options=json.dumps(quiz["options"], ensure_ascii=False),
                answer=quiz["answer"],
                explanation=quiz["explanation"],
                difficulty=quiz.get("difficulty", 1),
            )
        }]
    )

    usage = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}
    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

    return json.loads(raw), usage  # 파싱 실패 시 호출자가 처리


async def verify_and_filter(quizzes: list[dict], source_text: str) -> tuple[list[dict], dict]:
    """
    퀴즈 목록 검증 후 PASS된 것만 반환.
    검증 API 오류/파싱 실패 시 해당 퀴즈는 보수적으로 탈락 처리한다.
    (passed 목록, 누적 {input, output} 토큰) 반환.
    """
    passed = []
    failed_count = 0
    total_input = 0
    total_output = 0

    for quiz in quizzes:
        try:
            result, usage = await verify_quiz(quiz, source_text)
            total_input += usage["input"]
            total_output += usage["output"]
            if result.get("pass"):
                quiz["verified"] = True
                passed.append(quiz)
                print(f"    [PASS] {quiz['concept']} — {result['reason']}")
            else:
                failed_count += 1
                print(f"    [FAIL] {quiz['concept']} — {result['reason']}")
        except Exception as e:
            # 파싱/API 오류 → 불확실하므로 탈락 (silent pass 금지)
            failed_count += 1
            print(f"    [검증 오류-FAIL] {quiz.get('concept', '?')} — {e}")

    total = len(quizzes)
    pass_rate = len(passed) / total * 100 if total > 0 else 0
    print(f"    [검증 결과] {len(passed)}/{total} 통과 ({pass_rate:.0f}%)")

    return passed, {"input": total_input, "output": total_output}
