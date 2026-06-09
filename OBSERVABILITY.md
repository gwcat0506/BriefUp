# BriefUp AI Observability 설계

> "AI 에이전트는 배포하면 끝이 아니다. 의도한 대로 돌아가는지 살피고, 실패 패턴을 지표로 잡아내고, 원인을 되짚는 것이 핵심이다."
> — 박성호 (네이버 AI 엔지니어)

---

## 문제 정의

BriefUp은 Claude Haiku + GPT가 협력하는 멀티모델 파이프라인이다.
매일 자동 실행되면서 기사 수집 → 요약 → 퀴즈 생성 → 저장 4단계를 처리하는데,
개선 전에는 아래 3가지를 알 수 없었다.

| 알 수 없었던 것 | 왜 문제인가 |
|----------------|------------|
| 실패가 왜 났는지 | `status="failed"` 하나로만 기록 — API 오류인지, 품질 기준 미달인지 구분 불가 |
| Claude가 무엇을 왜 건너뛰었는지 | Claude의 판단(스킵)이 로그에 전혀 남지 않음 — 블랙박스 |
| 파이프라인이 "잘 됐는지" | 콘텐츠가 1개만 저장돼도 `success` — 퀴즈 통과율, 충실도 등 품질 지표 없음 |

---

## 해결 방법

### 1. 실패 유형 분류 (Failure Type Classification)

**문제**: 모든 실패가 동일한 `status="failed"`로 기록

**해결**: `failure_type` 속성을 각 스텝 로그의 `output` JSONB에 추가

```
technical        → API 오류, 네트워크 실패 등 기술적 문제
policy_rejected  → 검증 기준 미달 (충실도 < 0.7, 퀴즈 전량 탈락)
quality_rejected → 수집 결과 0건 (검색어와 매칭되는 기사 없음)
not_found        → article_id 참조 오류 (시스템 내부 일관성 문제)
```

**박성호님 표현으로**: "주방 사정(technical)인지, 가게 방침(policy_rejected)인지 구분해 기록해야 정확한 원인 파악이 가능하다."

**실제 조회 예시** (`GET /api/pipeline/runs/{id}/failures`):
```json
{
  "by_failure_type": {
    "technical": [{"tool_name": "collect", "error_message": "Tavily API timeout"}],
    "policy_rejected": [{"tool_name": "summarize", "error_message": "충실도 미달 (score=0.52)"}],
    "quality_rejected": [{"tool_name": "collect", "error_message": null}]
  }
}
```

---

### 2. 스킵 추론 (Agent Decision Inference)

**문제**: Claude가 관련성 낮다고 판단해 아티클을 건너뛰어도 어디에도 기록이 없음

**해결**: `report_skip` 도구를 추가하는 대신, **사후 추론(post-hoc inference)** 방식 채택

```
수집된 article_id 집합  (collect_articles 반환값 전체)
       ↕ 비교
요약된 article_id 집합  (_session["articles"]에서 "summary" 키 있는 것)

차집합 = Claude가 판단해 건너뛴 아티클
```

**왜 이 방식인가**: OpenTelemetry 표준에서 에이전트 스킵은 별도 도구 호출 없이 **tool call 시퀀스의 갭**으로 추론한다. `report_skip` 도구 방식은 Claude가 지시를 빠뜨릴 경우 신뢰성이 떨어진다.

**결과로 알 수 있는 것** (run 통계에 `skipped` 필드로 기록):
```json
{
  "skipped": {
    "by_agent": 3,           // Claude가 관련성 판단으로 스킵
    "by_faithfulness": 1,    // 충실도 검증 탈락
    "total_collected": 12,
    "total_summarized": 8,
    "total_saved": 5
  }
}
```

---

### 3. Tool Call 계층 구조 (Span Hierarchy)

**문제**: 모든 스텝 로그가 flat — "어떤 collect의 자식 summarize인지" 연결 불가

**해결**: `parent_step_order` 속성을 output JSONB에 추가

```
collect(topic="AI/ML")  [step_order=3]
  └─ summarize(ai_abc123)  [parent_step_order=3, step_order=5]
  └─ summarize(ai_def456)  [parent_step_order=3, step_order=6]

collect(topic="철학")  [step_order=4]
  └─ summarize(philo_xyz)  [parent_step_order=4, step_order=7]
```

**OpenTelemetry 표준과의 정렬**: OTel GenAI Semantic Conventions는 `invoke_agent → execute_tool` 의 부모-자식 span 구조를 표준으로 정의한다. 이 구현은 동일 개념을 Supabase JSONB로 경량 구현한 것.

---

### 4. Run 품질 점수 (Run Quality Score)

**문제**: 콘텐츠 1개 저장 = `success`, 0개 = `failed` — 이분법적 판정

**해결**: 3단계 `run_quality` + 수치 지표

| 판정 | 조건 |
|------|------|
| `success` | 콘텐츠 저장 성공 + 실패/스킵이 저장 수의 2배 이하 |
| `partial` | 콘텐츠는 있지만 실패/스킵 비율 과다 |
| `failed` | 저장된 콘텐츠 0개 |

**추가 지표**:
- `quiz_pass_rate`: 생성 퀴즈 대비 검증 통과 퀴즈 비율
- `avg_faithfulness`: 아티클별 충실도 점수 평균 (Claude가 GPT 요약을 교차 검증)
- `cost_usd`: Claude + GPT 토큰 합산 실행 비용

---

### 5. 관측 API (Observability Endpoints)

이전에는 Supabase 대시보드를 직접 열어야만 파이프라인 상태를 볼 수 있었다.

| 엔드포인트 | 용도 |
|-----------|------|
| `GET /api/pipeline/runs` | 최근 실행 목록 + 품질 요약 |
| `GET /api/pipeline/runs/{id}` | 특정 실행의 전체 스텝 + 계층 구조 + 실패 분석 |
| `GET /api/pipeline/runs/{id}/failures` | 실패 스텝만 필터 + 유형별 그룹화 |

---

## 아키텍처 결정 요약

| 결정 | 선택 | 이유 |
|------|------|------|
| 외부 observability 도구 (Langfuse, LangSmith 등) | **미도입** | 이 규모에서는 오버킬. 동일 개념을 Supabase로 경량 구현 |
| `report_skip` 도구 추가 | **미채택** | Claude 지시 이행 여부에 의존 → 신뢰성 낮음. 사후 추론 방식이 더 견고 |
| `failure_type` 별도 컬럼 vs JSONB 내 속성 | **JSONB 내 속성** | DB 마이그레이션 없이 즉시 적용. 쿼리는 `output->>'failure_type'`으로 가능 |
| `parent_step_order` 구현 방식 | **JSONB 내 속성** | OTel span 계층 개념을 Supabase에서 경량 구현 |

---

## 개선 전 / 후 비교

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| 실패 로그 | `status: "failed"` (원인 불명) | `failure_type`: technical / policy_rejected / quality_rejected / not_found |
| Claude 스킵 가시성 | 없음 (블랙박스) | `skipped.by_agent` 집계 (수집-처리 갭 추론) |
| 충실도 검증 실패 | `failed`로 묻힘 | `by_faithfulness` 별도 집계 + `policy_rejected` 유형 |
| 퀴즈 품질 | 검증 통과 수만 기록 | `quiz_pass_rate` (생성 대비 통과 비율) |
| Run 판정 | 이분법 (success/failed) | 3단계 (success/partial/failed) + 수치 지표 |
| 스텝 간 관계 | flat 순서 번호 | `parent_step_order`로 계층 연결 |
| 상태 조회 | Supabase 대시보드 직접 접속 | REST API 3개 (`/runs`, `/runs/{id}`, `/runs/{id}/failures`) |

---

## 산업 표준과의 정렬

이 구현은 OpenTelemetry GenAI Semantic Conventions (2025-2026)의 핵심 개념을 경량화한 것:

- **`execute_tool` span** → `pipeline_logs` 테이블의 각 행
- **`error.type` attribute** → `output.failure_type` 속성
- **부모-자식 span 계층** → `output.parent_step_order` 속성
- **tail-based sampling** → 실패 로그 100% 보존 (현재 전량 보존)

외부 observability 플랫폼(LangSmith, Arize Phoenix, Langfuse) 없이 동일 개념을 직접 구현한 이유: MVP 단계에서 인프라 복잡도를 최소화하면서 핵심 관측성을 확보하기 위함.
