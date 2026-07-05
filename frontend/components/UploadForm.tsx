"use client";
import { useState, useCallback } from "react";
import {
  UploadCloudIcon,
  FileAudioIcon,
  CheckIcon,
  PlayIcon,
  AlertTriangleIcon,
} from "@/components/Icons";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

const NODE_ORDER = [
  { key: "read_audio",             label: "Đọc file audio" },
  { key: "transcribe_audio",       label: "Transcribe audio" },
  { key: "classify_and_resolved",  label: "Phân loại case" },
  { key: "summarize_conversation", label: "Tóm tắt nội dung" },
  { key: "score_qa",               label: "Chấm điểm QA" },
  { key: "analyze_negative",       label: "Phân tích tiêu cực" },
  { key: "merge_output",           label: "Hoàn thành" },
];

type Props = { onResult: (data: Record<string, unknown>) => void };

export default function UploadForm({ onResult }: Props) {
  const [file, setFile]           = useState<File | null>(null);
  const [loading, setLoading]     = useState(false);
  const [completed, setCompleted] = useState<string[]>([]);
  const [message, setMessage]     = useState("");
  const [error, setError]         = useState("");
  const [dragging, setDragging]   = useState(false);

  const handleFile = (f: File | null) => {
    if (!f) return;
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (!["wav", "mp3", "m4a", "flac", "ogg"].includes(ext || "")) {
      setError("Chỉ hỗ trợ file wav, mp3, m4a, flac, ogg");
      return;
    }
    setError("");
    setFile(f);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setCompleted([]);
    setMessage("Đang khởi động...");
    setError("");

    try {
      const form = new FormData();
      form.append("audio", file);

      const res = await fetch(`${API_URL}/pipeline/run/stream`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader  = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer    = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const event = JSON.parse(line.slice(5).trim());

          if (event.type === "progress") {
            setMessage(event.message || "");
            setCompleted(event.completed || []);
          }
          if (event.type === "result") {
            onResult(event.data);
            setLoading(false);
            setMessage("Phân tích hoàn thành");
          }
          if (event.type === "error") {
            setError(event.message);
            setLoading(false);
          }
        }
      }
    } catch (err) {
      setError(`Lỗi kết nối: ${err}`);
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById("file-input")?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
            dragging
              ? "border-blue-400 bg-blue-50"
              : file
              ? "border-green-400 bg-green-50"
              : "border-slate-300 hover:border-blue-300 hover:bg-slate-50"
          }`}
        >
          <div className={`flex justify-center mb-3 ${file ? "text-green-600" : "text-slate-400"}`}>
            {file
              ? <FileAudioIcon size={40} />
              : <UploadCloudIcon size={40} />
            }
          </div>
          {file ? (
            <div>
              <p className="font-semibold text-green-700">{file.name}</p>
              <p className="text-xs text-slate-400 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          ) : (
            <div>
              <p className="text-slate-600 font-medium">Kéo thả hoặc click để chọn file</p>
              <p className="text-xs text-slate-400 mt-1">Hỗ trợ: wav, mp3, m4a, flac, ogg</p>
            </div>
          )}
          <input
            id="file-input" type="file" accept=".wav,.mp3,.m4a,.flac,.ogg" hidden
            onChange={(e) => handleFile(e.target.files?.[0] || null)}
          />
        </div>



        {error && (
          <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 px-4 py-2.5 rounded-lg border border-red-100">
            <AlertTriangleIcon size={15} className="flex-shrink-0" />
            {error}
          </div>
        )}

        <button
          type="submit" disabled={!file || loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <PlayIcon size={16} />
          {loading ? "Đang phân tích..." : "Phân tích cuộc gọi"}
        </button>
      </form>

      {/* Progress */}
      {(loading || completed.length > 0) && (
        <div className="mt-6 pt-6 border-t border-slate-100">
          <p className="text-sm font-medium text-slate-500 mb-4">{message}</p>
          <div className="space-y-2.5">
            {NODE_ORDER.map(({ key, label }, i) => {
              const done   = completed.includes(key);
              const active = !done && completed.length === i && loading;
              return (
                <div key={key} className="flex items-center gap-3">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                    done   ? "bg-green-500 text-white"
                    : active ? "bg-blue-500 animate-pulse"
                    : "bg-slate-200"
                  }`}>
                    {done && <CheckIcon size={11} />}
                  </div>
                  <span className={`text-sm transition-colors ${
                    done   ? "text-green-700 font-medium"
                    : active ? "text-blue-600 font-medium"
                    : "text-slate-400"
                  }`}>
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
