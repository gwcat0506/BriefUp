# AGENTS.md

## Commands

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload              # http://localhost:8000
python -m agent.scheduler              # 파이프라인 수동 1회 실행
```

### Frontend
```bash
cd frontend
npm run dev     # http://localhost:3000
npm run build
npm run lint
```

## Architecture

### Data Flow
```
[파이프라인 실행 — POST /api/content/run-pipeline or python -m agent.scheduler]
  agent_runner.py (Codex Haiku 4.5 + FastMCP Client 에이전트)
    → mcp_server.py 도구들 (in-process 연결):
        get_active_topics()       ← DB 활성 토픽 조회
        get_collection_plan()     ← 커리큘럼 기반 오늘 챕터 + 검색 힌트
        collect_articles()        ← collector.py (arxiv/RSS) + web_search.py (Tavily)
        summarize_article()       ← summarizer.py (GPT-4o-mini) + Faithfulness 검증
        generate_quizzes()        ← quiz_gen.py + verifier.py (생성 + 교차 검증)
        save_content()            ← Supabase 저장
        save_reflection()         ← 실행 품질 평가 + 다음 실행 전략 기록

[유저 관심사 추가]
  POST /api/user/topic → classifier.py (카테고리 분류)
                       → curriculum_gen.py (Codex Haiku로 커리큘럼 자동 생성)
                       → topic_curricula DB 캐시

[유저 요청]
  Next.js page → lib/api.ts → FastAPI → Supabase
```

### 모델 역할 분리
- **Codex Haiku 4.5** (`ANTHROPIC_API_KEY`): 파이프라인 오케스트레이션, 커리큘럼 설계, 퀴즈 검증
- **GPT-4o-mini** (`OPENAI_API_KEY`): 요약 생성, 퀴즈 생성

### 에이전트 핵심 설계 결정
- **세션 스토어**: 원문 텍스트는 `_session["articles"]`에만 보관. Codex에는 `article_id` + 메타데이터만 노출 → 토큰 비용 절감, 할루시네이션 방지
- **FastMCP 전환**: 도구를 `@mcp.tool()` 데코레이터로 선언적 관리. Codex Desktop 외부 연결도 지원
- **병렬 실행**: Codex가 여러 tool_use를 한 응답에서 반환하면 `asyncio.gather`로 실제 병렬 처리
- **MAX_ITERATIONS = 50**: 토픽 수 × 아티클 수 × 7단계를 고려
- **비용 추적**: Codex + GPT 토큰 모두 집계 → USD 계산 → pipeline_runs.stats에 저장
- **Cross-Model Verification**: GPT가 생성한 요약·퀴즈를 Codex가 원문 기준 교차 검증. 불확실하면 탈락 (보수적 실패 원칙)
- **Cross-Run Memory**: save_reflection 결과가 다음 실행 SYSTEM_PROMPT에 주입 → 수집 전략 자동 조정

## Working Conventions

- `frontend/lib/api.ts` — 백엔드 호출 유틸 + 모든 TypeScript 타입의 단일 출처. **새 엔드포인트는 반드시 여기에 추가**
- 모든 프론트 페이지: `"use client"` + `useEffect` 패턴, `max-w-md mx-auto` 레이아웃 (모바일 중심)
- 에러 처리: `Promise.allSettled`로 API 부분 실패 허용 — `Promise.all` 사용 금지

## 배포

- **Frontend**: Vercel — `brief-up` 프로젝트, Root Directory: `frontend`
  - 프로덕션 URL: https://brief-up.vercel.app
  - 배포: `cd frontend && vercel --prod`
- **Backend**: Render — `briefup` 서비스, Root Directory: `backend`, Starter 티어
  - 프로덕션 URL: https://briefup.onrender.com
  - 배포: `git push` (GitHub 연동 자동 배포)
  - `core/logger.py` — 단계별 실행 로그를 `pipeline_logs` DB에 기록 (로그 소실 대응)

## Scope Guard

**명시적 요청 없이 절대 바꾸지 않을 것**
- `_session["articles"]` 패턴 — 원문을 에이전트 메시지에 직접 넣으면 안 됨 (토큰 폭증 + 할루시네이션)
- 모델 역할 교체 — Codex(오케스트레이션·검증) ↔ GPT(생성) 역할 분리는 의도적 설계. 같은 모델이 생성·검증하면 blind spot이 겹침
- `SYSTEM_PROMPT` in agent_runner.py — 전체 재작성 금지, 특정 단계만 수정
- `TEMP_USER_ID` — MVP 결정. Auth 구현 요청 없이는 건드리지 않음
- 퀴즈 검증 탈락 처리 — 통과율 30~40%는 버그가 아닌 의도적 엄격 기준

**새 패키지 추가 시**: `httpx>=0.28.1`, `pydantic-settings>=2.5.2` 하한 유지 (fastmcp/mcp 의존성)

## 변경 후 검증

**백엔드 변경 시**
```bash
cd backend && source .venv/bin/activate
python -c "from agent.mcp_server import mcp; from agent.agent_runner import run_agent_pipeline; print('imports OK')"
uvicorn main:app --reload  # /docs 접속해 엔드포인트 확인
```

**프론트엔드 변경 시**
```bash
cd frontend && npm run lint && npm run build
```

**파이프라인 변경 시**: `python -m agent.scheduler` 1회 실행 후 Supabase `contents`, `pipeline_runs` 테이블 결과 확인

## 비목표 (현재 MVP 범위 밖 — 요청 없으면 구현하지 않음)

- **실시간 파이프라인**: 수동/스케줄 실행만, WebSocket 없음
- **발생 불가능한 시나리오 방어 코드**: 내부 코드와 프레임워크 보장을 신뢰, 시스템 경계에서만 검증

설계 의도 상세: `DESIGN.md` 참조.
DB 스키마 상세: `DB.md` 참조.
