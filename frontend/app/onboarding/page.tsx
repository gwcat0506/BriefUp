"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { api, TEMP_USER_ID } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { SUGGESTED_TOPICS as SUGGESTED } from "@/lib/topics";

type TopicStatus = "pending" | "loading" | "done" | "error";
interface SavingTopic {
  label: string;
  isCustom: boolean;
  status: TopicStatus;
  category?: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const { show: showToast, ToastComponent } = useToast();
  const [step, setStep] = useState(1);
  const [nickname, setNickname] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [customTopics, setCustomTopics] = useState<string[]>([]);
  const [customInput, setCustomInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [savingTopics, setSavingTopics] = useState<SavingTopic[]>([]);
  const [customElapsed, setCustomElapsed] = useState(0);
  const customTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function startCustomTimer() {
    setCustomElapsed(0);
    customTimerRef.current = setInterval(() => {
      setCustomElapsed(s => s + 1);
    }, 1000);
  }

  function stopCustomTimer() {
    if (customTimerRef.current) {
      clearInterval(customTimerRef.current);
      customTimerRef.current = null;
    }
  }

  useEffect(() => () => stopCustomTimer(), []);

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

    const topicList: SavingTopic[] = [
      ...selectedIds.map(id => {
        const item = SUGGESTED.find(i => i.id === id)!;
        return { label: item.label, isCustom: false, status: "pending" as TopicStatus, category: item.category };
      }),
      ...customTopics.map(label => ({ label, isCustom: true, status: "pending" as TopicStatus })),
    ];
    setSavingTopics(topicList);

    try {
      await api.createUser(TEMP_USER_ID, nickname || "학습자").catch(() => {});

      for (let i = 0; i < topicList.length; i++) {
        const item = topicList[i];
        setSavingTopics(prev => prev.map((t, idx) => idx === i ? { ...t, status: "loading" } : t));
        if (item.isCustom) startCustomTimer();
        try {
          await api.addTopic(TEMP_USER_ID, item.label, item.category).catch(() => {});
          setSavingTopics(prev => prev.map((t, idx) => idx === i ? { ...t, status: "done" } : t));
        } catch {
          setSavingTopics(prev => prev.map((t, idx) => idx === i ? { ...t, status: "error" } : t));
        } finally {
          if (item.isCustom) stopCustomTimer();
        }
      }

      localStorage.setItem("onboarding_done", "true");
      localStorage.setItem("user_nickname", nickname || "학습자");
      router.push("/home");
    } catch {
      showToast("저장 중 오류가 생겼어요. 다시 시도해주세요.", "error");
      setSaving(false);
    }
  }

  const totalSteps = 2;
  const progress = (step / totalSteps) * 100;
  const doneCount = savingTopics.filter(t => t.status === "done").length;
  const allDone = savingTopics.length > 0 && doneCount === savingTopics.length;

  return (
    <div className="flex flex-col min-h-screen bg-[#FAFAF8]">
      {ToastComponent}

      {saving && (
        <div className="fixed inset-0 z-50 bg-[#FAFAF8] flex flex-col items-center justify-center px-8">
          {!allDone ? (
            <>
              <div className="w-12 h-12 rounded-full border-4 border-[#D1FAE5] border-t-[#10B981] animate-spin mb-5" />
              <h2 className="text-xl font-bold text-[#1C1C1E] mb-1 text-center">학습 준비 중이에요</h2>
              <p className="text-[#9CA3AF] text-sm text-center mb-6">커리큘럼을 설계하고 있어요</p>
            </>
          ) : (
            <>
              <div className="w-12 h-12 rounded-full bg-[#ECFDF5] flex items-center justify-center mb-5">
                <span className="text-2xl">✅</span>
              </div>
              <h2 className="text-xl font-bold text-[#1C1C1E] mb-1 text-center">모든 준비가 끝났어요!</h2>
              <p className="text-[#9CA3AF] text-sm text-center mb-6">홈으로 이동하고 있어요...</p>
            </>
          )}

          <div className="w-full max-w-sm flex flex-col gap-2">
            {savingTopics.map((item, i) => (
              <div key={i} className="bg-white rounded-2xl px-4 py-3 card-shadow">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                    {item.status === "pending" && (
                      <div className="w-4 h-4 rounded-full border-2 border-[#E5E7EB]" />
                    )}
                    {item.status === "loading" && (
                      <div className="w-4 h-4 rounded-full border-2 border-[#D1FAE5] border-t-[#10B981] animate-spin" />
                    )}
                    {item.status === "done" && (
                      <span className="text-[#10B981] text-sm font-bold">✓</span>
                    )}
                    {item.status === "error" && (
                      <span className="text-[#EF4444] text-sm">!</span>
                    )}
                  </div>
                  <span className="text-[#1C1C1E] text-sm font-medium flex-1">{item.label}</span>
                  {item.isCustom && item.status === "pending" && (
                    <span className="text-[#9CA3AF] text-xs">최대 2분</span>
                  )}
                  {item.isCustom && item.status === "loading" && (
                    <span className="text-[#6B7280] text-xs tabular-nums">
                      {customElapsed < 90 ? `약 ${90 - customElapsed}초 남음` : "거의 다 됐어요"}
                    </span>
                  )}
                  {item.isCustom && item.status === "done" && (
                    <span className="text-[#10B981] text-xs font-medium">완료!</span>
                  )}
                </div>
                {item.isCustom && item.status === "loading" && (
                  <div className="mt-2 h-1 bg-[#F3F4F6] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[#10B981] to-[#34D399] rounded-full transition-all duration-1000"
                      style={{ width: `${Math.min((customElapsed / 90) * 100, 95)}%` }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="w-full bg-[#F3F4F6] h-1.5">
        <div
          className="h-1.5 bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex-1 px-6 pt-12 pb-8 flex flex-col">

        {/* Step 1 — 닉네임 */}
        {step === 1 && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 flex flex-col justify-center">
              <div className="text-center mb-8">
                <p className="text-5xl mb-4">👋</p>
                <h1 className="text-2xl font-bold text-[#1C1C1E] mb-2">
                  어떻게 불러드릴까요?
                </h1>
                <p className="text-[#9CA3AF] text-sm">닉네임은 나중에 바꿀 수 있어요</p>
              </div>
              <div className="bg-white rounded-3xl p-5 card-shadow">
                <input
                  type="text"
                  placeholder="닉네임 입력 (선택)"
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
              다음 →
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

            <div className={`bg-white rounded-2xl border-2 p-4 mb-4 transition-colors ${customTopics.length > 0 ? "border-[#FCD34D]" : "border-[#F3F4F6]"}`}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-[#6B7280] text-xs font-medium">직접 입력하기</p>
                {customTopics.length > 0 && (
                  <span className="text-[#D97706] text-xs font-medium">⏱ 주제당 최대 2분 소요</span>
                )}
              </div>
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
              {customTopics.length > 0 && (
                <p className="text-[#9CA3AF] text-xs mt-2">AI가 직접 커리큘럼을 설계해요. 추천 주제보다 시간이 더 걸려요.</p>
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
