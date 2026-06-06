"use client";

import { useEffect, useState } from "react";
import { api, ConceptLevel, TEMP_USER_ID } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";

export default function MapPage() {
  const [levels, setLevels] = useState<ConceptLevel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLevels(TEMP_USER_ID)
      .then(setLevels)
      .finally(() => setLoading(false));
  }, []);

  // 카테고리별 그룹핑
  const grouped = levels.reduce<Record<string, ConceptLevel[]>>((acc, l) => {
    if (!acc[l.category]) acc[l.category] = [];
    acc[l.category].push(l);
    return acc;
  }, {});

  function levelColor(level: number) {
    if (level >= 80) return "bg-[#0D9488]";
    if (level >= 50) return "bg-[#0891B2]";
    if (level >= 20) return "bg-[#7C3AED]";
    return "bg-[#1E3A5F]";
  }

  return (
    <div className="flex flex-col min-h-screen pb-20">
      <div className="px-5 pt-12 pb-6">
        <h1 className="text-2xl font-bold text-white">지식 맵</h1>
        <p className="text-[#94A3B8] text-sm mt-1">개념별 학습 레벨</p>
      </div>

      <div className="px-5 flex-1">
        {loading && (
          <div className="flex flex-col gap-4">
            {[1, 2].map((i) => (
              <div key={i} className="bg-[#1E3A5F] rounded-2xl h-40 animate-pulse" />
            ))}
          </div>
        )}

        {!loading && levels.length === 0 && (
          <div className="text-center py-16">
            <p className="text-4xl mb-3">🗺️</p>
            <p className="text-white font-bold text-lg mb-1">아직 데이터가 없어요</p>
            <p className="text-[#94A3B8] text-sm">퀴즈를 풀면 지식 맵이 채워집니다</p>
          </div>
        )}

        {Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="mb-6">
            <h2 className="text-[#14B8A6] text-sm font-bold mb-3">{category}</h2>
            <div className="flex flex-col gap-3">
              {items.map((item) => (
                <div key={item.concept} className="bg-[#1E3A5F] rounded-2xl p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-white text-sm font-medium">{item.concept}</span>
                    <span className="text-[#14B8A6] font-bold text-sm">{item.level}%</span>
                  </div>
                  <div className="w-full bg-[#0F172A] rounded-full h-2 mb-2">
                    <div
                      className={`h-2 rounded-full transition-all ${levelColor(item.level)}`}
                      style={{ width: `${item.level}%` }}
                    />
                  </div>
                  <p className="text-[#475569] text-xs">
                    {item.total_attempts}회 시도 · {item.correct_attempts}회 정답
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <BottomNav active="map" />
    </div>
  );
}
