import { useEffect, useState } from "react";
import axios from "axios";
import {
  Users,
  FlaskConical,
  ListChecks,
  AlertCircle,
  AlertTriangle,
} from "lucide-react";

import { listPatients } from "../api/patientApi";
import { listTrials } from "../api/trialApi";
import StatCard from "../components/common/StatCard";

function extractErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (err.response?.status === 403) {
      return "You don't have permission to view this data.";
    }
  }

  return fallback;
}

function isWithinRange(
  isoDate: string,
  start: string,
  end: string
): boolean {
  const date = new Date(isoDate).getTime();

  if (start && date < new Date(start).getTime()) {
    return false;
  }

  // End date is inclusive through the end of that day.
  if (
    end &&
    date > new Date(end).getTime() + 24 * 60 * 60 * 1000 - 1
  ) {
    return false;
  }

  return true;
}

export default function Reports() {
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [patientDates, setPatientDates] = useState<string[]>([]);
  const [trialDates, setTrialDates] = useState<string[]>([]);

  const [trialsWithCriteria, setTrialsWithCriteria] = useState(0);
  const [totalTrials, setTotalTrials] = useState(0);
  const [totalPatients, setTotalPatients] = useState(0);

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  /*
   * rangeError is derived entirely from the selected dates.
   * It does not need its own state or useEffect.
   */
  const rangeError =
    startDate &&
    endDate &&
    new Date(startDate) > new Date(endDate)
      ? "Start date must be before end date."
      : null;

  /*
   * Fetch report source data.
   *
   * We intentionally do not call setIsLoading(true) or
   * setLoadError(null) synchronously from inside the effect.
   * The initial loading state is already true.
   */
  useEffect(() => {
    let cancelled = false;

    Promise.all([listPatients(), listTrials()])
      .then(([patientsRes, trials]) => {
        if (cancelled) {
          return;
        }

        setPatientDates(
          patientsRes.patients.map((patient) => patient.created_at)
        );

        setTotalPatients(patientsRes.patients.length);

        setTrialDates(
          trials.map((trial) => trial.created_at)
        );

        setTotalTrials(trials.length);

        setTrialsWithCriteria(
          trials.filter((trial) => trial.criteria.length > 0).length
        );

        setLoadError(null);
        setIsLoading(false);
      })
      .catch((err) => {
        if (cancelled) {
          return;
        }

        setLoadError(
          extractErrorMessage(
            err,
            "Could not load report data."
          )
        );

        setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const hasRange = Boolean(startDate || endDate);

  const patientsAdded = rangeError
    ? 0
    : patientDates.filter((date) =>
        isWithinRange(date, startDate, endDate)
      ).length;

  const trialsAdded = rangeError
    ? 0
    : trialDates.filter((date) =>
        isWithinRange(date, startDate, endDate)
      ).length;

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="text-xl font-semibold text-text">
          Reports
        </h1>

        <p className="text-sm text-text-muted">
          Activity summary for your hospital, derived from patient
          and trial records.
        </p>
      </div>

      {/* Date range */}
      <div className="flex flex-wrap items-end gap-4 rounded-2xl border border-border bg-surface p-5 shadow-sm">
        <div>
          <label
            htmlFor="reports-start-date"
            className="mb-1 block text-sm font-medium text-text"
          >
            Start date
          </label>

          <input
            id="reports-start-date"
            name="reports-start-date"
            type="date"
            value={startDate}
            onChange={(event) =>
              setStartDate(event.target.value)
            }
            className="rounded-lg border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div>
          <label
            htmlFor="reports-end-date"
            className="mb-1 block text-sm font-medium text-text"
          >
            End date
          </label>

          <input
            id="reports-end-date"
            name="reports-end-date"
            type="date"
            value={endDate}
            onChange={(event) =>
              setEndDate(event.target.value)
            }
            className="rounded-lg border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        {hasRange && (
          <button
            type="button"
            onClick={() => {
              setStartDate("");
              setEndDate("");
            }}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt"
          >
            Clear range
          </button>
        )}

        {rangeError && (
          <p className="flex items-center gap-2 text-sm text-status-down">
            <AlertCircle size={14} />
            {rangeError}
          </p>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="rounded-2xl border border-border bg-surface p-10 text-center text-sm text-text-muted shadow-sm">
          Loading report data...
        </div>
      )}

      {/* Error */}
      {!isLoading && loadError && (
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface p-10 text-sm text-status-down shadow-sm">
          <AlertCircle size={18} />
          {loadError}
        </div>
      )}

      {/* Report content */}
      {!isLoading && !loadError && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              label={
                hasRange
                  ? "Patients Added (range)"
                  : "Total Patients"
              }
              value={
                hasRange
                  ? patientsAdded
                  : totalPatients
              }
              icon={<Users size={18} />}
              hint={
                hasRange
                  ? undefined
                  : "No date range selected"
              }
            />

            <StatCard
              label={
                hasRange
                  ? "Trials Added (range)"
                  : "Total Trials"
              }
              value={
                hasRange
                  ? trialsAdded
                  : totalTrials
              }
              icon={<FlaskConical size={18} />}
              hint={
                hasRange
                  ? undefined
                  : "No date range selected"
              }
            />

            <StatCard
              label="Trials With Criteria"
              value={trialsWithCriteria}
              icon={<ListChecks size={18} />}
              hint="Current total, not date-filtered"
            />
          </div>

          {/* Honest backend gap notice */}
          <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800 shadow-sm">
            <AlertTriangle
              size={18}
              className="mt-0.5 shrink-0"
            />

            <div>
              <p className="font-medium">
                Eligibility evaluation metrics aren't available yet
              </p>

              <p className="mt-1 text-amber-700">
                <code className="rounded bg-amber-100 px-1 py-0.5">
                  /matching/evaluate
                </code>{" "}
                writes an{" "}
                <code className="rounded bg-amber-100 px-1 py-0.5">
                  ELIGIBILITY_EVALUATED
                </code>{" "}
                audit event, but the only retrieval endpoint currently
                confirmed is{" "}
                <code className="rounded bg-amber-100 px-1 py-0.5">
                  GET /audit-logs/user/&#123;userId&#125;
                </code>
                , which is scoped to a single user, not a hospital.
                A hospital-wide "evaluations run" metric needs either
                a hospital-scoped audit endpoint or a way to enumerate
                every user in the hospital — neither is confirmed yet.
                This card intentionally shows no number rather than
                guessing one.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}