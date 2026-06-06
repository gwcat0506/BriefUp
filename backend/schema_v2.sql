-- ================================================
-- BrefUp Schema v2 — 진행 상태 + 북마크
-- Supabase SQL Editor에 붙여넣고 실행
-- ================================================

-- 챕터 학습 진행 상태
create table if not exists chapter_progress (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  chapter_id text not null,           -- "rag-1", "agent-2" 등
  track text not null,                -- "rag", "agent", "llm"
  status text default 'started',      -- 'started' | 'completed'
  quiz_score int default 0,           -- 퀴즈 정답 수
  quiz_total int default 0,           -- 퀴즈 총 문제 수
  completed_at timestamptz,
  created_at timestamptz default now(),
  unique(user_id, chapter_id)
);

-- 북마크
create table if not exists bookmarks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  content_id uuid references contents(id) on delete cascade,
  note text,                          -- 메모 (선택)
  created_at timestamptz default now(),
  unique(user_id, content_id)
);

-- RLS
alter table chapter_progress enable row level security;
alter table bookmarks enable row level security;

create policy "chapter_progress_self" on chapter_progress
  for all using (auth.uid() = user_id);

create policy "bookmarks_self" on bookmarks
  for all using (auth.uid() = user_id);

-- 인덱스
create index if not exists idx_chapter_progress_user on chapter_progress(user_id);
create index if not exists idx_bookmarks_user on bookmarks(user_id);
