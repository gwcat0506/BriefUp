---
name: deploy-check
description: 배포 전 사전 검증. 의존성 충돌, Python 버전 불일치, import 오류, FastAPI 기동 여부를 순서대로 확인하고 문제가 있으면 즉시 수정 후 배포 진행.
---

# deploy-check

배포 전에 Render/Vercel에서 실제로 실패할 수 있는 항목들을 로컬에서 미리 검증한다.  
문제 발견 시 즉시 수정하고, 전부 통과한 뒤에만 배포를 진행한다.

---

## 실행 방법

사용자가 `/deploy-check` 를 입력하면 아래 단계를 **순서대로** 실행한다.  
한 단계가 실패하면 수정 후 해당 단계를 재확인한 뒤 다음으로 넘어간다.

---

## 검증 단계

### Step 1 — Python 버전 일관성

`runtime.txt`와 `render.yaml`의 Python 버전이 일치하는지 확인한다.

```bash
echo "runtime.txt: $(cat /Users/gwcat/Desktop/BrefUp/backend/runtime.txt)"
grep PYTHON_VERSION /Users/gwcat/Desktop/BrefUp/backend/render.yaml
```

확인 항목:
- `runtime.txt`의 버전과 `render.yaml`의 `PYTHON_VERSION` 값이 동일한지
- 불일치 시 `runtime.txt`를 render.yaml 기준으로 수정

---

### Step 2 — pip 의존성 충돌 검사

```bash
cd /Users/gwcat/Desktop/BrefUp/backend
source .venv/bin/activate
pip install -r requirements.txt --dry-run 2>&1 | grep -E "ERROR|error|Conflict|conflict|Cannot install"
```

확인 항목:
- ERROR 또는 Conflict 메시지가 없는지
- 충돌 발생 시 에러 메시지에서 충돌 패키지를 찾아 버전 범위 조정
- 과거 사례: `pydantic==2.9.2` → fastmcp-slim 3.4.2가 `pydantic>=2.11.7` 요구
- 과거 사례: `uvicorn==0.30.6` → fastmcp-slim 3.4.2가 `uvicorn>=0.35` 요구
- 상한선 없는 패키지는 `<next_major` 형태로 추가 (예: `>=0.35.0,<1.0.0`)

---

### Step 3 — 모듈 import 검사

백엔드 핵심 모듈이 오류 없이 임포트되는지 확인한다.

```bash
cd /Users/gwcat/Desktop/BrefUp/backend
source .venv/bin/activate
python -c "
import main
from api import quiz, user, content, chapter, progress, logs, home
from agent import curriculum_catalog, curriculum_gen, mcp_server
from agent import collector, summarizer, quiz_gen, verifier
from core import supabase
print('✅ 모든 모듈 import 성공')
"
```

확인 항목:
- ImportError, ModuleNotFoundError 없이 통과하는지
- 실패 시 누락된 패키지를 requirements.txt에 추가하거나 코드 오류 수정

---

### Step 4 — FastAPI 앱 기동 검사

uvicorn이 실제로 앱을 로드하고 라우터를 등록하는지 확인한다.

```bash
cd /Users/gwcat/Desktop/BrefUp/backend
source .venv/bin/activate
timeout 8 uvicorn main:app --host 0.0.0.0 --port 18765 2>&1 | head -20
```

확인 항목:
- `Application startup complete` 메시지가 출력되는지
- 라우터 등록 오류나 startup 예외가 없는지
- 포트 충돌은 무시 (18765는 임의 포트)

---

### Step 5 — 프론트엔드 빌드 검사

Vercel 배포 전 Next.js 빌드가 통과하는지 확인한다.

```bash
cd /Users/gwcat/Desktop/BrefUp/frontend
npm run build 2>&1 | tail -20
```

확인 항목:
- `✓ Compiled successfully` 또는 `Route (app)` 출력 여부
- TypeScript 타입 오류, import 오류 없는지
- 실패 시 빌드 로그에서 오류 파일/라인을 찾아 수정

---

## 결과 보고 형식

```
## 배포 사전 검증 결과

| 항목 | 상태 | 비고 |
|------|------|------|
| Python 버전 일관성 | ✅ PASS | runtime.txt = render.yaml = 3.11.0 |
| pip 의존성 충돌 | ✅ PASS | ERROR 없음 |
| 모듈 import | ✅ PASS | 전체 12개 모듈 |
| FastAPI 기동 | ✅ PASS | startup complete |
| 프론트엔드 빌드 | ✅ PASS | Compiled successfully |

→ 전체 통과. 배포 진행합니다.
```

실패 항목이 있으면:
- 실패 원인과 수정 내용을 인라인으로 기록
- 수정 후 해당 단계 재실행해서 통과 확인
- 전체 통과 후 `/deploy` 실행
