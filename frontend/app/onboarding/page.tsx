"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, TEMP_USER_ID } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

const SUGGESTED = [
  { id: "rag",        label: "RAG",         category: "AI/ML",  emoji: "🔍" },
  { id: "agent",      label: "Agentic AI",  category: "AI/ML",  emoji: "🤖" },
  { id: "llm",        label: "LLM 기초",    category: "AI/ML",  emoji: "🧠" },
  { id: "quantum",    label: "양자컴퓨팅",  category: undefined, emoji: "⚛️" },
  { id: "invest",     label: "주식/투자",   category: undefined, emoji: "📈" },
  { id: "psych",      label: "심리학",      category: "심리학", emoji: "🧬" },
  { id: "philosophy", label: "철학",        category: "철학",   emoji: "💭" },
  { id: "startup",    label: "스타트업",    category: undefined, emoji: "🚀" },
  { id: "health",     label: "헬스/운동",   category: undefined, emoji: "💪" },
  { id: "history",    label: "역사",        category: undefined, emoji: "📜" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { show: showToast, ToastComponent } = useToast();
  const [step, setStep] = useState(1);
  const [nickname, setNickname] = useState("");
  // { id, label, category? } — suggested는 id 기반, custom은 label이 id
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [customTopics, setCustomTopics] = useState<string[]>([]);
  const [customInput, setCustomInput] = useState("");
  const [saving, setSaving] = useState(false);

  function toggleSuggested(id: string) {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  }

  function addCustomTopic() {
    const trimmed = customInput.trim();
    if (!trimmed || customTopics.includes(trimmed)) return;
    setCustomTopics(prev => [...prev, trimmed]);
    setCustomInput("");
  }

  function removeCustomTopic(label: string) {
    setCustomTopics(prev => prev.filter(t => t !== label));
  }

  const hasAnySelection = selectedIds.length > 0 || customTopics.length > 0;

  async function handleFinish() {
    setSaving(true);
    try {
      await api.createUser(TEMP_USER_ID, nickname || "학습자").catch(() => {});

      for (const id of selectedIds) {
        const item = SUGGESTED.find(i => i.id === id);
        if (!item) continue;
        await api.addTopic(TEMP_USER_ID, item.label, item.category).catch(() => {});
      }

      for (const label of customTopics) {
        // category 없이 보내면 백엔드에서 GPT로 자동 분류
        await api.addTopic(TEMP_USER_ID, label).catch(() => {});
      }

      localStorage.setItem("onboarding_done", "true");
      localStorage.setItem("user_nickname", nickname || "학습자");

      router.push("/home");
    } catch {
      showToast("저장 중 오류가 생겼어요. 다시 시도해주세요.", "error");
    } finally {
      setSaving(false);
    }
  }

  const totalSteps = 2;
  const progress = (step / totalSteps) * 100;

  return (
    <div className="flex flex-col min-h-screen bg-[#FAFAF8]">
      {ToastComponent}
      {/* 진행 바 */}
      <div className="w-full bg-[#F3F4F6] h-1.5">
        <div
          className="h-1.5 bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex-1 px-6 pt-12 pb-8 flex flex-col">

        {/* Step 1 — 환영 */}
        {step === 1 && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col items-center justify-center text-center">
              <p className="text-6xl mb-6">👋</p>
              <h1 className="text-2xl font-bold text-[#1C1C1E] mb-3">
                BrefUp에 오신 걸 환영해요!
              </h1>
              <p className="text-[#6B7280] text-base leading-relaxed mb-8">
                매일 10분, 카드 형식으로<br />AI를 쉽고 재미있게 배워요
              </p>
              <div className="w-full bg-white rounded-3xl p-5 card-shadow text-left">
                <p className="text-[#6B7280] text-sm mb-2">이름이 뭐예요? (선택)</p>
                <input
                  type="text"
                  placeholder="닉네임 입력"
                  value={nickname}
                  onChange={e => setNickname(e.target.value)}
                  maxLength={10}
                  className="w-full bg-[#F9FAFB] text-[#1C1C1E] text-base px-4 py-3 rounded-xl outline-none border border-[#F3F4F6] focus:border-[#10B981] transition-all"
                />
              </div>
            </div>
            <button
              onClick={() => setStep(2)}
              className="w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-base shadow-lg shadow-emerald-100 active:scale-95 transition-all"
            >
              시작하기 →
            </button>
          </div>
        )}

        {/* Step 2 — 관심사 */}
        {step === 2 && (
          <div className="flex-1 flex flex-col">
            <div className="mb-5">
              <button onClick={() => setStep(1)} className="text-[#9CA3AF] text-sm mb-3 flex items-center gap-1 active:opacity-60">← 이전</button>
              <p className="text-[#10B981] text-sm font-medium mb-1">2 / {totalSteps}</p>
              <h2 className="text-2xl font-bold text-[#1C1C1E]">무엇이 궁금해요?</h2>
              <p className="text-[#9CA3AF] text-sm mt-1">관심사면 뭐든 OK — 여러 개 선택 가능해요</p>
            </div>

            {/* 추천 태그 */}
            <div className="flex flex-wrap gap-2 mb-5">
              {SUGGESTED.map(item => (
                <button
                  key={item.id}
                  onClick={() => toggleSuggested(item.id)}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-full border-2 text-sm font-medium transition-all active:scale-95 ${
                    selectedIds.includes(item.id)
                      ? "border-[#10B981] bg-[#ECFDF5] text-[#065F46]"
                      : "border-[#F3F4F6] bg-white text-[#374151]"
                  }`}
                >
                  <span>{item.emoji}</span>
                  <span>{item.label}</span>
                  {selectedIds.includes(item.id) && <span className="text-[#10B981]">✓</span>}
                </button>
              ))}
            </div>

            {/* 직접 입력 */}
            <div className="bg-white rounded-2xl border-2 border-[#F3F4F6] p-4 mb-4">
              <p className="text-[#6B7280] text-xs mb-2 font-medium">직접 입력하기</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="예) 양자컴퓨팅, 클래식 음악, 요리..."
                  value={customInput}
                  onChange={e => setCustomInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && addCustomTopic()}
                  maxLength={20}
                  className="flex-1 bg-[#F9FAFB] text-[#1C1C1E] text-sm px-3 py-2.5 rounded-xl outline-none border border-[#F3F4F6] focus:border-[#10B981] transition-all"
                />
                <button
                  onClick={addCustomTopic}
                  disabled={!customInput.trim()}
                  className="bg-[#10B981] text-white text-sm font-bold px-4 py-2.5 rounded-xl disabled:opacity-40 active:scale-95 transition-all"
                >
                  추가
                </button>
              </div>
              {customTopics.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {customTopics.map(label => (
                    <span
                      key={label}
                      className="flex items-center gap-1.5 bg-[#ECFDF5] border border-[#10B981] text-[#065F46] text-xs font-medium px-3 py-1.5 rounded-full"
                    >
                      {label}
                      <button onClick={() => removeCustomTopic(label)} className="text-[#6B7280] hover:text-[#DC2626] ml-0.5">×</button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleFinish}
              disabled={!hasAnySelection || saving}
              className="mt-auto w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-base shadow-lg shadow-emerald-100 active:scale-95 transition-all disabled:opacity-40"
            >
              {saving ? "저장 중..." : "🎉 학습 시작하기"}
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
