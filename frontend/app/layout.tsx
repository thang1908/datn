import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { MicrophoneIcon, ListIcon, PlayIcon } from "@/components/Icons";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CS Agent QA — Phân tích chất lượng cuộc gọi",
  description: "Hệ thống phân tích và đánh giá chất lượng cuộc gọi chăm sóc khách hàng",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className={`${inter.className} bg-slate-50 min-h-screen`}>
        <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <Link href="/" className="font-bold text-slate-800 text-lg flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                <MicrophoneIcon size={15} />
              </span>
              CS Agent QA
            </Link>
            <div className="flex items-center gap-1 text-sm font-medium">
              <Link
                href="/"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-all"
              >
                <PlayIcon size={14} />
                Phân tích
              </Link>
              <Link
                href="/history"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-all"
              >
                <ListIcon size={14} />
                Lịch sử
              </Link>
            </div>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
