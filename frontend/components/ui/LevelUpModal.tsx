"use client";

import { useEffect, useState } from "react";
import { XpInfo } from "@/lib/api";

interface LevelUpModalProps {
  xpInfo: XpInfo;
  onClose: () => void;
}

export default function LevelUpModal({ xpInfo, onClose }: LevelUpModalProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);
  }, []);

  const handleClose = () => {
    setVisible(false);
    setTimeout(onClose, 300);
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center px-6 transition-all duration-300 ${
        visible ? "bg-black/50 opacity-100" : "bg-black/0 opacity-0"
      }`}
      onClick={handleClose}
    >
      <div
        className={`bg-white rounded-3xl p-8 w-full max-w-sm text-center transition-all duration-300 ${
          visible ? "scale-100 opacity-100" : "scale-90 opacity-0"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 축하 이모지 */}
        <div className="text-5xl mb-2 level-up-pop inline-block">🎉</div>

        <h2 className="text-[#1C1C1E] text-2xl font-bold mb-1">레벨 업!</h2>
        <p className="text-[#6B7280] text-sm mb-6">
          Lv.{(xpInfo.old_level ?? xpInfo.level - 1)} → Lv.{xpInfo.level}
        </p>

        {/* 캐릭터 */}
        <div className="bg-gradient-to-br from-[#ECFDF5] to-[#D1FAE5] rounded-3xl p-6 mb-6">
          <div className="text-7xl mb-3 character-heartbeat inline-block">
            {xpInfo.char_emoji}
          </div>
          <p className="text-[#065F46] font-bold text-xl">{xpInfo.char_name}</p>
          <p className="text-[#10B981] text-sm font-medium">{xpInfo.char_title} 달성!</p>
        </div>

        {/* XP 바 */}
        <div className="mb-6">
          <div className="flex justify-between text-xs text-[#9CA3AF] mb-2">
            <span>Lv.{xpInfo.level}</span>
            <span>{xpInfo.xp_in_level} / {xpInfo.xp_needed} XP</span>
          </div>
          <div className="w-full bg-[#F3F4F6] rounded-full h-2.5 overflow-hidden">
            <div
              className="h-2.5 rounded-full bg-gradient-to-r from-[#10B981] to-[#34D399] transition-all duration-1000"
              style={{ width: `${xpInfo.progress_pct}%` }}
            />
          </div>
        </div>

        <button
          onClick={handleClose}
          className="w-full bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-4 rounded-2xl text-base shadow-lg shadow-emerald-100 active:scale-95 transition-all"
        >
          계속 학습하기 🚀
        </button>
      </div>
    </div>
  );
}
