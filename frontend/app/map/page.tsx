"use client";

import { useEffect, useState } from "react";
import { api, ConceptLevel, TEMP_USER_ID } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";

const LEVEL_BADGE = [
  { min: 80, label: "마스터", color: "#F59E0B", bg: "#FFFBEB" },
  { min: 50, label: "숙련",   color: "#10B981", bg: "#ECFDF5" },
  { min: 20, label: "기초",   color: "#3B82F6", bg: "#EFF6FF" },
  { min: 0,  label: "입문",   color: "#9CA3AF", bg: "#F9FAFB" },
];

function badge(level: number) {
  return LEVEL_BADGE.find((b) => level >= b.min)!;
}

const RADIUS = 26;
const CIRC = 2 * Math.PI * RADIUS;

function RingCard({ item }: { item: ConceptLevel }) {
  const b = badge(item.level);
  const offset = CIRC - (item.level / 100) * CIRC;

  return (
    <div className="bg-white rounded-3xl p-4 card-shadow flex flex-col items-center gap-2">
      <svg width="72" height="72" viewBox="0 0 72 72">
        <circle cx="36" cy="36" r={RADIUS} fill="none" stroke="#F3F4F6" strokeWidth="6" />
        <circle
          cx="36" cy="36" r={RADIUS}
          fill="none"
          stroke={b.color}
          strokeWidth="6"
          strokeDasharray={CIRC}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 36 36)"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        <text x="36" y="41" textAnchor="middle" fontSize="13" fontWeight="bold" fill={b.color}>
          {item.level}%
        </text>
      </svg>
      <p className="text-[#1C1C1E] text-xs font-semibold text-center leading-tight">{item.concept}</p>
      <span
        className="text-[10px] font-bold px-2 py-0.5 rounded-full"
        style={{ color: b.color, backgroundColor: b.bg }}
      >
        {b.label}
      </span>
    </div>
  );
}

const CATEGORY_EMOJI: Record<string, string> = {
  "AI/ML": "🤖", "프로그래밍": "💻", "수학": "📐", "데이터": "📊",
  "경제": "💹", "철학": "🧠", "과학": "🔬", "역사": "📜",
};

export default function MapPage() {
  const [levels, setLevels] = useState<ConceptLevel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLevels(TEMP_USER_ID)
      .then(setLevels)
      .finally(() => setLoading(false));
  }, []);

  const grouped = levels.reduce<Record<string, ConceptLevel[]>>((acc, l) => {
    if (!acc[l.category]) acc[l.category] = [];
    acc[l.category].push(l);
    return acc;
  }, {});

  const totalMastered = levels.filter((l) => l.level >= 80).length;

  return (
    <div className="flex flex-col min-h-screen pb-24 bg-[#FAFAF8]">
      <div className="px-5 pt-14 pb-4">
        <p className="text-[#6B7280] text-sm mb-0.5">내 학습 현황</p>
        <h1 className="text-2xl font-bold text-[#1C1C1E]">지식 맵 🗺️</h1>
      </div>

      {/* 요약 칩 */}
      {!loading && levels.length > 0 && (
        <div className="flex gap-2 px-5 mb-4">
          <div className="bg-white rounded-2xl px-4 py-2.5 card-shadow text-center">
            <p className="text-[#1C1C1E] font-bold text-lg">{levels.length}</p>
            <p className="text-[#9CA3AF] text-xs">개념 수</p>
          </div>
          <div className="bg-white rounded-2xl px-4 py-2.5 card-shadow text-center">
            <p className="text-[#F59E0B] font-bold text-lg">{totalMastered}</p>
            <p className="text-[#9CA3AF] text-xs">마스터</p>
          </div>
          <div className="bg-white rounded-2xl px-4 py-2.5 card-shadow text-center flex-1">
            <p className="text-[#10B981] font-bold text-lg">
              {levels.length > 0 ? Math.round(levels.reduce((a, b) => a + b.level, 0) / levels.length) : 0}%
            </p>
            <p className="text-[#9CA3AF] text-xs">평균 숙련도</p>
          </div>
        </div>
      )}

      <div className="px-5 flex-1">
        {loading && (
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-3xl h-36 animate-pulse card-shadow" />
            ))}
          </div>
        )}

        {!loading && levels.length === 0 && (
          <div className="text-center py-20">
            <p className="text-5xl mb-4">🗺️</p>
            <p className="text-[#1C1C1E] font-bold text-lg mb-1">아직 데이터가 없어요</p>
            <p className="text-[#9CA3AF] text-sm">커리큘럼 퀴즈를 풀면 채워져요</p>
          </div>
        )}

        {Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="mb-6">
            <p className="text-[#1C1C1E] font-bold text-sm mb-3">
              {CATEGORY_EMOJI[category] ?? "📌"} {category}
            </p>
            <div className="grid grid-cols-2 gap-3">
              {items.map((item) => (
                <RingCard key={item.concept} item={item} />
              ))}
            </div>
          </div>
        ))}
      </div>

      <BottomNav active="map" />
    </div>
  );
}
