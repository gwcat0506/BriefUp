"""
STEP 2 — 요약 생성
소스 본문 기반으로만 생성 → 할루시네이션 최소화
GPT-5 사용
"""

from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SUMMARY_PROMPT = """당신은 {category} 분야 전문가입니다.
아래 [원문]을 읽고, 독자가 "이걸 알면 실제로 뭐가 달라지는지" 느낄 수 있도록 핵심을 정리하세요.

작성 구조 (이 순서로):
1. **핵심 발견/주장**: 이 글이 말하는 가장 중요한 것 (1~2문장)
2. **왜 중요한가**: 기존 방식과 뭐가 다른지, 어떤 문제를 해결하는지 (1~2문장)
3. **실제 적용**: 현실에서 어디에 쓰이는지 구체적 사례 (1문장)
4. **핵심 포인트**: 기억해야 할 한 가지 (반드시 "핵심 포인트: ~"로 시작)

규칙:
- 원문에 없는 내용 추가 금지
- 전문용어는 영어 그대로 (RAG, LLM 등)
- 총 5~7문장, 한국어
- 뻔한 말 금지: "이 글은 ~을 다룹니다", "~에 대해 알아봅니다" 시작 금지

[원문 제목]
{title}

[원문 내용]
{text}

요약문만 반환하세요. JSON 불필요."""


async def summarize(title: str, text: str, category: str) -> tuple[str, dict]:
    """소스 기반 요약 생성. (요약문, {input, output} 토큰) 반환"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": SUMMARY_PROMPT.format(
                category=category,
                title=title,
                text=text[:6000],
            )
        }]
    )
    usage = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}
    return response.choices[0].message.content.strip(), usage
