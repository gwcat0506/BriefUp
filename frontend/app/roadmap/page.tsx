"use client";

import { useState, useEffect } from "react";
import BottomNav from "@/components/layout/BottomNav";
import { useRouter } from "next/navigation";
import { api, CurriculumTrack, TEMP_USER_ID } from "@/lib/api";
import { SkeletonCard } from "@/components/ui/Skeleton";

const LEVEL_COLOR: Record<string, string> = {
  "입문": "#10B981",
  "기본": "#F59E0B",
  "심화": "#EF4444",
};

export default function RoadmapPage() {
  const router = useRouter();
  const [curricula, setCurricula] = useState<CurriculumTrack[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCurricula(TEMP_USER_ID)
      .then((data) => {
        setCurricula(data);
        if (data.length > 0) setSelected(data[0].id);
      })
      .catch(() => {
        // API 실패 시 기본 3트랙 폴백 (Render 콜드 스타트 등)
        const fallback = [
          { id: "rag",   title: "RAG (검색 증강 생성)", emoji: "🔍", color: "#10B981", description: "AI가 외부 지식을 검색해서 답하는 기술 — Naive부터 Graph RAG까지", totalChapters: 10, chapters: [] },
          { id: "agent", title: "Agentic AI",          emoji: "🤖", color: "#8B5CF6", description: "스스로 계획하고, 도구를 쓰고, 협력하는 AI 에이전트 설계",        totalChapters: 10, chapters: [] },
          { id: "llm",   title: "LLM 이론과 실제",     emoji: "🧠", color: "#F59E0B", description: "Transformer 구조부터 RLHF·추론 최적화까지 — 대형 언어 모델의 모든 것", totalChapters: 10, chapters: [] },
        ] as any[];
        setCurricula(fallback);
        setSelected("rag");
      })
      .finally(() => setLoading(false));
  }, []);

  const curriculum = curricula.find((c) => c.id === selected);

  return (
    <div className="flex flex-col min-h-screen pb-24 bg-[#FAFAF8]">

      {/* 헤더 */}
      <div className="px-5 pt-14 pb-4 bg-white border-b border-[#F9FAFB]">
        <h1 className="text-2xl font-bold text-[#1C1C1E]">학습 로드맵 📚</h1>
        <p className="text-[#9CA3AF] text-sm mt-1">관심사 기반 단계별 커리큘럼</p>
      </div>

      {loading ? (
        <div className="px-5 pt-4 flex flex-col gap-3">
          <div className="flex gap-2 overflow-x-auto pb-1">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex-shrink-0 w-28 h-9 bg-[#F3F4F6] rounded-full animate-pulse" />
            ))}
          </div>
          <SkeletonCard className="h-36" />
          <SkeletonCard className="h-24" />
          <SkeletonCard className="h-24" />
        </div>
      ) : curricula.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 px-5 text-center">
          <p className="text-5xl mb-4">📭</p>
          <p className="text-[#1C1C1E] font-bold text-lg mb-2">관심사를 먼저 설정해주세요</p>
          <p className="text-[#9CA3AF] text-sm mb-6">마이페이지에서 관심사를 추가하면<br />맞춤 커리큘럼이 나타나요</p>
          <button
            onClick={() => router.push("/mypage")}
            className="bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold px-6 py-3 rounded-2xl text-sm"
          >
            관심사 설정하러 가기 →
          </button>
        </div>
      ) : (
        <>
          {/* 주제 탭 */}
          <div className="px-5 pt-4 pb-2">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {curricula.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelected(c.id)}
                  className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    selected === c.id
                      ? "text-white shadow-md"
                      : "bg-white text-[#6B7280] card-shadow"
                  }`}
                  style={selected === c.id ? { backgroundColor: c.color } : {}}
                >
                  {c.emoji} {c.title}
                </button>
              ))}
            </div>
          </div>

          {curriculum && (
            <div className="px-5 mt-2">
              {/* 커리큘럼 소개 */}
              {(() => {
                const completedCount = curriculum.chapters.filter(
                  (ch) => ch.status === "completed"
                ).length;
                const pct = Math.round((completedCount / curriculum.totalChapters) * 100);
                return (
                  <div
                    className="rounded-3xl p-4 mb-4 text-white"
                    style={{ backgroundColor: curriculum.color }}
                  >
                    <p className="text-4xl mb-2">{curriculum.emoji}</p>
                    <h2 className="font-bold text-lg">{curriculum.title}</h2>
                    <p className="text-white/80 text-sm mt-1">{curriculum.description}</p>
                    <div className="flex items-center gap-3 mt-3">
                      <span className="bg-white/20 text-white text-xs px-3 py-1 rounded-full">
                        {completedCount}/{curriculum.totalChapters} 완료
                      </span>
                      <span className="bg-white/20 text-white text-xs px-3 py-1 rounded-full">
                        {pct}%
                      </span>
                    </div>
                    <div className="mt-3 w-full bg-white/20 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-1.5 bg-white rounded-full transition-all duration-700"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })()}

              {/* 챕터 목록 */}
              <div className="flex flex-col gap-3">
                {curriculum.chapters.map((ch, idx) => {
                  const isCompleted = ch.status === "completed";
                  const isStarted = ch.status === "started";
                  const isLocked = ch.status === "locked";

                  return (
                    <div
                      key={ch.chapter_id}
                      className={`bg-white rounded-3xl p-4 card-shadow ${
                        isLocked ? "opacity-60" : ""
                      } ${isCompleted ? "border-2 border-[#10B981]/30" : ""}`}
                    >
                      <div className="flex items-start gap-3">
                        {/* 챕터 번호 / 상태 */}
                        <div
                          className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5"
                          style={
                            isLocked
                              ? { backgroundColor: "#F3F4F6", color: "#9CA3AF" }
                              : isCompleted
                              ? { backgroundColor: "#ECFDF5", color: "#10B981" }
                              : { backgroundColor: `${curriculum.color}15`, color: curriculum.color }
                          }
                        >
                          {isLocked ? "🔒" : isCompleted ? "✓" : isStarted ? "▶" : idx + 1}
                        </div>

                        {/* 챕터 내용 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className="text-xs px-2 py-0.5 rounded-full font-medium"
                              style={{
                                backgroundColor: `${LEVEL_COLOR[ch.level]}15`,
                                color: LEVEL_COLOR[ch.level],
                              }}
                            >
                              {ch.level}
                            </span>
                            <span className="text-[#9CA3AF] text-xs">{ch.duration}</span>
                          </div>
                          <p className={`font-bold text-sm ${isLocked ? "text-[#9CA3AF]" : "text-[#1C1C1E]"}`}>
                            {ch.title}
                          </p>
                          <p className="text-[#9CA3AF] text-xs mt-0.5 leading-relaxed">
                            {ch.description}
                          </p>
                        </div>

                        {/* 시작 버튼 */}
                        {!isLocked && (
                          <button
                            onClick={() => router.push(`/learn?id=${ch.chapter_id}`)}
                            className="flex-shrink-0 px-3 py-1.5 rounded-xl text-xs font-bold active:scale-95 transition-all"
                            style={isCompleted
                              ? { backgroundColor: "#ECFDF5", color: "#10B981" }
                              : { backgroundColor: curriculum.color, color: "#fff" }
                            }
                          >
                            {isCompleted ? "복습" : isStarted ? "이어서" : "시작"}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* 안내 */}
              <div className="mt-4 bg-[#FFFBEB] border border-[#FDE68A] rounded-2xl p-4">
                <p className="text-[#92400E] text-xs leading-relaxed">
                  💡 <span className="font-bold">어떻게 학습하나요?</span><br />
                  홈에서 오늘의 브리핑을 읽고, 퀴즈를 풀면 해당 챕터의 레벨이 올라가요.
                  앞 챕터를 완료하면 다음 챕터가 해금됩니다!
                </p>
              </div>
            </div>
          )}
        </>
      )}

      <BottomNav active="roadmap" />
    </div>
  );
}
