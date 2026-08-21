import type { ReactNode } from "react";

interface TableCardProps {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export default function TableCard({ title, action, children, className = "" }: TableCardProps) {
  return (
    <div className={`overflow-hidden rounded-2xl border border-border bg-surface shadow-sm ${className}`}>
      <div className="flex items-center justify-between border-b border-border p-5">
        <h2 className="text-sm font-semibold text-text">{title}</h2>
        {action}
      </div>
      <div className="overflow-x-auto">{children}</div>
    </div>
  );
}
