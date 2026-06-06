"use client";

import { useEffect, useState } from "react";
import { api, QuizResult, TEMP_USER_ID } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";

export default function HistoryPage() {
  const [history, setHistory] = useState<QuizResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHistory(TEMP_USER_ID)
      .then(setHistory)
      .finally(() => setLoading(false));
  }, []);

  const correct = history.filter((h) => h.is_correct).length;

  return (
    <div className="flex flex-col min-h-screen pb-20">
      <div className="px-5 pt-12 pb-6">
        <h1 className="text-2xl font-bold text-white">학습 기록</h1>
        {history.length > 0 && (
          <p className="text-[#94A3B8] text-sm mt-1">
            총 {history.length}문제 · 정답 {correct}개 ({Math.round(correct / history.length * 100)}%)
          </p>
        )}
      </div>

      <div className="px-5 flex-1">
        {loading && (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-[#1E3A5F] rounded-2xl h-20 animate-pulse" />
            ))}
          </div>
        )}

        {!loading && history.length === 0 && (
          <div className="text-center py-16">
            <p className="text-4xl mb-3">📝</p>
            <p className="text-white font-bold text-lg mb-1">아직 기록이 없어요</p>
            <p className="text-[#94A3B8] text-sm">퀴즈를 풀면 여기에 기록됩니다</p>
          </div>
        )}

        <div className="flex flex-col gap-3">
          {history.map((h) => (
            <div key={h.id} className="bg-[#1E3A5F] rounded-2xl p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <p className="text-white text-sm font-medium leading-snug">
                    {h.quizzes?.question || "질문 없음"}
                  </p>
                  {h.quizzes?.concept && (
                    <span className="inline-block mt-1 bg-[#0D9488]/20 text-[#14B8A6] text-xs px-2 py-0.5 rounded-full">
                      {h.quizzes.concept}
                    </span>
                  )}
                </div>
                <span className={`text-lg flex-shrink-0 ${h.is_correct ? "text-[#0D9488]" : "text-red-400"}`}>
                  {h.is_correct ? "✅" : "❌"}
                </span>
              </div>
              {!h.is_correct && h.quizzes?.explanation && (
                <p className="text-[#94A3B8] text-xs mt-2 leading-relaxed">
                  {h.quizzes.explanation}
                </p>
              )}
              <p className="text-[#475569] text-xs mt-2">
                {new Date(h.answered_at).toLocaleDateString("ko-KR")}
              </p>
            </div>
          ))}
        </div>
      </div>

      <BottomNav active="history" />
    </div>
  );
}
