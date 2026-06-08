"""
STEP 3 — 퀴즈 생성
소스 본문 기반으로만 생성 → 할루시네이션 최소화
GPT-4o-mini 사용
"""

from openai import AsyncOpenAI
import os
import json

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

QUIZ_PROMPT = """
당신은 {category} 분야를 쉽고 재미있게 가르치는 선생님입니다.
아래 [원문] 내용을 바탕으로, 처음 배우는 사람도 이해할 수 있는 퀴즈 2개를 만드세요.

퀴즈 작성 원칙:
1. 일상적인 비유나 예시를 사용해서 친근하게 — "마치 ~처럼", "예를 들어 ~"
2. 외우는 문제 ❌ → 개념을 이해했는지 확인하는 문제 ✅
3. 질문은 짧고 명확하게 (2줄 이내)
4. 해설은 왜 그게 정답인지 쉬운 말로 설명
5. 원문에 있는 내용만 사용 (없는 내용 추가 금지)
6. 한국어로 작성 (전문용어는 괄호로 영어 병기 가능)

좋은 예시:
- "RAG 시스템을 도서관에 비유하면, 검색(Retrieval)은 어떤 역할일까요?"
- "오늘 배운 내용에서 Agent가 도구를 사용하는 이유로 가장 적절한 것은?"

나쁜 예시 (이렇게 하지 마세요):
- "다음 중 Chunking의 overlap 파라미터의 역할은?" (너무 지엽적)
- "논문에서 제시한 3가지 방법론 중 첫 번째는?" (암기식)

[원문 제목]
{title}

[원문 내용]
{text}

아래 JSON 형식으로만 응답:
{{
  "quizzes": [
    {{
      "question": "친근하고 이해 중심의 질문",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "1",
      "explanation": "왜 정답인지 쉬운 말로 설명 (비유 포함 권장)",
      "concept": "핵심개념",
      "difficulty": 1
    }},
    {{
      "question": "친근하고 이해 중심의 질문2",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "2",
      "explanation": "왜 정답인지 쉬운 말로 설명",
      "concept": "핵심개념2",
      "difficulty": 2
    }}
  ]
}}
"""


async def generate_quizzes(title: str, text: str, category: str) -> tuple[list[dict], dict]:
    """소스 기반 퀴즈 생성. (퀴즈 목록, {input, output} 토큰) 반환"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1200,
        messages=[{
            "role": "user",
            "content": QUIZ_PROMPT.format(
                category=category,
                title=title,
                text=text[:3000]
            )
        }]
    )

    usage = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}
    raw = response.choices[0].message.content.strip()
    raw = _extract_json(raw)
    data = json.loads(raw)
    return data.get("quizzes", []), usage


def _extract_json(text: str) -> str:
    """LLM 응답에서 JSON 블록 추출"""
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text
