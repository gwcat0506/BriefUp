"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Root() {
  const router = useRouter();
  const [pct, setPct] = useState(0);

  useEffect(() => {
    localStorage.setItem("onboarding_done", "true");
    if (!localStorage.getItem("user_nickname")) {
      localStorage.setItem("user_nickname", "최고운");
    }
    // 짧은 진행 바 후 이동 (실제 작업은 즉시 완료되므로 0.6초 연출)
    const start = Date.now();
    const timer = setInterval(() => {
      const p = Math.min(100, ((Date.now() - start) / 600) * 100);
      setPct(p);
      if (p >= 100) {
        clearInterval(timer);
        router.replace("/home");
      }
    }, 30);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#FAFAF8] px-8 gap-4">
      <p className="text-5xl mb-2">📖</p>
      <p className="text-[#1C1C1E] font-bold text-lg">BrefUp</p>
      <div className="w-48 bg-[#F3F4F6] rounded-full h-1.5 overflow-hidden mt-2">
        <div
          className="h-1.5 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-75"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
