"use client";

import { useEffect, useState, useRef } from "react";
import { api, Topic, TEMP_USER_ID } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";
import { useRouter } from "next/navigation";
import { useToast } from "@/components/ui/Toast";
import { savePipelinePending, clearPipelinePending } from "@/components/ui/GlobalPipelineWatcher";
import { SUGGESTED_TOPICS as SUGGESTED } from "@/lib/topics";
import ProgressBar from "@/components/ui/ProgressBar";

type Tab = "settings" | "bookmarks" | "feedback";
type FeedbackType = "positive" | "negative" | "suggestion";

type PipelineStatus = {
  topicName: string;
  phase: "curriculum" | "pipeline";
  elapsed: number;
  startedAt: number; // 파이프라인 시작 Unix ms — 이 시점 이후 생성된 콘텐츠만 감지
  done: boolean;
};

const PIPELINE_ESTIMATE = 90; // 예상 파이프라인 소요 시간 (초)

const PIPELINE_MSGS = [
  { emoji: "📚", text: "커리큘럼 구성 중" },
  { emoji: "🔍", text: "관련 논문·뉴스 검색 중" },
  { emoji: "🧠", text: "핵심 개념 추출 중" },
  { emoji: "✍️", text: "요약 카드 작성 중" },
  { emoji: "✏️", text: "퀴즈 문제 생성 중" },
  { emoji: "🔎", text: "품질 최종 검증 중" },
];

export default function MyPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [bookmarks, setBookmarks] = useState<any[]>([]);
  const [adding, setAdding] = useState<string | null>(null);
  const [customInput, setCustomInput] = useState("");
  const [tab, setTab] = useState<Tab>("settings");
  const [nickname, setNickname] = useState("");
  const [editingNickname, setEditingNickname] = useState(false);
  const [nicknameInput, setNicknameInput] = useState("");
  const [confirmTopic, setConfirmTopic] = useState<{ id: string; name: string } | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [feedbackType, setFeedbackType] = useState<FeedbackType>("suggestion");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [pipelineMsgIdx, setPipelineMsgIdx] = useState(0);
  const pipelineTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const msgTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const router = useRouter();
  const { show: showToast, ToastComponent } = useToast();

  function clearPipelineTimers() {
    if (pipelineTimerRef.current) { clearInterval(pipelineTimerRef.current); pipelineTimerRef.current = null; }
    if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; }
    if (msgTimerRef.current) { clearInterval(msgTimerRef.current); msgTimerRef.current = null; }
  }

  useEffect(() => () => clearPipelineTimers(), []);

  useEffect(() => {
    const saved = localStorage.getItem("user_nickname") || "학습자";
    setNickname(saved);
    setNicknameInput(saved);
  }, []);

  useEffect(() => {
    api.getTopics(TEMP_USER_ID).then(setTopics);
    api.getBookmarks(TEMP_USER_ID).then(setBookmarks);
  }, []);

  // 페이지 복귀 시 진행 중인 파이프라인 복원
  useEffect(() => {
    const raw = localStorage.getItem("briefup_pipeline_pending");
    if (!raw) return;
    try {
      const entry = JSON.parse(raw);
      // 3분 초과 항목은 무시
      if (Date.now() - entry.startedAt > 180000) {
        clearPipelinePending();
        return;
      }
      startPipelinePhase(entry.topicName, entry.startedAt);
    } catch {
      clearPipelinePending();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function startPipelinePhase(topicName: string, existingStartedAt?: number) {
    const startedAt = existingStartedAt ?? Date.now();
    const initialElapsed = existingStartedAt ? Math.floor((Date.now() - existingStartedAt) / 1000) : 0;
    let succeeded = false;
    if (!existingStartedAt) savePipelinePending({ topicName, startedAt });
    setPipelineStatus({ topicName, phase: "pipeline", elapsed: initialElapsed, startedAt, done: false });

    // 메시지 로테이션 (12초마다)
    setPipelineMsgIdx(0);
    msgTimerRef.current = setInterval(() => {
      setPipelineMsgIdx(prev => (prev + 1) % PIPELINE_MSGS.length);
    }, 12000);

    pipelineTimerRef.current = setInterval(() => {
      setPipelineStatus(prev => prev ? { ...prev, elapsed: prev.elapsed + 1 } : null);
    }, 1000);

    // 15초마다 폴링 — topic name으로 조회 + startedAt 이후 생성된 것만 감지
    const checkContent = async () => {
      try {
        const data = await api.getContentsByCategory(topicName, 5);
        const hasNew = data.some(c => new Date(c.created_at).getTime() >= startedAt);
        if (hasNew) {
          succeeded = true;
          clearPipelineTimers();
          clearPipelinePending();
          setPipelineStatus(prev => prev ? { ...prev, done: true } : null);
          api.getTopics(TEMP_USER_ID).then(setTopics);
          showToast(`'${topicName}' 브리핑이 준비됐어요!`, "success");
          setTimeout(() => setPipelineStatus(null), 4000);
        }
      } catch {}
    };
    pollTimerRef.current = setInterval(checkContent, 15000);
    // 최대 3분 후 강제 종료
    setTimeout(() => {
      clearPipelineTimers();
      clearPipelinePending();
      if (!succeeded) {
        showToast(`'${topicName}' 관련 자료를 충분히 찾지 못했어요 🙏`, "error");
      }
      setPipelineStatus(prev => prev && !prev.done ? { ...prev, done: true } : prev);
      setTimeout(() => setPipelineStatus(null), 4000);
    }, 180000);
  }

  async function handleSaveNickname() {
    const trimmed = nicknameInput.trim();
    if (!trimmed) return;
    localStorage.setItem("user_nickname", trimmed);
    setNickname(trimmed);
    setEditingNickname(false);
    await api.createUser(TEMP_USER_ID, trimmed).catch(() => {});
    showToast("닉네임이 변경됐어요!", "success");
  }

  async function handleRemoveTopic(topicId: string) {
    const snapshot = topics;
    setTopics(prev => prev.filter(t => t.id !== topicId));
    setConfirmTopic(null);
    try {
      await api.removeTopic(topicId);
      localStorage.removeItem(`home_summary_v1_${TEMP_USER_ID}`);
    } catch {
      setTopics(snapshot);
    }
  }

  async function handleAddSuggested(id: string, label: string, category: string) {
    const existing = topics.find(t => t.name === label);
    if (existing) {
      setConfirmTopic({ id: existing.id, name: label });
      return;
    }
    if (adding) return;
    setAdding(id);
    setPipelineStatus({ topicName: label, phase: "curriculum", elapsed: 0, startedAt: Date.now(), done: false });
    try {
      await api.addTopic(TEMP_USER_ID, label, category);
      const updated = await api.getTopics(TEMP_USER_ID);
      setTopics(updated);
      startPipelinePhase(label);
    } catch {
      showToast("추가 중 오류가 생겼어요. 다시 시도해주세요.", "error");
      setPipelineStatus(null);
    } finally {
      setAdding(null);
    }
  }

  async function handleAddCustom() {
    const trimmed = customInput.trim();
    if (!trimmed || adding) return;
    setAdding("custom");
    setPipelineStatus({ topicName: trimmed, phase: "curriculum", elapsed: 0, startedAt: Date.now(), done: false });
    try {
      await api.addTopic(TEMP_USER_ID, trimmed);
      const updated = await api.getTopics(TEMP_USER_ID);
      setTopics(updated);
      setCustomInput("");
      startPipelinePhase(trimmed);
    } catch {
      showToast("추가 중 오류가 생겼어요. 다시 시도해주세요.", "error");
      setPipelineStatus(null);
    } finally {
      setAdding(null);
    }
  }

  async function handleSubmitFeedback() {
    const trimmed = feedbackMessage.trim();
    if (!trimmed || feedbackSubmitting) return;
    setFeedbackSubmitting(true);
    try {
      await api.submitFeedback({ user_id: TEMP_USER_ID, feedback_type: feedbackType, message: trimmed });
      setFeedbackMessage("");
      showToast("피드백을 전달했어요! 더 나은 브리핑을 만들게요 🙏", "success");
    } catch {
      showToast("전송 중 오류가 생겼어요. 다시 시도해주세요.", "error");
    } finally {
      setFeedbackSubmitting(false);
    }
  }

  async function handleRemoveBookmark(contentId: string) {
    await api.toggleBookmark(TEMP_USER_ID, contentId);
    setBookmarks(bm => bm.filter(b => b.content_id !== contentId));
  }

  return (
    <div className="flex flex-col min-h-screen pb-24 bg-[#FAFAF8]">
      {ToastComponent}
      <div className="px-5 pt-14 pb-5 bg-white border-b border-[#F9FAFB]">
        <h1 className="text-2xl font-bold text-[#1C1C1E] mb-3">마이페이지</h1>
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#10B981] to-[#059669] flex items-center justify-center text-white text-xl font-bold flex-shrink-0">
            {nickname.charAt(0) || "?"}
          </div>
          <div className="flex-1 min-w-0">
            {editingNickname ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={nicknameInput}
                  onChange={e => setNicknameInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleSaveNickname()}
                  maxLength={10}
                  autoFocus
                  className="flex-1 bg-[#F9FAFB] text-[#1C1C1E] text-sm px-3 py-1.5 rounded-xl outline-none border border-[#10B981] min-w-0"
                />
                <button
                  onClick={handleSaveNickname}
                  className="text-white bg-[#10B981] text-xs font-bold px-3 py-1.5 rounded-xl flex-shrink-0"
                >
                  저장
                </button>
                <button
                  onClick={() => { setEditingNickname(false); setNicknameInput(nickname); }}
                  className="text-[#9CA3AF] text-xs px-2 py-1.5 flex-shrink-0"
                >
                  취소
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <p className="text-[#1C1C1E] font-bold text-base">{nickname}</p>
                <button
                  onClick={() => setEditingNickname(true)}
                  className="text-[#9CA3AF] text-xs underline"
                >
                  수정
                </button>
              </div>
            )}
            <p className="text-[#9CA3AF] text-xs mt-0.5">BriefUp 학습자</p>
          </div>
        </div>
      </div>

      {/* 탭 */}
      <div className="px-5 pt-4 pb-2 flex gap-2">
        {[
          { key: "settings", label: "⚙️ 설정" },
          { key: "bookmarks", label: `🔖 북마크 ${bookmarks.length > 0 ? `(${bookmarks.length})` : ""}` },
          { key: "feedback", label: "💬 피드백" },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as Tab)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              tab === t.key
                ? "bg-[#10B981] text-white"
                : "bg-white text-[#6B7280] card-shadow"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="px-5 flex-1">

        {/* 설정 탭 */}
        {tab === "settings" && (
          <div className="mt-4 flex flex-col gap-4">

            {/* 가치 설명 카드 */}
            <div className="bg-gradient-to-br from-[#10B981] to-[#059669] rounded-3xl p-5 text-white">
              <p className="font-bold text-base leading-snug mb-4">관심사만 고르면,<br/>나머지는 BriefUp이 알아서 해요</p>
              <div className="flex items-start gap-1 text-sm">
                <div className="flex flex-col items-center gap-1 flex-1">
                  <span className="text-xl">🎯</span>
                  <span className="text-white/90 text-xs font-medium text-center">관심사<br/>선택</span>
                </div>
                <span className="text-white/50 mt-2">→</span>
                <div className="flex flex-col items-center gap-1 flex-1">
                  <span className="text-xl">📚</span>
                  <span className="text-white/90 text-xs font-medium text-center">커리큘럼<br/>자동 생성</span>
                </div>
                <span className="text-white/50 mt-2">→</span>
                <div className="flex flex-col items-center gap-1 flex-1">
                  <span className="text-xl">📰</span>
                  <span className="text-white/90 text-xs font-medium text-center">매일<br/>브리핑</span>
                </div>
                <span className="text-white/50 mt-2">→</span>
                <div className="flex flex-col items-center gap-1 flex-1">
                  <span className="text-xl">✏️</span>
                  <span className="text-white/90 text-xs font-medium text-center">퀴즈<br/>자동 출제</span>
                </div>
              </div>
            </div>

            {/* 관심사 추가 */}
            <div className="bg-white rounded-3xl p-4 card-shadow">
              <p className="text-[#1C1C1E] font-bold text-sm mb-0.5">관심사 추가</p>
              <p className="text-[#9CA3AF] text-xs mb-3">배우고 싶은 걸 입력하거나, 아래에서 골라보세요</p>

              {/* 직접 입력 */}
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  placeholder="예: 블록체인, 영양학, 클래식 음악..."
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddCustom()}
                  maxLength={20}
                  className="flex-1 bg-[#F9FAFB] text-[#1C1C1E] placeholder-[#9CA3AF] text-sm px-4 py-3 rounded-xl outline-none border border-[#F3F4F6] focus:border-[#10B981]"
                />
                <button
                  onClick={handleAddCustom}
                  disabled={!customInput.trim() || adding !== null}
                  className="bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold px-4 py-3 rounded-xl text-sm active:scale-95 transition-all disabled:opacity-40"
                >
                  {adding === "custom" ? "생성 중" : "추가"}
                </button>
              </div>
              {pipelineStatus && (
                <div className="mb-4">
                  {pipelineStatus.done ? (
                    <div className="bg-[#ECFDF5] border border-[#A7F3D0] rounded-2xl px-4 py-3 flex items-center gap-2">
                      <span className="text-base">✅</span>
                      <p className="text-[#10B981] text-xs font-medium flex-1">
                        <span className="font-bold">'{pipelineStatus.topicName}'</span> 브리핑이 준비됐어요!
                      </p>
                    </div>
                  ) : pipelineStatus.phase === "curriculum" ? (
                    <div className="bg-[#F0FDF4] border border-[#D1FAE5] rounded-2xl px-4 py-3 flex items-center gap-2">
                      <div className="w-3.5 h-3.5 rounded-full border-2 border-[#D1FAE5] border-t-[#10B981] animate-spin flex-shrink-0" />
                      <p className="text-[#10B981] text-xs">
                        <span className="font-bold">'{pipelineStatus.topicName}'</span> 커리큘럼 구성 중...
                      </p>
                    </div>
                  ) : (
                    <div className="bg-[#F0FDF4] border border-[#D1FAE5] rounded-2xl px-4 py-3">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-base">{PIPELINE_MSGS[pipelineMsgIdx].emoji}</span>
                        <p className="text-[#10B981] text-xs font-medium flex-1">
                          {PIPELINE_MSGS[pipelineMsgIdx].text}...
                        </p>
                        <span className="text-[#6B7280] text-[10px] tabular-nums flex-shrink-0">
                          {pipelineStatus.elapsed < PIPELINE_ESTIMATE
                            ? `약 ${PIPELINE_ESTIMATE - pipelineStatus.elapsed}초`
                            : "거의 다 됐어요"}
                        </span>
                      </div>
                      <ProgressBar pct={Math.min((pipelineStatus.elapsed / PIPELINE_ESTIMATE) * 100, 95)} height="sm" duration={1000} />
                      <p className="text-[#9CA3AF] text-[10px] mt-1.5">
                        AI가 <span className="font-medium text-[#10B981]">'{pipelineStatus.topicName}'</span> 브리핑을 만들고 있어요
                      </p>
                    </div>
                  )}
                </div>
              )}
              {!pipelineStatus && <div className="mb-4" />}

              {/* 구분선 */}
              <div className="flex items-center gap-2 mb-3">
                <div className="flex-1 h-px bg-[#F3F4F6]" />
                <span className="text-[#9CA3AF] text-xs">추천 주제</span>
                <div className="flex-1 h-px bg-[#F3F4F6]" />
              </div>

              {/* 추천 주제 칩 */}
              <div className="flex flex-wrap gap-2">
                {SUGGESTED.map((item) => {
                  const already = topics.some(t => t.name === item.label);
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleAddSuggested(item.id, item.label, item.category)}
                      disabled={!already && adding !== null}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-full border-2 text-sm font-medium transition-all active:scale-95 disabled:cursor-default ${
                        already
                          ? "border-[#10B981] bg-[#ECFDF5] text-[#065F46]"
                          : "border-[#F3F4F6] bg-[#F9FAFB] text-[#374151]"
                      }`}
                    >
                      <span>{item.emoji}</span>
                      <span>{item.label}</span>
                      {already && <span className="text-[#10B981] text-xs">✓</span>}
                      {adding === item.id && <span className="text-[#9CA3AF] text-xs">생성 중...</span>}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 내 관심사 */}
            <div className="bg-white rounded-3xl p-4 card-shadow">
              <p className="text-[#1C1C1E] font-bold text-sm mb-2">
                내 관심사{topics.length > 0 ? ` (${topics.length}개)` : ""}
              </p>
              {topics.length === 0 ? (
                <p className="text-[#9CA3AF] text-sm text-center py-3">아직 추가한 관심사가 없어요</p>
              ) : (
                <>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {topics.map((t) => (
                      <span key={t.id} className="flex items-center gap-1 bg-[#ECFDF5] text-[#10B981] text-sm px-3 py-1.5 rounded-full font-medium">
                        {t.name}
                        <button
                          onClick={() => setConfirmTopic({ id: t.id, name: t.name })}
                          className="text-[#10B981]/60 hover:text-[#EF4444] ml-0.5 leading-none"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={() => router.push("/roadmap")}
                    className="w-full bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] text-white font-bold py-3 rounded-2xl text-sm active:scale-95 transition-all"
                  >
                    📚 내 로드맵 보러 가기 →
                  </button>
                </>
              )}
            </div>

          </div>
        )}

        {/* 북마크 탭 */}
        {tab === "bookmarks" && (
          <div className="mt-4">
            {bookmarks.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-4xl mb-3">🔖</p>
                <p className="text-[#1C1C1E] font-bold mb-1">북마크가 없어요</p>
                <p className="text-[#9CA3AF] text-sm">학습 중 🏷️ 버튼으로 저장해보세요</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {bookmarks.map((bm) => (
                  <div key={bm.id} className="bg-white rounded-3xl p-4 card-shadow">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <span className="bg-[#ECFDF5] text-[#10B981] text-xs px-2 py-0.5 rounded-full font-medium">
                          {bm.contents?.source || "챕터"}
                        </span>
                        <p className="text-[#1C1C1E] font-bold text-sm mt-2 line-clamp-2">
                          {bm.contents?.title}
                        </p>
                        <p className="text-[#9CA3AF] text-xs mt-1">
                          {new Date(bm.created_at).toLocaleDateString("ko-KR")} 저장
                        </p>
                      </div>
                      <button
                        onClick={() => handleRemoveBookmark(bm.content_id)}
                        className="text-[#9CA3AF] text-xs flex-shrink-0 mt-1"
                      >
                        삭제
                      </button>
                    </div>
                    <button
                      onClick={() => router.push(`/quiz?content_id=${bm.content_id}`)}
                      className="mt-3 w-full bg-[#ECFDF5] text-[#10B981] text-xs font-bold py-2.5 rounded-xl active:scale-95 transition-all"
                    >
                      ✏️ 이 내용으로 퀴즈 풀기
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {/* 피드백 탭 */}
        {tab === "feedback" && (
          <div className="mt-4 flex flex-col gap-4">
            <div className="bg-white rounded-3xl p-5 card-shadow">
              <p className="text-[#1C1C1E] font-bold text-base mb-1">BriefUp에 의견 보내기</p>
              <p className="text-[#9CA3AF] text-sm mb-5">여러분의 피드백이 AI 브리핑 품질을 높여요</p>

              {/* 피드백 유형 선택 */}
              <p className="text-[#374151] text-xs font-semibold mb-2">어떤 종류의 피드백인가요?</p>
              <div className="flex gap-2 mb-5">
                {([
                  { type: "positive" as FeedbackType, emoji: "👍", label: "좋아요" },
                  { type: "negative" as FeedbackType, emoji: "👎", label: "아쉬워요" },
                  { type: "suggestion" as FeedbackType, emoji: "💡", label: "제안해요" },
                ]).map((item) => (
                  <button
                    key={item.type}
                    onClick={() => setFeedbackType(item.type)}
                    className={`flex-1 flex flex-col items-center gap-1.5 py-3 rounded-2xl border-2 text-sm font-medium transition-all ${
                      feedbackType === item.type
                        ? "border-[#10B981] bg-[#ECFDF5] text-[#065F46]"
                        : "border-[#F3F4F6] bg-[#F9FAFB] text-[#6B7280]"
                    }`}
                  >
                    <span className="text-xl">{item.emoji}</span>
                    <span className="text-xs">{item.label}</span>
                  </button>
                ))}
              </div>

              {/* 메시지 입력 */}
              <p className="text-[#374151] text-xs font-semibold mb-2">내용을 적어주세요</p>
              <textarea
                value={feedbackMessage}
                onChange={(e) => setFeedbackMessage(e.target.value)}
                placeholder={
                  feedbackType === "positive" ? "어떤 점이 좋았나요?" :
                  feedbackType === "negative" ? "어떤 점이 아쉬웠나요?" :
                  "어떤 기능이나 개선을 원하시나요?"
                }
                maxLength={500}
                rows={4}
                className="w-full bg-[#F9FAFB] text-[#1C1C1E] placeholder-[#9CA3AF] text-sm px-4 py-3 rounded-2xl outline-none border border-[#F3F4F6] focus:border-[#10B981] resize-none"
              />
              <div className="flex items-center justify-between mt-1 mb-4">
                <span className="text-[#9CA3AF] text-xs">{feedbackMessage.length}/500</span>
              </div>

              <button
                onClick={handleSubmitFeedback}
                disabled={!feedbackMessage.trim() || feedbackSubmitting}
                className="w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-sm active:scale-95 transition-all disabled:opacity-40"
              >
                {feedbackSubmitting ? "전송 중..." : "피드백 보내기"}
              </button>
            </div>

            <div className="bg-[#F9FAFB] rounded-2xl p-4 text-center">
              <p className="text-[#9CA3AF] text-xs leading-relaxed">
                보내주신 피드백은 AI 에이전트가 다음 브리핑 생성 시<br/>
                참고 자료로 직접 반영돼요
              </p>
            </div>
          </div>
        )}

      </div>

      <BottomNav active="mypage" />

      {/* 관심사 제거 확인 모달 */}
      {confirmTopic && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center"
          onClick={() => setConfirmTopic(null)}
        >
          <div className="absolute inset-0 bg-black/40" />
          <div
            className="relative w-full max-w-md bg-white rounded-t-3xl px-5 pt-6 pb-10 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-10 h-1 bg-[#E5E7EB] rounded-full mx-auto mb-5" />
            <p className="text-[#1C1C1E] font-bold text-base mb-1 text-center">
              관심사를 제거할까요?
            </p>
            <p className="text-[#6B7280] text-sm text-center mb-6">
              <span className="font-bold text-[#1C1C1E]">{confirmTopic.name}</span>을(를) 목록에서 지워요.
              <br />관련 커리큘럼과 진행 상태는 그대로 남아요.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmTopic(null)}
                className="flex-1 py-3.5 rounded-2xl bg-[#F3F4F6] text-[#374151] font-bold text-sm active:scale-95 transition-all"
              >
                취소
              </button>
              <button
                onClick={() => handleRemoveTopic(confirmTopic.id)}
                className="flex-1 py-3.5 rounded-2xl bg-[#EF4444] text-white font-bold text-sm active:scale-95 transition-all"
              >
                제거
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
