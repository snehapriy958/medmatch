import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  hint?: string;
}

export default function StatCard({ label, value, icon, hint }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm text-text-muted">{label}</p>
        {icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-bg text-primary">
            {icon}
          </div>
        )}
      </div>
      <p className="mt-2 text-2xl font-semibold text-text">{value}</p>
      {hint && <p className="mt-1 text-xs text-text-muted">{hint}</p>}
    </div>
  );
}
