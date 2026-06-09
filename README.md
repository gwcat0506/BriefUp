# BriefUp — AI 브리핑 학습 서비스

> 관심사를 입력하면, 최신 콘텐츠를 자동 수집·요약해 퀴즈로 지식 레벨을 채워가는 PWA

**프로덕션:** https://brief-up.vercel.app  
**백엔드 API:** https://briefup.onrender.com

---

## 핵심 철학

**"결정할 게 없어야 한다"**

완벽주의로 시작을 못 하는 패턴을 깨는 방법은 선택지를 없애는 것.  
매일 아침 앱을 열면 오늘 공부할 내용이 준비되어 있다.  
관심사 = 커리큘럼 = 오늘의 아티클 = 오늘의 퀴즈. 유저가 결정할 건 없다.

---

## 서비스 개요

### 화면 구성

| 페이지 | 경로 | 설명 |
|--------|------|------|
| 홈 | `/home` | 스트릭·레벨 통계 + 오늘의 브리핑 카드 |
| 퀴즈 | `/quiz` | 오늘 수집된 아티클 기반 4지선다 퀴즈 |
| 로드맵 | `/roadmap` | 관심사별 커리큘럼 진행 상태 |
| 지식 맵 | `/map` | 학습한 개념 연결 시각화 |
| 챕터 학습 | `/learn` | 챕터별 학습 카드 + 퀴즈 |
| 히스토리 | `/history` | 풀었던 퀴즈 오답 복습 |
| 마이페이지 | `/mypage` | 관심사 관리, 통계 |
| 온보딩 | `/onboarding` | 첫 진입 시 관심사 선택 |

### 유저 경험 흐름

```
온보딩 (관심사 선택)
  → Claude가 커리큘럼 자동 생성 (챕터 구조 + 검색 힌트)
  → 파이프라인 실행 (POST /api/content/run-pipeline)
       → 커리큘럼 기반으로 오늘 다룰 챕터 결정
       → 챕터에 맞는 영문 쿼리로 아티클 수집
       → AI 요약 + 퀴즈 생성 + 자체 검증
  → 앱 열면 오늘의 브리핑 + 퀴즈 준비 완료
```

---

## 전체 아키텍처

```
[파이프라인 실행 — POST /api/content/run-pipeline]
        ↓
  agent_runner.py  ← Claude Haiku 4.5 + FastMCP 오케스트레이션
        ↓
  1. get_active_topics        ← DB 활성 토픽 목록
  2. get_collection_plan × N  ← 커리큘럼에서 오늘 챕터 + search_hints 선택
  3. collect_articles × N     ← 챕터 쿼리로 arxiv + RSS + Tavily 수집
  4. summarize_article        ← GPT-4o-mini 한국어 요약
  5. generate_quizzes         ← GPT-4o-mini 4지선다 퀴즈 생성
                              ← GPT-4o-mini Self-Verify 검증 (원문 기반)
  6. save_content             ← Supabase 저장
        ↓
  PipelineLogger → pipeline_runs / pipeline_logs 테이블

[유저 요청]
  Next.js → lib/api.ts → FastAPI → Supabase

[관심사 추가 시 (온보딩 / 마이페이지)]
  POST /api/user/topic
    → topic_curricula DB 조회 (캐시 HIT → 바로 반환)
    → 캐시 MISS → Claude Haiku로 커리큘럼 생성 → DB 저장
```

---

## Agent 오케스트레이션

### 구조

Claude Haiku 4.5가 FastMCP를 통해 도구를 자율적으로 선택·실행한다.  
단순 함수 호출 순서가 아니라 **Claude가 중간 결과를 보고 다음 행동을 직접 판단**한다.

```
Claude ←→ FastMCP (in-process)
           ├── get_active_topics
           ├── get_collection_plan   ← 커리큘럼 기반 오늘 챕터 + 검색 쿼리
           ├── collect_articles      ← arxiv_query / web_query 파라미터 지원
           ├── summarize_article
           ├── generate_quizzes
           └── save_content
```

### 병렬 실행

Claude가 여러 tool_calls를 한 응답에서 동시에 반환하면 `asyncio.gather`로 실제 병렬 처리.

```
[iteration 1] get_active_topics
[iteration 2] get_collection_plan × N 개 토픽 동시
[iteration 3] collect_articles × N 개 토픽 동시
[iteration 4~] 아티클별 summarize → quizzes → save (아티클 간 병렬)
```

### 자율 판단 권한

| 상황 | Claude의 행동 |
|------|-------------|
| collect_articles 결과 품질 낮음 | 해당 아티클 건너뜀 |
| summarize_article 실패 | 해당 아티클 건너뜀 |
| generate_quizzes verified_count = 0 | save_content 호출 안 함 |
| 토픽 수집 아티클 0개 | 기록 후 다음 토픽으로 |

### 세션 스토어 (토큰 절감)

원문 텍스트는 `_session["articles"]`에만 보관. Claude에는 `article_id + 메타데이터`만 노출.  
→ 토큰 비용 절감 + 할루시네이션 방지

---

## 커리큘럼 자동 생성 시스템

### 흐름

```
관심사 추가 (예: "양자컴퓨팅")
  ↓
topic_curricula DB에 "quantum-computing" key로 조회
  ├── HIT  → 저장된 커리큘럼 반환
  └── MISS → Claude Haiku가 커리큘럼 생성:
               {
                 chapters: [
                   {
                     id: "quantum-computing-1",
                     title: "큐비트란 무엇인가?",
                     concepts: ["큐비트", "중첩", "얽힘"],
                     search_hints: {
                       arxiv_query: "qubit quantum computing basics 2024",
                       web_query: "what is qubit explained simply"
                     }
                   }, ...
                 ]
               }
             → DB 저장 후 반환
```

### 파이프라인과의 연계

매일 파이프라인 실행 시 `get_collection_plan`이:
1. 저장된 커리큘럼 조회
2. 최근 7일 이미 다룬 챕터 확인
3. **아직 안 다룬 챕터 중 가장 앞선 것 선택**
4. 해당 챕터의 `search_hints`를 Claude에게 전달

Claude는 `search_hints.arxiv_query`, `search_hints.web_query`를  
`collect_articles`의 `arxiv_query`, `web_query` 인자로 직접 사용.  
→ **한국어 토픽명 → 챕터별 최적 영문 쿼리 자동 변환**

---

## 파이프라인 상세

### STEP 1 — 콘텐츠 수집 (`agent/collector.py` + `agent/web_search.py`)

3-tier 수집 후 URL 기준 중복 제거:

**Tier 1: arxiv**
- `arxiv_query` 파라미터 우선 사용 (Claude가 작성한 영문 쿼리)
- 없으면 `topic_name` 그대로 사용

**Tier 2: RSS** (`agent/collector.py`)

| 카테고리 | 소스 |
|----------|------|
| AI/ML | HuggingFace Blog, TLDR AI |
| 철학 | Philosophy Bites, Philosophers Mag |
| 경제 | Freakonomics, Economist |
| 심리학 | Psychology Today |

**Tier 3: 웹 검색** (`agent/web_search.py`)
- Tavily API로 `web_query` 검색 (`TAVILY_API_KEY` 없으면 자동 스킵)
- **신뢰도 점수** = Tavily 관련성 60% + 도메인 점수 40%
  - arxiv.org, nature.com → 1.0 / openai.com, anthropic.com → 0.9 / MIT, Stanford → 0.85
  - medium.com, substack.com → 0.5 / 약어 사전류 블랙리스트 → 0.0
  - 임계값 0.65 미만 제거

**품질 필터:**
- 본문 150자 미만 버림
- arxiv·Tavily 소스는 관련성 필터 스킵 (이미 관련 쿼리로 수집됨)
- RSS 소스는 query 키워드 포함 여부 확인
- 오늘 이미 DB에 있는 URL 제거

---

### STEP 2 — 요약 생성 (`agent/summarizer.py`)

```
원문 본문 (최대 3,000자) → GPT-4o-mini → 3~5문장 한국어 요약

규칙:
- 원문에 없는 내용 절대 추가 금지
- 마지막 문장은 "핵심 포인트: ~" 형식
- 전문용어는 영어 그대로 (RAG, LLM 등)
```

---

### STEP 3 — 퀴즈 생성 (`agent/quiz_gen.py`)

```
원문 본문 (최대 3,000자) → GPT-4o-mini → 4지선다 퀴즈 2개 (JSON)

퀴즈 필드: question, options, answer, explanation, concept, difficulty
원칙: 이해 중심 (암기식 금지), 일상 비유 사용, 한국어
```

---

### STEP 4 — 자체 검증 (`agent/verifier.py`)

생성된 퀴즈를 GPT-4o-mini가 원문 기준으로 재검증.

```
검증 기준 (모두 PASS여야 저장):
1. 정답이 원문에서 명확히 찾을 수 있는가?
2. 오답 보기들이 원문에서 틀린 내용인가?
3. 해설이 원문 내용과 일치하는가?
4. 문제가 명확하고 모호하지 않은가?

FAIL → 해당 퀴즈 폐기 / verified_count=0 → save_content 호출 안 함
```

| 생성 방식 | 할루시네이션 비율 |
|-----------|---------------|
| 오픈엔디드 생성 | 40~80% |
| 소스 기반 생성 | ~2% |
| 소스 기반 + 자체 검증 | ~1% 목표 |

---

### STEP 5 — 저장 (`agent/mcp_server.py`)

검증 통과한 항목만 Supabase에 저장.

```
contents: topic_category, source, title, original_url, summary, collected_at
quizzes:  content_id, question, options, answer, explanation, concept, difficulty
```

---

## DB 스키마

| 테이블 | 용도 |
|--------|------|
| `users` | 유저 계정 (현재 TEMP_USER_ID 하드코딩, Auth 예정) |
| `topics` | 유저별 관심 토픽 (`is_active`로 활성화 관리) |
| `topic_curricula` | 토픽별 커리큘럼 (챕터 구조 + search_hints, Claude 자동 생성) |
| `contents` | 수집된 원문 + AI 요약 |
| `quizzes` | 검증된 4지선다 퀴즈 |
| `quiz_results` | 유저 퀴즈 풀이 기록 |
| `concept_levels` | 개념별 레벨 (0~100%, 낮아지지 않음) |
| `streaks` | 연속 출석 기록 + 프리즈 |
| `push_subscriptions` | 웹 푸시 알림 구독 |
| `chapter_progress` | 챕터 학습 진행 상태 |
| `bookmarks` | 북마크한 콘텐츠 |
| `pipeline_runs` | 파이프라인 실행 이력 |
| `pipeline_logs` | 파이프라인 단계별 로그 |

스키마 파일: `backend/schema_v2.sql`, `backend/schema_curricula.sql`

### topic_curricula chapters JSONB 구조

```json
[
  {
    "id": "quantum-computing-1",
    "title": "큐비트란 무엇인가?",
    "description": "0과 1을 동시에 가지는 비트의 세계",
    "level": "입문",
    "duration": "7분",
    "concepts": ["큐비트", "중첩", "얽힘"],
    "search_hints": {
      "arxiv_query": "qubit quantum computing basics 2024",
      "web_query": "what is qubit quantum computing explained simply"
    }
  }
]
```

---

## 파이프라인 로깅 (`core/logger.py`)

Render Free 티어는 로그가 소실되므로 Supabase에 직접 기록.

```
pipeline_runs  — run_id, status, started_at, finished_at, stats(토큰/비용/저장수)
pipeline_logs  — tool_name, category, inputs(메타만), output, duration_ms, status, error_message
```

원문 텍스트는 로그에 기록하지 않음. `/api/logs` 엔드포인트로 조회 가능.

---

## 기술 스택

| 파트 | 기술 |
|------|------|
| Frontend | Next.js 14 (App Router), Tailwind CSS, PWA |
| Backend | Python 3.11, FastAPI |
| DB | Supabase (PostgreSQL + RLS) |
| AI 오케스트레이션 | Claude Haiku 4.5 (Anthropic) + FastMCP |
| AI 처리 | GPT-4o-mini (OpenAI) — 요약 / 퀴즈 생성 / 자체 검증 |
| 웹 검색 | Tavily API (선택) |
| 수집 | httpx, feedparser, arxiv API |
| 배포 | Vercel (프론트) + Render Free (백엔드) |

---

## 백엔드 파일 구조

```
backend/
├── main.py                    FastAPI 앱 진입점
├── agent/
│   ├── agent_runner.py        Claude + FastMCP 오케스트레이터 (MAX_ITERATIONS=50)
│   ├── mcp_server.py          FastMCP 서버 — 도구 6개 정의 + 세션 스토어
│   ├── curriculum_gen.py      커리큘럼 자동 생성 (get_or_create_curriculum)
│   ├── curriculum_catalog.py  기존 하드코딩 커리큘럼 (DB seed 용도)
│   ├── collector.py           arxiv API + RSS 수집 (arxiv_query 파라미터 지원)
│   ├── web_search.py          Tavily 검색 + 도메인 신뢰도 필터
│   ├── summarizer.py          GPT-4o-mini 요약 생성
│   ├── quiz_gen.py            GPT-4o-mini 퀴즈 생성
│   ├── verifier.py            GPT-4o-mini 자체 검증
│   ├── classifier.py          토픽 카테고리 자동 분류
│   └── scheduler.py           파이프라인 실행 진입점 (직접 실행 or API 트리거)
├── api/
│   ├── user.py                유저 + 관심사 추가 (커리큘럼 자동 생성 연동)
│   ├── content.py             오늘의 브리핑 조회
│   ├── quiz.py                퀴즈 조회 + 결과 저장
│   ├── chapter.py             챕터 학습 콘텐츠 (GPT 즉시 생성 + 캐시)
│   ├── progress.py            로드맵 + 챕터 진행 상태
│   └── logs.py                파이프라인 로그 조회
├── core/
│   ├── supabase.py            싱글톤 Supabase 클라이언트
│   └── logger.py              PipelineLogger
└── requirements.txt
```

---

## 프론트엔드 파일 구조

```
frontend/
├── app/
│   ├── page.tsx               루트 (홈으로 리다이렉트)
│   ├── onboarding/page.tsx    관심사 선택 온보딩
│   ├── home/page.tsx          오늘의 브리핑 + 스트릭/레벨 통계
│   ├── quiz/page.tsx          퀴즈 풀기
│   ├── roadmap/page.tsx       커리큘럼 로드맵
│   ├── map/page.tsx           지식 맵 시각화
│   ├── learn/page.tsx         챕터 학습 카드
│   ├── mypage/page.tsx        마이페이지 + 관심사 관리
│   └── history/page.tsx       퀴즈 오답 복습
└── lib/
    └── api.ts                 백엔드 호출 유틸 + 모든 TypeScript 타입 (단일 소스)
```

모든 페이지: `"use client"` + `useEffect` 데이터 페칭 패턴, `max-w-md mx-auto` (모바일 중심)

---

## 환경변수

### `backend/.env`

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SECRET_KEY=...       # 서비스 롤 키 (RLS 우회)
ANTHROPIC_API_KEY=...         # 필수 — 오케스트레이션 + 커리큘럼 생성
OPENAI_API_KEY=...            # 필수 — 요약 / 퀴즈 생성 / 검증
TAVILY_API_KEY=...            # 선택 — 없으면 웹 검색 스킵
FRONTEND_URL=http://localhost:3000
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 로컬 실행

### 백엔드

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # .env 값 채우기
uvicorn main:app --reload       # http://localhost:8000

# 파이프라인 수동 실행
python -m agent.scheduler
```

### 프론트엔드

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev                     # http://localhost:3000
```

### DB 초기화 순서

```
1. Supabase SQL Editor에서 schema_v2.sql 실행
2. Supabase SQL Editor에서 schema_curricula.sql 실행
3. python seed_curricula.py     # 기존 9개 토픽 커리큘럼 seed
```

---

## 배포

### 프론트엔드 → Vercel

- 프로젝트: `brief-up` / Root Directory: `frontend`
- 배포: `cd frontend && vercel --prod`
- 프로덕션: https://brief-up.vercel.app

### 백엔드 → Render

- 서비스: `briefup` / Root Directory: `backend`
- 배포: `git push` (GitHub 연동 자동 배포)
- 프로덕션: https://briefup.onrender.com
- **주의:** Free 티어 — 15분 비활성 시 슬립, 첫 요청 시 30~60초 콜드 스타트

---

## 주요 설계 결정

| 결정 | 이유 |
|------|------|
| Claude가 도구를 직접 선택 (MCP Tool Use) | 고정 파이프라인은 오류 복구 불가. 에이전트가 중간 결과 보고 판단 |
| 세션 스토어로 원문 텍스트 격리 | LLM에 원문 노출 시 토큰 비용 폭증 + 할루시네이션 위험 |
| asyncio.gather 병렬 실행 | 토픽 N개 → N배 빠름 |
| 퀴즈 자체 검증 (verifier.py) | LLM이 원문 없는 내용으로 퀴즈 만드는 것 방지 |
| 커리큘럼 DB 캐시 | 동일 토픽 재생성 없이 즉시 반환. Claude API 호출 최소화 |
| search_hints로 쿼리 위임 | 한국어 토픽명을 Claude가 챕터 맥락에 맞는 영문 쿼리로 직접 변환 |
| arxiv/Tavily 관련성 필터 스킵 | 이미 관련 쿼리로 수집됨. 불필요한 키워드 매칭 제거 |
| concept_levels 낮아지지 않음 | 레벨 하락 → 좌절 → 이탈. 항상 성장하는 느낌 유지 |
| 스트릭 프리즈 | 하루 빠졌을 때 이탈 방지. Duolingo 이탈률 연구 기반 |
| TEMP_USER_ID 하드코딩 | MVP. Supabase Auth 붙이면 이 상수만 교체 |
| Render Free 콜드 스타트 폴백 | API 실패 시 하드코딩 기본 데이터로 빈 화면 방지 |

---

## 의존성 주의사항

- `httpx`: `fastmcp`(≥0.28.1)와 `openai`(≥1.52.0) 요구사항에 맞게 고정
- `supabase`: 2.x 최신은 2.9.1 (2.12.0은 존재하지 않음)
- `pydantic-settings`: `mcp` 때문에 ≥2.5.2 필요

---

## Auth 현황

현재 MVP: `TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"` 하드코딩.  
Supabase Auth 연동 예정. 유저 관련 로직 수정 시 이 상수를 참고.
