"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const SLIDES = [
  {
    emoji: "📖",
    title: "BriefUp에 오신 걸\n환영해요",
    desc: "관심사를 말하면 AI가 오늘 읽을\n학습 카드를 직접 만들어줘요.",
    sub: "매일 아침, 딱 맞는 지식이 준비돼 있어요",
    bg: "from-emerald-50 to-white",
    accent: "#10B981",
  },
  {
    emoji: "🎯",
    title: "내 관심사만 골라서\n매일 배워요",
    desc: "AI가 관심사에 맞는 최신 자료를 찾아\n5분 분량 카드로 만들어줘요.",
    sub: "퀴즈까지 풀면 진짜 내 것이 돼요 ✅",
    bg: "from-blue-50 to-white",
    accent: "#3B82F6",
  },
  {
    emoji: "🔥",
    title: "매일 하면\n실력이 달라져요",
    desc: "학습을 완료할 때마다 연속 기록이 쌓이고\n레벨이 올라가요.",
    sub: "하루 빠져도 OK — 보호권 1장이 기록을 지켜줘요 🛡️",
    bg: "from-orange-50 to-white",
    accent: "#F97316",
  },
];

export default function Root() {
  const router = useRouter();
  const [slide, setSlide] = useState(0);

  function proceed() {
    router.replace("/home");
  }

  function nextSlide() {
    if (slide < SLIDES.length - 1) {
      setSlide(s => s + 1);
    } else {
      proceed();
    }
  }

  const s = SLIDES[slide];

  return (
    <div className={`flex flex-col min-h-screen bg-gradient-to-b ${s.bg} transition-all duration-500`}>
      {/* 점 인디케이터 */}
      <div className="flex justify-center gap-2 pt-10">
        {SLIDES.map((_, i) => (
          <div
            key={i}
            className="rounded-full transition-all duration-300"
            style={{
              width: i === slide ? 20 : 6,
              height: 6,
              backgroundColor: i === slide ? s.accent : "#D1FAE5",
            }}
          />
        ))}
      </div>

      {/* 콘텐츠 */}
      <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
        <div
          className="w-24 h-24 rounded-3xl flex items-center justify-center mb-8 shadow-lg"
          style={{ backgroundColor: `${s.accent}18` }}
        >
          <span className="text-5xl">{s.emoji}</span>
        </div>
        <h1 className="text-2xl font-bold text-[#1C1C1E] leading-tight mb-4 whitespace-pre-line">
          {s.title}
        </h1>
        <p className="text-[#6B7280] text-base leading-relaxed whitespace-pre-line mb-3">
          {s.desc}
        </p>
        <p
          className="text-sm font-medium px-4 py-2 rounded-full"
          style={{ color: s.accent, backgroundColor: `${s.accent}15` }}
        >
          {s.sub}
        </p>
      </div>

      {/* 버튼 */}
      <div className="px-6 pb-12 flex flex-col gap-3">
        <button
          onClick={nextSlide}
          className="w-full text-white font-bold py-4 rounded-2xl text-base shadow-lg active:scale-95 transition-all"
          style={{ backgroundColor: s.accent }}
        >
          {slide < SLIDES.length - 1 ? "다음 →" : "시작하기 🎉"}
        </button>
        {slide < SLIDES.length - 1 && (
          <button
            onClick={proceed}
            className="text-[#9CA3AF] text-sm py-2 active:opacity-60"
          >
            건너뛰기
          </button>
        )}
      </div>
    </div>
  );
}
