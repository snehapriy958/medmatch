import type { ReactNode } from "react";

// Shared styling + small building blocks used by the patient Add/Edit form.
// Kept local to the patient form (not shared with TrialFormModal) so this
// redesign can't affect unrelated forms.

export const inputClass =
  "w-full rounded-lg border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary";

export const textareaClass = `${inputClass} resize-y`;

export function SectionHeading({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-3">
      <h3 className="text-sm font-semibold text-text">{title}</h3>
      {description && (
        <p className="mt-0.5 text-xs text-text-muted">{description}</p>
      )}
    </div>
  );
}

export function Field({
  id,
  label,
  error,
  required,
  helperText,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  required?: boolean;
  helperText?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1 block text-sm font-medium text-text"
      >
        {label}
        {required && (
          <span className="ml-0.5 text-status-down" aria-hidden="true">
            *
          </span>
        )}
      </label>

      {children}

      {helperText && !error && (
        <p className="mt-1 text-xs text-text-muted">{helperText}</p>
      )}

      {error && (
        <p
          className="mt-1 text-xs text-status-down"
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
}
