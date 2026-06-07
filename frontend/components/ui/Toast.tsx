"use client";

import { useEffect, useState } from "react";

interface ToastProps {
  message: string;
  type?: "error" | "success" | "info";
  onClose: () => void;
}

export function Toast({ message, type = "error", onClose }: ToastProps) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000);
    return () => clearTimeout(t);
  }, [onClose]);

  const styles = {
    error:   "bg-[#FEF2F2] border-[#FCA5A5] text-[#DC2626]",
    success: "bg-[#ECFDF5] border-[#6EE7B7] text-[#059669]",
    info:    "bg-[#EFF6FF] border-[#93C5FD] text-[#2563EB]",
  };

  const icons = { error: "❌", success: "✅", info: "ℹ️" };

  return (
    <div className={`fixed bottom-24 left-1/2 -translate-x-1/2 w-[90%] max-w-sm z-50
      flex items-center gap-3 px-4 py-3 rounded-2xl border card-shadow
      animate-in slide-in-from-bottom-4 duration-300 ${styles[type]}`}>
      <span>{icons[type]}</span>
      <p className="text-sm font-medium flex-1">{message}</p>
      <button onClick={onClose} className="text-xs opacity-60">✕</button>
    </div>
  );
}

// 전역 토스트 훅
export function useToast() {
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" | "info" } | null>(null);

  const show = (message: string, type: "error" | "success" | "info" = "error") => {
    setToast({ message, type });
  };

  const hide = () => setToast(null);

  const ToastComponent = toast
    ? <Toast message={toast.message} type={toast.type} onClose={hide} />
    : null;

  return { show, ToastComponent };
}
