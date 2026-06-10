"""
STEP 3 — 퀴즈 생성
소스 본문 기반으로만 생성 → 할루시네이션 최소화
GPT-5 사용
"""

from openai import AsyncOpenAI
import os
import json

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

QUIZ_PROMPT = """당신은 {category} 분야의 전문가이자 교육자입니다.
아래 [원문]을 바탕으로 난이도가 다른 퀴즈 3개를 만드세요.

## 난이도별 기준 (엄격하게 구분)

**difficulty 1 — 개념 이해**
- 이 개념이 왜 존재하는지, 어떤 문제를 해결하는지 묻는 문제
- 단순 정의 암기 ❌ → 개념의 본질을 이해했는지 확인 ✅
- 예: "RAG가 Fine-tuning보다 유리한 상황은 언제인가?"

**difficulty 2 — 원인·비교·선택**
- 두 개념의 차이, 어떤 상황에서 무엇을 선택하는지 묻는 문제
- 보기는 "비슷해 보이지만 다른" 함정 보기 포함
- 예: "청크 크기를 줄이면 검색 정밀도는 올라가지만 어떤 부작용이 생기는가?"

**difficulty 3 — 실제 적용·트레이드오프**
- 현실 상황에서 어떻게 판단하는지, 어떤 결과가 생기는지 묻는 문제
- "현업 엔지니어라면 이 상황에서 어떤 선택을 하겠는가?" 수준
- 예: "RAG 시스템에서 응답 속도를 높이려 할 때 가장 먼저 검토해야 할 것은?"

## 공통 원칙
- 원문에 있는 내용만 사용 (없는 내용 추가 금지)
- 오답 보기는 그럴 듯하지만 틀린 것으로 구성 (명백히 틀린 보기 ❌)
- 해설은 왜 정답인지 + 왜 나머지가 오답인지 핵심만 설명
- 한국어 작성, 전문용어는 영어 병기 가능

[원문 제목]
{title}

[원문 내용]
{text}

JSON 형식으로만 응답:
{{
  "quizzes": [
    {{
      "question": "개념의 본질을 묻는 질문 (difficulty 1)",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "1",
      "explanation": "정답 이유 + 핵심 오답 이유 (2~3문장)",
      "concept": "핵심개념",
      "difficulty": 1
    }},
    {{
      "question": "비교·선택을 묻는 질문 (difficulty 2)",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "2",
      "explanation": "정답 이유 + 핵심 오답 이유",
      "concept": "핵심개념2",
      "difficulty": 2
    }},
    {{
      "question": "실제 적용·트레이드오프를 묻는 질문 (difficulty 3)",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "3",
      "explanation": "정답 이유 + 왜 이 판단이 중요한지",
      "concept": "핵심개념3",
      "difficulty": 3
    }}
  ]
}}"""


async def generate_quizzes(title: str, text: str, category: str) -> tuple[list[dict], dict]:
    """소스 기반 퀴즈 생성. (퀴즈 목록, {input, output} 토큰) 반환"""
    response = await client.chat.completions.create(
        model="gpt-5",
        max_completion_tokens=5000,
        messages=[{
            "role": "user",
            "content": QUIZ_PROMPT.format(
                category=category,
                title=title,
                text=text[:6000],
            )
        }]
    )

    usage = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}
    raw = response.choices[0].message.content.strip()
    raw = _extract_json(raw)
    data = json.loads(raw)
    return data.get("quizzes", []), usage


def _extract_json(text: str) -> str:
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text
