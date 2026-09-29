import type { ReactNode } from "react";
import type { EvidenceType } from "../../types/evaluation";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  evidenceType?: EvidenceType;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

function getEvidenceBadge(evidence?: EvidenceType) {
  if (!evidence) return null;

  switch (evidence) {
    case "MEASURED":
      return (
        <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
          MEASURED
        </span>
      );
    case "OFFLINE EXPERIMENT":
      return (
        <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200">
          OFFLINE EXPERIMENT
        </span>
      );
    case "SYNTHETIC / DEVELOPMENT FIXTURE":
      return (
        <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 border border-amber-200">
          SYNTHETIC / DEV FIXTURE
        </span>
      );
    case "CONFIGURATION RISK ONLY":
      return (
        <span className="inline-flex items-center rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-semibold text-purple-700 border border-purple-200">
          CONFIG RISK ONLY
        </span>
      );
    case "NOT MEASURED":
      return (
        <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 border border-slate-300">
          NOT MEASURED
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center rounded-full bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-600 border border-slate-200">
          {evidence}
        </span>
      );
  }
}

export default function ChartCard({
  title,
  subtitle,
  evidenceType,
  action,
  children,
  className = "",
}: ChartCardProps) {
  return (
    <div
      className={`rounded-2xl border border-border bg-surface shadow-sm ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border p-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-base font-semibold text-text">{title}</h2>
            {getEvidenceBadge(evidenceType)}
          </div>
          {subtitle && (
            <p className="mt-1 text-xs text-text-muted">{subtitle}</p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}
