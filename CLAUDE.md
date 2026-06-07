# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload          # http://localhost:8000
python -m agent.scheduler          # 파이프라인 수동 1회 실행
python benchmark.py                # 퀴즈 정확도 벤치마크 (AI/ML)
python benchmark.py 철학           # 특정 카테고리 벤치마크
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
[매일 05:00 APScheduler]
  agent_runner.py (GPT-4o-mini Tool Use 오케스트레이션)
    → mcp_tools.py  → run_pipeline_for_category()
        collector.py  → 원문 수집 (arxiv API, RSS)
        summarizer.py → GPT-4o-mini 요약 생성
        quiz_gen.py   → GPT-4o-mini 퀴즈 생성 (4지선다 2개)
        verifier.py   → GPT-4o-mini 자체 검증 (PASS/FAIL)
        Supabase 저장

[유저 요청]
  Next.js page → lib/api.ts → FastAPI → Supabase
```

**중요:** README는 Claude Haiku라고 쓰여 있지만 실제 코드(`summarizer.py`, `quiz_gen.py`, `agent_runner.py`)는 모두 OpenAI GPT-4o-mini를 사용한다. `OPENAI_API_KEY`가 필수 환경변수다.

### Backend (`backend/`)
- `main.py` — FastAPI 앱 진입점. APScheduler lifespan, 라우터 등록, CORS 설정
- `agent/agent_runner.py` — GPT-4o-mini Tool Use 루프로 파이프라인 오케스트레이션 (MAX_ITERATIONS=20)
- `agent/mcp_tools.py` — Tool 스키마 정의 + `run_pipeline_for_category()` 실제 실행 함수
- `core/supabase.py` — 싱글톤 Supabase 클라이언트. `.env` 로드 우선순위: `BrefUp/.env` → `backend/.env`
- `core/logger.py` — `PipelineLogger`: 파이프라인 실행 로그를 Supabase `pipeline_logs` 테이블에 기록

### Frontend (`frontend/`)
- `lib/api.ts` — 백엔드 호출 유틸 + 모든 TypeScript 타입 정의의 단일 출처. 새 엔드포인트는 여기에 추가
- `lib/supabase.ts` — Supabase Auth 클라이언트 (프론트용, anon key)
- `components/layout/BottomNav.tsx` — `active` prop으로 탭 강조 (`"home" | "quiz" | "roadmap" | "map" | "mypage"`)
- `components/ui/` — `Skeleton`, `Toast` 공통 컴포넌트

모든 페이지는 `"use client"` + `useEffect` 데이터 페칭 패턴. 레이아웃은 `max-w-md mx-auto` (모바일 중심).

### Auth 상태
현재 MVP: `TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"` 하드코딩. Supabase Auth 연동 예정. 유저 관련 로직 수정 시 이 상수를 참고.

### DB 스키마
- `schema_v2.sql` — `chapter_progress`, `bookmarks` 테이블 (기존 스키마에 추가)
- 기존 주요 테이블: `users`, `topics`, `contents`, `quizzes`, `quiz_results`, `concept_levels`, `streaks`, `push_subscriptions`
- 백엔드는 `SUPABASE_SECRET_KEY`(서비스 롤)를 사용해 RLS를 우회

### 환경변수
**backend/.env**
```
SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SECRET_KEY
OPENAI_API_KEY
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
