-- XP 게임화 시스템 마이그레이션
-- Supabase SQL Editor에서 실행

ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0;

-- 기존 유저 XP 초기화 (없으면 0)
UPDATE users SET xp = 0 WHERE xp IS NULL;
