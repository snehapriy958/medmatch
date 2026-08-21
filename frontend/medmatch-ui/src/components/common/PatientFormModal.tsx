import { useEffect, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "./Modal";
import type { PatientResponse } from "../../types/patient";

// Status is a free-text field in the backend schema (no enum was provided in the
// OpenAPI spec). These options are a UI convenience based on common clinical-trial
// statuses — not a backend-enforced enum. Update this list if the backend defines one.
const STATUS_OPTIONS = [
  "ACTIVE",
  "SCREENING",
  "ENROLLED",
  "INACTIVE",
  "WITHDRAWN",
];

const baseFields = {
  first_name: z.string().min(1, "Required").max(100),

  last_name: z.string().min(1, "Required").max(100),

  age: z
    .string()
    .min(1, "Required")
    .refine(
      (v) => /^\d+$/.test(v.trim()),
      "Must be a whole number",
    )
    .refine(
      (v) => Number(v) >= 0 && Number(v) <= 150,
      "Must be between 0 and 150",
    ),

  gender: z.string().min(1, "Required").max(20),

  diagnosis: z.string().min(1, "Required").max(255),

  cancer_type: z
    .string()
    .max(255)
    .optional()
    .or(z.literal("")),

  stage: z
    .string()
    .max(50)
    .optional()
    .or(z.literal("")),

  phone: z
    .string()
    .max(30)
    .optional()
    .or(z.literal("")),

  email: z
    .string()
    .email("Invalid email")
    .optional()
    .or(z.literal("")),
};

const createSchema = z.object({
  mrn: z.string().min(1, "Required").max(50),
  ...baseFields,
});

const editSchema = z.object({
  ...baseFields,
  status: z.string().optional(),
});

export type CreateFormValues = z.infer<typeof createSchema>;
export type EditFormValues = z.infer<typeof editSchema>;

interface PatientFormModalProps {
  isOpen: boolean;
  mode: "create" | "edit";
  patient?: PatientResponse | null;
  isSubmitting: boolean;
  errorMessage?: string | null;
  onClose: () => void;
  onSubmitCreate: (values: CreateFormValues) => void;
  onSubmitEdit: (values: EditFormValues) => void;
}

function toOptionalString(
  value: string | null | undefined,
): string {
  return value ?? "";
}

export default function PatientFormModal({
  isOpen,
  mode,
  patient,
  isSubmitting,
  errorMessage,
  onClose,
  onSubmitCreate,
  onSubmitEdit,
}: PatientFormModalProps) {
  const isEdit = mode === "edit";

  const createForm = useForm<CreateFormValues>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      mrn: "",
      first_name: "",
      last_name: "",
      age: "",
      gender: "",
      diagnosis: "",
      cancer_type: "",
      stage: "",
      phone: "",
      email: "",
    },
  });

  const editForm = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      age: "",
      gender: "",
      diagnosis: "",
      cancer_type: "",
      stage: "",
      phone: "",
      email: "",
      status: "",
    },
  });

  useEffect(() => {
    if (isEdit && patient) {
      editForm.reset({
        first_name: patient.first_name,
        last_name: patient.last_name,
        age: String(patient.age),
        gender: patient.gender,
        diagnosis: patient.diagnosis,
        cancer_type: toOptionalString(patient.cancer_type),
        stage: toOptionalString(patient.stage),
        phone: toOptionalString(patient.phone),
        email: toOptionalString(patient.email),
        status: patient.status,
      });
    }

    if (!isEdit) {
      createForm.reset();
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEdit, patient, isOpen]);

  function handleValid(
    values: CreateFormValues | EditFormValues,
  ) {
    if (isEdit) {
      onSubmitEdit(values as EditFormValues);
    } else {
      onSubmitCreate(values as CreateFormValues);
    }
  }

  type CommonField =
    | "first_name"
    | "last_name"
    | "age"
    | "gender"
    | "diagnosis"
    | "cancer_type"
    | "stage"
    | "phone"
    | "email";

  function registerCommon(name: CommonField) {
    return isEdit
      ? editForm.register(name)
      : createForm.register(name);
  }

  const errors = (
    isEdit
      ? editForm.formState.errors
      : createForm.formState.errors
  ) as Record<
    string,
    { message?: string } | undefined
  >;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Patient" : "Add Patient"}
      widthClassName="max-w-2xl"
    >
      <form
        onSubmit={
          isEdit
            ? editForm.handleSubmit(handleValid)
            : createForm.handleSubmit(handleValid)
        }
        className="space-y-4"
      >
        {!isEdit && (
          <Field
            id="patient-mrn"
            label="MRN"
            error={errors.mrn?.message}
          >
            <input
              id="patient-mrn"
              {...createForm.register("mrn")}
              className={inputClass}
              placeholder="MRN-00123"
              autoComplete="off"
            />
          </Field>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            id="patient-first-name"
            label="First name"
            error={errors.first_name?.message}
          >
            <input
              id="patient-first-name"
              {...registerCommon("first_name")}
              className={inputClass}
              autoComplete="given-name"
            />
          </Field>

          <Field
            id="patient-last-name"
            label="Last name"
            error={errors.last_name?.message}
          >
            <input
              id="patient-last-name"
              {...registerCommon("last_name")}
              className={inputClass}
              autoComplete="family-name"
            />
          </Field>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            id="patient-age"
            label="Age"
            error={errors.age?.message}
          >
            <input
              id="patient-age"
              type="text"
              inputMode="numeric"
              {...registerCommon("age")}
              className={inputClass}
              autoComplete="off"
            />
          </Field>

          <Field
            id="patient-gender"
            label="Gender"
            error={errors.gender?.message}
          >
            <input
              id="patient-gender"
              {...registerCommon("gender")}
              className={inputClass}
              placeholder="e.g. Female"
              autoComplete="sex"
            />
          </Field>
        </div>

        <Field
          id="patient-diagnosis"
          label="Diagnosis"
          error={errors.diagnosis?.message}
        >
          <input
            id="patient-diagnosis"
            {...registerCommon("diagnosis")}
            className={inputClass}
            autoComplete="off"
          />
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            id="patient-cancer-type"
            label="Cancer type (optional)"
            error={errors.cancer_type?.message}
          >
            <input
              id="patient-cancer-type"
              {...registerCommon("cancer_type")}
              className={inputClass}
              autoComplete="off"
            />
          </Field>

          <Field
            id="patient-stage"
            label="Stage (optional)"
            error={errors.stage?.message}
          >
            <input
              id="patient-stage"
              {...registerCommon("stage")}
              className={inputClass}
              autoComplete="off"
            />
          </Field>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            id="patient-phone"
            label="Phone (optional)"
            error={errors.phone?.message}
          >
            <input
              id="patient-phone"
              {...registerCommon("phone")}
              className={inputClass}
              autoComplete="tel"
            />
          </Field>

          <Field
            id="patient-email"
            label="Email (optional)"
            error={errors.email?.message}
          >
            <input
              id="patient-email"
              {...registerCommon("email")}
              className={inputClass}
              autoComplete="email"
            />
          </Field>
        </div>

        {isEdit && (
          <Field
            id="patient-status"
            label="Status"
          >
            <select
              id="patient-status"
              {...editForm.register("status")}
              className={inputClass}
              autoComplete="off"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </Field>
        )}

        {errorMessage && (
          <p className="text-sm text-status-down">
            {errorMessage}
          </p>
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
                : "Add patient"}
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
        <p className="mt-1 text-xs text-status-down">
          {error}
        </p>
      )}
    </div>
  );
}