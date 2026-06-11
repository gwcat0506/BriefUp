"""
토픽 카테고리 자동 분류
사용자가 자유 입력한 관심사를 RSS 소스 선택용 카테고리로 매핑
"""

import os
from openai import AsyncOpenAI
from core.config import GPT_4O_MINI_MODEL

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORIES = ["AI/ML", "철학", "경제", "심리학", "과학/기술", "역사/사회", "건강/의학", "예술/문화", "비즈니스", "기타"]

CLASSIFY_PROMPT = f"""다음 관심사를 아래 카테고리 중 하나로 분류하세요.

카테고리 목록: {', '.join(CATEGORIES)}

관심사: {{topic_name}}

카테고리명만 반환하세요. 다른 텍스트 없이."""


async def classify_topic(topic_name: str) -> str:
    """관심사 → 카테고리 자동 분류 (RSS 소스 선택용)"""
    response = await client.chat.completions.create(
        model=GPT_4O_MINI_MODEL,
        max_tokens=20,
        messages=[{
            "role": "user",
            "content": CLASSIFY_PROMPT.format(topic_name=topic_name),
        }],
    )
    result = response.choices[0].message.content.strip()
    return result if result in CATEGORIES else "기타"
