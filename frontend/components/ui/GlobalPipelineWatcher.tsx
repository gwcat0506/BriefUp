"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Toast } from "@/components/ui/Toast";

const STORAGE_KEY = "briefup_pipeline_pending";

export type PipelineEntry = {
  topicName: string;
  startedAt: number;
};

export function savePipelinePending(entry: PipelineEntry) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entry));
}

export function clearPipelinePending() {
  localStorage.removeItem(STORAGE_KEY);
}

export default function GlobalPipelineWatcher() {
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  function stopPolling() {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    if (timeoutRef.current) { clearTimeout(timeoutRef.current); timeoutRef.current = null; }
  }

  function startWatching(entry: PipelineEntry) {
    stopPolling();
    let succeeded = false;

    const check = async () => {
      try {
        const data = await api.getContentsByCategory(entry.topicName, 5);
        const hasNew = data.some(c => new Date(c.created_at).getTime() >= entry.startedAt);
        if (hasNew) {
          succeeded = true;
          stopPolling();
          clearPipelinePending();
          setToast({ message: `'${entry.topicName}' 브리핑이 준비됐어요!`, type: "success" });
        }
      } catch {}
    };

    pollRef.current = setInterval(check, 15000);

    // 3분 후 강제 종료
    timeoutRef.current = setTimeout(() => {
      stopPolling();
      clearPipelinePending();
      if (!succeeded) {
        setToast({ message: `'${entry.topicName}' 관련 자료를 충분히 찾지 못했어요 🙏`, type: "error" });
      }
    }, 180000);
  }

  // 페이지 전환마다 localStorage 확인
  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const entry: PipelineEntry = JSON.parse(raw);
      // 마이페이지에선 자체 폴러가 있으므로 전역 폴러는 생략
      if (pathname === "/mypage") return;
      startWatching(entry);
    } catch {
      clearPipelinePending();
    }
    return () => stopPolling();
  }, [pathname]);

  if (!toast) return null;

  const isSuccess = toast.type === "success";

  return (
    <div
      className={`fixed bottom-24 left-1/2 -translate-x-1/2 w-[90%] max-w-sm z-50
        flex items-center gap-3 px-4 py-3 rounded-2xl border card-shadow
        animate-in slide-in-from-bottom-4 duration-300
        ${isSuccess
          ? "bg-[#ECFDF5] border-[#6EE7B7] text-[#059669] cursor-pointer"
          : "bg-[#FEF2F2] border-[#FECACA] text-[#DC2626]"
        }`}
      onClick={() => { if (isSuccess) { setToast(null); router.push("/home"); } }}
    >
      <span>{isSuccess ? "✅" : "🙏"}</span>
      <p className="text-sm font-medium flex-1">
        {toast.message}{isSuccess ? " 홈에서 확인하세요 →" : ""}
      </p>
      <button
        onClick={e => { e.stopPropagation(); setToast(null); }}
        className="text-xs opacity-60"
      >
        ✕
      </button>
    </div>
  );
}
