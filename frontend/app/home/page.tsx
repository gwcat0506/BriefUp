"use client";

import { useEffect, useState } from "react";
import { api, Content, Streak, ConceptLevel, NextChapter, StreakStatus, XpInfo, CurriculumTrack, TEMP_USER_ID } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SkeletonCard, SkeletonStat } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";

export default function HomePage() {
  const [contents, setContents] = useState<Content[]>([]);
  const [streak, setStreak] = useState<Streak | null>(null);
  const [streakStatus, setStreakStatus] = useState<StreakStatus | null>(null);
  const [levels, setLevels] = useState<ConceptLevel[]>([]);
  const [xpInfo, setXpInfo] = useState<XpInfo | null>(null);
  const [nextChapter, setNextChapter] = useState<NextChapter | null>(null);
  const [curricula, setCurricula] = useState<CurriculumTrack[]>([]);
  const [reviewCount, setReviewCount] = useState(0);
  const [statsLoading, setStatsLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [expandedNews, setExpandedNews] = useState<string | null>(null);
  const [expandedTrack, setExpandedTrack] = useState<string | null>(null);
  const [milestoneShown, setMilestoneShown] = useState(false);
  const router = useRouter();
  const { show: showToast, ToastComponent } = useToast();

  const loadData = () => {
    setLoading(true);
    setStatsLoading(true);

    // 통계 카드 — 빠르게 먼저 표시 (streak/levels/xp/status)
    Promise.allSettled([
      api.getStreak(TEMP_USER_ID),
      api.getLevels(TEMP_USER_ID),
      api.getStreakStatus(TEMP_USER_ID),
      api.getUserXp(TEMP_USER_ID),
    ]).then(([s, l, status, xp]) => {
      if (s.status === "fulfilled") {
        setStreak(s.value);
        if (s.value?.milestone && !milestoneShown) {
          showToast(`${s.value.milestone.badge} ${s.value.milestone.reward}`, "success");
          setMilestoneShown(true);
        }
      }
      if (l.status === "fulfilled") setLevels(l.value);
      if (status.status === "fulfilled") setStreakStatus(status.value);
      if (xp.status === "fulfilled") setXpInfo(xp.value);
    }).finally(() => setStatsLoading(false));

    // 콘텐츠 — 느려도 괜찮은 항목
    Promise.allSettled([
      api.getTodayContentForUser(TEMP_USER_ID),
      api.getNextChapter(TEMP_USER_ID),
      api.getReviewQuizzes(TEMP_USER_ID),
      api.getCurricula(TEMP_USER_ID),
    ]).then(([c, next, reviews, curricRes]) => {
      if (c.status === "fulfilled") setContents(c.value);
      if (next.status === "fulfilled") setNextChapter(next.value);
      if (reviews.status === "fulfilled") setReviewCount(reviews.value.length);
      if (curricRes.status === "fulfilled" && curricRes.value) setCurricula(curricRes.value);
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  // 페이지 포커스 시 데이터 갱신 (퀴즈 완료 후 돌아올 때)
  useEffect(() => {
    const handleFocus = () => loadData();
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  async function handleStreakFreeze() {
    try {
      const res = await api.useStreakFreeze(TEMP_USER_ID);
      showToast(res.message, "success");
      loadData();
    } catch (e: any) {
      showToast(e.message || "프리즈 사용 실패", "error");
    }
  }

  const avgLevel = levels.length
    ? Math.round(levels.reduce((a, b) => a + b.level, 0) / levels.length)
    : 0;
  const totalQuizzes = levels.reduce((a, b) => a + b.total_attempts, 0);
  const correctQuizzes = levels.reduce((a, b) => a + b.correct_attempts, 0);
  const accuracy = totalQuizzes > 0 ? Math.round(correctQuizzes / totalQuizzes * 100) : 0;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "좋은 아침이에요 ☀️" : hour < 18 ? "오늘도 화이팅! 💪" : "오늘 하루 수고했어요 🌙";
  const today = new Date().toLocaleDateString("ko-KR", { month: "long", day: "numeric", weekday: "long" });

  return (
    <div className="flex flex-col min-h-screen pb-24 bg-[#FAFAF8]">
      {ToastComponent}

      {/* 헤더 */}
      <div className="px-5 pt-14 pb-2">
        <p className="text-[#6B7280] text-sm mb-0.5">{today}</p>
        <h1 className="text-2xl font-bold text-[#1C1C1E]">{greeting}</h1>
      </div>

      {/* 캐릭터 + 레벨 카드 */}
      {statsLoading ? <div className="mx-5 mt-4"><SkeletonStat /></div> : null}
      <div className={`mx-5 mt-4 bg-white rounded-3xl p-5 card-shadow ${statsLoading ? "hidden" : ""}`}>
        <div className="flex items-center gap-4">
          {/* 캐릭터 */}
          <div className="flex-shrink-0 w-20 h-20 bg-gradient-to-br from-[#ECFDF5] to-[#D1FAE5] rounded-2xl flex items-center justify-center">
            <span className="text-4xl character-heartbeat inline-block">
              {xpInfo?.char_emoji ?? "🥚"}
            </span>
          </div>

          {/* 레벨 정보 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-0.5">
              <div>
                <span className="text-[#10B981] font-bold text-lg">Lv.{xpInfo?.level ?? 1}</span>
                <span className="text-[#6B7280] text-sm ml-2">{xpInfo?.char_title ?? "입문자"}</span>
              </div>
              <span className="text-[#1C1C1E] font-bold text-sm">{xpInfo?.char_name ?? "알"}</span>
            </div>

            {/* XP 바 */}
            <div className="w-full bg-[#F3F4F6] rounded-full h-2.5 mb-1.5 overflow-hidden">
              <div
                className="h-2.5 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-1000"
                style={{ width: `${xpInfo?.progress_pct ?? 0}%` }}
              />
            </div>
            <div className="flex justify-between items-center">
              <p className="text-[#9CA3AF] text-xs">
                {xpInfo?.xp_in_level ?? 0} / {xpInfo?.xp_needed ?? 50} XP
              </p>
              <p className="text-[#9CA3AF] text-xs">
                다음 레벨까지 {(xpInfo?.xp_needed ?? 50) - (xpInfo?.xp_in_level ?? 0)} XP
              </p>
            </div>
          </div>
        </div>

        {/* 스트릭 + 정답률 */}
        <div className="flex gap-3 mt-4 pt-4 border-t border-[#F3F4F6]">
          <div className="flex-1 text-center bg-[#FFFBEB] rounded-2xl py-2.5">
            <p className="text-[#F59E0B] text-lg font-bold">🔥 {streak?.current_streak ?? 0}일</p>
            <p className="text-[#92400E] text-xs mt-0.5">연속 학습</p>
          </div>
          <div className="flex-1 text-center bg-[#ECFDF5] rounded-2xl py-2.5">
            <p className="text-[#10B981] text-lg font-bold">{accuracy}%</p>
            <p className="text-[#065F46] text-xs mt-0.5">정답률</p>
          </div>
          <div className="flex-1 text-center bg-[#EFF6FF] rounded-2xl py-2.5">
            <p className="text-[#3B82F6] text-lg font-bold">{xpInfo?.total_xp ?? 0}</p>
            <p className="text-[#1D4ED8] text-xs mt-0.5">총 XP</p>
          </div>
        </div>
      </div>

      {/* 스트릭 상태 배너 */}
      {streakStatus && streakStatus.status !== "done" && streakStatus.status !== "new" && (
        <div className={`mx-5 mt-3 rounded-2xl p-4 flex items-center justify-between ${
          streakStatus.status === "pending" || streakStatus.status === "freezeable"
            ? "bg-[#FFF7ED] border border-[#FED7AA]"
            : "bg-[#FEF2F2] border border-[#FCA5A5]"
        }`}>
          <div>
            <p className={`font-bold text-sm ${
              streakStatus.status === "broken" ? "text-[#DC2626]" : "text-[#C2410C]"
            }`}>
              {streakStatus.message}
            </p>
            {streakStatus.freeze_available && streakStatus.freeze_available > 0 && (
              <p className="text-[#9CA3AF] text-xs mt-0.5">
                프리즈 {streakStatus.freeze_available}개 보유 중
              </p>
            )}
          </div>
          {(streakStatus.status === "freezeable") && (
            <button
              onClick={handleStreakFreeze}
              className="bg-[#F59E0B] text-white text-xs font-bold px-3 py-2 rounded-xl active:scale-95 transition-all"
            >
              🧊 프리즈 사용
            </button>
          )}
        </div>
      )}

      {/* 마일스톤 달성 배너 */}
      {streak?.milestone && (
        <div className="mx-5 mt-3 bg-gradient-to-r from-[#F59E0B] to-[#EF4444] rounded-2xl p-4 text-white">
          <p className="font-bold text-base">{streak.milestone.badge}</p>
          <p className="text-yellow-100 text-sm mt-0.5">{streak.milestone.reward}</p>
        </div>
      )}

      {/* 다음 마일스톤까지 */}
      {streak && !streak.milestone && streak.days_to_next && streak.current_streak > 0 && (
        <div className="mx-5 mt-3 bg-[#FFFBEB] border border-[#FDE68A] rounded-2xl px-4 py-3 flex items-center justify-between">
          <p className="text-[#92400E] text-xs">
            🔥 {streak.next_milestone}일 달성까지 <span className="font-bold">{streak.days_to_next}일</span> 남았어요
          </p>
          <div className="flex">
            {Array.from({ length: Math.min(streak.days_to_next, 7) }).map((_, i) => (
              <div key={i} className="w-2 h-2 rounded-full bg-[#FDE68A] ml-1" />
            ))}
          </div>
        </div>
      )}

      {/* 복습 퀴즈 배너 (틀린 개념 있을 때) */}
      {reviewCount > 0 && (
        <div
          className="mx-5 mt-3 bg-[#FDF4FF] border border-[#E9D5FF] rounded-2xl p-4 flex items-center justify-between cursor-pointer active:scale-[0.98] transition-all"
          onClick={() => router.push(`/quiz?mode=review`)}
        >
          <div>
            <p className="text-[#7E22CE] font-bold text-sm">💪 복습할 개념이 있어요</p>
            <p className="text-[#9CA3AF] text-xs mt-0.5">틀린 {reviewCount}개 개념 다시 도전</p>
          </div>
          <span className="text-[#7E22CE] font-bold">→</span>
        </div>
      )}

      {/* 오늘 학습할 챕터 — 동적 추천 */}
      {nextChapter && (
        <div className="mx-5 mt-4">
          <p className="text-[#1C1C1E] font-bold text-base mb-3">오늘 학습할 챕터 🎯</p>
          <div
            className="bg-white rounded-3xl p-4 card-shadow cursor-pointer active:scale-[0.98] transition-all"
            onClick={() => router.push(`/learn?id=${nextChapter.chapter_id}`)}
          >
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#10B981] to-[#059669] flex items-center justify-center text-2xl flex-shrink-0">
                📖
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="bg-[#ECFDF5] text-[#10B981] text-xs px-2 py-0.5 rounded-full font-medium">
                    {nextChapter.track_title}
                  </span>
                  <span className="text-[#9CA3AF] text-xs">{nextChapter.level}</span>
                </div>
                <p className="text-[#1C1C1E] font-bold text-sm">{nextChapter.chapter_title}</p>
                <p className="text-[#9CA3AF] text-xs mt-0.5">{nextChapter.duration} · 다음 학습</p>
              </div>
              <span className="text-[#10B981] text-lg">→</span>
            </div>
          </div>
        </div>
      )}

      {/* 내 커리큘럼 */}
      <div className="mx-5 mt-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[#1C1C1E] font-bold text-base">내 커리큘럼 📚</p>
          <Link href="/roadmap" className="text-[#10B981] text-sm font-medium">전체 보기</Link>
        </div>

        {loading && (
          <div className="flex flex-col gap-3">
            <SkeletonCard className="h-24" />
            <SkeletonCard className="h-24" />
          </div>
        )}

        {!loading && curricula.length === 0 && (
          <Link href="/roadmap">
            <div className="bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] rounded-3xl p-4 flex items-center justify-between text-white">
              <div>
                <p className="text-purple-200 text-xs mb-0.5">학습 경로</p>
                <p className="font-bold">커리큘럼 로드맵 보기</p>
                <p className="text-purple-200 text-xs mt-0.5">RAG · Agentic AI · LLM 단계별 학습</p>
              </div>
              <span className="text-2xl">→</span>
            </div>
          </Link>
        )}

        <div className="flex flex-col gap-3">
          {curricula.map((track) => {
            const completedCount = track.chapters.filter(c => c.status === "completed").length;
            const isExpanded = expandedTrack === track.id;
            const visibleChapters = isExpanded ? track.chapters : track.chapters.slice(0, 4);

            return (
              <div key={track.id} className="bg-white rounded-3xl card-shadow overflow-hidden">
                {/* 트랙 헤더 */}
                <div
                  className="p-4 cursor-pointer active:bg-[#FAFAF8] transition-colors"
                  onClick={() => setExpandedTrack(isExpanded ? null : track.id)}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-2xl flex items-center justify-center text-xl flex-shrink-0"
                      style={{ background: `${track.color}20` }}
                    >
                      {track.emoji}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-[#1C1C1E] font-bold text-sm">{track.title}</p>
                        <span className="text-[#9CA3AF] text-xs">
                          {completedCount}/{track.totalChapters}
                        </span>
                      </div>
                      <div className="w-full bg-[#F3F4F6] rounded-full h-1.5 mt-1.5 overflow-hidden">
                        <div
                          className="h-1.5 rounded-full transition-all duration-700"
                          style={{
                            width: `${track.totalChapters > 0 ? (completedCount / track.totalChapters) * 100 : 0}%`,
                            background: track.color,
                          }}
                        />
                      </div>
                    </div>
                    <span className="text-[#9CA3AF] text-xs ml-1">{isExpanded ? "▲" : "▼"}</span>
                  </div>
                </div>

                {/* 챕터 목록 */}
                <div className="border-t border-[#F3F4F6]">
                  {visibleChapters.map((ch, idx) => {
                    const isCompleted = ch.status === "completed";
                    const isLocked = ch.status === "locked";
                    return (
                      <div
                        key={ch.chapter_id}
                        className={`flex items-center gap-3 px-4 py-3 border-b border-[#F9FAFB] last:border-0 ${isLocked ? "opacity-50" : "cursor-pointer active:bg-[#FAFAF8]"}`}
                        onClick={() => !isLocked && router.push(`/learn?id=${ch.chapter_id}`)}
                      >
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                          isCompleted
                            ? "bg-[#10B981] text-white"
                            : ch.status === "available" || ch.status === "started"
                            ? "text-white"
                            : "bg-[#F3F4F6] text-[#9CA3AF]"
                        }`}
                          style={!isCompleted && !isLocked ? { background: track.color } : undefined}
                        >
                          {isCompleted ? "✓" : idx + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium leading-tight ${isLocked ? "text-[#9CA3AF]" : "text-[#1C1C1E]"}`}>
                            {ch.title}
                          </p>
                          <p className="text-[#9CA3AF] text-xs mt-0.5">{ch.level} · {ch.duration}</p>
                        </div>
                        {!isLocked && (
                          <span className="text-[#9CA3AF] text-sm">→</span>
                        )}
                        {isLocked && (
                          <span className="text-[#9CA3AF] text-sm">🔒</span>
                        )}
                      </div>
                    );
                  })}
                  {!isExpanded && track.chapters.length > 4 && (
                    <button
                      className="w-full py-3 text-[#10B981] text-xs font-medium text-center"
                      onClick={() => setExpandedTrack(track.id)}
                    >
                      {track.chapters.length - 4}개 챕터 더 보기 ▼
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 오늘의 브리핑 — 콘텐츠 있을 때만 표시 */}
      {contents.length > 0 && (
        <div className="mx-5 mt-4">
          <p className="text-[#1C1C1E] font-bold text-base mb-3">오늘의 브리핑</p>
          <p className="text-[#9CA3AF] text-xs mb-3">읽고 나서 퀴즈로 확인해보세요 ✏️</p>
          <div className="flex flex-col gap-4">
            {contents.map((c) => (
              <div key={c.id} className="bg-white rounded-3xl card-shadow overflow-hidden">
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-[#ECFDF5] text-[#10B981] text-xs px-2.5 py-1 rounded-full font-medium">
                      {c.source}
                    </span>
                    <span className="text-[#9CA3AF] text-xs">{c.topic_category}</span>
                  </div>
                  <h3 className="text-[#1C1C1E] font-bold text-sm leading-snug mb-2">{c.title}</h3>
                  <p className={`text-[#6B7280] text-xs leading-relaxed ${expandedNews === c.id ? "" : "line-clamp-2"}`}>
                    {c.summary}
                  </p>
                  <button
                    onClick={() => setExpandedNews(expandedNews === c.id ? null : c.id)}
                    className="text-[#10B981] text-xs mt-1 font-medium"
                  >
                    {expandedNews === c.id ? "접기 ↑" : "더 읽기 ↓"}
                  </button>
                </div>
                <div className="border-t border-[#F9FAFB] flex">
                  {c.original_url && (
                    <a href={c.original_url} target="_blank" rel="noreferrer"
                      className="flex-1 py-3 text-center text-[#6B7280] text-xs font-medium">
                      원문 읽기 →
                    </a>
                  )}
                  <button
                    onClick={() => router.push(`/quiz?content_id=${c.id}`)}
                    className="flex-1 py-3 text-center bg-[#ECFDF5] text-[#10B981] text-xs font-bold rounded-br-3xl"
                  >
                    ✏️ 이 내용으로 퀴즈 풀기
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 개념별 레벨 */}
      {levels.length > 0 && (
        <div className="mx-5 mt-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[#1C1C1E] font-bold text-base">내 지식 레벨</p>
            <Link href="/map" className="text-[#10B981] text-sm font-medium">전체 보기</Link>
          </div>
          <div className="bg-white rounded-3xl p-4 card-shadow flex flex-col gap-3">
            {levels.slice(0, 3).map((l) => (
              <div key={l.concept}>
                <div className="flex justify-between mb-1">
                  <span className="text-[#1C1C1E] text-sm font-medium">{l.concept}</span>
                  <span className="text-[#10B981] text-sm font-bold">{l.level}%</span>
                </div>
                <div className="w-full bg-[#F3F4F6] rounded-full h-2 overflow-hidden">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-700"
                    style={{ width: `${l.level}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <BottomNav active="home" />
    </div>
  );
}
