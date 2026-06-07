"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, TEMP_USER_ID } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

const INTERESTS = [
  { id: "rag",    label: "RAG",         category: "AI/ML", emoji: "🔍", desc: "검색 기반 AI" },
  { id: "agent",  label: "Agentic AI",  category: "AI/ML", emoji: "🤖", desc: "자율 행동 AI" },
  { id: "llm",    label: "LLM 기초",    category: "AI/ML", emoji: "🧠", desc: "언어 모델 원리" },
  { id: "prompt", label: "프롬프트",    category: "AI/ML", emoji: "✍️", desc: "AI 잘 쓰는 법" },
  { id: "deploy", label: "AI 서비스화", category: "AI/ML", emoji: "🚀", desc: "실전 배포/운영" },
];

const GOALS = [
  { id: "job",    label: "취업/이직",   emoji: "💼" },
  { id: "study",  label: "자기계발",    emoji: "📚" },
  { id: "build",  label: "직접 만들기", emoji: "🛠️" },
  { id: "trend",  label: "트렌드 파악", emoji: "📰" },
];

const TIMES = [
  { id: "5",  label: "5분",  desc: "진짜 바쁠 때" },
  { id: "10", label: "10분", desc: "출퇴근 시간" },
  { id: "20", label: "20분", desc: "여유 있을 때" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { show: showToast, ToastComponent } = useToast();
  const [step, setStep] = useState(1);
  const [nickname, setNickname] = useState("");
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [selectedGoal, setSelectedGoal] = useState("");
  const [selectedTime, setSelectedTime] = useState("10");
  const [saving, setSaving] = useState(false);

  function toggleInterest(id: string) {
    setSelectedInterests(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  }

  async function handleFinish() {
    setSaving(true);
    try {
      await api.createUser(TEMP_USER_ID, nickname || "학습자");

      for (const id of selectedInterests) {
        const item = INTERESTS.find(i => i.id === id);
        if (!item) continue;
        await api.addTopic(TEMP_USER_ID, item.label, item.category).catch(() => {});
      }

      localStorage.setItem("onboarding_done", "true");
      localStorage.setItem("user_nickname", nickname || "학습자");
      localStorage.setItem("user_goal", selectedGoal);
      localStorage.setItem("user_daily_minutes", selectedTime);

      router.push("/home");
    } catch {
      showToast("저장 중 오류가 생겼어요. 다시 시도해주세요.", "error");
    } finally {
      setSaving(false);
    }
  }

  const totalSteps = 4;
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
            <div className="mb-6">
              <button onClick={() => setStep(1)} className="text-[#9CA3AF] text-sm mb-3 flex items-center gap-1 active:opacity-60">← 이전</button>
              <p className="text-[#10B981] text-sm font-medium mb-1">2 / {totalSteps}</p>
              <h2 className="text-2xl font-bold text-[#1C1C1E]">무엇을 배우고 싶어요?</h2>
              <p className="text-[#9CA3AF] text-sm mt-1">여러 개 선택 가능해요</p>
            </div>
            <div className="flex flex-col gap-3 flex-1">
              {INTERESTS.map(interest => (
                <button
                  key={interest.id}
                  onClick={() => toggleInterest(interest.id)}
                  className={`flex items-center gap-4 p-4 rounded-2xl border-2 transition-all active:scale-[0.98] ${
                    selectedInterests.includes(interest.id)
                      ? "border-[#10B981] bg-[#ECFDF5]"
                      : "border-[#F3F4F6] bg-white"
                  }`}
                >
                  <span className="text-2xl">{interest.emoji}</span>
                  <div className="text-left flex-1">
                    <p className={`font-bold text-sm ${selectedInterests.includes(interest.id) ? "text-[#065F46]" : "text-[#1C1C1E]"}`}>
                      {interest.label}
                    </p>
                    <p className="text-[#9CA3AF] text-xs">{interest.desc}</p>
                  </div>
                  {selectedInterests.includes(interest.id) && (
                    <span className="text-[#10B981] font-bold">✓</span>
                  )}
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(3)}
              disabled={selectedInterests.length === 0}
              className="mt-4 w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-base shadow-lg shadow-emerald-100 active:scale-95 transition-all disabled:opacity-40"
            >
              다음 →
            </button>
          </div>
        )}

        {/* Step 3 — 목표 */}
        {step === 3 && (
          <div className="flex-1 flex flex-col">
            <div className="mb-6">
              <button onClick={() => setStep(2)} className="text-[#9CA3AF] text-sm mb-3 flex items-center gap-1 active:opacity-60">← 이전</button>
              <p className="text-[#10B981] text-sm font-medium mb-1">3 / {totalSteps}</p>
              <h2 className="text-2xl font-bold text-[#1C1C1E]">학습 목표가 뭐예요?</h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {GOALS.map(goal => (
                <button
                  key={goal.id}
                  onClick={() => setSelectedGoal(goal.id)}
                  className={`flex flex-col items-center justify-center gap-2 p-5 rounded-2xl border-2 transition-all active:scale-95 ${
                    selectedGoal === goal.id
                      ? "border-[#10B981] bg-[#ECFDF5]"
                      : "border-[#F3F4F6] bg-white"
                  }`}
                >
                  <span className="text-3xl">{goal.emoji}</span>
                  <p className={`font-bold text-sm text-center ${selectedGoal === goal.id ? "text-[#065F46]" : "text-[#1C1C1E]"}`}>
                    {goal.label}
                  </p>
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(4)}
              disabled={!selectedGoal}
              className="mt-4 w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-base shadow-lg shadow-emerald-100 active:scale-95 transition-all disabled:opacity-40"
            >
              다음 →
            </button>
          </div>
        )}

        {/* Step 4 — 학습 시간 */}
        {step === 4 && (
          <div className="flex-1 flex flex-col">
            <div className="mb-6">
              <button onClick={() => setStep(3)} className="text-[#9CA3AF] text-sm mb-3 flex items-center gap-1 active:opacity-60">← 이전</button>
              <p className="text-[#10B981] text-sm font-medium mb-1">4 / {totalSteps}</p>
              <h2 className="text-2xl font-bold text-[#1C1C1E]">하루 몇 분 학습할 수 있어요?</h2>
              <p className="text-[#9CA3AF] text-sm mt-1">나중에 바꿀 수 있어요</p>
            </div>
            <div className="flex flex-col gap-3 flex-1">
              {TIMES.map(time => (
                <button
                  key={time.id}
                  onClick={() => setSelectedTime(time.id)}
                  className={`flex items-center justify-between p-5 rounded-2xl border-2 transition-all active:scale-[0.98] ${
                    selectedTime === time.id
                      ? "border-[#10B981] bg-[#ECFDF5]"
                      : "border-[#F3F4F6] bg-white"
                  }`}
                >
                  <div className="text-left">
                    <p className={`font-bold text-lg ${selectedTime === time.id ? "text-[#065F46]" : "text-[#1C1C1E]"}`}>
                      {time.label}
                    </p>
                    <p className="text-[#9CA3AF] text-sm">{time.desc}</p>
                  </div>
                  {selectedTime === time.id && (
                    <span className="text-[#10B981] text-xl font-bold">✓</span>
                  )}
                </button>
              ))}
            </div>
            <button
              onClick={handleFinish}
              disabled={saving}
              className="mt-4 w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-base shadow-lg shadow-emerald-100 active:scale-95 transition-all disabled:opacity-50"
            >
              {saving ? "저장 중..." : "🎉 학습 시작하기"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
