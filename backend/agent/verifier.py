"""
STEP 4 — 퀴즈 교차 검증 (Cross-Model Verification) + 요약 충실도 검증
GPT-5가 생성한 퀴즈를 Claude Haiku가 재검증 — 동일 모델 blind spot 방지
"""

import os
import json
import anthropic

claude = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-haiku-4-5-20251001"

# ── 요약 충실도 검증 ────────────────────────────────────────────

FAITHFULNESS_PROMPT = """당신은 팩트체크 전문가입니다.
아래 [요약문]의 모든 주장이 [원문]에 근거하는지 엄격하게 검증하세요.

## FAITHFUL 조건 (모두 충족해야 함)
1. 요약문의 모든 주장을 원문에서 직접 근거를 찾을 수 있는가?
2. 원문에 없는 외부 지식이나 추론을 추가하지 않았는가?
3. 원문의 수치·사실을 왜곡하거나 과장하지 않았는가?

## FAIL 조건 (하나라도 해당하면 fail)
- 원문에 없는 사실, 수치, 이름이 등장함
- 원문의 결론과 반대되는 주장이 있음
- 원문에 없는 비교나 인과관계를 추가함

[원문] (앞부분)
{source_text}

[요약문]
{summary}

JSON으로만 응답:
{{"faithful": true or false, "score": 0.0~1.0, "issues": ["문제점1"] or []}}"""


async def check_faithfulness(summary: str, source_text: str) -> tuple[bool, float, list[str], dict]:
    """
    요약문이 원문에 충실한지 Claude Haiku로 검증.
    Returns: (is_faithful, score, issues, {"claude_input": N, "claude_output": N})
    """
    text_slice = source_text[:2000] + source_text[-500:] if len(source_text) > 2500 else source_text

    response = await claude.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": FAITHFULNESS_PROMPT.format(
                source_text=text_slice,
                summary=summary,
            )
        }]
    )

    usage = {
        "claude_input": response.usage.input_tokens,
        "claude_output": response.usage.output_tokens,
    }
    raw = response.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

    try:
        result = json.loads(raw)
        return result.get("faithful", False), result.get("score", 0.0), result.get("issues", []), usage
    except Exception:
        # 파싱 실패 → 보수적으로 충실도 낮음 처리
        return False, 0.0, ["파싱 오류"], usage


# ── 퀴즈 교차 검증 ─────────────────────────────────────────────

VERIFY_PROMPT = """당신은 퀴즈 품질 검증 전문가입니다.
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
{{"pass": true or false, "reason": "판단 근거 한 문장"}}"""


async def verify_quiz(quiz: dict, source_text: str) -> tuple[dict, dict]:
    """
    퀴즈 단건 검증 (Claude Haiku).
    Returns: (결과 dict, {"claude_input": N, "claude_output": N})
    """
    text = source_text[:1500] + source_text[-500:] if len(source_text) > 2000 else source_text

    response = await claude.messages.create(
        model=MODEL,
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

    usage = {
        "claude_input": response.usage.input_tokens,
        "claude_output": response.usage.output_tokens,
    }
    raw = response.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

    return json.loads(raw), usage  # 파싱 실패 시 호출자가 처리


async def verify_and_filter(quizzes: list[dict], source_text: str) -> tuple[list[dict], dict]:
    """
    퀴즈 목록 검증 후 PASS된 것만 반환 (Claude Haiku 교차검증).
    검증 오류/파싱 실패 시 해당 퀴즈는 탈락 (보수적 처리).
    Returns: (passed 목록, {"claude_input": N, "claude_output": N})
    """
    passed = []
    failed_count = 0
    total_claude_input = 0
    total_claude_output = 0

    for quiz in quizzes:
        try:
            result, usage = await verify_quiz(quiz, source_text)
            total_claude_input += usage["claude_input"]
            total_claude_output += usage["claude_output"]
            if result.get("pass"):
                quiz["verified"] = True
                passed.append(quiz)
                print(f"    [PASS] {quiz['concept']} — {result['reason']}")
            else:
                failed_count += 1
                print(f"    [FAIL] {quiz['concept']} — {result['reason']}")
        except Exception as e:
            failed_count += 1
            print(f"    [검증 오류-FAIL] {quiz.get('concept', '?')} — {e}")

    total = len(quizzes)
    pass_rate = len(passed) / total * 100 if total > 0 else 0
    print(f"    [검증 결과] {len(passed)}/{total} 통과 ({pass_rate:.0f}%)")

    return passed, {"claude_input": total_claude_input, "claude_output": total_claude_output}
