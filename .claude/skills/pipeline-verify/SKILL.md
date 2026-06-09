---
name: pipeline-verify
description: 파이프라인 코드 수정 후 각 계층을 순서대로 테스트. web_search.py, collector.py, mcp_tools.py, agent_runner.py 순으로 실행하고 결과 요약.
---

# pipeline-verify

파이프라인 관련 코드 수정 후 각 계층을 순서대로 테스트하고 결과를 요약하는 스킬.

## 실행 방법

사용자가 `/pipeline-verify` 를 입력하면 아래 단계를 **순서대로** 실행한다.  
한 단계가 실패하면 이후 단계는 건너뛰고 실패 원인을 즉시 보고한다.

---

## 테스트 단계

모든 명령은 `backend/` 디렉토리에서 실행한다:

```bash
cd /Users/gwcat/Desktop/BrefUp/backend
source .venv/bin/activate
```

### Step 1 — web_search.py

```bash
python test_web_search.py
```

확인 항목:
- 검색 결과가 1건 이상 반환되는지
- trust score 필터링이 동작하는지
- 오류 없이 종료되는지

### Step 2 — collector.py

```bash
python test_collector.py
```

확인 항목:
- `collect_for_category()` 가 콘텐츠를 수집하는지
- `_is_quality_content()` 필터가 적용되는지
- 수집 건수가 0이 아닌지

### Step 3 — mcp_tools.py (파이프라인 엔드투엔드)

```bash
python test_mcp_server.py
```

확인 항목:
- MCP 도구가 정상 임포트되는지
- `run_pipeline_for_category()` 가 summarizer → quiz_gen → verifier 를 호출하는지
- Supabase 저장까지 오류 없이 완료되는지

### Step 4 — agent_runner.py (Tool Use 루프 전체 실행)

```bash
python -m agent.scheduler
```

확인 항목:
- Tool Use 루프가 MAX_ITERATIONS=20 내에서 종료되는지
- `pipeline_logs` 테이블에 로그가 기록되는지
- 전체 카테고리 중 FAIL 비율이 50% 미만인지

---

## 결과 보고 형식

각 단계가 끝나면 아래 형식으로 요약한다:

```
[ Step 1 ] web_search   ✓ PASS  — 검색 결과 N건, 신뢰 점수 평균 X.X
[ Step 2 ] collector    ✓ PASS  — 수집 N건 (필터 후 M건)
[ Step 3 ] mcp_tools    ✗ FAIL  — verifier 호출 시 OpenAI API 타임아웃
[ Step 4 ] agent_runner — SKIP  (Step 3 실패로 건너뜀)

실패 위치: Step 3 — mcp_tools.py
원인: verifier.py 내 OpenAI 호출 타임아웃 (timeout=30 초과)
제안: backend/agent/verifier.py 의 timeout 값을 늘리거나 재시도 로직 추가
```

---

## 실패 진단 규칙

| 증상 | 의심 위치 | 확인할 것 |
|------|-----------|-----------|
| `ModuleNotFoundError` | 임포트 경로 | `.venv` 활성화 여부, `requirements.txt` 설치 |
| `OPENAI_API_KEY` 없음 | 환경변수 | `backend/.env` 또는 `BrefUp/.env` 에 키 존재 여부 |
| `SUPABASE_SECRET_KEY` 없음 | 환경변수 | 동일 `.env` 확인 |
| 수집 건수 0 | collector / web_search | 네트워크, RSS URL 만료, arxiv API 응답 확인 |
| FAIL 비율 ≥ 50% | verifier | GPT-4o-mini 프롬프트 or 토픽 품질 문제 |
| Tool Use 루프 MAX_ITERATIONS 도달 | agent_runner | 루프 탈출 조건 확인 (`mcp_tools.py` 반환값) |

---

## 주의사항

- Step 3·4는 실제 OpenAI API와 Supabase를 호출하므로 비용이 발생한다.  
  코드 변경이 `web_search.py` 또는 `collector.py` 에만 해당되면 Step 1·2만 실행해도 된다고 사용자에게 안내한다.
- `TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"` 하드코딩 상태이므로 유저 관련 검증은 불필요하다.
