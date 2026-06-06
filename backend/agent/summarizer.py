"""
STEP 2 — 요약 생성
소스 본문 기반으로만 요약 → 할루시네이션 최소화
GPT-4o-mini 사용 (비용 최적화)
"""

from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SUMMARY_PROMPT = """
당신은 {category} 분야 학습 콘텐츠 전문가입니다.
아래 [원문]을 바탕으로, 원문에 있는 내용만 사용해서 핵심 요약을 작성하세요.

규칙:
- 원문에 없는 내용 절대 추가 금지
- 3~5문장, 한국어
- 전문 용어는 영어 그대로 사용 (RAG, LLM 등)
- 마지막 문장은 "핵심 포인트: ~" 형식으로 마무리

[원문 제목]
{title}

[원문 내용]
{text}

요약문만 반환하세요. JSON 불필요.
"""


async def summarize(title: str, text: str, category: str) -> str:
    """소스 기반 요약 생성"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": SUMMARY_PROMPT.format(
                category=category,
                title=title,
                text=text[:3000]
            )
        }]
    )
    return response.choices[0].message.content.strip()
