"use client";

import { useState, useEffect } from "react";
import BottomNav from "@/components/layout/BottomNav";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, TEMP_USER_ID } from "@/lib/api";

// 커리큘럼 데이터 — 나중에 백엔드에서 가져오도록 확장 가능
const CURRICULA = [
  {
    id: "rag",
    title: "RAG (검색 증강 생성)",
    emoji: "🔍",
    color: "#10B981",
    description: "AI가 외부 지식을 검색해서 답하는 기술",
    totalChapters: 5,
    chapters: [
      {
        id: 1,
        title: "검색이란 무엇인가?",
        description: "정보를 찾는 방법 — 키워드 검색부터 의미 검색까지",
        level: "입문",
        duration: "5분",
        status: "available",
      },
      {
        id: 2,
        title: "임베딩과 벡터 DB",
        description: "텍스트를 숫자로 바꾸면 뭐가 달라질까?",
        level: "기본",
        duration: "7분",
        status: "available",
      },
      {
        id: 3,
        title: "Chunking 전략",
        description: "긴 문서를 어떻게 잘라야 AI가 잘 이해할까?",
        level: "기본",
        duration: "6분",
        status: "locked",
      },
      {
        id: 4,
        title: "고급 RAG 기법 (HyDE, Re-ranking)",
        description: "검색 정확도를 더 높이는 방법들",
        level: "심화",
        duration: "10분",
        status: "locked",
      },
      {
        id: 5,
        title: "실전 RAG 파이프라인 구축",
        description: "처음부터 끝까지 직접 만들어보기",
        level: "심화",
        duration: "15분",
        status: "locked",
      },
    ],
  },
  {
    id: "agent",
    title: "Agentic AI",
    emoji: "🤖",
    color: "#8B5CF6",
    description: "스스로 생각하고 도구를 사용하는 AI",
    totalChapters: 5,
    chapters: [
      {
        id: 1,
        title: "Agent란 무엇인가?",
        description: "단순 AI와 Agent의 차이, ReAct 패턴 이해",
        level: "입문",
        duration: "5분",
        status: "available",
      },
      {
        id: 2,
        title: "도구 사용 (Tool Use)",
        description: "AI가 계산기, 검색, 코드를 직접 실행한다면?",
        level: "기본",
        duration: "7분",
        status: "locked",
      },
      {
        id: 3,
        title: "멀티 에이전트 시스템",
        description: "여러 AI가 협력해서 문제를 푸는 방법",
        level: "기본",
        duration: "8분",
        status: "locked",
      },
      {
        id: 4,
        title: "메모리와 상태 관리",
        description: "Agent가 대화를 기억하고 학습하는 방법",
        level: "심화",
        duration: "10분",
        status: "locked",
      },
      {
        id: 5,
        title: "실전 Agent 배포",
        description: "내 Agent를 실제 서비스로 만들기",
        level: "심화",
        duration: "15분",
        status: "locked",
      },
    ],
  },
  {
    id: "llm",
    title: "LLM 기초",
    emoji: "🧠",
    color: "#F59E0B",
    description: "대형 언어 모델의 작동 원리",
    totalChapters: 4,
    chapters: [
      {
        id: 1,
        title: "Transformer 쉽게 이해하기",
        description: "GPT, Claude는 어떻게 글을 쓸까?",
        level: "입문",
        duration: "8분",
        status: "available",
      },
      {
        id: 2,
        title: "프롬프트 엔지니어링",
        description: "AI에게 잘 부탁하는 방법",
        level: "기본",
        duration: "6분",
        status: "locked",
      },
      {
        id: 3,
        title: "Fine-tuning vs RAG",
        description: "언제 학습시키고 언제 검색시킬까?",
        level: "심화",
        duration: "10분",
        status: "locked",
      },
      {
        id: 4,
        title: "LLM 평가와 벤치마크",
        description: "AI 성능을 어떻게 측정할까?",
        level: "심화",
        duration: "8분",
        status: "locked",
      },
    ],
  },
];

const LEVEL_COLOR: Record<string, string> = {
  "입문": "#10B981",
  "기본": "#F59E0B",
  "심화": "#EF4444",
};

export default function RoadmapPage() {
  const [selected, setSelected] = useState<string>("rag");
  const curriculum = CURRICULA.find((c) => c.id === selected)!;
  const router = useRouter();
  const [progress, setProgress] = useState<Record<string, any>>({});

  useEffect(() => {
    api.getProgress(TEMP_USER_ID).then(setProgress).catch(() => {});
  }, []);

  return (
    <div className="flex flex-col min-h-screen pb-24 bg-[#FAFAF8]">

      {/* 헤더 */}
      <div className="px-5 pt-14 pb-4 bg-white border-b border-[#F9FAFB]">
        <h1 className="text-2xl font-bold text-[#1C1C1E]">학습 로드맵 📚</h1>
        <p className="text-[#9CA3AF] text-sm mt-1">책 목차처럼 단계별로 배워요</p>
      </div>

      {/* 주제 탭 */}
      <div className="px-5 pt-4 pb-2">
        <div className="flex gap-2 overflow-x-auto pb-1">
          {CURRICULA.map((c) => (
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

      {/* 선택된 커리큘럼 */}
      <div className="px-5 mt-2">

        {/* 커리큘럼 소개 */}
        {(() => {
          const completedCount = curriculum.chapters.filter(
            ch => progress[`${curriculum.id}-${ch.id}`]?.status === "completed"
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
            <div className="h-1.5 bg-white rounded-full transition-all duration-700"
              style={{ width: `${pct}%` }} />
          </div>
        </div>
          );
        })()}

        {/* 챕터 목록 */}
        <div className="flex flex-col gap-3">
          {curriculum.chapters.map((ch, idx) => {
            const chapterId = `${curriculum.id}-${ch.id}`;
            const prog = progress[chapterId];
            const isCompleted = prog?.status === "completed";
            const isStarted = prog?.status === "started";

            return (
            <div
              key={ch.id}
              className={`bg-white rounded-3xl p-4 card-shadow ${
                ch.status === "locked" ? "opacity-60" : ""
              } ${isCompleted ? "border-2 border-[#10B981]/30" : ""}`}
            >
              <div className="flex items-start gap-3">
                {/* 챕터 번호 / 상태 */}
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5"
                  style={
                    ch.status === "locked"
                      ? { backgroundColor: "#F3F4F6", color: "#9CA3AF" }
                      : isCompleted
                      ? { backgroundColor: "#ECFDF5", color: "#10B981" }
                      : { backgroundColor: `${curriculum.color}15`, color: curriculum.color }
                  }
                >
                  {ch.status === "locked" ? "🔒" : isCompleted ? "✓" : isStarted ? "▶" : idx + 1}
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
                  <p className={`font-bold text-sm ${ch.status === "locked" ? "text-[#9CA3AF]" : "text-[#1C1C1E]"}`}>
                    {ch.title}
                  </p>
                  <p className="text-[#9CA3AF] text-xs mt-0.5 leading-relaxed">
                    {ch.description}
                  </p>
                </div>

                {/* 시작 버튼 */}
                {ch.status === "available" && (
                  <button
                    onClick={() => router.push(`/learn?id=${curriculum.id}-${ch.id}`)}
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

      <BottomNav active="home" />
    </div>
  );
}
