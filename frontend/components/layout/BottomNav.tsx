import Link from "next/link";

const TABS = [
  { key: "home",    label: "홈",   icon: "🏠", href: "/home" },
  { key: "roadmap", label: "로드맵", icon: "📚", href: "/roadmap" },
  { key: "history", label: "기록", icon: "📋", href: "/history" },
  { key: "map",     label: "맵",   icon: "🗺️", href: "/map" },
  { key: "mypage",  label: "마이", icon: "👤", href: "/mypage" },
];

export default function BottomNav({ active }: { active: string }) {
  return (
    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-md bg-white border-t border-[#F3F4F6] flex"
      style={{ boxShadow: "0 -4px 20px rgba(0,0,0,0.06)" }}>
      {TABS.map((tab) => (
        <Link key={tab.key} href={tab.href}
          className={`flex-1 flex flex-col items-center py-3 gap-0.5 transition-all ${
            active === tab.key ? "text-[#10B981]" : "text-[#9CA3AF]"
          }`}>
          <span className="text-xl">{tab.icon}</span>
          <span className={`text-[10px] font-medium ${active === tab.key ? "text-[#10B981]" : "text-[#9CA3AF]"}`}>
            {tab.label}
          </span>
          {active === tab.key && (
            <span className="w-1 h-1 rounded-full bg-[#10B981] mt-0.5" />
          )}
        </Link>
      ))}
    </nav>
  );
}
