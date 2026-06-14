"use client";

import { useEffect, useRef, useState } from "react";
import { api, HomeSummary, Streak, ConceptLevel, StreakStatus, XpInfo, CurriculumTrack, TEMP_USER_ID } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SkeletonCard, SkeletonStat } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import ProgressBar from "@/components/ui/ProgressBar";

// ── localStorage SWR 캐시 ────────────────────────────────────────
const CACHE_KEY = `home_summary_v1_${TEMP_USER_ID}`;
const CACHE_TTL = 5 * 60 * 1000; // 5분

function getCached(): HomeSummary | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL) return null;
    return data as HomeSummary;
  } catch {
    return null;
  }
}

function setCached(data: HomeSummary) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ data, ts: Date.now() }));
  } catch {}
}

// ── 컴포넌트 ────────────────────────────────────────────────────
export default function HomePage() {
  const [streak, setStreak] = useState<Streak | null>(null);
  const [streakStatus, setStreakStatus] = useState<StreakStatus | null>(null);
  const [levels, setLevels] = useState<ConceptLevel[]>([]);
  const [xpInfo, setXpInfo] = useState<XpInfo | null>(null);
  const [curricula, setCurricula] = useState<CurriculumTrack[]>([]);
  const [reviewCount, setReviewCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [milestoneShown, setMilestoneShown] = useState(false);
  const router = useRouter();
  const { show: showToast, ToastComponent } = useToast();
  const lastFetchRef = useRef(0);
  const milestoneShownRef = useRef(false);

  const applyData = (data: HomeSummary) => {
    if (data.streak) {
      setStreak(data.streak);
      if (data.streak.milestone && !milestoneShownRef.current) {
        showToast(`${data.streak.milestone.badge} ${data.streak.milestone.reward}`, "success");
        milestoneShownRef.current = true;
        setMilestoneShown(true);
      }
    }
    if (data.streak_status) setStreakStatus(data.streak_status);
    if (data.xp_info) setXpInfo(data.xp_info);
    setLevels(data.levels ?? []);
    setReviewCount(data.review_count ?? 0);
    if (data.curricula?.length) {
      const sorted = [...data.curricula].sort((a, b) => {
        const score = (t: CurriculumTrack) => {
          if (t.chapters.some(ch => ch.status === "started")) return 2;
          if (t.chapters.some(ch => ch.status === "available")) return 1;
          return 0;
        };
        return score(b) - score(a);
      });
      setCurricula(sorted);
    }
  };

  const loadData = (force = false) => {
    const now = Date.now();
    // 5분 내 재호출은 무시 (window focus 반복 방지). force=true면 항상 실행
    if (!force && now - lastFetchRef.current < CACHE_TTL) return;
    lastFetchRef.current = now;

    // 캐시가 있으면 즉시 렌더링 (체감 0초)
    const cached = getCached();
    if (cached) {
      applyData(cached);
      setLoading(false);
    }

    // 백그라운드에서 최신 데이터 페치
    api.getHomeSummary(TEMP_USER_ID)
      .then(data => {
        setCached(data);
        applyData(data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(true); }, []);

  useEffect(() => {
    const handleFocus = () => loadData();
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  async function handleStreakFreeze() {
    try {
      const res = await api.useStreakFreeze(TEMP_USER_ID);
      showToast(res.message, "success");
      lastFetchRef.current = 0; // 강제 재로드
      loadData(true);
    } catch (e: any) {
      showToast(e.message || "프리즈 사용 실패", "error");
    }
  }

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

      {/* 전체 로딩 중 skeleton (캐시 없을 때만) */}
      {loading && (
        <div className="mx-5 mt-4 flex flex-col gap-4">
          <SkeletonStat />
          <SkeletonCard className="h-12" />
          <SkeletonCard className="h-48" />
        </div>
      )}

      {/* 데이터 있으면 표시 */}
      {!loading && (
        <>
          {/* 캐릭터 + 레벨 카드 */}
          <div className="mx-5 mt-4 bg-white rounded-3xl p-5 card-shadow">
            <div className="flex items-center gap-4">
              <div className="flex-shrink-0 w-20 h-20 bg-gradient-to-br from-[#ECFDF5] to-[#D1FAE5] rounded-2xl flex items-center justify-center">
                <span className="text-4xl character-heartbeat inline-block">{xpInfo?.char_emoji ?? "🥚"}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-0.5">
                  <div>
                    <span className="text-[#10B981] font-bold text-lg">Lv.{xpInfo?.level ?? 1}</span>
                    <span className="text-[#6B7280] text-sm ml-2">{xpInfo?.char_title ?? "입문자"}</span>
                  </div>
                  <span className="text-[#1C1C1E] font-bold text-sm">{xpInfo?.char_name ?? "알"}</span>
                </div>
                <ProgressBar pct={xpInfo?.progress_pct ?? 0} height="md" duration={1000} className="mb-1.5" />
                <div className="flex justify-between items-center">
                  <p className="text-[#9CA3AF] text-xs">{xpInfo?.xp_in_level ?? 0} / {xpInfo?.xp_needed ?? 50} XP</p>
                  <p className="text-[#9CA3AF] text-xs">다음 레벨까지 {(xpInfo?.xp_needed ?? 50) - (xpInfo?.xp_in_level ?? 0)} XP</p>
                </div>
              </div>
            </div>

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
                <p className={`font-bold text-sm ${streakStatus.status === "broken" ? "text-[#DC2626]" : "text-[#C2410C]"}`}>
                  {streakStatus.message}
                </p>
                {streakStatus.freeze_available && streakStatus.freeze_available > 0 && (
                  <p className="text-[#9CA3AF] text-xs mt-0.5">프리즈 {streakStatus.freeze_available}개 보유 중</p>
                )}
              </div>
              {streakStatus.status === "freezeable" && (
                <button onClick={handleStreakFreeze} className="bg-[#F59E0B] text-white text-xs font-bold px-3 py-2 rounded-xl active:scale-95 transition-all">
                  🧊 프리즈 사용
                </button>
              )}
            </div>
          )}

          {/* 마일스톤 */}
          {streak?.milestone && (
            <div className="mx-5 mt-3 bg-gradient-to-r from-[#F59E0B] to-[#EF4444] rounded-2xl p-4 text-white">
              <p className="font-bold text-base">{streak.milestone.badge}</p>
              <p className="text-yellow-100 text-sm mt-0.5">{streak.milestone.reward}</p>
            </div>
          )}
          {streak && !streak.milestone && streak.days_to_next && streak.current_streak > 0 && (
            <div className="mx-5 mt-3 bg-[#FFFBEB] border border-[#FDE68A] rounded-2xl px-4 py-3.5">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[#92400E] text-xs font-bold">
                  🔥 {streak.days_to_next}일만 더 하면 보상이 와요!
                </p>
                <div className="flex gap-1">
                  {Array.from({ length: Math.min(streak.days_to_next, 7) }).map((_, i) => (
                    <div key={i} className="w-2 h-2 rounded-full bg-[#FDE68A]" />
                  ))}
                </div>
              </div>
              {streak.next_milestone_reward && (
                <p className="text-[#B45309] text-xs">
                  🎁 {streak.next_milestone}일 달성 시 → <span className="font-semibold">{streak.next_milestone_reward}</span>
                </p>
              )}
            </div>
          )}

          {/* 복습 퀴즈 */}
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

          {/* 내 관심사 */}
          <div className="mt-4">
            <div className="flex items-center justify-between px-5 mb-3">
              <p className="text-[#1C1C1E] font-bold text-base">내 관심사</p>
              <button onClick={() => router.push("/mypage")} className="text-[#10B981] text-sm font-medium">
                + 추가
              </button>
            </div>
            <div className="px-5">
              {curricula.length === 0 ? (
                <button
                  onClick={() => router.push("/mypage")}
                  className="w-full bg-gradient-to-r from-[#10B981] to-[#059669] rounded-3xl p-5 text-left text-white active:scale-[0.98] transition-all"
                >
                  <p className="text-green-100 text-xs mb-1">원하는 주제라면 무엇이든</p>
                  <p className="font-bold text-base">AI, 경제, 심리학... 뭐든 배워요</p>
                  <p className="text-green-100 text-sm mt-1.5">주제를 추가하면 맞춤 커리큘럼이 자동으로 만들어져요 →</p>
                </button>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {curricula.map((track) => (
                    <span
                      key={track.id}
                      className="flex items-center gap-1.5 bg-white border border-[#E5E7EB] rounded-full px-3 py-1.5 text-sm text-[#1C1C1E] font-medium card-shadow"
                    >
                      <span>{track.emoji}</span>
                      <span>{track.title}</span>
                    </span>
                  ))}
                  <button
                    onClick={() => router.push("/mypage")}
                    className="flex items-center gap-1 bg-[#F0FDF4] border border-[#BBF7D0] rounded-full px-3 py-1.5 text-sm text-[#10B981] font-medium"
                  >
                    + 추가
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* 오늘의 챕터 */}
          <div className="mt-4">
            <div className="flex items-center justify-between px-5 mb-3">
              <p className="text-[#1C1C1E] font-bold text-base">오늘의 챕터 📖</p>
              <Link href="/roadmap" className="text-[#10B981] text-sm font-medium">전체 보기</Link>
            </div>

            {curricula.length === 0 && (
              <div className="px-5">
                <div className="bg-white rounded-3xl card-shadow px-5 py-6 text-center">
                  <p className="text-[#9CA3AF] text-sm">관심사를 추가하면 오늘의 챕터가 나타나요</p>
                </div>
              </div>
            )}

            {curricula.length > 0 && (
              <div className="px-5 flex flex-col gap-3">
                {curricula.map((track) => {
                  const nextCh = track.chapters.find(c => c.status === "started" || c.status === "available");
                  const completedCount = track.chapters.filter(c => c.status === "completed").length;
                  const pct = track.totalChapters > 0 ? Math.round((completedCount / track.totalChapters) * 100) : 0;
                  const chapterNum = nextCh
                    ? track.chapters.findIndex(c => c.chapter_id === nextCh.chapter_id) + 1
                    : null;

                  return (
                    <div key={track.id} className="bg-white rounded-3xl card-shadow overflow-hidden">
                      {/* 트랙 헤더 */}
                      <div className="px-4 pt-4 pb-3 border-b border-[#F3F4F6]">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-base">{track.emoji}</span>
                          <span className="text-sm font-semibold text-[#1C1C1E] truncate">{track.title}</span>
                          <span className="ml-auto text-xs text-[#9CA3AF] flex-shrink-0">{completedCount}/{track.totalChapters} 완료</span>
                        </div>
                        <ProgressBar pct={pct} height="sm" color={track.color} duration={700} />
                      </div>

                      {/* 다음 챕터 */}
                      {nextCh ? (
                        <div className="px-4 py-4 flex items-center gap-3">
                          <div
                            className="w-10 h-10 rounded-2xl flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                            style={{ background: track.color }}
                          >
                            {nextCh.status === "started" ? "▶" : `CH.${chapterNum}`}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-[#1C1C1E] font-semibold text-sm leading-tight">{nextCh.title}</p>
                            <p className="text-[#9CA3AF] text-xs mt-0.5">
                              {nextCh.status === "started" && chapterNum ? `CH.${chapterNum} · ` : ""}{nextCh.level} · {nextCh.duration}
                            </p>
                          </div>
                          <button
                            onClick={() => router.push(`/learn?id=${nextCh.chapter_id}`)}
                            className="flex-shrink-0 px-4 py-2 rounded-2xl text-white text-xs font-bold active:scale-95 transition-all"
                            style={{ background: track.color }}
                          >
                            {nextCh.status === "started" ? "계속하기" : "시작"}
                          </button>
                        </div>
                      ) : (
                        <div className="px-4 py-4 text-center">
                          <p className="text-[#10B981] text-sm font-bold">✅ 완료</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </>
      )}

      <BottomNav active="home" />
    </div>
  );
}
