# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload              # http://localhost:8000
python -m agent.scheduler              # 파이프라인 수동 1회 실행 (직접 실행용)
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
  agent_runner.py (Claude Haiku 4.5 + FastMCP Client 에이전트)
    → mcp_server.py 도구들 (in-process 연결):
        get_active_topics()       ← DB 활성 토픽 조회
        get_collection_plan()     ← 커리큘럼 기반 오늘 챕터 + 검색 힌트
        collect_articles()        ← collector.py (arxiv/RSS) + web_search.py (Tavily)
        summarize_article()       ← summarizer.py (GPT-4o-mini)
        generate_quizzes()        ← quiz_gen.py + verifier.py (생성 + 자체 검증)
        save_content()            ← Supabase 저장

[유저 관심사 추가]
  POST /api/user/topic → classifier.py (카테고리 분류)
                       → curriculum_gen.py (Claude Haiku로 커리큘럼 자동 생성)
                       → topic_curricula DB 캐시

[유저 요청]
  Next.js page → lib/api.ts → FastAPI → Supabase
```

### 모델 역할 분리
- **Claude Haiku 4.5** (`ANTHROPIC_API_KEY`): 파이프라인 오케스트레이션, 커리큘럼 설계
- **GPT-4o-mini** (`OPENAI_API_KEY`): 요약 생성, 퀴즈 생성, 퀴즈 검증

### 에이전트 핵심 설계 결정
- **FastMCP 전환**: 도구를 `@mcp.tool()` 데코레이터로 선언적 관리. Claude Desktop 외부 연결도 지원 (`python -m agent.mcp_server`)
- **세션 스토어**: 원문 텍스트는 `_session["articles"]`에만 보관. Claude에는 `article_id` + 메타데이터만 노출 → 토큰 비용 절감, 할루시네이션 방지
- **병렬 실행**: Claude가 여러 tool_use를 한 응답에서 반환하면 `asyncio.gather`로 실제 병렬 처리
- **MAX_ITERATIONS = 50**: 토픽 수 × 아티클 수 × 5단계를 고려
- **비용 추적**: Claude + GPT 토큰 모두 집계 → USD 계산 → pipeline_runs.stats에 저장
- **퀴즈 검증 강화**: 검증 오류 시 이전(보수적 통과)과 달리 탈락 처리 (불확실하면 탈락)

### Backend (`backend/`)
- `main.py` — FastAPI 앱 진입점. 라우터 등록, CORS 설정
- `agent/agent_runner.py` — Claude Haiku + FastMCP Client 에이전트. MCP 도구 목록 동적 조회, 병렬 실행
- `agent/mcp_server.py` — FastMCP 서버. 도구 5개 정의 (`@mcp.tool()`): get_active_topics / get_collection_plan / collect_articles / summarize_article / generate_quizzes / save_content + 세션 스토어
- `agent/curriculum_gen.py` — 관심사 추가 시 Claude Haiku로 커리큘럼 자동 생성. `topic_curricula` DB에 캐시. alias 매칭 지원
- `agent/curriculum_catalog.py` — 하드코딩 커리큘럼 카탈로그 10트랙. chapter.py + progress.py 모두 여기서 import
- `agent/collector.py` — arxiv API + RSS 수집. `arxiv_query` 파라미터로 챕터별 정밀 검색 지원
- `agent/web_search.py` — Tavily 웹 검색 + 도메인 신뢰도 점수 필터 (0.65 미만 제외)
- `agent/summarizer.py` — GPT-4o-mini 요약. `tuple[str, dict]` 반환 (요약문, 토큰 usage)
- `agent/quiz_gen.py` — GPT-4o-mini 퀴즈 생성. `tuple[list[dict], dict]` 반환 (퀴즈, 토큰 usage)
- `agent/verifier.py` — GPT-4o-mini 퀴즈 검증. `tuple[list[dict], dict]` 반환 (통과 퀴즈, 토큰 usage). 검증 오류 시 탈락
- `core/supabase.py` — 싱글톤 Supabase 클라이언트. `.env` 로드 우선순위: `BriefUp/.env` → `backend/.env`
- `core/logger.py` — `PipelineLogger`: 단계별 실행 로그를 `pipeline_logs` 테이블에 기록 (Render 무료 티어 로그 소실 대응)

### Frontend (`frontend/`)
- `lib/api.ts` — 백엔드 호출 유틸 + 모든 TypeScript 타입 정의의 단일 출처. 새 엔드포인트는 여기에 추가
- `components/layout/BottomNav.tsx` — `active` prop으로 탭 강조 (`"home" | "quiz" | "roadmap" | "map" | "mypage"`)
- `components/ui/` — `Skeleton`, `Toast` 공통 컴포넌트
- 홈 페이지: 통계(streak/levels)를 먼저 로드하고 브리핑 콘텐츠를 나중에 로드 (Perceived performance)
- 퀴즈 페이지: content_id 퀴즈 없으면 오늘 전체 퀴즈로 폴백. 선택 즉시 연한 강조 (Optimistic UI)
- 로드맵 페이지: API 실패 시 기본 3트랙 하드코딩 폴백 (Render 콜드 스타트 대응)

모든 페이지는 `"use client"` + `useEffect` 데이터 페칭 패턴. 레이아웃은 `max-w-md mx-auto` (모바일 중심).

### Auth 상태
현재 MVP: `TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"` 하드코딩. Supabase Auth 연동 예정. 유저 관련 로직 수정 시 이 상수를 참고.

### DB 스키마
- 주요 테이블: `users`, `topics`, `contents`, `quizzes`, `quiz_results`, `concept_levels`, `streaks`, `push_subscriptions`
- `chapter_progress`, `bookmarks` — 챕터 진행 상태 + 북마크
- `topic_curricula` — 챕터 구조 + 검색 힌트 JSONB
- `pipeline_runs`, `pipeline_logs` — 파이프라인 실행 로그
- 백엔드는 `SUPABASE_SECRET_KEY`(서비스 롤)를 사용해 RLS를 우회

### 환경변수
**backend/.env**
```
SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SECRET_KEY
OPENAI_API_KEY        # GPT-4o-mini (요약, 퀴즈 생성, 검증)
ANTHROPIC_API_KEY     # Claude Haiku (에이전트 오케스트레이션, 커리큘럼 생성)
TAVILY_API_KEY
FRONTEND_URL
```

**frontend/.env.local**
```
NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_API_URL
```

### 배포
- Frontend: Vercel — `brief-up` 프로젝트, Root Directory: `frontend`
  - 프로덕션 URL: https://brief-up.vercel.app
  - 배포: `cd frontend && vercel --prod`
- Backend: Render — `briefup` 서비스, Root Directory: `backend`, Free 티어
  - 프로덕션 URL: https://briefup.onrender.com
  - 배포: `git push` (GitHub 연동 자동 배포)
  - **주의:** Free 티어는 15분 비활성 시 슬립, 첫 요청 시 30~60초 콜드 스타트

### 의존성 주의사항
- `httpx`는 `fastmcp`(>=0.28.1)와 `openai`(>=1.52.0) 요구사항에 맞게 고정
- `supabase` 2.x 최신은 2.9.1 (2.12.0은 존재하지 않음)
- `pydantic-settings`는 `mcp` 때문에 >=2.5.2 필요

설계 의도 상세: `DESIGN.md` 참조.
