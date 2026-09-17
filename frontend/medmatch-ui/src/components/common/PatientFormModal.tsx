import { useEffect, useMemo } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Modal from "./Modal";
import { Field, SectionHeading, inputClass, textareaClass } from "./PatientFormFields";
import type { PatientResponse } from "../../types/patient";

// ----------------------------------------------------------------------
// Backend contract notes (see services/ai-service/app/schemas/patient.py
// and app/schemas/patient_note.py — this frontend must not drift from it):
//
// - Patient fields supported by the API: mrn, first_name, last_name, age,
//   gender, diagnosis, cancer_type, stage, phone, email, status.
// - "status" is a free-text field in the backend schema (no enum defined),
//   so STATUS_OPTIONS below is a UI convenience, not a backend-enforced list.
// - There is no dedicated cancer "grade" or "biomarkers" field, and no
//   medications/allergies/pregnancy-status fields anywhere in the backend.
//   Those are NOT sent to the API from this form — see the helper text on
//   the Clinical Notes field, which IS backend-supported via the separate
//   POST /patients/{id}/notes endpoint (PatientNoteCreate: 10-10000 chars).
// ----------------------------------------------------------------------

const STATUS_OPTIONS = [
  "ACTIVE",
  "SCREENING",
  "ENROLLED",
  "INACTIVE",
  "WITHDRAWN",
];

const GENDER_OPTIONS = ["Female", "Male", "Other", "Prefer not to say"];

const ONCOLOGY_KEYWORDS =
  /cancer|carcinoma|tumou?r|oncolog|lymphoma|leukemia|leukaemia|melanoma|sarcoma|malignan/i;

function looksOncology(diagnosis: string, cancerType: string): boolean {
  return (
    ONCOLOGY_KEYWORDS.test(diagnosis) || ONCOLOGY_KEYWORDS.test(cancerType)
  );
}

const baseFields = {
  first_name: z.string().min(1, "First name is required.").max(100),

  last_name: z.string().min(1, "Last name is required.").max(100),

  age: z
    .string()
    .min(1, "Age is required.")
    .refine(
      (v) => /^\d+$/.test(v.trim()),
      "Enter a whole number (e.g. 45)."
    )
    .refine(
      (v) => Number(v) >= 0 && Number(v) <= 150,
      "Age must be between 0 and 150."
    ),

  gender: z.string().min(1, "Select a gender.").max(20),

  diagnosis: z
    .string()
    .min(1, "Primary diagnosis is required.")
    .max(
      255,
      "Diagnosis is too long for this field (255 character max). Keep this short — put detailed history, labs, or medications in Clinical Notes below."
    ),

  clinical_notes: z
    .string()
    .max(10000, "Clinical note is too long (10,000 character max).")
    .optional()
    .or(z.literal(""))
    .refine(
      (v) => !v || v.trim().length >= 10,
      "Clinical note must be at least 10 characters, or left blank."
    ),

  is_oncology: z.boolean().optional(),

  cancer_type: z
    .string()
    .max(255, "Cancer type is too long (255 character max).")
    .optional()
    .or(z.literal("")),

  stage: z
    .string()
    .max(50, "Stage is too long (50 character max).")
    .optional()
    .or(z.literal("")),

  phone: z
    .string()
    .max(30, "Phone number is too long (30 character max).")
    .optional()
    .or(z.literal("")),

  email: z
    .string()
    .email("Enter a valid email address.")
    .optional()
    .or(z.literal("")),
};

const createSchema = z.object({
  mrn: z.string().min(1, "MRN is required.").max(50),
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

function toOptionalString(value: string | null | undefined): string {
  return value ?? "";
}

const emptyCreateDefaults: CreateFormValues = {
  mrn: "",
  first_name: "",
  last_name: "",
  age: "",
  gender: "",
  diagnosis: "",
  clinical_notes: "",
  is_oncology: false,
  cancer_type: "",
  stage: "",
  phone: "",
  email: "",
};

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
    defaultValues: emptyCreateDefaults,
  });

  const editForm = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      age: "",
      gender: "",
      diagnosis: "",
      clinical_notes: "",
      is_oncology: false,
      cancer_type: "",
      stage: "",
      phone: "",
      email: "",
      status: "",
    },
  });

  useEffect(() => {
    if (isEdit && patient) {
      const hadCancerInfo = Boolean(patient.cancer_type || patient.stage);

      editForm.reset({
        first_name: patient.first_name,
        last_name: patient.last_name,
        age: String(patient.age),
        gender: patient.gender,
        diagnosis: patient.diagnosis,
        clinical_notes: "",
        is_oncology:
          hadCancerInfo ||
          looksOncology(patient.diagnosis, patient.cancer_type ?? ""),
        cancer_type: toOptionalString(patient.cancer_type),
        stage: toOptionalString(patient.stage),
        phone: toOptionalString(patient.phone),
        email: toOptionalString(patient.email),
        status: patient.status,
      });
    }

    if (!isEdit) {
      createForm.reset(emptyCreateDefaults);
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEdit, patient, isOpen]);

  function handleValid(values: CreateFormValues | EditFormValues) {
    if (isEdit) {
      onSubmitEdit(values as EditFormValues);
    } else {
      onSubmitCreate(values as CreateFormValues);
    }
  }

  const errors = (
    isEdit ? editForm.formState.errors : createForm.formState.errors
  ) as Record<string, { message?: string } | undefined>;

  // react-hook-form's generics don't unify cleanly across two differently
  // shaped forms (create vs edit), so watch/register are read from each
  // form separately and merged into plain values below rather than
  // holding a single "active form" reference typed as a union.
  const createWatchedDiagnosis = useWatch({
    control: createForm.control,
    name: "diagnosis",
  });

  const createWatchedCancerType = useWatch({
    control: createForm.control,
    name: "cancer_type",
  });

  const createWatchedIsOncology = useWatch({
    control: createForm.control,
    name: "is_oncology",
  });

  const createWatchedGender = useWatch({
    control: createForm.control,
    name: "gender",
  });

  const editWatchedDiagnosis = useWatch({
    control: editForm.control,
    name: "diagnosis",
  });

  const editWatchedCancerType = useWatch({
    control: editForm.control,
    name: "cancer_type",
  });

  const editWatchedIsOncology = useWatch({
    control: editForm.control,
    name: "is_oncology",
  });

  const editWatchedGender = useWatch({
    control: editForm.control,
    name: "gender",
  });

  const watchedDiagnosis =
    (isEdit ? editWatchedDiagnosis : createWatchedDiagnosis) ?? "";
  const watchedCancerType =
    (isEdit ? editWatchedCancerType : createWatchedCancerType) ?? "";
  const watchedIsOncology =
    (isEdit ? editWatchedIsOncology : createWatchedIsOncology) ?? false;
  const watchedGender =
    (isEdit ? editWatchedGender : createWatchedGender) ?? "";

  const detectedOncology = looksOncology(watchedDiagnosis, watchedCancerType);
  const showCancerSection = watchedIsOncology || detectedOncology;

  const genderOptions = useMemo(() => {
    if (watchedGender && !GENDER_OPTIONS.includes(watchedGender)) {
      return [...GENDER_OPTIONS, watchedGender];
    }
    return GENDER_OPTIONS;
  }, [watchedGender]);

  type CommonField =
    | "first_name"
    | "last_name"
    | "age"
    | "gender"
    | "diagnosis"
    | "clinical_notes"
    | "cancer_type"
    | "stage"
    | "phone"
    | "email";

  function registerCommon(name: CommonField) {
    return isEdit ? editForm.register(name) : createForm.register(name);
  }

  const formId = isEdit ? "edit-patient-form" : "add-patient-form";

  const footer = (
    <div className="flex justify-end gap-3">
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
        form={formId}
        disabled={isSubmitting}
        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark disabled:opacity-60"
      >
        {isSubmitting
          ? "Saving..."
          : isEdit
            ? "Update Patient"
            : "Save Patient"}
      </button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Patient" : "Add Patient"}
      widthClassName="max-w-2xl"
      footer={footer}
    >
      <form
        id={formId}
        onSubmit={
          isEdit
            ? editForm.handleSubmit(handleValid)
            : createForm.handleSubmit(handleValid)
        }
        className="space-y-6"
      >
        {/* ---------------------------------------------------------- */}
        {/* Section 1 — Patient Information                            */}
        {/* ---------------------------------------------------------- */}
        <section>
          <SectionHeading title="Patient Information" />

          <div className="space-y-4">
            {!isEdit && (
              <Field
                id="patient-mrn"
                label="MRN"
                required
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
                required
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
                required
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
                required
                error={errors.age?.message}
              >
                <input
                  id="patient-age"
                  type="text"
                  inputMode="numeric"
                  {...registerCommon("age")}
                  className={inputClass}
                  placeholder="e.g. 45"
                  autoComplete="off"
                />
              </Field>

              <Field
                id="patient-gender"
                label="Gender"
                required
                error={errors.gender?.message}
              >
                <select
                  id="patient-gender"
                  {...registerCommon("gender")}
                  className={inputClass}
                  autoComplete="sex"
                >
                  <option value="">Select...</option>
                  {genderOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </Field>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field
                id="patient-phone"
                label="Phone"
                error={errors.phone?.message}
                helperText="Optional"
              >
                <input
                  id="patient-phone"
                  type="tel"
                  {...registerCommon("phone")}
                  className={inputClass}
                  placeholder="e.g. 9000000001"
                  autoComplete="tel"
                />
              </Field>

              <Field
                id="patient-email"
                label="Email"
                error={errors.email?.message}
                helperText="Optional"
              >
                <input
                  id="patient-email"
                  type="email"
                  {...registerCommon("email")}
                  className={inputClass}
                  placeholder="name@example.com"
                  autoComplete="email"
                />
              </Field>
            </div>
          </div>
        </section>

        {/* ---------------------------------------------------------- */}
        {/* Section 2 — Clinical Information                           */}
        {/* ---------------------------------------------------------- */}
        <section className="border-t border-border pt-6">
          <SectionHeading
            title="Clinical Information"
            description="Keep the diagnosis short. Detailed history, labs, medications, allergies, or pregnancy status go in Clinical Notes."
          />

          <div className="space-y-4">
            <Field
              id="patient-diagnosis"
              label="Primary diagnosis"
              required
              error={errors.diagnosis?.message}
              helperText='Short label, e.g. "Type 2 Diabetes Mellitus" (max 255 characters).'
            >
              <input
                id="patient-diagnosis"
                {...registerCommon("diagnosis")}
                className={inputClass}
                maxLength={255}
                autoComplete="off"
              />
            </Field>

            <Field
              id="patient-clinical-notes"
              label="Clinical notes / medical history"
              error={errors.clinical_notes?.message}
              helperText="Optional. Saved as a dated clinical note on the patient record (min 10 characters if provided). Not tracked as separate fields yet, so include current medications, allergies, or pregnancy status here if relevant."
            >
              <textarea
                id="patient-clinical-notes"
                {...registerCommon("clinical_notes")}
                className={textareaClass}
                rows={5}
                maxLength={10000}
                placeholder="e.g. HbA1c 8.4%, BMI 31, on Metformin 1000mg twice daily, no known cardiovascular disease..."
              />
            </Field>
          </div>
        </section>

        {/* ---------------------------------------------------------- */}
        {/* Section 3 — Cancer Information (conditional)                */}
        {/* ---------------------------------------------------------- */}
        <section className="border-t border-border pt-6">
          <div className="mb-3 flex items-start justify-between gap-4">
            <SectionHeading
              title="Cancer Information"
              description="Only shown for oncology patients. Grade and biomarkers aren't tracked in MedMatch yet."
            />

            <label className="flex shrink-0 items-center gap-2 text-xs font-medium text-text-muted">
              <input
                type="checkbox"
                {...(isEdit
                  ? editForm.register("is_oncology")
                  : createForm.register("is_oncology"))}
                className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
              />
              Oncology patient
            </label>
          </div>

          {showCancerSection ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field
                id="patient-cancer-type"
                label="Cancer type"
                error={errors.cancer_type?.message}
                helperText="Optional"
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
                label="Stage"
                error={errors.stage?.message}
                helperText="Optional"
              >
                <input
                  id="patient-stage"
                  {...registerCommon("stage")}
                  className={inputClass}
                  placeholder="e.g. Stage II"
                  autoComplete="off"
                />
              </Field>
            </div>
          ) : (
            <p className="text-xs text-text-muted">
              Hidden for non-oncology patients. Check "Oncology patient"
              above if this section applies.
            </p>
          )}
        </section>

        {/* ---------------------------------------------------------- */}
        {/* Section 4 — Record Status (edit only)                      */}
        {/* ---------------------------------------------------------- */}
        {isEdit && (
          <section className="border-t border-border pt-6">
            <SectionHeading title="Record Status" />

            <Field id="patient-status" label="Status">
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
          </section>
        )}

        {errorMessage && (
          <p className="text-sm text-status-down" role="alert">
            {errorMessage}
          </p>
        )}
      </form>
    </Modal>
  );
}
