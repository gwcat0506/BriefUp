# BrefUp — AI 브리핑 학습 Agent

> 관심사를 입력하면, 매일 최신 콘텐츠를 자동 수집·요약해 퀴즈로 지식 레벨을 채워가는 PWA

---

## 핵심 철학

**"결정할 게 없어야 한다"**
완벽주의로 시작을 못 하는 패턴을 깨는 방법은 선택지를 없애는 것.
매일 아침 앱을 열면 오늘 공부할 내용이 준비되어 있다.

---

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                  Agent 파이프라인                    │
│              (매일 새벽 5시 자동 실행)               │
│                                                     │
│  STEP 1       STEP 2       STEP 3       STEP 4      │
│  수집    →    요약    →   퀴즈생성  →   검증         │
│  (API/RSS)  (Claude)    (Claude)   (Self-Verify)    │
│                                         ↓           │
│                                      STEP 5         │
│                                       저장           │
│                                    (Supabase)       │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────┐    ┌─────────────────────────────┐
│   PWA (Next.js) │    │       Backend (FastAPI)      │
│                 │    │                             │
│  홈/브리핑      │←──→│  /api/content  /api/quiz    │
│  퀴즈 풀기      │    │  /api/user                  │
│  지식 맵        │    │                             │
│  기록/마이페이지│    └─────────────────────────────┘
└─────────────────┘
```

---

## Agent 파이프라인 상세

### STEP 1 — 콘텐츠 수집 (`agent/collector.py`)

신뢰도 높은 공식 API/RSS만 사용해 노이즈 최소화.

| 카테고리 | 소스 |
|----------|------|
| AI/ML | arxiv API, HuggingFace Blog RSS, TLDR AI RSS |
| 철학 | Philosophy Bites RSS, Philosophers Mag RSS |
| 경제 | Freakonomics RSS, Economist RSS |
| 심리학 | Psychology Today RSS |

**품질 필터 3단계:**
1. 길이 체크 — 본문 150자 미만 버림
2. 관련성 체크 — 카테고리 키워드 포함 여부
3. 중복 체크 — 오늘 이미 수집된 URL 버림

### STEP 2 — 요약 생성 (`agent/summarizer.py`)

```
원문 본문 → Claude Haiku → 3~5문장 요약

규칙:
- 원문에 없는 내용 절대 추가 금지
- "핵심 포인트: ~" 형식으로 마무리
- 전문용어는 영어 그대로 유지
```

### STEP 3 — 퀴즈 생성 (`agent/quiz_gen.py`)

```
원문 본문 → Claude Haiku → 4지선다 퀴즈 2개

규칙:
- 원문에 명시된 내용만 정답/해설에 사용
- 오답 보기는 원문에서 틀린 내용으로 구성
- 개념명(concept) 반드시 포함 → 레벨 추적용
```

### STEP 4 — 자체 검증 (`agent/verifier.py`)

**Self-Verification 방식:**
Claude가 자신이 만든 퀴즈를 원문 기준으로 재검증.

```
검증 기준 (모두 통과해야 PASS):
1. 정답이 원문에서 명확히 찾을 수 있는가?
2. 오답 보기들이 원문에서는 틀린 내용인가?
3. 해설이 원문 내용과 일치하는가?
4. 문제가 명확하고 모호하지 않은가?

FAIL → 해당 퀴즈 폐기
PASS → STEP 5 저장
```

**할루시네이션 비율 (연구 기준):**
| 방식 | 할루시네이션 |
|------|------------|
| 오픈엔디드 생성 | 40~80% |
| 소스 기반 생성 | 2% 미만 |
| **소스 기반 + 검증** | **~1% 목표** |

### STEP 5 — 저장 (`agent/scheduler.py`)

검증 통과한 콘텐츠/퀴즈만 Supabase에 저장.
파이프라인 실행 결과 리포트 콘솔 출력.

---

## DB 스키마

```
users
topics          → 유저별 관심사
contents        → 수집된 콘텐츠 + 요약
quizzes         → 검증된 퀴즈
quiz_results    → 유저 퀴즈 결과
concept_levels  → 개념별 레벨 (0~100%)
streaks         → 연속 출석
push_subscriptions → 웹 푸시 알림
```

`backend/schema.sql` 참고.

---

## 기술 스택

| 파트 | 기술 |
|------|------|
| Frontend | Next.js 14, Tailwind CSS, PWA |
| Backend | Python 3.11, FastAPI, APScheduler |
| DB | Supabase (PostgreSQL + RLS) |
| AI | Claude Haiku (Anthropic) |
| 수집 | httpx, feedparser, arxiv API |
| 배포 | Vercel (프론트) + Railway (백엔드) |

---

## 로컬 실행

### 백엔드

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # .env 값 채우기
uvicorn main:app --reload      # http://localhost:8000
```

### 프론트엔드

```bash
cd frontend
npm install
cp .env.local.example .env.local   # .env.local 값 채우기
npm run dev                         # http://localhost:3000
```

---

## 벤치마크 테스트

퀴즈 정확도 측정 (목표: 검증 통과율 90% 이상)

```bash
cd backend
source venv/bin/activate
python benchmark.py            # AI/ML 카테고리 기본
python benchmark.py 철학       # 다른 카테고리 테스트
```

결과는 `benchmark_result.json`에 저장됨.

---

## 환경변수

### `backend/.env`

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SECRET_KEY=...
ANTHROPIC_API_KEY=...
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
2. `backend/` 폴더 선택
3. 환경변수 설정 (Variables 탭)
4. 자동 배포

### 프론트엔드 → Vercel

1. [vercel.com](https://vercel.com) → Import → GitHub 레포 연결
2. Root Directory: `frontend`
3. 환경변수 설정
4. Deploy

---

## 개발 로드맵

```
Week 1 — Agent 파이프라인 ✅
  수집 → 요약 → 퀴즈생성 → 검증 → 저장

Week 2 — API + 프론트 MVP
  FastAPI 엔드포인트
  Next.js 홈/퀴즈 화면

Week 3 — 레벨 시스템 + 배포
  개념 레벨 추적
  스트릭 시스템
  Railway + Vercel 배포

Week 4 — 고도화
  PWA 푸시 알림
  지식 맵 시각화
  다양한 카테고리 확장
```
