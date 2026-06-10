# BriefUp — AI 브리핑 학습 서비스

> 관심사를 입력하면 AI 에이전트가 커리큘럼을 짜고, 매일 최신 콘텐츠를 수집·요약해 퀴즈로 지식을 쌓아가는 PWA

**프로덕션:** https://brief-up.vercel.app  
**백엔드 API:** https://briefup.onrender.com  
**설계 의도 상세:** [DESIGN.md](./DESIGN.md)

---

## 핵심 아이디어

**"결정할 게 없어야 한다"**

완벽주의로 시작을 못 하는 패턴을 깨는 방법은 선택지를 없애는 것.  
관심사 하나만 고르면 AI가 커리큘럼을 짜고, 매일 어떤 챕터를 공부할지 정하고, 아티클을 찾아 요약하고, 퀴즈를 만든다.

```
유저가 하는 것  →  관심사 입력
AI가 하는 것    →  커리큘럼 설계 + 매일 콘텐츠 수집 + 요약 + 퀴즈 생성 + 검증
```

---

## 기술적으로 흥미로운 부분 3가지

### 1. Claude가 도구를 자율적으로 선택한다

고정된 함수 호출 순서가 아니다. Claude Haiku가 중간 결과를 보고 다음 행동을 직접 판단한다.

- 수집된 아티클이 토픽과 관련 없으면 → 건너뛴다
- 요약 충실도가 0.7 미만이면 → 퀴즈 생성 없이 탈락
- 수집 결과가 부족하면 (`needs_retry=true`) → 더 넓은 쿼리로 재시도
- `verified_count=0`이면 → `save_content`를 호출하지 않는다

```
Claude Haiku 4.5  ←→  FastMCP (in-process)
                        ├── get_active_topics       DB 활성 토픽 목록
                        ├── get_collection_plan     오늘 챕터 + 검색 쿼리
                        ├── collect_articles        arxiv / RSS / Tavily
                        ├── summarize_article       GPT-4o-mini 요약 → 충실도 검증
                        ├── generate_quizzes        GPT-4o-mini 생성 → 교차 검증
                        └── save_content            Supabase 저장
```

### 2. 두 모델이 역할을 나눈다

| 역할 | 모델 |
|------|------|
| 오케스트레이션, 커리큘럼 설계, 요약 검증 | Claude Haiku 4.5 |
| 요약 생성, 퀴즈 생성, 퀴즈 검증 | GPT-4o-mini |

GPT가 만든 퀴즈를 Claude가 검증한다. 같은 모델이 만들고 검증하면 blind spot이 겹치기 때문이다.

### 3. 세션 스토어로 원문을 Claude에 숨긴다

원문 텍스트는 Python `_session["articles"]`에만 보관한다.  
Claude에는 `article_id + 메타데이터`만 노출한다.

```python
# Claude가 받는 것 (token 절약)
{"id": "rag_3f8a2c", "title": "RAG Chunking Strategies", "text_length": 4200, "text_preview": "..."}

# Python이 보관하는 것 (Claude에 비공개)
{"title": "...", "text": "전체 원문 4200자", "url": "..."}
```

원문을 Claude 컨텍스트에 넣으면 아티클 1개당 2,000~3,000 토큰이 소비된다.  
Claude는 "어떤 아티클을 어떤 순서로 처리할지"만 판단하고, 실제 텍스트 처리는 Python이 담당한다.

---

## 전체 실행 흐름

```
1. 유저가 관심사 추가 (예: "양자컴퓨팅")
   └─ Claude Haiku → 12~14챕터 커리큘럼 자동 생성 + DB 캐시
   └─ 즉시 파이프라인 백그라운드 실행 → 첫 브리핑 1~2분 내 생성

2. 매일 파이프라인 실행
   ├─ get_collection_plan: 기수집 날짜 수 % 전체 챕터 수 = 오늘 챕터 결정
   ├─ collect_articles: 챕터 검색 힌트(arxiv_query + web_query)로 수집
   ├─ summarize_article × N 병렬: GPT-4o-mini 요약 → Claude 충실도 검증(≥0.7)
   ├─ generate_quizzes × N 병렬: GPT-4o-mini 생성 → Claude 교차 검증
   └─ save_content: 검증 통과한 것만 Supabase 저장

3. 유저 사용
   ├─ 홈: 오늘의 브리핑 카드 (토픽별 최대 3개)
   ├─ 퀴즈: 브리핑 기반 4지선다 → 개념 레벨 상승
   ├─ 로드맵: 챕터 진행 상황 시각화
   └─ 스트릭: 매일 학습 연속 기록
```

---

## 커리큘럼 기반 수집

관심사 이름을 그대로 검색 쿼리로 쓰면 매일 같은 결과가 나온다.  
대신 커리큘럼의 **챕터별 검색 힌트**를 쓴다.

```json
{
  "chapter": "Chunking이 검색 품질을 결정한다 (3/13)",
  "arxiv_query": "document chunking strategies retrieval augmented generation 2024",
  "web_query": "RAG chunking semantic fixed size comparison best practices 2024"
}
```

`get_collection_plan`은 `len(기수집날짜) % len(챕터목록)`으로 오늘 챕터를 결정한다.  
수집이 쌓일수록 자동으로 다음 챕터로 진행한다.

---

## 퀴즈 교차 검증

```
GPT-4o-mini → 퀴즈 생성
                 ↓
Claude Haiku → 검증 (원문에 근거 있는가? 단순 암기 문제 아닌가?)
                 ↓
         PASS → DB 저장   FAIL → 폐기
```

실제 결과: 생성된 퀴즈의 약 30~40%가 검증을 통과한다.  
엄격한 기준(불확실하면 탈락)을 유지한 결과다.

---

## 파이프라인 실제 실행 기록

```
[iteration 1]  get_collection_plan(RAG) → 챕터 3/13: Chunking이 검색 품질을 결정한다
[iteration 2]  collect_articles × 5토픽 동시  (arxiv 4개 + 웹 7개 = 11개 수집)
[iteration 3]  summarize_article × 11개 동시
               [충실도 PASS] rag_a3f2  score=0.95
               [충실도 미달] rag_b8c1  score=0.35  → 스킵
[iteration 4]  generate_quizzes × 통과 아티클
               [PASS] "Chunking 전략 비교" — 원문 근거 명확
               [FAIL] "RAG란 무엇인가?" — 단순 정의 암기 문제
[iteration 5]  save_content × 검증 통과분
[iteration 6]  save_reflection → 다음 실행 전략 기록

비용: $0.10 / 실행  |  저장: 3~5개 콘텐츠 + 퀴즈
```

---

## 주요 설계 결정

| 결정 | 이유 |
|------|------|
| Claude가 도구를 자율 선택 | 고정 파이프라인은 중간 실패 시 복구 불가. 에이전트가 결과 보고 판단 |
| 세션 스토어로 원문 격리 | 원문 노출 시 토큰 비용 폭증 + 할루시네이션 위험 |
| GPT 생성 → Claude 검증 | 같은 모델이 생성·검증하면 blind spot 공유. 교차 검증으로 방지 |
| 검증 오류 시 탈락 (통과 아님) | 불확실한 퀴즈가 유저에게 미치는 피해가 더 큼 |
| asyncio.gather 병렬 실행 | 토픽 N개 → N배 빠름 |
| 커리큘럼 DB 캐시 | 동일 토픽 재생성 없이 즉시 반환. 동의어 매칭(주식 = 주식/투자) |
| 레벨 하락 없음 | 레벨이 떨어지면 좌절 → 이탈. 항상 성장하는 느낌 유지 |
| 스트릭 프리즈 | 하루 빠진 순간 이탈률 급증. Duolingo 연구 기반 |

---

## 현재 구현 범위 (MVP)

**완성된 것**

- AI 에이전트 파이프라인 (커리큘럼 → 수집 → 요약 → 퀴즈 → 검증 → 저장)
- 임의 관심사 추가 → 커리큘럼 자동 생성 → 즉시 파이프라인 실행
- 브리핑 카드 / 퀴즈 / 로드맵 / 스트릭 / 개념 레벨
- 파이프라인 실행 비용 추적 (Claude + GPT 토큰 → USD)

**MVP 이후 과제**

- 일일 자동 스케줄러 (현재는 수동 트리거)
- 사용자 인증 (현재 `TEMP_USER_ID` 하드코딩)
- 퀴즈 통과율 개선 (현재 ~33%)

---

## 기술 스택

| 파트 | 기술 |
|------|------|
| Frontend | Next.js 14 (App Router), Tailwind CSS, PWA |
| Backend | Python 3.11, FastAPI, asyncio |
| DB | Supabase (PostgreSQL) |
| AI 오케스트레이션 | Claude Haiku 4.5 + FastMCP |
| AI 콘텐츠 생성 | GPT-4o-mini |
| 웹 검색 | Tavily API |
| 배포 | Vercel (프론트) + Render Free (백엔드) |

---

## 로컬 실행

```bash
# 백엔드
cd backend
cp .env.example .env        # API 키 입력
pip install -r requirements.txt
uvicorn main:app --reload   # http://localhost:8000

# 파이프라인 수동 실행
python -m agent.scheduler

# 프론트엔드
cd frontend
cp .env.local.example .env.local
npm install
npm run dev                 # http://localhost:3000
```

환경변수: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `TAVILY_API_KEY`
