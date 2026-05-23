"use client";
import { useState } from "react";
import UploadForm from "@/components/UploadForm";
import ResultDashboard from "@/components/ResultDashboard";

export default function HomePage() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  return (
    <div>
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-slate-800 mb-2">
          Phân tích chất lượng cuộc gọi
        </h1>
        <p className="text-slate-500">
          Upload file audio để nhận kết quả phân tích QA theo thời gian thực
        </p>
      </div>

      <UploadForm onResult={setResult} />

      {result && (
        <div className="mt-10">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-px flex-1 bg-slate-200" />
            <span className="text-sm font-medium text-slate-500">Kết quả phân tích</span>
            <div className="h-px flex-1 bg-slate-200" />
          </div>
          <ResultDashboard data={result} />
        </div>
      )}
    </div>
  );
}
