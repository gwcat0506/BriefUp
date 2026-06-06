import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def summarize_and_generate_quiz(title: str, raw_text: str, category: str) -> dict:
    """
    소스 텍스트 → 요약 + 퀴즈 2문제 생성
    소스 기반으로만 생성 → 할루시네이션 최소화
    """
    prompt = f"""
당신은 {category} 분야 학습 콘텐츠를 만드는 전문가입니다.

아래 원문을 바탕으로 (원문 내용에서만 근거를 찾아서):
1. 핵심 요약 (3~5문장, 한국어)
2. 퀴즈 2문제 (4지선다, 한국어)

[원문 제목]
{title}

[원문 내용]
{raw_text}

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "summary": "요약 내용",
  "quizzes": [
    {{
      "question": "질문",
      "options": {{"1": "보기1", "2": "보기2", "3": "보기3", "4": "보기4"}},
      "answer": "1",
      "explanation": "해설 (원문 근거 포함)",
      "concept": "핵심 개념명 (영어 또는 한국어 단어 하나)",
      "difficulty": 1
    }}
  ]
}}
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    text = message.content[0].text.strip()

    # JSON 파싱
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    return json.loads(text)
