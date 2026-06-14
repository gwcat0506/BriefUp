import type { Metadata, Viewport } from "next";
import "./globals.css";
import GlobalPipelineWatcher from "@/components/ui/GlobalPipelineWatcher";

export const metadata: Metadata = {
  title: "BriefUp",
  description: "매일 아침 10분, AI 브리핑 학습",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "BriefUp",
  },
};

export const viewport: Viewport = {
  themeColor: "#10B981",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-[#FAFAF8] text-[#1C1C1E] min-h-screen max-w-md mx-auto">
        {children}
        <GlobalPipelineWatcher />
      </body>
    </html>
  );
}
