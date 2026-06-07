"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Root() {
  const router = useRouter();

  useEffect(() => {
    const done = localStorage.getItem("onboarding_done");
    if (done) {
      router.replace("/home");
    } else {
      router.replace("/onboarding");
    }
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#FAFAF8]">
      <div className="text-center">
        <p className="text-5xl animate-bounce">📖</p>
      </div>
    </div>
  );
}
