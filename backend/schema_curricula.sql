-- topic_curricula: 토픽별 커리큘럼 (챕터 구조 + 검색 힌트)
-- 토픽 추가 시 Claude가 자동 생성, DB에 캐시
-- chapters JSONB 구조:
--   [{id, title, description, level, duration, concepts, search_hints: {arxiv_query, web_query}}]

CREATE TABLE IF NOT EXISTS topic_curricula (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_key    TEXT        UNIQUE NOT NULL,    -- slug: "rag", "quantum-computing"
    topic_name   TEXT        NOT NULL,            -- 표시 이름: "RAG", "양자컴퓨팅"
    category     TEXT        NOT NULL,
    topic_aliases TEXT[]     DEFAULT '{}',        -- 동의어: ["주식", "투자", "주식/투자"]
    emoji        TEXT        DEFAULT '📚',
    color        TEXT        DEFAULT '#6366F1',
    description  TEXT,
    chapters     JSONB       NOT NULL DEFAULT '[]',
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- RLS 비활성화 (백엔드 서비스 롤로 접근)
ALTER TABLE topic_curricula DISABLE ROW LEVEL SECURITY;

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS topic_curricula_updated_at ON topic_curricula;
CREATE TRIGGER topic_curricula_updated_at
    BEFORE UPDATE ON topic_curricula
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
