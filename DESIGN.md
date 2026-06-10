# BriefUp 설계 의도 문서

> 발표용 — 각 기능을 **왜** 그렇게 만들었는지 설명합니다.

---

## 목차

1. [서비스 개요](#1-서비스-개요)
2. [파이프라인 아키텍처](#2-파이프라인-아키텍처)
3. [콘텐츠 수집 전략](#3-콘텐츠-수집-전략)
4. [AI 퀴즈 생성과 자체 검증](#4-ai-퀴즈-생성과-자체-검증)
5. [에이전트 설계 — Claude + FastMCP](#5-에이전트-설계--claude--fastmcp)
6. [커리큘럼 시스템](#6-커리큘럼-시스템)
7. [학습 동기 시스템](#7-학습-동기-시스템)
8. [프론트엔드 UX 설계](#8-프론트엔드-ux-설계)
9. [인프라와 배포 전략](#9-인프라와-배포-전략)

---

## 1. 서비스 개요

**BriefUp**은 사용자의 관심사(예: RAG, 양자컴퓨팅, 철학)에 맞춰 최신 콘텐츠를 자동 수집·요약하고 퀴즈로 지식 레벨을 쌓아가는 AI 학습 서비스입니다.

### 해결하려는 문제

- 공부하고 싶은데 **뭘 읽어야 할지** 모른다
- 긴 논문/아티클을 읽어도 **기억에 남지 않는다**
- 꾸준히 하려고 하는데 **습관이 형성되지 않는다**

### 핵심 루프

```
파이프라인 실행 → AI 요약 → AI 퀴즈 생성 → 검증
→ 유저: 브리핑 읽기 → 퀴즈 풀기 → 개념 레벨 상승 → 스트릭 유지
```

---

## 2. 파이프라인 아키텍처

### 전체 흐름

```
파이프라인 실행 (POST /api/content/run-pipeline or python -m agent.scheduler)
  └─ agent_runner.py (Claude Haiku 4.5 + FastMCP Client)
       ├─ get_active_topics()       ← DB에서 유저 관심사 조회
       ├─ get_collection_plan()     ← 오늘 다룰 챕터 + 검색 힌트
       ├─ collect_articles()        ← arxiv + RSS + 웹 검색 병렬 수집
       ├─ summarize_article()       ← GPT-4o-mini 요약
       ├─ generate_quizzes()        ← GPT-4o-mini 퀴즈 생성 + 자동 검증
       └─ save_content()            ← Supabase 저장
```

### 두 모델의 역할 분리

| 역할 | 모델 | 이유 |
|------|------|------|
| **오케스트레이션** (어떤 도구를 어떤 순서로 쓸지 판단) | Claude Haiku 4.5 | Tool Use + 지시 이해 능력. 도구 조합 판단에 강함 |
| **콘텐츠 생성** (요약, 퀴즈, 검증) | GPT-4o-mini | 한국어 콘텐츠 생성 품질, 비용 효율 |
| **커리큘럼 설계** (동적 챕터 구성) | Claude Haiku 4.5 | 구조적 JSON 생성, 교육 콘텐츠 설계 능력 |

두 모델을 섞어 쓰는 이유: 각 모델이 잘하는 것이 다릅니다. 오케스트레이션은 Claude가, 대량 반복 처리(요약·퀴즈)는 GPT-4o-mini가 담당해 **품질과 비용을 모두 최적화**합니다.

### 비용 추적

```python
_HAIKU_IN  = 1.00 / 1_000_000   # Claude Haiku 4.5 input
_HAIKU_OUT = 5.00 / 1_000_000   # Claude Haiku 4.5 output
_GPT_IN    = 0.15 / 1_000_000   # GPT-4o-mini input
_GPT_OUT   = 0.60 / 1_000_000   # GPT-4o-mini output
```

파이프라인 실행마다 Claude/GPT 각각 토큰을 집계해 USD 비용을 계산합니다. pipeline_runs.stats에 저장 → `/api/logs/runs`로 조회 가능.

---

## 3. 콘텐츠 수집 전략

### 커리큘럼 기반 수집 (신규)

기존에는 topic_name을 그대로 검색 쿼리로 썼습니다. 문제: "양자컴퓨팅"을 검색하면 매일 같은 결과가 나오고, 초보자에게 어려운 논문이 섞입니다.

새 방식: 커리큘럼의 **챕터별 검색 힌트**를 사용합니다.

```python
# get_collection_plan이 반환하는 today_chapter 예시
{
  "id": "quantum-2",
  "title": "큐비트와 양자 게이트",
  "search_hints": {
    "arxiv_query": "qubit quantum gate circuit implementation",
    "web_query": "what is qubit quantum computing explained simply"
  }
}
```

- **arxiv_query**: 학술 논문에 적합한 영문 쿼리
- **web_query**: 웹 검색에 적합한 영문 쿼리 (더 쉬운 설명 찾기)
- 챕터 순서대로 진행 → `기수집 날짜 수 % 전체 챕터 수`로 오늘 챕터 자동 결정

### 3-tier 수집 소스

| 소스 | 역할 | 특징 |
|------|------|------|
| **arxiv** | 최신 연구 논문 | 챕터 arxiv_query로 정밀 검색. AI/ML에 특히 강력 |
| **RSS** | 신뢰도 높은 미디어 | HuggingFace, Economist 등 카테고리별 고품질 소스 |
| **Tavily 웹 검색** | 쉬운 설명 찾기 | 챕터 web_query로 초보자용 설명 자료 보완 |

### 웹 콘텐츠 신뢰도 필터링

```
신뢰도 점수 = Tavily 관련성 × 0.6 + 도메인 점수 × 0.4
```

- arxiv.org, nature.com → 1.0점
- openai.com, anthropic.com → 0.9점
- medium.com → 0.5점
- acronymfinder.com, dictionary.com → 0.0점 (블랙리스트)
- 0.65점 미만 → 자동 제외

**왜?** Tavily는 관련성은 잘 잡지만 소스 신뢰도를 모릅니다. 도메인 점수를 40% 가중치로 섞어 약어 사전, 광고성 사이트가 섞이는 걸 막습니다.

### 품질 필터 3단계

1. **길이 체크**: 150자 미만 제거 (스니펫, 광고 문구 등)
2. **관련성 체크**: topic_name 키워드가 제목/본문에 포함되는지 확인
3. **중복 체크**: 오늘 이미 저장된 URL은 건너뜀 (배치 쿼리 1회)

---

## 4. AI 퀴즈 생성과 자체 검증

### 생성 원칙

```
❌ "다음 중 Chunking의 overlap 파라미터 역할은?"  → 암기식, 지엽적
✅ "RAG 시스템을 도서관에 비유하면, 검색은 어떤 역할일까요?"  → 이해 확인
```

프롬프트에 "좋은 예시"와 "나쁜 예시"를 모두 명시해 GPT가 암기식 문제를 만들지 않도록 강제합니다.

### 왜 자체 검증(verifier.py)이 필요한가?

LLM은 퀴즈를 만들 때 **원문에 없는 내용을 만들어낼 수 있습니다(할루시네이션)**. 잘못된 퀴즈를 유저에게 보여주면 오히려 잘못된 지식을 심어줍니다.

```
[생성된 퀴즈]
  ↓
[별도 GPT 호출로 검증]
  "이 퀴즈의 정답이 원문에서 찾을 수 있는가?"
  "오답들이 원문 기준으로 틀린 내용인가?"
  ↓
PASS → 저장
FAIL → 폐기
```

실측 통과율: 약 30~40%. 엄격한 기준(불확실하면 탈락)을 의도적으로 유지한 결과다.

### 검증 실패 시 탈락 처리 (이전 버전과 다름)

```python
# 이전 (v1): 검증 오류 시 "보수적으로 통과"
except Exception as e:
    quiz["verified"] = False
    passed.append(quiz)  # 일단 통과

# 현재: 검증 오류 시 탈락 (silent pass 금지)
except Exception as e:
    failed_count += 1   # 불확실하면 탈락
    print(f"[검증 오류-FAIL]")
```

**왜 바꿨나?** 이전에는 "콘텐츠가 0개가 되는 것보다 낫다"는 이유로 오류 시 통과시켰습니다. 그런데 검증이 실패했다는 것은 해당 퀴즈의 품질을 보장할 수 없다는 뜻입니다. 잘못된 퀴즈 하나가 유저에게 미치는 피해가 더 크므로, 불확실하면 탈락이 맞습니다.

### 검증 원문 범위 개선

```python
# 이전: 원문 앞 2000자만 사용
source_text[:2000]

# 현재: 앞 1500자 + 뒤 500자 (긴 원문에서 뒷부분 결론도 반영)
text = source_text[:1500] + source_text[-500:]
```

긴 논문의 경우 결론이 뒷부분에 있어 앞부분만 보면 검증 오류가 납니다.

### 모든 AI 호출이 토큰 사용량 반환

```python
# summarize, generate_quizzes, verify_and_filter 모두 동일 패턴
summary, usage = await summarize(title, text, category)
quizzes, usage = await generate_quizzes(title, text, category)
passed, usage  = await verify_and_filter(quizzes, text)

# usage = {"input": <tokens>, "output": <tokens>}
```

비용 추적을 위해 모든 OpenAI 호출이 (결과, 토큰) 튜플을 반환합니다.

---

## 5. 에이전트 설계 — Claude + FastMCP

### 아키텍처 변천

```
v1: OpenAI GPT-4o-mini
    └─ agent_runner.py가 TOOL_SCHEMAS 직접 관리
       └─ 도구 함수를 mcp_tools.py에서 직접 호출

v2 (현재): Claude Haiku 4.5 + FastMCP
    └─ agent_runner.py → FastMCP Client → mcp_server.py 도구들
       └─ 도구는 @mcp.tool() 데코레이터로 정의
```

### 왜 FastMCP로 바꿨나?

| 항목 | v1 (직접 Tool Use) | v2 (FastMCP) |
|------|------|------|
| 도구 등록 | TOOL_SCHEMAS 딕셔너리 수동 관리 | `@mcp.tool()` 데코레이터로 자동 등록 |
| 외부 연결 | 불가 | `python -m agent.mcp_server`로 Claude Desktop 등에서 직접 연결 가능 |
| 스키마 생성 | 수동 작성 | 타입 힌트 + docstring에서 자동 생성 |
| 모델 교체 | GPT 종속 | `client.create(model=...)` 파라미터만 바꾸면 됨 |

FastMCP는 도구 정의를 `@mcp.tool()`로 선언적으로 관리할 수 있어 유지보수가 훨씬 간단합니다. 또한 같은 MCP 서버를 Claude Desktop 같은 외부 도구에도 연결할 수 있습니다.

### In-process MCP 연결

```python
async with Client(mcp) as mcp_client:           # mcp 객체를 직접 넘김 (stdio 없음)
    tools = await mcp_client.list_tools()       # 도구 목록 동적 조회
    result = await mcp_client.call_tool(...)    # 도구 실행
```

별도 프로세스 없이 in-process로 연결합니다. 오버헤드 없이 MCP 표준을 따릅니다.

### 세션 스토어 패턴

```python
_session = {
    "articles": {},  # article_id → {title, text, source, url, summary?, quizzes?}
    "run_stats": {"total_contents": 0, "total_quizzes": 0, "tokens": {...}},
    "logger": None,
}
```

**에이전트(Claude)에는 article_id와 메타데이터만 보여줍니다. 원문 텍스트는 Python 세션에만 존재합니다.**

왜? 원문 텍스트를 Claude 메시지에 넣으면:
- 토큰 비용 폭증 (아티클 하나당 2,000~3,000 토큰)
- Claude가 직접 원문을 다루면서 할루시네이션 위험 증가
- 컨텍스트 길이 초과 위험

Claude는 "어떤 아티클을 어떤 순서로 처리할지"만 결정하고, 실제 텍스트 처리는 Python이 담당합니다.

### 병렬 실행

```python
# Claude가 병렬로 요청한 tool_use들을 실제로 asyncio.gather로 병렬 실행
results = await asyncio.gather(
    *[mcp_client.call_tool(b.name, b.input) for b in tool_blocks],
    return_exceptions=True,
)
```

Claude가 여러 토픽의 `collect_articles`를 한 응답에서 동시에 요청하면, Python이 실제로 병렬 처리합니다.

### 새 도구: get_collection_plan

```python
@mcp.tool()
async def get_collection_plan(topic_name: str, category: str) -> dict:
    """
    커리큘럼 기반으로 오늘 수집할 챕터와 검색 힌트를 반환합니다.
    collect_articles 호출 전에 반드시 먼저 호출하세요.
    """
```

collect_articles 전에 항상 이 도구를 먼저 호출해 오늘 어떤 챕터를 다룰지, 어떤 쿼리로 검색할지 계획을 잡습니다. 기수집 날짜 수를 기준으로 다음 챕터를 자동으로 결정합니다.

---

## 6. 커리큘럼 시스템

### 두 가지 커리큘럼 소스

| 소스 | 파일 | 용도 |
|------|------|------|
| **하드코딩 카탈로그** | `curriculum_catalog.py` | 10개 주요 트랙 (RAG, Agent, LLM 등) 초기 데이터 |
| **동적 AI 생성** | `curriculum_gen.py` | 유저가 임의 관심사 추가 시 Claude가 자동 생성 |

두 소스 모두 `topic_curricula` DB 테이블에 캐시됩니다. `seed_curricula.py`가 초기 카탈로그를 DB에 삽입합니다.

### curriculum_gen.py — Claude가 커리큘럼 설계

유저가 "딥러닝 최적화"같은 새 관심사를 추가하면:

```python
# user.py - POST /api/user/topic
curriculum = await get_or_create_curriculum(body.name, category)
```

Claude Haiku가 즉시:
1. 5~7개 챕터 구성 (기초 → 심화)
2. 각 챕터에 "독자가 진짜 궁금해할 질문" 형식 제목
3. 챕터별 검색 힌트 (arxiv_query, web_query)
4. 동의어 목록 (topic_aliases: "주식" = "주식/투자")

**왜 Claude를 커리큘럼 설계에 쓰나?** GPT보다 Claude가 구조적 JSON 생성과 교육 콘텐츠 설계에서 더 일관된 결과를 보여줬습니다. 또한 이미 에이전트에서 Claude를 쓰고 있어 ANTHROPIC_API_KEY가 있으면 추가 비용 없음.

### DB 캐시 + alias 매칭

```python
# 1. topic_key로 직접 조회
existing = supabase.table("topic_curricula").eq("topic_key", topic_key)

# 2. 없으면 alias로 검색 ("주식" → "주식/투자" 커리큘럼 재사용)
alias_match = supabase.table("topic_curricula").contains("topic_aliases", [topic_name])

# 3. 그래도 없으면 Claude로 신규 생성 → DB 저장
curriculum = await _generate_curriculum(topic_name, category, topic_key)
```

동의어 매칭으로 비슷한 관심사에 대해 중복 생성을 방지합니다.

### 챕터 순환 로직

```python
# contents 테이블에서 이 토픽의 기수집 날짜 수 조회
count_res = supabase.table("contents")
    .select("collected_at")
    .eq("topic_category", topic_name)
    .execute()

collected_dates = {r["collected_at"] for r in count_res.data}

# 수집이 쌓일수록 자동으로 다음 챕터로 진행
chapter_index = len(collected_dates) % len(chapters)
```

수집 횟수가 쌓일수록 자동으로 다음 챕터로 진행합니다. 전체 챕터를 소화하면 처음으로 순환합니다.

### curriculum_catalog.py — 단일 소스 오브 트루스 (하드코딩)

하드코딩된 10트랙은 여전히 유지됩니다. `seed_curricula.py`가 이를 DB에 넣고, 이후에는 DB가 권위 있는 소스가 됩니다.

```python
# chapter.py (학습 내용 생성) - CHAPTERS 사용
from agent.curriculum_catalog import CHAPTERS

# progress.py (로드맵 API) - CURRICULUM_CATALOG 사용
from agent.curriculum_catalog import CURRICULUM_CATALOG
```

### 챕터 잠금 해제 시퀀스

```
챕터 1: 항상 열림
챕터 N: 챕터 N-1 완료 시 해금
```

**왜?** 고급 내용을 먼저 보면 좌절하기 쉽습니다. 기초 → 기본 → 심화 순서가 학습 효과를 높입니다.

### 챕터 즉시 생성 + 캐싱 (chapter.py)

```python
# DB에 캐시된 것 있으면 즉시 반환
cached = supabase.table("contents").select("*").eq("source", f"chapter:{chapter_id}").execute()
if cached.data:
    return cached.data[0]  # 캐시 히트

# 없으면 GPT-4o-mini로 즉시 생성
cards = await client.chat.completions.create(model="gpt-4o-mini", ...)
supabase.table("contents").insert({...}).execute()  # 캐시 저장
```

**왜 미리 생성하지 않나?** 50개 챕터를 모두 미리 생성하면 비용이 크고 대부분 안 읽힙니다. 첫 접근 시 즉시 생성, 이후 캐시를 쓰는 방식이 합리적입니다.

### 5-카드 학습 형식

| 카드 타입 | 역할 | 예시 |
|-----------|------|------|
| hook | 공감 유도 | "혹시 검색해도 원하는 답이 안 나온 경험 있나요?" |
| concept | 핵심 개념 설명 | "RAG는 마치 오픈북 시험처럼..." |
| example | 실제 사례 | "ChatGPT가 최신 정보를 모르는 이유가..." |
| insight | 핵심 인사이트 | "결국 AI의 '기억'을 외부화한 것" |
| summary | 3가지 요점 | 기억하기 쉬운 불릿 포인트 |

모바일에서 스와이프하며 읽을 수 있는 짧은 카드 형식. 한 카드에 3~5문장만 담아 모바일 집중력에 맞춤.

---

## 7. 학습 동기 시스템

### 개념 레벨 (concept_levels)

퀴즈를 맞히면 해당 개념의 레벨이 +5씩 오릅니다(최대 100). 틀려도 내려가지 않습니다.

**왜 틀렸을 때 깎지 않나?** 레벨이 떨어지면 유저가 좌절하고 포기합니다. 맞히면 오르기만 하는 구조로 항상 "성장하고 있다"는 느낌을 줍니다.

### 복습 퀴즈 자동 재출제

```python
# 정답률 50% 미만 개념 중 오래된 것부터 재출제
weak = supabase.table("concept_levels")
    .lt("level", 50)
    .order("level")
    .limit(5)
```

틀린 개념은 다음 날 다시 나옵니다. **간격 반복 학습(Spaced Repetition)** 원리를 단순화한 구현입니다.

### 스트릭 시스템

- 매일 퀴즈 제출 시 스트릭 +1
- 7일, 30일, 100일, 365일 마일스톤에 배지 지급
- **스트릭 프리즈**: 하루를 빠졌을 때 구제 아이템

**왜 프리즈가 있나?** Duolingo 연구에서 스트릭이 끊기는 순간 이탈률이 급증합니다. 프리즈를 제공하면 "이미 끊겼으니까 그냥 관뒀지"라는 심리를 막을 수 있습니다.

### 상태별 배너

```
done      → 오늘 학습 완료! (배너 없음)
pending   → "오늘 아직 안 했어요! 위험" (주황 배너)
freezeable → "프리즈 사용할까요?" (프리즈 버튼)
broken    → "다시 시작! 💪" (빨간 배너)
```

매일 앱을 열 때 현재 상태를 즉시 전달해 행동을 유도합니다.

---

## 8. 프론트엔드 UX 설계

### Promise.allSettled로 부분 로딩

```typescript
// 한 API가 실패해도 다른 데이터는 정상 표시
Promise.allSettled([
  api.getStreak(TEMP_USER_ID),
  api.getLevels(TEMP_USER_ID),
  api.getStreakStatus(TEMP_USER_ID),
]).then(([s, l, status]) => {
  if (s.status === "fulfilled") setStreak(s.value);
})
```

`Promise.all`을 쓰면 하나가 실패했을 때 화면 전체가 빈칸이 됩니다. `Promise.allSettled`는 각 결과를 독립적으로 처리해 부분적으로라도 화면을 채웁니다.

### 통계 카드 먼저, 콘텐츠는 나중에

```typescript
// 1단계: 빠른 통계 (streak, levels)
Promise.allSettled([...빠른 API...]).then(() => setStatsLoading(false));

// 2단계: 느린 콘텐츠 (브리핑, 챕터 추천)
Promise.allSettled([...느린 API...]).then(() => setLoading(false));
```

유저가 앱을 열면 스트릭/레벨부터 바로 보입니다. Perceived performance를 높입니다.

### 퀴즈 폴백 체인

```typescript
// 브리핑별 퀴즈 없으면 → 오늘 전체 퀴즈로 폴백
api.getQuizzesByContent(contentId)
  .catch(() => api.getTodayQuizzes(TEMP_USER_ID))
```

특정 브리핑의 퀴즈가 아직 생성 안 됐더라도 빈 화면 대신 오늘의 퀴즈를 보여줍니다.

### 퀴즈 즉시 피드백 (Optimistic UI)

선택지를 고르면 **API 응답을 기다리지 않고** 선택한 항목을 연한 초록으로 강조합니다. API 응답이 오면 정답/오답 색으로 전환합니다. 체감 응답 속도를 높이는 패턴입니다.

### 로드맵 API 실패 시 폴백

```typescript
.catch(() => {
  // Render Free 티어 콜드 스타트 등으로 API 실패 시
  // 기본 3트랙(RAG, Agent, LLM)을 하드코딩으로 표시
  setCurricula(fallback);
})
```

Render Free 티어는 15분 비활성 후 슬립 → 첫 요청 30~60초 소요. 이 시간 동안 로드맵 화면이 빈칸이 되지 않도록 기본 트랙을 하드코딩으로 보여줍니다.

### 모바일 최적화

- 모든 페이지: `max-w-md mx-auto` (모바일 중심 레이아웃)
- 터치 피드백: `active:scale-[0.98]`, `active:scale-95`
- 스켈레톤 UI: 로딩 중 레이아웃 유지 (Layout Shift 방지)

---

## 9. 인프라와 배포 전략

### 프론트엔드: Vercel

- Next.js App Router와 최적화된 통합
- 자동 HTTPS, CDN, 프리뷰 배포
- 배포: `cd frontend && vercel --prod`

### 백엔드: Render Free 티어

**왜 Free 티어?** MVP 단계에서 비용을 0으로 유지. 단점(콜드 스타트 30~60초)은 프론트엔드 폴백으로 커버.

**왜 FastAPI?** 비동기(async/await)가 필수인 파이프라인(여러 API 동시 호출)에서 Flask보다 훨씬 빠릅니다.

### PipelineLogger (관찰 가능성)

```python
logger.log_step(tool_name="collect", status="success", duration_ms=1200, ...)
```

파이프라인의 모든 단계를 `pipeline_logs` 테이블에 기록합니다.

**왜 필요한가?** Render Free 티어는 로그가 사라집니다. 파이프라인이 어느 단계에서 실패했는지 추적하려면 DB에 기록해야 합니다.

### TEMP_USER_ID 하드코딩

```python
TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"
```

현재 MVP에서 Supabase Auth가 연동되어 있지 않습니다. Auth를 붙이면 이 상수만 Supabase의 실제 user.id로 교체하면 됩니다.

---

## 요약: 핵심 설계 원칙

| 원칙 | 구현 |
|------|------|
| **역할별 최적 모델 선택** | 오케스트레이션·커리큘럼 설계 = Claude Haiku, 콘텐츠 생성 = GPT-4o-mini |
| **AI는 판단만, 데이터는 Python이** | 세션 스토어로 원문 텍스트를 Claude에 노출하지 않음 |
| **커리큘럼 기반 구조화된 수집** | 매일 다른 챕터, 챕터별 검색 힌트로 정밀 타겟팅 |
| **병렬 처리로 속도 확보** | asyncio.gather로 여러 토픽/아티클 동시 처리 |
| **할루시네이션은 검증으로** | verifier.py가 생성된 퀴즈를 원문 기준으로 재검증, 오류 시 탈락 |
| **실패해도 계속 진행** | 하나의 아티클/토픽 실패가 전체를 멈추지 않음 |
| **동적 관심사 기반 개인화** | 임의 관심사 → Claude가 커리큘럼 자동 설계 → DB 캐시 |
| **학습 지속성을 위한 동기 설계** | 스트릭, 복습 퀴즈, 마일스톤으로 이탈 방지 |
| **모바일 UX 우선** | 5-카드 형식, Skeleton UI, Optimistic UI, 폴백 체인 |
| **비용 투명성** | 매 실행마다 Claude + GPT 토큰 집계 → USD 비용 로깅 |
