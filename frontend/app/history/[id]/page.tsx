"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import ResultDashboard from "@/components/ResultDashboard";
import {
  ArrowLeftIcon,
  EditIcon,
  SaveIcon,
  Trash2Icon,
  CheckCircleIcon,
  XCircleIcon,
} from "@/components/Icons";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const EDITABLE_FIELDS = [
  { key: "CaseType",                  label: "Case Type",             type: "text" },
  { key: "Resolved",                  label: "Kết quả xử lý",         type: "select", options: ["YES", "NO", "PARTIAL"] },
  { key: "IsNegative",                label: "Tiêu cực",              type: "select", options: ["TRUE", "FALSE", "UNCERTAIN"] },
  { key: "NegativeReasonCode",        label: "Mã lý do tiêu cực",     type: "text" },
  { key: "NegativeReasonDescription", label: "Mô tả lý do tiêu cực",  type: "textarea" },
  { key: "Summary",                   label: "Tóm tắt",               type: "textarea" },
] as const;

type EditableKey = typeof EDITABLE_FIELDS[number]["key"];

export default function HistoryDetailPage() {
  const { id }  = useParams<{ id: string }>();
  const router  = useRouter();

  const [data,       setData]       = useState<Record<string, unknown> | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [notFound,   setNotFound]   = useState(false);

  const [editing,    setEditing]    = useState(false);
  const [form,       setForm]       = useState<Partial<Record<EditableKey, string>>>({});
  const [saving,     setSaving]     = useState(false);
  const [saveMsg,    setSaveMsg]    = useState<{ ok: boolean; text: string } | null>(null);

  const [confirmDel, setConfirmDel] = useState(false);
  const [deleting,   setDeleting]   = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/conversations/${id}`)
      .then((r) => {
        if (r.status === 404) { setNotFound(true); setLoading(false); return null; }
        return r.json();
      })
      .then((d) => {
        if (d) {
          setData(d);
          const initial: Partial<Record<EditableKey, string>> = {};
          EDITABLE_FIELDS.forEach(({ key }) => { initial[key] = (d[key] as string) ?? ""; });
          setForm(initial);
          setLoading(false);
        }
      })
      .catch(() => setLoading(false));
  }, [id]);

  async function handleSave() {
    setSaving(true);
    setSaveMsg(null);
    const body: Record<string, string> = {};
    EDITABLE_FIELDS.forEach(({ key }) => {
      if (form[key] !== undefined && form[key] !== "") body[key] = form[key]!;
    });
    try {
      const res = await fetch(`${API_URL}/conversations/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json();
        setSaveMsg({ ok: false, text: err.detail ?? res.statusText });
      } else {
        const updated = await res.json();
        setData(updated);
        setEditing(false);
        setSaveMsg({ ok: true, text: "Cập nhật thành công" });
        setTimeout(() => setSaveMsg(null), 3000);
      }
    } catch {
      setSaveMsg({ ok: false, text: "Không thể kết nối đến server." });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      const res = await fetch(`${API_URL}/conversations/${id}`, { method: "DELETE" });
      if (!res.ok) {
        const err = await res.json();
        alert(`Xóa thất bại: ${err.detail ?? res.statusText}`);
        setDeleting(false);
        setConfirmDel(false);
      } else {
        router.push("/history");
      }
    } catch {
      alert("Không thể kết nối đến server.");
      setDeleting(false);
      setConfirmDel(false);
    }
  }

  return (
    <div>
      {/* Breadcrumb + action bar */}
      <div className="flex items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-2 text-sm">
          <Link
            href="/history"
            className="flex items-center gap-1 text-slate-500 hover:text-slate-800 transition-colors"
          >
            <ArrowLeftIcon size={14} />
            Lịch sử
          </Link>
          <span className="text-slate-300">/</span>
          <span className="font-mono text-slate-600 text-xs">{id}</span>
        </div>

        {data && (
          <div className="flex items-center gap-2">
            {!editing ? (
              <button
                id="btn-edit-conversation"
                onClick={() => { setEditing(true); setSaveMsg(null); }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                <EditIcon size={14} />
                Chỉnh sửa
              </button>
            ) : (
              <>
                <button
                  id="btn-save-conversation"
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  <SaveIcon size={14} />
                  {saving ? "Đang lưu…" : "Lưu"}
                </button>
                <button
                  id="btn-cancel-edit"
                  onClick={() => { setEditing(false); setSaveMsg(null); }}
                  className="px-3 py-1.5 text-sm rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
                >
                  Huỷ
                </button>
              </>
            )}

            {!confirmDel ? (
              <button
                id="btn-delete-conversation"
                onClick={() => setConfirmDel(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
              >
                <Trash2Icon size={14} />
                Xóa
              </button>
            ) : (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-1.5">
                <span className="text-xs text-red-600 font-medium">Xác nhận xóa?</span>
                <button
                  id="btn-confirm-delete"
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-2 py-0.5 text-xs rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                >
                  {deleting ? "Đang xóa…" : "Xóa"}
                </button>
                <button
                  id="btn-cancel-delete"
                  onClick={() => setConfirmDel(false)}
                  className="px-2 py-0.5 text-xs rounded bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
                >
                  Huỷ
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Toast */}
      {saveMsg && (
        <div className={`mb-4 flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border ${
          saveMsg.ok
            ? "bg-green-50 text-green-700 border-green-200"
            : "bg-red-50 text-red-700 border-red-200"
        }`}>
          {saveMsg.ok
            ? <CheckCircleIcon size={15} className="flex-shrink-0" />
            : <XCircleIcon size={15} className="flex-shrink-0" />
          }
          {saveMsg.text}
        </div>
      )}

      {/* Edit form */}
      {editing && data && (
        <div className="mb-6 bg-white border border-blue-200 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <EditIcon size={15} className="text-blue-600" />
            <h2 className="text-sm font-semibold text-blue-700">Chỉnh sửa kết quả phân tích</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {EDITABLE_FIELDS.map(({ key, label, type, ...rest }) => (
              <div key={key} className={type === "textarea" ? "md:col-span-2" : ""}>
                <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                  {label}
                </label>
                {type === "select" ? (
                  <select
                    id={`edit-${key}`}
                    value={form[key] ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white"
                  >
                    <option value="">— chọn —</option>
                    {("options" in rest ? (rest as { readonly options: readonly string[] }).options : []).map((o) => (
                      <option key={o} value={o}>{o}</option>
                    ))}
                  </select>
                ) : type === "textarea" ? (
                  <textarea
                    id={`edit-${key}`}
                    rows={3}
                    value={form[key] ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none"
                  />
                ) : (
                  <input
                    id={`edit-${key}`}
                    type="text"
                    value={form[key] ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {loading && <p className="text-slate-400 text-center py-20">Đang tải...</p>}
      {notFound && (
        <div className="text-center py-20 text-slate-400">
          <div className="flex justify-center mb-3">
            <SearchNotFoundIcon />
          </div>
          <p>Không tìm thấy cuộc gọi này</p>
        </div>
      )}
      {data && <ResultDashboard data={data} />}
    </div>
  );
}

function SearchNotFoundIcon() {
  return (
    <svg width={56} height={56} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.25} strokeLinecap="round" strokeLinejoin="round" className="text-slate-300">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}
