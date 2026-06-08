"use client";

import { useEffect, useState, Suspense, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import BottomNav from "@/components/layout/BottomNav";
import { api, TEMP_USER_ID } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Card {
  type: "hook" | "concept" | "example" | "insight" | "summary";
  emoji: string;
  title: string;
  content?: string;
  points?: string[];
}

interface CardsData {
  chapter_title: string;
  cards: Card[];
}

interface ContentRow {
  id: string;
  title: string;
  summary: string;
}

const LOADING_STEPS = [
  { label: "챕터 내용 확인 중", pct: 15 },
  { label: "AI가 설명 카드 생성 중", pct: 35 },
  { label: "개념 정리하는 중", pct: 55 },
  { label: "예시와 인사이트 추가 중", pct: 75 },
  { label: "마무리 중", pct: 90 },
];

function LoadingScreen() {
  const [pct, setPct] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let elapsed = 0;
    timerRef.current = setInterval(() => {
      elapsed += 200;
      // 20초 기준으로 진행률 계산 (최대 92%에서 멈춤)
      const natural = Math.min(92, (elapsed / 20000) * 100);
      setPct(natural);
      // 단계 메시지 업데이트
      const idx = [...LOADING_STEPS].reverse().findIndex(s => natural >= s.pct - 15);
      const resolvedIdx = idx === -1 ? 0 : LOADING_STEPS.length - 1 - idx;
      setStepIdx(resolvedIdx);
    }, 200);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  const step = LOADING_STEPS[stepIdx];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#FAFAF8] px-8">
      <div className="text-6xl mb-6">📖</div>
      <p className="text-[#1C1C1E] font-bold text-lg mb-1">설명 카드 준비 중</p>
      <p className="text-[#9CA3AF] text-sm mb-8">{step.label}...</p>

      {/* 진행 바 */}
      <div className="w-full max-w-xs bg-[#F3F4F6] rounded-full h-2.5 overflow-hidden mb-3">
        <div
          className="h-2.5 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-[#10B981] text-xs font-bold">{Math.round(pct)}%</p>

      <p className="text-[#D1D5DB] text-xs mt-6">AI가 실시간으로 만들어요 — 처음엔 15초 정도</p>
    </div>
  );
}

// 카드 타입별 배경색
const CARD_STYLES: Record<string, { bg: string; border: string; titleColor: string }> = {
  hook:    { bg: "#FFF7ED", border: "#FED7AA", titleColor: "#C2410C" },
  concept: { bg: "#ECFDF5", border: "#A7F3D0", titleColor: "#065F46" },
  example: { bg: "#EFF6FF", border: "#BFDBFE", titleColor: "#1D4ED8" },
  insight: { bg: "#FDF4FF", border: "#E9D5FF", titleColor: "#7E22CE" },
  summary: { bg: "#FFFBEB", border: "#FDE68A", titleColor: "#92400E" },
};

function LearnContent() {
  const searchParams = useSearchParams();
  const chapterId = searchParams.get("id") || "";
  const router = useRouter();

  const [cards, setCards] = useState<Card[]>([]);
  const [contentRow, setContentRow] = useState<ContentRow | null>(null);
  const [cardIdx, setCardIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const touchStartX = useRef<number | null>(null);

  const track = chapterId.split("-")[0] || "rag";

  useEffect(() => {
    if (!chapterId) { setError("챕터 ID가 없어요."); setLoading(false); return; }

    fetch(`${API_URL}/api/chapter/${chapterId}`)
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || `오류: ${r.status}`);
        setContentRow(data.content);
        if (data.cards?.cards) {
          setCards(data.cards.cards);
        } else {
          throw new Error("카드 데이터가 없어요.");
        }
        // 학습 시작 기록
        await api.updateProgress({
          user_id: TEMP_USER_ID,
          chapter_id: chapterId,
          track,
          status: "started",
        });
        // 북마크 여부 확인
        if (data.content?.id) {
          const bm = await api.checkBookmark(TEMP_USER_ID, data.content.id);
          setBookmarked(bm.bookmarked);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [chapterId]);

  const currentCard = cards[cardIdx];
  const progress = cards.length > 0 ? ((cardIdx + 1) / cards.length) * 100 : 0;
  const style = (currentCard && CARD_STYLES[currentCard.type]) ?? CARD_STYLES.hook;

  async function handleNext() {
    if (cardIdx + 1 >= cards.length) {
      // 챕터 학습 완료 기록
      await api.updateProgress({
        user_id: TEMP_USER_ID,
        chapter_id: chapterId,
        track,
        status: "completed",
      });
      setDone(true);
    } else {
      setCardIdx(i => i + 1);
    }
  }

  async function handleBookmark() {
    if (!contentRow?.id) return;
    const res = await api.toggleBookmark(TEMP_USER_ID, contentRow.id);
    setBookmarked(res.bookmarked);
  }

  // ── 로딩 ──
  if (loading) return <LoadingScreen />;

  // ── 에러 ──
  if (error) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#FAFAF8] px-5 text-center gap-4">
      <p className="text-5xl">😢</p>
      <p className="text-[#EF4444] text-sm">{error}</p>
      <button onClick={() => router.back()} className="bg-[#10B981] text-white px-5 py-2.5 rounded-xl font-medium text-sm">
        돌아가기
      </button>
    </div>
  );

  // ── 완료 ──
  if (done) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#FAFAF8] px-5 pb-24">
      <div className="text-center mb-8">
        <p className="text-7xl mb-4">🎉</p>
        <h2 className="text-[#1C1C1E] text-2xl font-bold mb-2">학습 완료!</h2>
        <p className="text-[#6B7280] text-sm">이제 퀴즈로 확인해볼까요?</p>
      </div>
      <div className="w-full flex flex-col gap-3">
        <button
          onClick={() => contentRow && router.push(`/quiz?content_id=${contentRow.id}`)}
          className="w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-base shadow-lg shadow-emerald-100 active:scale-95 transition-all"
        >
          ✏️ 퀴즈 풀기
        </button>
        <button
          onClick={() => router.push("/roadmap")}
          className="w-full bg-white text-[#6B7280] font-medium py-4 rounded-2xl text-sm border border-[#F3F4F6]"
        >
          로드맵으로 돌아가기
        </button>
      </div>
      <BottomNav active="home" />
    </div>
  );

  if (!currentCard) return null;

  return (
    <div className="flex flex-col min-h-screen bg-[#FAFAF8] pb-24">

      {/* 헤더 + 진행 바 */}
      <div className="bg-white border-b border-[#F9FAFB] px-5 pt-14 pb-4">
        <div className="flex items-center justify-between mb-3">
          <button onClick={() => router.back()} className="text-[#9CA3AF] text-sm">← 뒤로</button>
          <div className="flex items-center gap-3">
            <span className="text-[#9CA3AF] text-xs font-medium">{cardIdx + 1} / {cards.length}</span>
            <button
              onClick={handleBookmark}
              className="text-xl transition-all active:scale-90"
              title={bookmarked ? "북마크 해제" : "북마크"}
            >
              {bookmarked ? "🔖" : "🏷️"}
            </button>
          </div>
        </div>
        <div className="w-full bg-[#F3F4F6] rounded-full h-2 overflow-hidden">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* 카드 */}
      <div className="flex-1 px-5 py-6 flex flex-col">
        <div
          key={cardIdx}
          className="flex-1 rounded-3xl p-6 border-2 flex flex-col justify-between"
          style={{ backgroundColor: style.bg, borderColor: style.border }}
        >
          {/* 카드 상단 */}
          <div>
            <div className="flex items-center gap-3 mb-5">
              <span className="text-4xl">{currentCard.emoji}</span>
              <div>
                <p className="text-xs font-medium mb-0.5" style={{ color: style.titleColor }}>
                  {currentCard.type === "hook" ? "공감하기" :
                   currentCard.type === "concept" ? "개념 이해" :
                   currentCard.type === "example" ? "실제 사례" :
                   currentCard.type === "insight" ? "핵심 인사이트" : "정리"}
                </p>
                <h2 className="text-[#1C1C1E] font-bold text-lg leading-tight">
                  {currentCard.title}
                </h2>
              </div>
            </div>

            {/* 내용 */}
            {currentCard.content && (
              <p className="text-[#374151] text-base leading-relaxed">
                {currentCard.content}
              </p>
            )}

            {/* summary 카드 포인트 */}
            {currentCard.points && (
              <div className="flex flex-col gap-3 mt-2">
                {currentCard.points.map((pt, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <span
                      className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 text-white"
                      style={{ backgroundColor: style.titleColor }}
                    >
                      {i + 1}
                    </span>
                    <p className="text-[#374151] text-sm leading-relaxed flex-1">{pt}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 카드 하단 — 탭 인디케이터 */}
          <div className="flex gap-1.5 justify-center mt-6">
            {cards.map((_, i) => (
              <div
                key={i}
                className="h-1.5 rounded-full transition-all duration-300"
                style={{
                  width: i === cardIdx ? "24px" : "6px",
                  backgroundColor: i === cardIdx ? style.titleColor : "#D1D5DB",
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* 다음 버튼 */}
      <div className="px-5 pb-2">
        <button
          onClick={handleNext}
          className="w-full font-bold py-4 rounded-2xl text-base active:scale-95 transition-all text-white shadow-lg"
          style={{ background: `linear-gradient(to right, ${style.titleColor}, ${style.titleColor}cc)` }}
        >
          {cardIdx + 1 >= cards.length ? "학습 완료! 퀴즈 풀기 →" : "다음 카드 →"}
        </button>
      </div>

      <BottomNav active="home" />
    </div>
  );
}

export default function LearnPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-[#FAFAF8]">
        <p className="text-5xl animate-bounce">📖</p>
      </div>
    }>
      <LearnContent />
    </Suspense>
  );
}
