"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api, Quiz, AnswerResult, TEMP_USER_ID } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";
import Link from "next/link";

type Step = "loading" | "quiz" | "result" | "done" | "empty" | "error";

const DIFFICULTY_LABEL = ["", "입문", "기본", "심화"];
const DIFFICULTY_COLOR = ["", "#10B981", "#F59E0B", "#EF4444"];

function QuizContent() {
  const searchParams = useSearchParams();
  const contentId = searchParams.get("content_id");
  const router = useRouter();

  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [step, setStep] = useState<Step>("loading");
  const [score, setScore] = useState({ correct: 0, total: 0 });
  const [error, setError] = useState("");

  useEffect(() => {
    const load = contentId
      ? api.getQuizzesByContent(contentId)
      : api.getTodayQuizzes(TEMP_USER_ID);

    load
      .then((q) => {
        if (q.length === 0) setStep("empty");
        else { setQuizzes(q); setStep("quiz"); }
      })
      .catch((e) => {
        // content_id 퀴즈가 없으면 오늘 전체 퀴즈로 폴백
        if (contentId) {
          api.getTodayQuizzes(TEMP_USER_ID)
            .then((q) => {
              if (q.length === 0) setStep("empty");
              else { setQuizzes(q); setStep("quiz"); }
            })
            .catch((e2) => { setError(e2.message); setStep("error"); });
        } else {
          setError(e.message);
          setStep("error");
        }
      });
  }, [contentId]);

  const quiz = quizzes[currentIdx];

  async function handleSelect(key: string) {
    if (selected || !quiz) return;
    setSelected(key);
    try {
      const res = await api.submitAnswer({
        user_id: TEMP_USER_ID,
        quiz_id: quiz.id,
        content_id: quiz.content_id,
        selected: key,
      });
      setResult(res);
      setStep("result");
      setScore((s) => ({ correct: s.correct + (res.is_correct ? 1 : 0), total: s.total + 1 }));
    } catch (e: any) { setError(e.message); setStep("error"); }
  }

  function handleNext() {
    if (currentIdx + 1 >= quizzes.length) {
      setStep("done");
    } else {
      setCurrentIdx(i => i + 1);
      setSelected(null);
      setResult(null);
      setStep("quiz");
    }
  }

  // ── 로딩 ──
  if (step === "loading") return (
    <div className="flex items-center justify-center min-h-screen bg-[#FAFAF8]">
      <div className="text-center">
        <p className="text-5xl mb-3 animate-bounce">🧠</p>
        <p className="text-[#6B7280]">퀴즈 불러오는 중...</p>
      </div>
    </div>
  );

  // ── 에러 ──
  if (step === "error") return (
    <div className="flex flex-col items-center justify-center min-h-screen px-5 gap-4 bg-[#FAFAF8] pb-20">
      <p className="text-[#EF4444] text-center text-sm">{error}</p>
      <button onClick={() => window.location.reload()} className="text-[#10B981] font-medium">다시 시도</button>
      <BottomNav active="quiz" />
    </div>
  );

  // ── 빈 상태 ──
  if (step === "empty") return (
    <div className="flex flex-col items-center justify-center min-h-screen px-5 text-center pb-20 bg-[#FAFAF8]">
      <p className="text-6xl mb-4">📭</p>
      <p className="text-[#1C1C1E] text-xl font-bold mb-2">퀴즈가 없어요</p>
      <p className="text-[#9CA3AF] text-sm mb-6">브리핑을 먼저 읽어보세요</p>
      <Link href="/home" className="bg-[#10B981] text-white px-6 py-3 rounded-2xl font-bold text-sm">
        홈으로 가기
      </Link>
      <BottomNav active="quiz" />
    </div>
  );

  // ── 완료 ──
  if (step === "done") {
    const pct = Math.round((score.correct / score.total) * 100);
    return (
      <div className="flex flex-col min-h-screen bg-[#FAFAF8] pb-24">
        <div className="flex-1 flex flex-col items-center justify-center px-5 text-center">
          <p className="text-7xl mb-5">{pct >= 70 ? "🎉" : "💪"}</p>
          <h2 className="text-[#1C1C1E] text-2xl font-bold mb-1">퀴즈 완료!</h2>
          <p className="text-[#6B7280] text-sm mb-8">
            {score.total}문제 중 <span className="text-[#10B981] font-bold">{score.correct}문제</span> 정답
          </p>

          <div className="w-full bg-white rounded-3xl p-6 card-shadow mb-6">
            <div className="flex justify-between mb-3">
              <span className="text-[#6B7280] text-sm">정답률</span>
              <span className="text-[#10B981] font-bold text-xl">{pct}%</span>
            </div>
            <div className="w-full bg-[#F3F4F6] rounded-full h-3 overflow-hidden mb-3">
              <div
                className="h-3 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-1000"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="text-[#9CA3AF] text-xs">
              {pct >= 80 ? "오늘 정말 잘했어요! 내일도 이 기세로 🔥" :
               pct >= 50 ? "잘 하고 있어요! 조금씩 늘고 있어요 📈" :
               "틀린 문제는 내일 다시 나올 거예요. 파이팅! 💪"}
            </p>
          </div>

          <div className="flex gap-3 w-full">
            <button
              onClick={() => router.push("/home")}
              className="flex-1 bg-[#F3F4F6] text-[#1C1C1E] font-bold py-4 rounded-2xl text-sm"
            >
              홈으로
            </button>
            <Link href="/history" className="flex-1">
              <button className="w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-sm shadow-lg shadow-emerald-100">
                기록 보기 →
              </button>
            </Link>
          </div>
        </div>
        <BottomNav active="quiz" />
      </div>
    );
  }

  if (!quiz) return null;
  const optionKeys = Object.keys(quiz.options).sort();

  return (
    <div className="flex flex-col min-h-screen bg-[#FAFAF8] pb-24">

      {/* 헤더 */}
      <div className="px-5 pt-14 pb-4 bg-white border-b border-[#F9FAFB]">
        <div className="flex items-center justify-between mb-3">
          <button onClick={() => router.back()} className="text-[#9CA3AF] text-sm">← 돌아가기</button>
          <span
            className="text-xs px-3 py-1 rounded-full font-medium"
            style={{
              backgroundColor: `${DIFFICULTY_COLOR[quiz.difficulty || 1]}15`,
              color: DIFFICULTY_COLOR[quiz.difficulty || 1]
            }}
          >
            {DIFFICULTY_LABEL[quiz.difficulty || 1]}
          </span>
        </div>

        {/* 진행 바 */}
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-[#F3F4F6] rounded-full h-2 overflow-hidden">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-500"
              style={{ width: `${((currentIdx) / quizzes.length) * 100}%` }}
            />
          </div>
          <span className="text-[#9CA3AF] text-xs font-medium">
            {currentIdx + 1}/{quizzes.length}
          </span>
        </div>
      </div>

      <div className="px-5 py-5 flex-1">
        {/* 개념 태그 */}
        <div className="mb-4">
          <span className="bg-[#ECFDF5] text-[#10B981] text-xs px-3 py-1.5 rounded-full font-medium">
            💡 {quiz.concept}
          </span>
        </div>

        {/* 문제 */}
        <div className="bg-white rounded-3xl p-5 mb-5 card-shadow">
          <p className="text-[#1C1C1E] font-semibold text-base leading-relaxed">
            {quiz.question}
          </p>
        </div>

        {/* 보기 */}
        <div className="flex flex-col gap-3">
          {optionKeys.map((key) => {
            let cls = "bg-white border-2 border-transparent text-[#1C1C1E] card-shadow";
            if (selected) {
              if (key === result?.answer) cls = "bg-[#ECFDF5] border-2 border-[#10B981] text-[#065F46]";
              else if (key === selected && !result?.is_correct) cls = "bg-[#FEF2F2] border-2 border-[#EF4444] text-[#991B1B]";
              else cls = "bg-[#F9FAFB] border-2 border-transparent text-[#9CA3AF]";
            }
            return (
              <button
                key={key}
                onClick={() => handleSelect(key)}
                disabled={!!selected}
                className={`w-full text-left p-4 rounded-2xl transition-all active:scale-[0.98] ${cls}`}
              >
                <span className="font-bold mr-3 text-sm">{key}</span>
                <span className="text-sm">{quiz.options[key]}</span>
              </button>
            );
          })}
        </div>

        {/* 결과 피드백 */}
        {result && (
          <div className={`mt-4 rounded-3xl p-4 ${
            result.is_correct
              ? "bg-[#ECFDF5] border border-[#10B981]/30"
              : "bg-[#FEF2F2] border border-[#EF4444]/30"
          }`}>
            <p className={`font-bold mb-2 text-sm ${result.is_correct ? "text-[#059669]" : "text-[#DC2626]"}`}>
              {result.is_correct ? "✅ 정답이에요!" : "❌ 아쉬워요!"}
            </p>
            <p className="text-[#374151] text-sm leading-relaxed">{result.explanation}</p>
          </div>
        )}
      </div>

      {/* 다음 버튼 */}
      {result && (
        <div className="px-5 pb-2">
          <button
            onClick={handleNext}
            className="w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-base active:scale-95 transition-all shadow-lg shadow-emerald-100"
          >
            {currentIdx + 1 >= quizzes.length ? "결과 보기 🎉" : "다음 문제 →"}
          </button>
        </div>
      )}

      <BottomNav active="quiz" />
    </div>
  );
}

export default function QuizPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-[#FAFAF8]">
        <p className="text-5xl animate-bounce">🧠</p>
      </div>
    }>
      <QuizContent />
    </Suspense>
  );
}
