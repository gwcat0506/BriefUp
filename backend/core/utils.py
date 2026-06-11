import json


def extract_json(text: str) -> dict | None:
    """LLM 응답에서 JSON 객체 추출. 코드블록·앞뒤 텍스트 제거."""
    text = text.strip()
    # 1단계: 코드블록
    if "```" in text:
        parts = text.split("```")
        for part in parts[1::2]:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            try:
                return json.loads(candidate)
            except Exception:
                continue

    # 2단계: 첫 번째 { ... } (중첩 허용)
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except Exception:
                        break

    # 3단계: 직접 파싱
    try:
        return json.loads(text)
    except Exception:
        return None
