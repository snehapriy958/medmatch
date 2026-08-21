import { useEffect, useState } from "react";
import axios from "axios";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Search,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from "lucide-react";

import {
  searchTrials,
  evaluateEligibility,
} from "../api/matchingApi";

import {
  listPatients,
  listPatientNotes,
} from "../api/patientApi";

import StatCard from "../components/common/StatCard";
import TableCard from "../components/common/TableCard";

import type {
  MatchingResponse,
  EligibilityResponse,
  EligibilityEvaluationResponse,
  EligibilityStatus,
} from "../types/matching";

import type {
  PatientResponse,
  PatientNote,
} from "../types/patient";

type Mode = "search" | "evaluate";

const queryFormSchema = z.object({
  patient_note: z
    .string()
    .min(20, "Must be at least 20 characters")
    .max(10000, "Must be at most 10,000 characters"),

  limit: z
    .string()
    .optional()
    .or(z.literal(""))
    .refine(
      (v) => !v || /^\d+$/.test(v),
      "Must be a whole number"
    )
    .refine(
      (v) => !v || (Number(v) >= 1 && Number(v) <= 100),
      "Must be between 1 and 100"
    ),
});

type QueryFormValues = z.infer<typeof queryFormSchema>;

function toApiLimit(limit?: string): number | undefined {
  return limit ? Number(limit) : undefined;
}

function extractErrorMessage(
  err: unknown,
  fallback: string
): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (err.response?.status === 403) {
      return "You don't have permission to perform this action.";
    }

    if (err.response?.status === 422) {
      return "The patient note doesn't meet the required format (20–10,000 characters).";
    }
  }

  return fallback;
}

const eligibilityStyles: Record<
  EligibilityStatus,
  {
    badge: string;
    icon: typeof CheckCircle2;
  }
> = {
  Eligible: {
    badge: "bg-primary-bg text-primary-dark",
    icon: CheckCircle2,
  },

  "Not Eligible": {
    badge: "bg-red-50 text-status-down",
    icon: XCircle,
  },

  "Possibly Eligible": {
    badge: "bg-amber-100 text-amber-700",
    icon: HelpCircle,
  },
};

export default function Matching() {
  const [mode, setMode] = useState<Mode>("search");

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [submitError, setSubmitError] =
    useState<string | null>(null);

  const [searchResult, setSearchResult] =
    useState<MatchingResponse | null>(null);

  const [evalResult, setEvalResult] =
    useState<EligibilityEvaluationResponse | null>(null);

  // =========================================================
  // PATIENT / NOTE SELECTION
  // =========================================================

  const [patients, setPatients] = useState<PatientResponse[]>([]);

  const [selectedPatientId, setSelectedPatientId] =
    useState("");

  const [patientNotes, setPatientNotes] =
    useState<PatientNote[]>([]);

  const [selectedNoteId, setSelectedNoteId] =
    useState("");

  const [loadingPatients, setLoadingPatients] =
    useState(false);

  const [loadingNotes, setLoadingNotes] =
    useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<QueryFormValues>({
    resolver: zodResolver(queryFormSchema),
    defaultValues: {
      patient_note: "",
      limit: "",
    },
  });

  // =========================================================
  // LOAD PATIENTS
  // =========================================================

  useEffect(() => {
    let cancelled = false;

    async function loadPatients() {
      try {
        setLoadingPatients(true);

        const response = await listPatients();

        if (!cancelled) {
          setPatients(response.patients);
        }
      } catch (error) {
        console.error(
          "Failed to load patients:",
          error
        );

        if (!cancelled) {
          setPatients([]);
        }
      } finally {
        if (!cancelled) {
          setLoadingPatients(false);
        }
      }
    }

    void loadPatients();

    return () => {
      cancelled = true;
    };
  }, []);

  // =========================================================
  // LOAD PATIENT NOTES
  // =========================================================

  useEffect(() => {
    if (!selectedPatientId) {
      return;
    }

    let cancelled = false;

    async function loadNotes() {
      try {
        setLoadingNotes(true);

        const notes = await listPatientNotes(
          selectedPatientId
        );

        if (!cancelled) {
          setPatientNotes(notes);

          if (notes.length > 0) {
            const latestNote = notes[0];

            setSelectedNoteId(latestNote.id);

            setValue(
              "patient_note",
              latestNote.note,
              {
                shouldValidate: true,
                shouldDirty: true,
              }
            );
          } else {
            setSelectedNoteId("");

            setValue(
              "patient_note",
              "",
              {
                shouldValidate: true,
              }
            );
          }
        }
      } catch (error) {
        console.error(
          "Failed to load patient notes:",
          error
        );

        if (!cancelled) {
          setPatientNotes([]);
          setSelectedNoteId("");

          setValue(
            "patient_note",
            "",
            {
              shouldValidate: false,
              shouldDirty: false,
            }
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingNotes(false);
        }
      }
    }

    void loadNotes();

    return () => {
      cancelled = true;
    };
  }, [selectedPatientId, setValue]);

  // =========================================================
  // MODE SWITCH
  // =========================================================

  function switchMode(next: Mode) {
    setMode(next);
    setSubmitError(null);
    setSearchResult(null);
    setEvalResult(null);
  }

  // =========================================================
  // PATIENT SELECTION
  // =========================================================

  function handlePatientChange(
    patientId: string
  ) {
    setSelectedPatientId(patientId);

    setSelectedNoteId("");
    setPatientNotes([]);

    setSubmitError(null);
    setSearchResult(null);
    setEvalResult(null);

    setValue(
      "patient_note",
      "",
      {
        shouldValidate: false,
        shouldDirty: false,
      }
    );
  }

  // =========================================================
  // NOTE SELECTION
  // =========================================================

  function handleNoteChange(
    noteId: string
  ) {
    setSelectedNoteId(noteId);

    const selectedNote = patientNotes.find(
      (note) => note.id === noteId
    );

    if (!selectedNote) {
      return;
    }

    setValue(
      "patient_note",
      selectedNote.note,
      {
        shouldValidate: true,
        shouldDirty: true,
      }
    );

    setSubmitError(null);
    setSearchResult(null);
    setEvalResult(null);
  }

  // =========================================================
  // SUBMIT
  // =========================================================

  async function onSubmit(
    values: QueryFormValues
  ) {
    setIsSubmitting(true);
    setSubmitError(null);
    setSearchResult(null);
    setEvalResult(null);

    const payload = {
      patient_note: values.patient_note,
      limit: toApiLimit(values.limit),
    };

    try {
      if (mode === "search") {
        const res = await searchTrials(payload);
        setSearchResult(res);
      } else {
        const res =
          await evaluateEligibility(payload);

        setEvalResult(res);
      }
    } catch (err) {
      const fallback =
        mode === "evaluate"
          ? "Could not evaluate eligibility. This can happen if the underlying LLM (Gemini) is rate-limited or its quota is exhausted."
          : "Could not search trials.";

      setSubmitError(
        extractErrorMessage(err, fallback)
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="text-xl font-semibold text-text">
          AI Matching
        </h1>

        <p className="text-sm text-text-muted">
          Search trial criteria by semantic similarity,
          or run a full Gemini-based eligibility
          evaluation.
        </p>
      </div>

      {/* Mode selector */}
      <div className="inline-flex rounded-lg border border-border bg-surface p-1">
        <button
          type="button"
          onClick={() => switchMode("search")}
          className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition ${
            mode === "search"
              ? "bg-primary text-white"
              : "text-text-muted hover:text-text"
          }`}
        >
          <Search size={16} />
          Search
        </button>

        <button
          type="button"
          onClick={() => switchMode("evaluate")}
          className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition ${
            mode === "evaluate"
              ? "bg-primary text-white"
              : "text-text-muted hover:text-text"
          }`}
        >
          <Sparkles size={16} />
          Evaluate
        </button>
      </div>

      {/* Input form */}
      <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4"
        >
          {/* =================================================
              PATIENT SELECTOR
              ================================================= */}

          <div>
            <label
              htmlFor="matching-patient"
              className="mb-1 block text-sm font-medium text-text"
            >
              Patient
            </label>

            <select
              id="matching-patient"
              value={selectedPatientId}
              onChange={(event) =>
                handlePatientChange(
                  event.target.value
                )
              }
              disabled={loadingPatients}
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-60"
            >
              <option value="">
                {loadingPatients
                  ? "Loading patients..."
                  : "Select a patient"}
              </option>

              {patients.map((patient) => (
                <option
                  key={patient.id}
                  value={patient.id}
                >
                  {patient.first_name}{" "}
                  {patient.last_name} —{" "}
                  {patient.mrn}
                </option>
              ))}
            </select>

            {!loadingPatients &&
              patients.length === 0 && (
                <p className="mt-1 text-xs text-text-muted">
                  No patients are available for your
                  hospital.
                </p>
              )}
          </div>

          {/* =================================================
              SAVED CLINICAL NOTE SELECTOR
              ================================================= */}

          {selectedPatientId && (
            <div>
              <label
                htmlFor="matching-patient-note-select"
                className="mb-1 block text-sm font-medium text-text"
              >
                Saved Clinical Note
              </label>

              <select
                id="matching-patient-note-select"
                value={selectedNoteId}
                onChange={(event) =>
                  handleNoteChange(
                    event.target.value
                  )
                }
                disabled={
                  loadingNotes ||
                  patientNotes.length === 0
                }
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-60"
              >
                <option value="">
                  {loadingNotes
                    ? "Loading clinical notes..."
                    : patientNotes.length === 0
                      ? "No clinical notes available"
                      : "Select a clinical note"}
                </option>

                {patientNotes.map((note) => (
                  <option
                    key={note.id}
                    value={note.id}
                  >
                    {new Date(
                      note.created_at
                    ).toLocaleString()}{" "}
                    —{" "}
                    {note.note.length > 80
                      ? `${note.note.slice(
                          0,
                          80
                        )}...`
                      : note.note}
                  </option>
                ))}
              </select>

              {patientNotes.length > 0 && (
                <p className="mt-1 text-xs text-text-muted">
                  Selecting a saved note loads it
                  into the editable patient note below.
                </p>
              )}
            </div>
          )}

          {/* =================================================
              PATIENT NOTE
              ================================================= */}

          <div>
            <label
              htmlFor="matching-patient-note"
              className="mb-1 block text-sm font-medium text-text"
            >
              Patient note
            </label>

            <textarea
              id="matching-patient-note"
              {...register("patient_note")}
              rows={5}
              placeholder="Select a patient and clinical note, or enter a clinical note manually. Example: 54-year-old male with Stage II colon cancer. Completed surgery. ECOG 0. No liver disease. Creatinine normal."
              className="w-full rounded-lg border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />

            {errors.patient_note && (
              <p className="mt-1 text-xs text-status-down">
                {errors.patient_note.message}
              </p>
            )}

            {selectedPatientId &&
              selectedNoteId && (
                <p className="mt-1 text-xs text-text-muted">
                  The note above was loaded from the
                  selected patient record. You can edit
                  it before running the AI matching.
                </p>
              )}
          </div>

          {/* =================================================
              RESULT LIMIT
              ================================================= */}

          <div className="max-w-xs">
            <label
              htmlFor="matching-limit"
              className="mb-1 block text-sm font-medium text-text"
            >
              Result limit (optional, 1–100)
            </label>

            <input
              id="matching-limit"
              type="text"
              inputMode="numeric"
              {...register("limit")}
              placeholder="Backend default"
              className="w-full rounded-lg border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />

            {errors.limit && (
              <p className="mt-1 text-xs text-status-down">
                {errors.limit.message}
              </p>
            )}
          </div>

          {/* =================================================
              SUBMIT
              ================================================= */}

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-white hover:bg-primary-dark disabled:opacity-60"
          >
            {mode === "search" ? (
              <Search size={16} />
            ) : (
              <Sparkles size={16} />
            )}

            {isSubmitting
              ? mode === "search"
                ? "Searching..."
                : "Evaluating..."
              : mode === "search"
                ? "Search trials"
                : "Evaluate eligibility"}
          </button>
        </form>
      </div>

      {/* Error */}
      {submitError && (
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface p-5 text-sm text-status-down shadow-sm">
          <AlertCircle size={18} />
          <span>{submitError}</span>
        </div>
      )}

      {/* Search results */}
      {mode === "search" && searchResult && (
        <SearchResults result={searchResult} />
      )}

      {/* Evaluation results */}
      {mode === "evaluate" && evalResult && (
        <EvaluationResults
          results={evalResult.results}
        />
      )}
    </div>
  );
}

/* =========================================================
   SEARCH RESULTS
   ========================================================= */

function SearchResults({
  result,
}: {
  result: MatchingResponse;
}) {
  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Total Matches"
          value={result.total_matches}
        />

        <StatCard
          label="Returned"
          value={result.returned_matches}
        />

        <StatCard
          label="Similarity Threshold"
          value={result.similarity_threshold.toFixed(2)}
          hint="Max cosine distance accepted"
        />
      </div>

      {/* No matches */}
      {result.matches.length === 0 ? (
        <div className="rounded-2xl border border-border bg-surface p-10 text-center shadow-sm">
          <p className="text-sm font-medium text-text">
            No matching criteria found
          </p>

          <p className="mt-1 text-sm text-text-muted">
            Try a broader patient note or a higher
            result limit.
          </p>
        </div>
      ) : (
        <TableCard
          title={`Matches (${result.matches.length})`}
        >
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead>
              <tr className="text-xs uppercase text-text-muted">
                <th className="px-5 py-3">
                  Trial
                </th>

                <th className="px-5 py-3">
                  Condition
                </th>

                <th className="px-5 py-3">
                  Phase
                </th>

                <th className="px-5 py-3">
                  Status
                </th>

                <th className="px-5 py-3">
                  Criteria Type
                </th>

                <th className="px-5 py-3">
                  Criterion
                </th>

                <th className="px-5 py-3">
                  Cosine Distance
                </th>
              </tr>
            </thead>

            <tbody>
              {result.matches.map((m) => (
                <tr
                  key={m.id}
                  className="border-t border-border align-top"
                >
                  <td className="px-5 py-3 font-medium text-text">
                    {m.title}
                  </td>

                  <td className="px-5 py-3 text-text-muted">
                    {m.condition ?? "—"}
                  </td>

                  <td className="px-5 py-3 text-text-muted">
                    {m.phase ?? "—"}
                  </td>

                  <td className="px-5 py-3 text-text-muted">
                    {m.status ?? "—"}
                  </td>

                  <td className="px-5 py-3 text-text-muted">
                    {m.criteria_type}
                  </td>

                  <td className="px-5 py-3 text-text-muted">
                    {m.description}
                  </td>

                  <td className="px-5 py-3 text-text-muted">
                    {m.distance.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
      )}
    </div>
  );
}

/* =========================================================
   EVALUATION RESULTS WRAPPER
   ========================================================= */

function EvaluationResults({
  results,
}: {
  results: EligibilityResponse[];
}) {
  if (results.length === 0) {
    return (
      <div className="rounded-2xl border border-border bg-surface p-10 text-center shadow-sm">
        <p className="text-sm font-medium text-text">
          No eligibility evaluation results were
          returned.
        </p>

        <p className="mt-1 text-sm text-text-muted">
          The backend completed the evaluation but
          returned no individual trial results.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overall evaluation summary */}
      <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-text">
              Eligibility Evaluation
            </h2>

            <p className="mt-1 text-sm text-text-muted">
              {results.length} trial
              {results.length === 1 ? "" : "s"}{" "}
              evaluated independently.
            </p>
          </div>

          <span className="rounded-full bg-primary-bg px-3 py-1 text-sm font-medium text-primary-dark">
            Evaluation complete
          </span>
        </div>
      </div>

      {/* Individual trial evaluations */}
      {results.map((result, index) => (
        <EvaluationResult
          key={`${index}-${result.trial_ids_evaluated.join(
            "-"
          )}`}
          result={result}
          resultNumber={index + 1}
        />
      ))}
    </div>
  );
}

/* =========================================================
   SINGLE ELIGIBILITY RESULT
   ========================================================= */

function EvaluationResult({
  result,
  resultNumber,
}: {
  result: EligibilityResponse;
  resultNumber: number;
}) {
  const style = eligibilityStyles[result.eligibility];

  const Icon = style.icon;

  return (
    <div className="space-y-4">
      {/* Result header */}
      <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-text">
            Trial Evaluation #{resultNumber}
          </h2>

          <span className="text-xs text-text-muted">
            {result.trial_ids_evaluated.length} trial
            {result.trial_ids_evaluated.length === 1
              ? ""
              : "s"}{" "}
            evaluated
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${style.badge}`}
          >
            <Icon size={16} />
            {result.eligibility}
          </span>

          <span className="text-sm text-text-muted">
            Confidence:{" "}
            {(result.confidence * 100).toFixed(0)}%
          </span>
        </div>

        <p className="mt-4 text-sm text-text">
          {result.summary}
        </p>
      </div>

      {/* Criteria */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <CriteriaList
          title="Matched Inclusion Criteria"
          items={result.matched_inclusion}
          tone="positive"
        />

        <CriteriaList
          title="Failed Inclusion Criteria"
          items={result.failed_inclusion}
          tone="negative"
        />

        <CriteriaList
          title="Satisfied Exclusion Criteria"
          items={result.satisfied_exclusion}
          tone="positive"
        />

        <CriteriaList
          title="Triggered Exclusion Criteria"
          items={result.triggered_exclusion}
          tone="negative"
        />
      </div>

      {/* Missing information */}
      <CriteriaList
        title="Missing Information"
        items={result.missing_information}
        tone="neutral"
      />

      {/* Recommendation */}
      <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-text">
          Recommendation
        </h3>

        <p className="text-sm text-text">
          {result.recommendation}
        </p>
      </div>

      {/* Reasoning */}
      <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-text">
          Reasoning
        </h3>

        <p className="whitespace-pre-wrap text-sm text-text-muted">
          {result.reasoning}
        </p>
      </div>
    </div>
  );
}

/* =========================================================
   CRITERIA LIST
   ========================================================= */

function CriteriaList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "negative" | "neutral";
}) {
  const dotColor =
    tone === "positive"
      ? "bg-status-up"
      : tone === "negative"
        ? "bg-status-down"
        : "bg-status-unknown";

  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold text-text">
        {title}
      </h3>

      {items.length === 0 ? (
        <p className="text-sm text-text-muted">
          None reported.
        </p>
      ) : (
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li
              key={index}
              className="flex items-start gap-2 text-sm text-text"
            >
              <span
                className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${dotColor}`}
              />

              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}