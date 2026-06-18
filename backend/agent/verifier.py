"""
STEP 4 — 퀴즈 교차 검증 (Cross-Model Verification) + 요약 faithfulness 검증
GPT-4o-mini가 생성한 퀴즈를 Claude Haiku가 재검증 — 동일 모델 blind spot 방지
"""

import os
import json
import anthropic
from core.config import CLAUDE_HAIKU_MODEL as MODEL
from core.utils import extract_json as _extract_json

claude = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── 요약 faithfulness 검증 ────────────────────────────────────────────

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

[원문]
"""

FAITHFULNESS_PROMPT_SUFFIX = """

[요약문]
"""

FAITHFULNESS_PROMPT_END = """

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 금지):
{"faithful": true or false, "score": 0.0~1.0, "issues": ["문제점"] or []}"""


async def check_faithfulness(summary: str, source_text: str) -> tuple[bool, float, list[str], dict]:
    """
    요약문이 원문에 충실한지 Claude Haiku로 검증.
    Returns: (is_faithful, score, issues, {"claude_input": N, "claude_output": N})
    """
    # 앞부분 + 뒷부분 슬라이스 (구분자 추가)
    if len(source_text) > 2500:
        text_slice = source_text[:2000] + "\n...(중략)...\n" + source_text[-400:]
    else:
        text_slice = source_text

    # .format() 대신 직접 연결 — source_text 내 {중괄호}로 인한 KeyError 방지
    prompt = FAITHFULNESS_PROMPT + text_slice + FAITHFULNESS_PROMPT_SUFFIX + summary + FAITHFULNESS_PROMPT_END

    for attempt in range(2):
        try:
            response = await claude.messages.create(
                model=MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            usage = {
                "claude_input": response.usage.input_tokens,
                "claude_output": response.usage.output_tokens,
            }
            raw = response.content[0].text.strip()
            result = _extract_json(raw)
            if result is not None:
                return (
                    result.get("faithful", False),
                    float(result.get("score", 0.0)),
                    result.get("issues", []),
                    usage,
                )
            # 파싱 실패 시 2차 시도: 더 짧은 원문으로 재요청
            if attempt == 0:
                text_slice = source_text[:800]
                prompt = FAITHFULNESS_PROMPT + text_slice + FAITHFULNESS_PROMPT_SUFFIX + summary + FAITHFULNESS_PROMPT_END
        except Exception as e:
            if attempt == 1:
                return False, 0.0, [f"검증 오류: {e}"], {"claude_input": 0, "claude_output": 0}

    return False, 0.0, ["파싱 오류"], {"claude_input": 0, "claude_output": 0}


# ── 퀴즈 교차 검증 ─────────────────────────────────────────────

VERIFY_PROMPT_HEAD = """당신은 퀴즈 품질 검증 전문가입니다.
아래 [퀴즈]를 [원문] 기준으로 검증하세요.

## PASS 조건 (모두 충족해야 함)
1. 정답의 근거가 원문에 있는가?
2. 오답 보기들이 그럴 듯하지만 원문 기준으로 틀린 내용인가?
3. 해설이 원문 내용과 일치하는가?
4. 문제가 명확하고 이해 가능한가?

## FAIL 조건 (하나라도 해당하면 FAIL)
- 정답 근거를 원문에서 찾을 수 없음
- 오답 보기 중 상식적으로 전혀 말이 안 되는 것이 포함됨 (누구나 바로 틀렸다고 알 수 있는 수준)
- 해설이 원문과 반대되는 내용을 포함함

[원문]
"""

VERIFY_PROMPT_END = """

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 금지):
{"pass": true or false, "reason": "판단 근거 한 문장"}"""


async def verify_quiz(quiz: dict, source_text: str) -> tuple[dict, dict]:
    """
    퀴즈 단건 검증 (Claude Haiku).
    Returns: (결과 dict, {"claude_input": N, "claude_output": N})
    """
    text = source_text[:1500] + "\n...(중략)...\n" + source_text[-300:] if len(source_text) > 1800 else source_text

    quiz_section = (
        f"\n[퀴즈] (difficulty: {quiz.get('difficulty', 1)})\n"
        f"문제: {quiz['question']}\n"
        f"보기: {json.dumps(quiz['options'], ensure_ascii=False)}\n"
        f"정답: {quiz['answer']}\n"
        f"해설: {quiz['explanation']}"
    )
    prompt = VERIFY_PROMPT_HEAD + text + quiz_section + VERIFY_PROMPT_END

    for attempt in range(2):
        response = await claude.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = {
            "claude_input": response.usage.input_tokens,
            "claude_output": response.usage.output_tokens,
        }
        raw = response.content[0].text.strip()
        result = _extract_json(raw)
        if result is not None:
            return result, usage
        if attempt == 0:
            # 짧은 원문으로 재시도
            text = source_text[:600]
            quiz_section_short = (
                f"\n[퀴즈]\n문제: {quiz['question']}\n"
                f"보기: {json.dumps(quiz['options'], ensure_ascii=False)}\n"
                f"정답: {quiz['answer']}"
            )
            prompt = VERIFY_PROMPT_HEAD + text + quiz_section_short + VERIFY_PROMPT_END

    raise ValueError(f"퀴즈 검증 JSON 파싱 실패 (2회 시도): {raw[:100]}")


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
