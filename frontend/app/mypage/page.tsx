"use client";

import { useEffect, useState } from "react";
import { api, Topic, TEMP_USER_ID } from "@/lib/api";
import BottomNav from "@/components/layout/BottomNav";
import { useRouter } from "next/navigation";

const CATEGORIES = [
  { label: "AI / ML", value: "AI/ML" },
  { label: "철학", value: "철학" },
  { label: "경제", value: "경제" },
  { label: "심리학", value: "심리학" },
];

type Tab = "settings" | "bookmarks";

export default function MyPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [bookmarks, setBookmarks] = useState<any[]>([]);
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCategory, setNewCategory] = useState("AI/ML");
  const [tab, setTab] = useState<Tab>("settings");
  const router = useRouter();

  useEffect(() => {
    api.getTopics(TEMP_USER_ID).then(setTopics);
    api.getBookmarks(TEMP_USER_ID).then(setBookmarks);
  }, []);

  async function handleAdd() {
    if (!newName.trim()) return;
    setAdding(true);
    try {
      await api.addTopic(TEMP_USER_ID, newName.trim(), newCategory);
      const updated = await api.getTopics(TEMP_USER_ID);
      setTopics(updated);
      setNewName("");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemoveBookmark(contentId: string) {
    await api.toggleBookmark(TEMP_USER_ID, contentId);
    setBookmarks(bm => bm.filter(b => b.content_id !== contentId));
  }

  return (
    <div className="flex flex-col min-h-screen pb-24 bg-[#FAFAF8]">
      <div className="px-5 pt-14 pb-4 bg-white border-b border-[#F9FAFB]">
        <h1 className="text-2xl font-bold text-[#1C1C1E]">마이페이지</h1>
      </div>

      {/* 탭 */}
      <div className="px-5 pt-4 pb-2 flex gap-2">
        {[
          { key: "settings", label: "⚙️ 설정" },
          { key: "bookmarks", label: `🔖 북마크 ${bookmarks.length > 0 ? `(${bookmarks.length})` : ""}` },
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
          <>
            <div className="mt-4">
              <h2 className="text-[#1C1C1E] font-bold text-sm mb-3">관심사 설정</h2>
              <div className="bg-white rounded-3xl p-4 card-shadow mb-3">
                {topics.length === 0 ? (
                  <p className="text-[#9CA3AF] text-sm text-center py-2">관심사를 추가해주세요</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {topics.map((t) => (
                      <span key={t.id} className="bg-[#ECFDF5] text-[#10B981] text-sm px-3 py-1 rounded-full font-medium">
                        {t.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-white rounded-3xl p-4 card-shadow flex flex-col gap-3">
                <input
                  type="text"
                  placeholder="관심사 입력 (예: Agentic AI)"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="bg-[#F9FAFB] text-[#1C1C1E] placeholder-[#9CA3AF] text-sm px-4 py-3 rounded-xl outline-none border border-[#F3F4F6] focus:border-[#10B981]"
                />
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="bg-[#F9FAFB] text-[#1C1C1E] text-sm px-4 py-3 rounded-xl outline-none border border-[#F3F4F6]"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
                <button
                  onClick={handleAdd}
                  disabled={adding}
                  className="bg-gradient-to-r from-[#10B981] to-[#059669] text-white font-bold py-3 rounded-xl text-sm active:scale-95 transition-all disabled:opacity-50"
                >
                  {adding ? "추가 중..." : "관심사 추가"}
                </button>
              </div>
            </div>

            <div className="mt-4">
              <h2 className="text-[#1C1C1E] font-bold text-sm mb-3">앱 정보</h2>
              <div className="bg-white rounded-3xl card-shadow divide-y divide-[#F9FAFB]">
                {[
                  { label: "버전", value: "0.1.0" },
                  { label: "AI 모델", value: "GPT-4o-mini" },
                  { label: "퀴즈 정확도 목표", value: "95%+" },
                ].map((item) => (
                  <div key={item.label} className="flex justify-between px-4 py-3">
                    <span className="text-[#6B7280] text-sm">{item.label}</span>
                    <span className="text-[#1C1C1E] text-sm font-medium">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
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
      </div>

      <BottomNav active="mypage" />
    </div>
  );
}
