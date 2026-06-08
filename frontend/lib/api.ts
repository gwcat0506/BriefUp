/**
 * 백엔드 API 호출 유틸
 * 환경변수 NEXT_PUBLIC_API_URL 기반
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 임시 유저 ID (로그인 없는 MVP용 — 나중에 Supabase Auth로 교체)
export const TEMP_USER_ID = "00000000-0000-0000-0000-000000000001";

async function fetcher<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `API 오류: ${res.status}`);
  }
  return res.json();
}

// ── 콘텐츠 ──────────────────────────────────────────
export const api = {
  // 오늘의 브리핑 — 유저 토픽 기반
  getTodayContentForUser: (userId: string) =>
    fetcher<Content[]>(`/api/content/today/for-user/${userId}`),

  // 오늘의 퀴즈
  getTodayQuizzes: (userId: string) =>
    fetcher<Quiz[]>(`/api/quiz/today/${userId}`),

  // 특정 브리핑의 퀴즈
  getQuizzesByContent: (contentId: string) =>
    fetcher<Quiz[]>(`/api/quiz/by-content/${contentId}`),

  // 퀴즈 답 제출
  submitAnswer: (body: AnswerBody) =>
    fetcher<AnswerResult>(`/api/quiz/answer`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // 퀴즈 기록
  getHistory: (userId: string) =>
    fetcher<QuizResult[]>(`/api/quiz/history/${userId}`),

  // 개념 레벨
  getLevels: (userId: string) =>
    fetcher<ConceptLevel[]>(`/api/quiz/levels/${userId}`),

  // 스트릭
  getStreak: (userId: string) =>
    fetcher<Streak>(`/api/user/${userId}/streak`),

  getStreakStatus: (userId: string) =>
    fetcher<StreakStatus>(`/api/user/${userId}/streak/status`),

  useStreakFreeze: (userId: string) =>
    fetcher<{ success: boolean; freeze_remaining: number; message: string }>(
      `/api/user/${userId}/streak/freeze`, { method: "POST" }
    ),

  // 복습 퀴즈 (틀린 개념 재출제)
  getReviewQuizzes: (userId: string) =>
    fetcher<Quiz[]>(`/api/quiz/review/${userId}`),

  // 유저 생성
  createUser: (userId: string, nickname: string) =>
    fetcher(`/api/user/`, {
      method: "POST",
      body: JSON.stringify({ id: userId, email: `${userId}@briefup.app`, nickname }),
    }),

  // 관심사
  getTopics: (userId: string) =>
    fetcher<Topic[]>(`/api/user/${userId}/topics`),

  addTopic: (userId: string, name: string, category?: string) =>
    fetcher(`/api/user/topic`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, name, category }),
    }),

  removeTopic: (topicId: string) =>
    fetcher(`/api/user/topic/${topicId}`, { method: "DELETE" }),

  // XP / 레벨
  getUserXp: (userId: string) =>
    fetcher<XpInfo>(`/api/user/${userId}/xp`),

  // 파이프라인 수동 실행 (테스트용)
  runPipeline: () =>
    fetcher(`/api/content/run-pipeline`, { method: "POST" }),

  // 챕터 진행 상태
  updateProgress: (body: { user_id: string; chapter_id: string; track: string; status: string; quiz_score?: number; quiz_total?: number }) =>
    fetcher(`/api/progress/chapter`, { method: "POST", body: JSON.stringify(body) }),

  getProgress: (userId: string) =>
    fetcher<Record<string, any>>(`/api/progress/chapter/${userId}`),

  getNextChapter: (userId: string) =>
    fetcher<NextChapter | null>(`/api/progress/chapter/${userId}/next`),

  // 유저 커리큘럼 (관심사 기반 동적 로드맵)
  getCurricula: (userId: string) =>
    fetcher<CurriculumTrack[]>(`/api/progress/curricula/${userId}`),

  // 홈 화면 집계 (7개 쿼리를 1회 왕복으로)
  getHomeSummary: (userId: string) =>
    fetcher<HomeSummary>(`/api/home/summary/${userId}`),

  // 북마크
  toggleBookmark: (userId: string, contentId: string) =>
    fetcher<{ bookmarked: boolean }>(`/api/progress/bookmark`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, content_id: contentId }),
    }),

  getBookmarks: (userId: string) =>
    fetcher<any[]>(`/api/progress/bookmark/${userId}`),

  checkBookmark: (userId: string, contentId: string) =>
    fetcher<{ bookmarked: boolean }>(`/api/progress/bookmark/${userId}/check/${contentId}`),
};

// ── 타입 ──────────────────────────────────────────
export interface Content {
  id: string;
  title: string;
  summary: string;
  source: string;
  original_url: string;
  topic_category: string;
  collected_at: string;
}

export interface Quiz {
  id: string;
  question: string;
  options: Record<string, string>;
  concept: string;
  difficulty: number;
  content_id: string;
  contents?: { title: string; source: string };
}

export interface AnswerBody {
  user_id: string;
  quiz_id: string;
  content_id: string;
  selected: string;
}

export interface XpInfo {
  level: number;
  total_xp: number;
  xp_in_level: number;
  xp_needed: number;
  progress_pct: number;
  char_emoji: string;
  char_name: string;
  char_title: string;
  xp_gained?: number;
  leveled_up?: boolean;
  old_level?: number;
}

export interface AnswerResult {
  is_correct: boolean;
  answer: string;
  explanation: string;
  concept: string;
  xp_gained?: number;
  xp_info?: XpInfo | null;
}

export interface QuizResult {
  id: string;
  is_correct: boolean;
  selected: string;
  answered_at: string;
  quizzes?: { question: string; concept: string; explanation: string };
}

export interface ConceptLevel {
  concept: string;
  category: string;
  level: number;
  total_attempts: number;
  correct_attempts: number;
}

export interface Streak {
  current_streak: number;
  longest_streak: number;
  last_active_date: string;
  freeze_available?: number;
  milestone?: { days: number; badge: string; reward: string } | null;
  next_milestone?: number | null;
  days_to_next?: number | null;
  next_milestone_reward?: string | null;
}

export interface StreakStatus {
  status: "done" | "pending" | "broken" | "new" | "freezeable";
  message: string;
  current_streak?: number;
  freeze_available?: number;
}

export interface Topic {
  id: string;
  name: string;
  category: string;
}

export interface CurriculumChapter {
  id: number;
  chapter_id: string;
  title: string;
  description: string;
  level: string;
  duration: string;
  status: "available" | "locked" | "started" | "completed";
}

export interface CurriculumTrack {
  id: string;
  title: string;
  emoji: string;
  color: string;
  description: string;
  totalChapters: number;
  chapters: CurriculumChapter[];
}

export interface HomeSummary {
  streak: Streak | null;
  streak_status: StreakStatus | null;
  xp_info: XpInfo | null;
  levels: ConceptLevel[];
  contents: Content[];
  review_count: number;
  curricula: CurriculumTrack[];
}

export interface NextChapter {
  chapter_id: string;
  track: string;
  track_title: string;
  chapter_title: string;
  level: string;
  duration: string;
}
