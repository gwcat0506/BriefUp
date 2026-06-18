# DB Schema

Supabase (PostgreSQL). 마이그레이션 파일 없음 — 코드 기반 관리.

---

## 테이블 목록

### users
사용자 계정.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| email | TEXT | |
| nickname | TEXT | |
| xp | INTEGER | 레벨 시스템 포인트 |
| created_at | TIMESTAMP | |

---

### topics
사용자 관심사. users : topics = 1 : N.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| name | TEXT | 예: "RAG", "심리학" |
| category | TEXT | 예: "AI/ML", "철학" |
| is_active | BOOLEAN | |
| created_at | TIMESTAMP | |

---

### contents
파이프라인이 수집·요약한 아티클.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| topic_category | TEXT | topics.name과 매칭 |
| source | TEXT | `"arxiv"` \| `"rss"` \| `"web"` \| `"chapter:<id>"` |
| title | TEXT | |
| summary | TEXT | GPT-4o-mini 생성 |
| original_url | TEXT | 원본 링크 |
| collected_at | DATE | 수집 날짜 |
| created_at | TIMESTAMP | |

---

### quizzes
contents : quizzes = 1 : N.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| content_id | UUID FK → contents.id | |
| question | TEXT | |
| options | JSON | `{"1": "보기1", "2": "보기2", ...}` |
| answer | TEXT | `"1"` \| `"2"` \| `"3"` \| `"4"` |
| explanation | TEXT | 정답/오답 해설 |
| concept | TEXT | 핵심 개념명 |
| difficulty | INTEGER | 1=입문, 2=기본, 3=중급 |
| created_at | TIMESTAMP | |

---

### quiz_results
퀴즈 풀이 기록.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| quiz_id | UUID FK → quizzes.id | |
| content_id | UUID FK → contents.id | |
| selected | TEXT | `"1"` \| `"2"` \| `"3"` \| `"4"` |
| is_correct | BOOLEAN | |
| answered_at | TIMESTAMP | |

---

### concept_levels
개념별 숙련도. 퀴즈 정답 시 +5.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| concept | TEXT | quizzes.concept과 매칭 |
| category | TEXT | |
| level | INTEGER | 0–100 |
| total_attempts | INTEGER | |
| correct_attempts | INTEGER | |
| created_at | TIMESTAMP | |

복습 추천: `level < 50` 기준으로 약한 개념 조회.

---

### streaks
연속 학습 기록.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| current_streak | INTEGER | 현재 연속 일수 |
| longest_streak | INTEGER | 최고 기록 |
| freeze_available | INTEGER | 스트릭 프리즈 개수 |
| last_active_date | DATE | 마지막 활동 날짜 |
| created_at | TIMESTAMP | |

---

### chapter_progress
챕터별 진행 상태. 복합 PK (user_id, chapter_id).

| 컬럼 | 타입 | 설명 |
|------|------|------|
| user_id | UUID FK → users.id | PK 복합 |
| chapter_id | TEXT | PK 복합, 예: `"rag-1"` |
| track | TEXT | 트랙명, 예: `"rag"` |
| status | TEXT | `"started"` \| `"completed"` \| `"locked"` |
| quiz_score | INTEGER | |
| quiz_total | INTEGER | |
| completed_at | TIMESTAMP | nullable |
| created_at | TIMESTAMP | |

upsert 시 `on_conflict="user_id,chapter_id"`.

---

### topic_curricula
동적 커리큘럼 캐시. 토픽 추가 시 Claude Haiku가 생성.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| topic_key | TEXT | 정규화 키, 예: `"rag"` |
| topic_name | TEXT | 원래 이름 |
| category | TEXT | |
| topic_aliases | JSON ARRAY | 동의어 목록 |
| emoji | TEXT | |
| color | TEXT | hex 색상 |
| description | TEXT | |
| chapters | JSON | 챕터 배열 (아래 구조 참조) |
| created_at | TIMESTAMP | |

**chapters 원소 구조:**
```json
{
  "id": "rag-1",
  "title": "챕터 제목",
  "description": "학습 결과 설명",
  "level": "입문|기본|중급|심화",
  "duration": "10분",
  "concepts": ["개념1", "개념2"],
  "search_hints": {
    "arxiv_query": "arxiv 검색어 또는 null",
    "web_query": "웹 검색어"
  }
}
```

---

### bookmarks

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| content_id | UUID FK → contents.id | |
| note | TEXT | 메모 |
| created_at | TIMESTAMP | |

---

### user_feedback

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| user_id | UUID FK → users.id | |
| feedback_type | TEXT | `"positive"` \| `"negative"` \| `"suggestion"` |
| message | TEXT | |
| content_id | UUID FK → contents.id | nullable |
| topic_name | TEXT | nullable |
| created_at | TIMESTAMP | |

---

### pipeline_runs
파이프라인 실행 세션.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| categories | JSON ARRAY | 실행 카테고리 목록 |
| status | TEXT | `"running"` \| `"success"` \| `"failed"` |
| stats | JSON | 아래 구조 참조 |
| started_at | TIMESTAMP | |
| finished_at | TIMESTAMP | |

**stats 구조:**
```json
{
  "total_contents": 0,
  "total_quizzes": 0,
  "total_failed": 0,
  "tokens": {
    "claude_input": 0,
    "claude_output": 0,
    "openai_input": 0,
    "openai_output": 0
  },
  "quality": {
    "faithfulness_scores": [],
    "faithfulness_failures": 0,
    "dedup_filtered": 0,
    "quiz_pass_rates": []
  }
}
```

---

### pipeline_logs
파이프라인 단계별 로그. pipeline_runs : pipeline_logs = 1 : N.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID PK | |
| run_id | UUID FK → pipeline_runs.id | |
| step_order | INTEGER | 실행 순서 |
| tool_name | TEXT | `"collect"` \| `"summarize"` \| `"quiz_gen"` \| `"verify"` \| `"save"` \| `"reflection"` |
| category | TEXT | 토픽 카테고리 |
| inputs | JSON | 입력 파라미터 |
| output | JSON | 출력 결과 및 메타데이터 |
| duration_ms | INTEGER | |
| status | TEXT | `"success"` \| `"failed"` |
| error_message | TEXT | nullable |
| created_at | TIMESTAMP | |

---

## 관계 요약

```
users
  ├─ topics (1:N)
  ├─ quiz_results (1:N)
  ├─ concept_levels (1:N)
  ├─ streaks (1:1)
  ├─ chapter_progress (1:N, 복합 PK)
  ├─ bookmarks (1:N)
  └─ user_feedback (1:N)

contents
  ├─ quizzes (1:N)
  │    └─ quiz_results (1:N)
  └─ bookmarks (1:N)

pipeline_runs
  └─ pipeline_logs (1:N)

topic_curricula (독립 캐시 테이블)
```

---

## 주요 쿼리 패턴

```python
# 일일 콘텐츠 조회
supabase.table("contents").select("*")
    .eq("collected_at", today_date)
    .in_("topic_category", user_topic_names)
    .limit(3)

# 복습 퀴즈 — 약한 개념
supabase.table("concept_levels").select("concept")
    .eq("user_id", user_id)
    .lt("level", 50)
    .order("level").limit(5)

# 중복 URL 체크
supabase.table("contents").select("original_url")
    .in_("original_url", urls_to_check)

# 챕터 진행 상태 upsert
supabase.table("chapter_progress").upsert(
    data, on_conflict="user_id,chapter_id"
)
```

---

## 참고

- `TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"` — MVP 하드코딩, Supabase Auth 미연동
- 백엔드: `SUPABASE_SECRET_KEY` (서비스 롤, RLS 우회) / 프론트: `SUPABASE_ANON_KEY`
- `core/supabase.py` — 클라이언트 초기화, `.env` 우선순위: `BriefUp/.env` → `backend/.env`
