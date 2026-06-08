"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Root() {
  const router = useRouter();
  const [pct, setPct] = useState(0);
  const [show, setShow] = useState(false);

  useEffect(() => {
    const done = localStorage.getItem("onboarding_done");
    if (!done) {
      router.replace("/onboarding");
      return;
    }
    setShow(true);
    const start = Date.now();
    const timer = setInterval(() => {
      const p = Math.min(100, ((Date.now() - start) / 700) * 100);
      setPct(p);
      if (p >= 100) {
        clearInterval(timer);
        router.replace("/home");
      }
    }, 30);
    return () => clearInterval(timer);
  }, []);

  if (!show) return null;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#FAFAF8] px-8">
      <div className="flex flex-col items-center gap-3">
        <p className="text-6xl">📖</p>
        <p className="text-[#1C1C1E] font-bold text-2xl tracking-tight">BrefUp</p>
        <p className="text-[#6B7280] text-sm text-center leading-relaxed">
          관심사를 고르면 AI가 매일<br />딱 맞는 학습 카드를 준비해줘요
        </p>
      </div>
      <div className="w-40 bg-[#F3F4F6] rounded-full h-1 overflow-hidden mt-10">
        <div
          className="h-1 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-75"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
