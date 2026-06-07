# BrefUp — AI 브리핑 학습 Agent

> 관심사를 입력하면, 매일 최신 콘텐츠를 자동 수집·요약해 퀴즈로 지식 레벨을 채워가는 PWA

---

## 핵심 철학

**"결정할 게 없어야 한다"**
완벽주의로 시작을 못 하는 패턴을 깨는 방법은 선택지를 없애는 것.
매일 아침 앱을 열면 오늘 공부할 내용이 준비되어 있다.

---

## 아키텍처 전체 흐름

```
[매일 새벽 05:00 — APScheduler]
        ↓
  agent_runner.py  ← GPT-4o-mini Tool Use 오케스트레이션 루프
        ↓
  get_active_topics()         ← DB에서 활성 토픽 목록 조회
        ↓
  run_pipeline_for_topic() × N  ← 토픽별 5단계 파이프라인 실행
   │
   ├─ STEP 1: 수집     collector.py (arxiv/RSS) + web_search.py (Tavily)
   ├─ STEP 2: 요약     summarizer.py (GPT-4o-mini)
   ├─ STEP 3: 퀴즈생성 quiz_gen.py (GPT-4o-mini)
   ├─ STEP 4: 검증     verifier.py (GPT-4o-mini Self-Verify)
   └─ STEP 5: 저장     Supabase contents / quizzes 테이블
        ↓
  PipelineLogger → pipeline_runs / pipeline_logs 테이블에 기록

[유저 요청]
  Next.js → lib/api.ts → FastAPI → Supabase
```

---

## Agent 오케스트레이션 (`agent/agent_runner.py`)

단순 함수 호출 순서가 아니라 **GPT-4o-mini가 Tool Use로 직접 실행 흐름을 결정**한다.

```
while 반복 (최대 20회):
    GPT에게 메시지 전달
        ↓
    GPT가 tool_calls 반환
        ↓
    각 tool 실행 → 결과를 messages에 추가
        ↓
    GPT가 텍스트만 반환 (tool_calls 없음) → 루프 종료
```

GPT에게 주어지는 도구는 2개:

| 도구 | 설명 |
|------|------|
| `get_active_topics` | DB `topics` 테이블에서 `is_active=true` 토픽 목록 조회 |
| `run_pipeline_for_topic` | 지정 토픽에 대해 수집→요약→퀴즈→검증→저장 전체 실행 |

GPT는 시스템 프롬프트 지시에 따라 먼저 `get_active_topics`를 호출하고, 이후 각 토픽마다 `run_pipeline_for_topic`을 순서대로 호출한다. 한 토픽에서 오류가 나도 다음 토픽은 반드시 처리한다.

---

## 파이프라인 5단계 상세

### STEP 1 — 콘텐츠 수집

두 경로를 병렬 수집 후 URL 기준 중복 제거한다.

**경로 A: arxiv + RSS** (`agent/collector.py`)

| 카테고리 | 소스 |
|----------|------|
| AI/ML | arxiv API (동적 쿼리), HuggingFace Blog RSS, TLDR AI RSS |
| 철학 | Philosophy Bites RSS, Philosophers Mag RSS |
| 경제 | Freakonomics RSS, Economist RSS |
| 심리학 | Psychology Today RSS |

- arxiv는 `topic_name`을 쿼리로 직접 사용 (예: "RAG", "LangGraph")
- RSS는 카테고리 전체 수집 후 `topic_name` 키워드로 필터

**경로 B: 웹 검색** (`agent/web_search.py`)

- Tavily API로 `"{topic_name} research OR paper OR guide"` 검색
- `TAVILY_API_KEY` 없으면 자동 스킵 (오류 아님)
- **신뢰도 점수** = Tavily 관련성 60% + 도메인 점수 40%
  - arxiv.org, nature.com: 1.0 / openai.com, anthropic.com: 0.9 / MIT, Stanford: 0.85
  - medium.com, substack.com: 0.5 / 약어 사전류 블랙리스트: 0.0
  - 임계값 0.65 미만 제거

**공통 품질 필터 3단계:**
1. 본문 150자 미만 버림
2. `topic_name` 키워드 포함 여부 확인
3. 오늘 이미 DB에 있는 URL 제거

---

### STEP 2 — 요약 생성 (`agent/summarizer.py`)

```
원문 본문 (최대 3,000자) → GPT-4o-mini → 3~5문장 한국어 요약

규칙:
- 원문에 없는 내용 절대 추가 금지 (할루시네이션 방지)
- 마지막 문장은 "핵심 포인트: ~" 형식
- 전문용어는 영어 그대로 (RAG, LLM 등)
```

---

### STEP 3 — 퀴즈 생성 (`agent/quiz_gen.py`)

```
원문 본문 (최대 3,000자) → GPT-4o-mini → 4지선다 퀴즈 2개 (JSON)

각 퀴즈 필드:
- question: 이해 중심 질문 (암기식 금지)
- options: {"1": ..., "2": ..., "3": ..., "4": ...}
- answer: 정답 번호 ("1"~"4")
- explanation: 정답 이유 (비유 포함 권장)
- concept: 핵심 개념명 (레벨 추적용)
- difficulty: 1 or 2
```

좋은 퀴즈 예시: "RAG 시스템을 도서관에 비유하면, 검색(Retrieval)은 어떤 역할일까요?"
나쁜 예시: "논문에서 제시한 3가지 방법론 중 첫 번째는?" (암기식)

---

### STEP 4 — 자체 검증 (`agent/verifier.py`)

퀴즈를 생성한 GPT가 동일 원문을 보고 자신이 만든 퀴즈를 **다시 검증**한다.

```
검증 기준 (모두 통과해야 PASS):
1. 정답이 원문에서 명확히 찾을 수 있는가?
2. 오답 보기들이 원문에서는 틀린 내용인가?
3. 해설이 원문 내용과 일치하는가?
4. 문제가 명확하고 모호하지 않은가?

FAIL → 해당 퀴즈 폐기
PASS → STEP 5 저장
검증 파싱 실패 → 보수적으로 통과 처리
```

**할루시네이션 비율 (연구 기준):**
| 방식 | 할루시네이션 |
|------|------------|
| 오픈엔디드 생성 | 40~80% |
| 소스 기반 생성 | 2% 미만 |
| 소스 기반 + 검증 | ~1% 목표 |

---

### STEP 5 — 저장 (`agent/mcp_tools.py`)

검증 통과한 항목만 Supabase에 저장.

```
contents 테이블: topic_category, source, title, original_url, summary, collected_at
quizzes 테이블:  content_id, question, options, answer, explanation, concept, difficulty
```

---

## 파이프라인 로깅 (`core/logger.py`)

각 단계 실행 결과를 Supabase에 자동 기록.

```
pipeline_runs  — 전체 실행 단위 (run_id, status, started_at, finished_at, stats)
pipeline_logs  — 단계별 로그 (tool_name, category, inputs, output, duration_ms, status, error_message)
```

- 원문 텍스트는 logs에 기록하지 않음 (메타데이터만)
- 로깅 실패가 파이프라인을 중단시키지 않음

관리자 페이지에서 `/api/logs`로 조회 가능.

---

## DB 스키마

```
users              — 유저 계정 (현재 TEMP_USER_ID 하드코딩)
topics             — 유저별 관심 토픽 (is_active로 활성화 관리)
contents           — 수집된 원문 + AI 요약
quizzes            — 검증된 4지선다 퀴즈
quiz_results       — 유저 퀴즈 풀이 기록
concept_levels     — 개념별 레벨 (0~100%)
streaks            — 연속 출석 기록
push_subscriptions — 웹 푸시 알림 구독
chapter_progress   — 챕터 학습 진행 상태
bookmarks          — 북마크한 콘텐츠
pipeline_runs      — 파이프라인 실행 이력
pipeline_logs      — 파이프라인 단계별 로그
```

`backend/schema.sql` + `backend/schema_v2.sql` 참고.

---

## 기술 스택

| 파트 | 기술 |
|------|------|
| Frontend | Next.js 14, Tailwind CSS, PWA |
| Backend | Python 3.10, FastAPI, APScheduler |
| DB | Supabase (PostgreSQL + RLS) |
| AI | GPT-4o-mini (OpenAI) — 요약/퀴즈생성/검증/오케스트레이션 |
| 웹 검색 | Tavily API (선택) |
| 수집 | httpx, feedparser, arxiv API |
| 배포 | Vercel (프론트) + Railway (백엔드) |

---

## 로컬 실행

### 백엔드

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # .env 값 채우기
uvicorn main:app --reload      # http://localhost:8000

# 파이프라인 수동 1회 실행
python -m agent.scheduler

# 벤치마크
python benchmark.py            # AI/ML 카테고리 기본
python benchmark.py 철학       # 특정 카테고리
```

### 프론트엔드

```bash
cd frontend
npm install
cp .env.local.example .env.local   # .env.local 값 채우기
npm run dev                         # http://localhost:3000
```

---

## 환경변수

### `backend/.env`

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SECRET_KEY=...          # 서비스 롤 키 (RLS 우회용)
OPENAI_API_KEY=...               # 필수 — 요약/퀴즈/검증/오케스트레이션
TAVILY_API_KEY=...               # 선택 — 없으면 웹 검색 스킵
FRONTEND_URL=http://localhost:3000
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 배포

### 백엔드 → Railway

1. [railway.app](https://railway.app) → New Project → GitHub 레포 연결
2. Root Directory: `backend/`
3. 환경변수 설정 (Variables 탭)
4. 자동 배포 (`backend/Procfile` + `backend/railway.toml` 참고)

### 프론트엔드 → Vercel

1. [vercel.com](https://vercel.com) → Import → GitHub 레포 연결
2. Root Directory: `frontend`
3. 환경변수 설정
4. Deploy

---

## 개발 로드맵

```
Week 1 — Agent 파이프라인 ✅
  수집(arxiv/RSS/웹) → 요약 → 퀴즈생성 → 검증 → 저장
  GPT-4o-mini Tool Use 오케스트레이션

Week 2 — API + 프론트 MVP ✅
  FastAPI 엔드포인트
  Next.js 홈/퀴즈/로드맵 화면

Week 3 — 레벨 시스템 + 배포 ✅
  챕터 학습 진행 상태
  북마크
  Railway + Vercel 배포

Week 4 — 고도화 (진행 중)
  PWA 푸시 알림
  지식 맵 시각화
  Supabase Auth 연동 (현재 TEMP_USER_ID 하드코딩)
```
