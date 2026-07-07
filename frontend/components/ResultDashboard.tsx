import {
  TagIcon,
  CheckCircleIcon,
  XCircleIcon,
  AlertTriangleIcon,
  TrophyIcon,
  BarChartIcon,
  FileTextIcon,
  MessageSquareIcon,
  UserIcon,
  HeadphonesIcon,
} from "@/components/Icons";

type Score     = { Communication: number; Attitude: number; DataCollection: number; ProblemSolving: number };
type Violation = { ViolationCode: string; Description: string; Deduction: number; CriterionId: string; Evidence: { Speaker: string; Text: string }[] };
type Turn      = { Speaker: string; Text: string };
type Props     = { data: Record<string, unknown> };

function asStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map(String).filter(Boolean);
  }
  if (typeof value === "string") {
    return value.trim() ? [value] : [];
  }
  return [];
}

export default function ResultDashboard({ data }: Props) {
  const scores     = (data.CriteriaScores as Score) || {};
  const violations = (data.Violations as Violation[]) || [];
  const transcript = (data.Transcript as Turn[]) || [];
  const negativeReasonCodes = asStringArray(data.NegativeReasonCode);

  const total = (
    (scores.Communication  || 0) * 0.2 +
    (scores.Attitude       || 0) * 0.3 +
    (scores.DataCollection || 0) * 0.1 +
    (scores.ProblemSolving || 0) * 0.4
  ).toFixed(1);

  const resolved   = data.Resolved   as string;
  const isNegative = data.IsNegative as string;

  return (
    <div className="space-y-6">

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          Icon={TagIcon}
          label="Case Type"
          value={String(data.CaseType || "—")}
          variant="blue"
        />
        <StatCard
          Icon={resolved === "YES" ? CheckCircleIcon : resolved === "NO" ? XCircleIcon : AlertTriangleIcon}
          label="Kết quả"
          value={resolved || "—"}
          variant={resolved === "YES" ? "green" : resolved === "NO" ? "red" : "yellow"}
        />
        <StatCard
          Icon={isNegative === "FALSE" ? CheckCircleIcon : AlertTriangleIcon}
          label="Tiêu cực"
          value={isNegative === "FALSE" ? "Không" : isNegative === "TRUE" ? "Có" : "Xem xét"}
          variant={isNegative === "FALSE" ? "green" : isNegative === "TRUE" ? "red" : "yellow"}
        />
        <StatCard
          Icon={TrophyIcon}
          label="Điểm QA"
          value={`${total}/10`}
          variant={parseFloat(total) >= 8 ? "green" : parseFloat(total) >= 6 ? "yellow" : "red"}
        />
      </div>

      <div className="grid md:grid-cols-2 gap-6">

        {/* Điểm chi tiết */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-800 mb-5 flex items-center gap-2">
            <BarChartIcon size={16} className="text-slate-500" />
            Điểm QA chi tiết
          </h3>
          <div className="space-y-4">
            {[
              { label: "Giao tiếp",          key: "Communication"  as keyof Score, weight: "20%" },
              { label: "Thái độ",            key: "Attitude"       as keyof Score, weight: "30%" },
              { label: "Thu thập dữ liệu",   key: "DataCollection" as keyof Score, weight: "10%" },
              { label: "Giải quyết vấn đề",  key: "ProblemSolving" as keyof Score, weight: "40%" },
            ].map(({ label, key, weight }) => {
              const val = scores[key] ?? 0;
              const pct = val * 10;
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="text-slate-600">
                      {label} <span className="text-slate-400 text-xs">({weight})</span>
                    </span>
                    <span className="font-semibold text-slate-800">{val}/10</span>
                  </div>
                  <div className="bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-700 ${
                        pct >= 70 ? "bg-green-500" : pct >= 50 ? "bg-yellow-400" : "bg-red-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tóm tắt */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <FileTextIcon size={16} className="text-slate-500" />
            Tóm tắt nội dung
          </h3>
          <p className="text-slate-600 leading-relaxed text-sm">
            {String(data.Summary) || "Không có tóm tắt."}
          </p>

          {negativeReasonCodes.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <p className="text-xs font-semibold text-red-600 mb-2">Mã tiêu cực</p>
              <div className="flex flex-wrap gap-1.5">
                {negativeReasonCodes.map((code) => (
                  <span key={code} className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-mono">
                    {code}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Transcript */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <MessageSquareIcon size={16} className="text-slate-500" />
          Transcript cuộc gọi
        </h3>
        <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
          {transcript.length === 0 && (
            <p className="text-slate-400 text-sm">Không có transcript.</p>
          )}
          {transcript.map((turn, i) => (
            <div key={i} className={`flex gap-3 ${turn.Speaker === "agent" ? "" : "flex-row-reverse"}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                turn.Speaker === "agent"
                  ? "bg-blue-100 text-blue-600"
                  : "bg-slate-100 text-slate-500"
              }`}>
                {turn.Speaker === "agent"
                  ? <HeadphonesIcon size={15} />
                  : <UserIcon size={15} />
                }
              </div>
              <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm ${
                turn.Speaker === "agent"
                  ? "bg-blue-50 text-blue-900 rounded-tl-none"
                  : "bg-slate-100 text-slate-800 rounded-tr-none"
              }`}>
                <p className="text-xs opacity-50 mb-1 capitalize">{turn.Speaker}</p>
                <p className="leading-relaxed">{turn.Text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Vi phạm */}
      {violations.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <AlertTriangleIcon size={16} className="text-red-500" />
            Vi phạm <span className="text-red-500">({violations.length})</span>
          </h3>
          <div className="space-y-3">
            {violations.map((v, i) => (
              <div key={i} className="rounded-xl border border-red-100 bg-red-50 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs bg-red-200 text-red-800 px-2 py-0.5 rounded">
                        {v.ViolationCode}
                      </span>
                      <span className="text-xs text-slate-500">{v.CriterionId}</span>
                    </div>
                    <p className="text-sm text-slate-700">{v.Description}</p>
                    {v.Evidence?.length > 0 && (
                      <div className="mt-2 pl-3 border-l-2 border-red-200">
                        {v.Evidence.map((e, j) => (
                          <p key={j} className="text-xs text-slate-500 italic">
                            <span className="font-medium not-italic text-slate-600">{e.Speaker}:</span> &ldquo;{e.Text}&rdquo;
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className="text-red-600 font-bold text-sm whitespace-nowrap flex-shrink-0">
                    -{v.Deduction} điểm
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── StatCard ──────────────────────────────────────────────────────────────────

type Variant = "blue" | "green" | "red" | "yellow";

const variantStyles: Record<Variant, { card: string; icon: string }> = {
  blue:   { card: "bg-blue-50   border-blue-200",   icon: "text-blue-600"   },
  green:  { card: "bg-green-50  border-green-200",  icon: "text-green-600"  },
  red:    { card: "bg-red-50    border-red-200",     icon: "text-red-600"    },
  yellow: { card: "bg-yellow-50 border-yellow-200", icon: "text-yellow-600" },
};

function StatCard({
  Icon, label, value, variant,
}: {
  Icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  value: string;
  variant: Variant;
}) {
  const s = variantStyles[variant];
  return (
    <div className={`rounded-2xl border p-4 ${s.card}`}>
      <div className={`mb-2 ${s.icon}`}>
        <Icon size={20} />
      </div>
      <p className="text-xs text-slate-500 mb-0.5">{label}</p>
      <p className="font-bold text-lg leading-tight text-slate-800">{value}</p>
    </div>
  );
}
