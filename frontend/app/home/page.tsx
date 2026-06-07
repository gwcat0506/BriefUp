"use client";

import { useEffect, useState } from "react";
import { api, Content, Streak, ConceptLevel, NextChapter, StreakStatus, TEMP_USER_ID } from "@/lib/api";
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
  const [nextChapter, setNextChapter] = useState<NextChapter | null>(null);
  const [reviewCount, setReviewCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expandedNews, setExpandedNews] = useState<string | null>(null);
  const [milestoneShown, setMilestoneShown] = useState(false);
  const router = useRouter();
  const { show: showToast, ToastComponent } = useToast();

  const loadData = () => {
    setLoading(true);
    // allSettled: 하나 실패해도 나머지 데이터는 표시
    Promise.allSettled([
      api.getTodayContentForUser(TEMP_USER_ID),
      api.getStreak(TEMP_USER_ID),
      api.getLevels(TEMP_USER_ID),
      api.getNextChapter(TEMP_USER_ID),
      api.getStreakStatus(TEMP_USER_ID),
      api.getReviewQuizzes(TEMP_USER_ID),
    ]).then(([c, s, l, next, status, reviews]) => {
      if (c.status === "fulfilled") setContents(c.value);
      if (s.status === "fulfilled") setStreak(s.value);
      if (l.status === "fulfilled") setLevels(l.value);
      if (next.status === "fulfilled") setNextChapter(next.value);
      if (status.status === "fulfilled") setStreakStatus(status.value);
      if (reviews.status === "fulfilled") setReviewCount(reviews.value.length);
      // 마일스톤 달성 시 토스트
      if (s.status === "fulfilled" && s.value?.milestone && !milestoneShown) {
        showToast(`${s.value.milestone.badge} ${s.value.milestone.reward}`, "success");
        setMilestoneShown(true);
      }
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

      {/* 학습 현황 카드 */}
      {loading ? <div className="mx-5 mt-4"><SkeletonStat /></div> : null}
      <div className={`mx-5 mt-4 bg-white rounded-3xl p-5 card-shadow ${loading ? "hidden" : ""}`}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-[#6B7280] text-xs mb-1">전체 학습 레벨</p>
            <p className="text-3xl font-bold text-[#1C1C1E]">
              {avgLevel}<span className="text-lg text-[#6B7280]">%</span>
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className="text-[#6B7280] text-xs">연속</p>
              <p className="text-lg font-bold text-[#F59E0B]">🔥 {streak?.current_streak ?? 0}일</p>
            </div>
            <div className="text-center">
              <p className="text-[#6B7280] text-xs">정답률</p>
              <p className="text-lg font-bold text-[#10B981]">{accuracy}%</p>
            </div>
          </div>
        </div>
        <div className="w-full bg-[#F3F4F6] rounded-full h-3 mb-2 overflow-hidden">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-1000"
            style={{ width: `${avgLevel}%` }}
          />
        </div>
        <p className="text-[#9CA3AF] text-xs">
          {avgLevel < 30 ? "시작이 반이에요! 꾸준히 해봐요 🌱" :
           avgLevel < 60 ? "잘 하고 있어요! 계속 달려봐요 🚀" :
           avgLevel < 90 ? "거의 다 왔어요! 조금만 더 💎" : "마스터에 가까워요 🏆"}
        </p>
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

      {/* 커리큘럼 로드맵 배너 */}
      <div className="mx-5 mt-4">
        <Link href="/roadmap">
          <div className="bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] rounded-3xl p-4 flex items-center justify-between text-white">
            <div>
              <p className="text-purple-200 text-xs mb-0.5">학습 경로</p>
              <p className="font-bold">커리큘럼 로드맵 보기 📚</p>
              <p className="text-purple-200 text-xs mt-0.5">RAG · Agentic AI · LLM 단계별 학습</p>
            </div>
            <span className="text-2xl">→</span>
          </div>
        </Link>
      </div>

      {/* 오늘의 브리핑 — 퀴즈 연결 */}
      <div className="mx-5 mt-4">
        <p className="text-[#1C1C1E] font-bold text-base mb-3">오늘의 브리핑</p>
        <p className="text-[#9CA3AF] text-xs mb-3">읽고 나서 퀴즈로 확인해보세요 ✏️</p>

        {loading && (
          <div className="flex flex-col gap-3">
            <SkeletonCard className="h-32" />
            <SkeletonCard className="h-32" />
          </div>
        )}

        {!loading && contents.length === 0 && (
          <div className="bg-white rounded-3xl p-6 text-center card-shadow">
            <p className="text-3xl mb-2">🌅</p>
            <p className="text-[#1C1C1E] font-bold mb-1">아직 오늘의 브리핑이 없어요</p>
            <p className="text-[#9CA3AF] text-sm">새벽 5시에 자동으로 준비됩니다</p>
          </div>
        )}

        <div className="flex flex-col gap-4">
          {contents.map((c) => (
            <div key={c.id} className="bg-white rounded-3xl card-shadow overflow-hidden">
              {/* 브리핑 헤더 */}
              <div className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="bg-[#ECFDF5] text-[#10B981] text-xs px-2.5 py-1 rounded-full font-medium">
                    {c.source}
                  </span>
                  <span className="text-[#9CA3AF] text-xs">{c.topic_category}</span>
                </div>
                <h3 className="text-[#1C1C1E] font-bold text-sm leading-snug mb-2">
                  {c.title}
                </h3>

                {/* 요약 — 펼치기 */}
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

              {/* 하단 액션 */}
              <div className="border-t border-[#F9FAFB] flex">
                {c.original_url && (
                  <a
                    href={c.original_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 py-3 text-center text-[#6B7280] text-xs font-medium"
                  >
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
