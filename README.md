# BrefUp — AI 브리핑 학습 Agent

> 관심사를 입력하면, 매일 최신 콘텐츠를 자동 수집 · 요약 · 퀴즈로 지식 레벨을 채워가는 PWA

---

## 구조

```
BrefUp/
├── frontend/     # Next.js 14 + Tailwind CSS (PWA)
└── backend/      # Python FastAPI + APScheduler
```

## 기술 스택

| 파트 | 기술 |
|------|------|
| Frontend | Next.js 14, Tailwind CSS, PWA |
| Backend | Python, FastAPI, APScheduler |
| DB | Supabase (PostgreSQL) |
| AI | Claude API (Haiku) |
| 배포 | Vercel (프론트) + Railway (백엔드) |

## 로컬 실행

### 백엔드
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # .env 값 채우기
uvicorn main:app --reload
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev
```

## 환경변수

`backend/.env.example` 참고
