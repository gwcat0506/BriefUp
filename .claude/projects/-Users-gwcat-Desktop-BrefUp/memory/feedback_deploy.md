---
name: feedback-deploy
description: BrefUp 배포 시 프론트+백엔드 항상 함께 배포해야 함
metadata:
  type: feedback
---

이 프로젝트에서 "배포해줘" 또는 "deploy"라고 하면 항상 두 가지를 모두 실행해야 한다.

1. `git push origin main` — Render 백엔드 자동 배포 트리거 (GitHub 연동)
2. `cd frontend && vercel --prod --yes` — Vercel 프론트엔드 배포

**Why:** 백엔드(Render)는 git push로 자동 배포되지만, 프론트엔드(Vercel)는 별도 CLI 명령이 필요하다. 한쪽만 배포하면 버전 불일치가 생긴다.

**How to apply:** 커밋/푸시 후 항상 vercel --prod까지 이어서 실행. `/deploy` 커스텀 커맨드도 `.claude/commands/deploy.md`에 정의되어 있음.
