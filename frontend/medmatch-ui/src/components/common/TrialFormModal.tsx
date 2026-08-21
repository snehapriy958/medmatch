import { useEffect, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "./Modal";
import type { TrialResponse } from "../../types/trial";

const trialFormSchema = z.object({
  title: z.string().min(1, "Required").max(500),
  brief_summary: z.string().max(5000).optional().or(z.literal("")),
  condition: z.string().max(255).optional().or(z.literal("")),
  phase: z.string().max(100).optional().or(z.literal("")),
  status: z.string().max(100).optional().or(z.literal("")),
});

export type TrialFormValues = z.infer<typeof trialFormSchema>;

const emptyDefaults: TrialFormValues = {
  title: "",
  brief_summary: "",
  condition: "",
  phase: "",
  status: "",
};

interface TrialFormModalProps {
  isOpen: boolean;
  mode: "create" | "edit";
  trial?: TrialResponse | null;
  isSubmitting: boolean;
  errorMessage?: string | null;
  onClose: () => void;
  onSubmit: (values: TrialFormValues) => void;
}

export default function TrialFormModal({
  isOpen,
  mode,
  trial,
  isSubmitting,
  errorMessage,
  onClose,
  onSubmit,
}: TrialFormModalProps) {
  const isEdit = mode === "edit";

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TrialFormValues>({
    resolver: zodResolver(trialFormSchema),
    defaultValues: emptyDefaults,
  });

  useEffect(() => {
    if (isEdit && trial) {
      reset({
        title: trial.title,
        brief_summary: trial.brief_summary ?? "",
        condition: trial.condition ?? "",
        phase: trial.phase ?? "",
        status: trial.status ?? "",
      });
    } else if (!isEdit) {
      reset(emptyDefaults);
    }
  }, [isEdit, trial, isOpen, reset]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Trial" : "Add Trial"}
      widthClassName="max-w-2xl"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Field
          id="trial-title"
          label="Title"
          error={errors.title?.message}
        >
          <input
            id="trial-title"
            {...register("title")}
            className={inputClass}
            placeholder="e.g. Phase II Study of ..."
          />
        </Field>

        <Field
          id="trial-brief-summary"
          label="Brief summary (optional)"
          error={errors.brief_summary?.message}
        >
          <textarea
            id="trial-brief-summary"
            {...register("brief_summary")}
            rows={4}
            className={inputClass}
          />
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            id="trial-condition"
            label="Condition (optional)"
            error={errors.condition?.message}
          >
            <input
              id="trial-condition"
              {...register("condition")}
              className={inputClass}
            />
          </Field>

          <Field
            id="trial-phase"
            label="Phase (optional)"
            error={errors.phase?.message}
          >
            <input
              id="trial-phase"
              {...register("phase")}
              className={inputClass}
              placeholder="e.g. Phase 2"
            />
          </Field>
        </div>

        <Field
          id="trial-status"
          label="Status (optional)"
          error={errors.status?.message}
        >
          <input
            id="trial-status"
            {...register("status")}
            className={inputClass}
            placeholder="e.g. Recruiting"
          />
        </Field>

        {errorMessage && (
          <p className="text-sm text-status-down">{errorMessage}</p>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt disabled:opacity-60"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark disabled:opacity-60"
          >
            {isSubmitting
              ? "Saving..."
              : isEdit
                ? "Save changes"
                : "Add trial"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

const inputClass =
  "w-full rounded-lg border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary";

function Field({
  id,
  label,
  error,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1 block text-sm font-medium text-text"
      >
        {label}
      </label>

      {children}

      {error && (
        <p className="mt-1 text-xs text-status-down">{error}</p>
      )}
    </div>
  );
}