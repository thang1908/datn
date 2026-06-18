"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  PlusIcon,
  Trash2Icon,
  InboxIcon,
  ArrowRightIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  AlertTriangleIcon,
} from "@/components/Icons";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Item = {
  _id: string;
  call_id: string;
  CaseType: string;
  Resolved: string;
  IsNegative: string;
  CriteriaScores: { Communication: number; Attitude: number; DataCollection: number; ProblemSolving: number };
  created_at: string;
};

function getTotalScore(s: Item["CriteriaScores"]) {
  if (!s) return null;
  return (s.Communication || 0) * 0.2 + (s.Attitude || 0) * 0.3 + (s.DataCollection || 0) * 0.1 + (s.ProblemSolving || 0) * 0.4;
}

export default function HistoryPage() {
  const [items,         setItems]         = useState<Item[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const [deleting,      setDeleting]      = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/conversations?limit=50`)
      .then((r) => r.json())
      .then((d) => { setItems(d.results || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  async function handleDelete(id: string) {
    setDeleting(true);
    try {
      const res = await fetch(`${API_URL}/conversations/${id}`, { method: "DELETE" });
      if (res.ok) {
        setItems((prev) => prev.filter((i) => i._id !== id));
      } else {
        const err = await res.json();
        alert(`Xóa thất bại: ${err.detail ?? res.statusText}`);
      }
    } catch {
      alert("Không thể kết nối đến server.");
    } finally {
      setDeleting(false);
      setPendingDelete(null);
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Lịch sử phân tích</h1>
          {!loading && (
            <p className="text-sm text-slate-400 mt-0.5">{items.length} cuộc gọi</p>
          )}
        </div>
        <Link
          href="/"
          className="flex items-center gap-1.5 text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          <PlusIcon size={15} />
          Phân tích mới
        </Link>
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-20 text-slate-400 text-sm">Đang tải...</div>
      )}

      {/* Empty */}
      {!loading && items.length === 0 && (
        <div className="text-center py-24 text-slate-400">
          <div className="flex justify-center mb-4">
            <InboxIcon size={48} className="text-slate-200" />
          </div>
          <p className="font-medium">Chưa có cuộc gọi nào được phân tích</p>
          <Link href="/" className="mt-3 inline-flex items-center gap-1 text-blue-600 hover:underline text-sm">
            Upload ngay <ArrowRightIcon size={13} />
          </Link>
        </div>
      )}

      {/* Table */}
      {items.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                {[
                  "Thời gian", "Call ID",
                  "Case Type", "Kết quả", "Tiêu cực", "Điểm QA", "",
                ].map((h) => (
                  <th
                    key={h}
                    className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => {
                const scoreRaw = getTotalScore(item.CriteriaScores);
                const score    = scoreRaw !== null ? scoreRaw.toFixed(1) : null;
                const isPending = pendingDelete === item._id;

                return (
                  <tr key={item._id} className="hover:bg-slate-50 transition-colors group">
                    {/* Thời gian */}
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <ClockIcon size={13} className="text-slate-300 flex-shrink-0" />
                        {item.created_at ? new Date(item.created_at).toLocaleString("vi-VN") : "—"}
                      </div>
                    </td>

                    {/* Call ID */}
                    <td className="px-4 py-3 font-mono text-xs text-slate-700">
                      {item.call_id || item._id}
                    </td>



                    {/* Case Type */}
                    <td className="px-4 py-3 text-slate-700">{item.CaseType || "—"}</td>

                    {/* Resolved */}
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold ${
                        item.Resolved === "YES"  ? "bg-green-100 text-green-700" :
                        item.Resolved === "NO"   ? "bg-red-100   text-red-700"   :
                                                   "bg-yellow-100 text-yellow-700"
                      }`}>
                        {item.Resolved === "YES"
                          ? <CheckCircleIcon size={11} />
                          : item.Resolved === "NO"
                          ? <XCircleIcon size={11} />
                          : <AlertTriangleIcon size={11} />
                        }
                        {item.Resolved || "—"}
                      </span>
                    </td>

                    {/* Tiêu cực */}
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold ${
                        item.IsNegative === "FALSE" ? "bg-green-100 text-green-700" :
                        item.IsNegative === "TRUE"  ? "bg-red-100   text-red-700"   :
                                                      "bg-yellow-100 text-yellow-700"
                      }`}>
                        {item.IsNegative === "FALSE"
                          ? <CheckCircleIcon size={11} />
                          : <AlertTriangleIcon size={11} />
                        }
                        {item.IsNegative === "FALSE" ? "Không" : item.IsNegative === "TRUE" ? "Có" : "Xem xét"}
                      </span>
                    </td>

                    {/* Score */}
                    <td className="px-4 py-3">
                      {score !== null ? (
                        <span className={`font-bold tabular-nums ${
                          parseFloat(score) >= 8 ? "text-green-600" :
                          parseFloat(score) >= 6 ? "text-yellow-600" : "text-red-600"
                        }`}>
                          {score}
                          <span className="text-slate-300 font-normal">/10</span>
                        </span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/history/${item._id}`}
                          className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs font-medium whitespace-nowrap transition-colors"
                        >
                          Xem / Sửa
                          <ArrowRightIcon size={12} />
                        </Link>

                        {!isPending ? (
                          <button
                            id={`btn-delete-${item._id}`}
                            onClick={() => setPendingDelete(item._id)}
                            className="p-1 rounded text-slate-300 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100"
                            title="Xóa"
                          >
                            <Trash2Icon size={14} />
                          </button>
                        ) : (
                          <span className="flex items-center gap-1">
                            <button
                              id={`btn-confirm-delete-${item._id}`}
                              onClick={() => handleDelete(item._id)}
                              disabled={deleting}
                              className="text-xs px-2 py-0.5 rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
                            >
                              {deleting ? "…" : "Xóa"}
                            </button>
                            <button
                              onClick={() => setPendingDelete(null)}
                              className="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
                            >
                              Huỷ
                            </button>
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
