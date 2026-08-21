import { Calendar, ListChecks } from "lucide-react";

import Modal from "./Modal";

import type {
  TrialResponse,
  CriterionResponse,
} from "../../types/trial";

interface TrialDetailModalProps {
  isOpen: boolean;
  trial: TrialResponse | null;
  onClose: () => void;
  onEdit?: () => void;
}

export default function TrialDetailModal({
  isOpen,
  trial,
  onClose,
  onEdit,
}: TrialDetailModalProps) {
  if (!trial) {
    return null;
  }

  /*
   * Group criteria by the actual criteria_type value stored
   * by the backend.
   *
   * We intentionally do not assume that the backend only uses
   * "inclusion" or "exclusion".
   */
  const grouped = trial.criteria.reduce<
    Record<string, CriterionResponse[]>
  >((acc, criterion) => {
    const key =
      criterion.criteria_type || "Uncategorized";

    if (!acc[key]) {
      acc[key] = [];
    }

    acc[key].push(criterion);

    return acc;
  }, {});

  const groupEntries = Object.entries(grouped);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={trial.title}
      widthClassName="max-w-2xl"
    >
      <div className="space-y-6">
        {/* Trial metadata */}
        <div className="flex flex-wrap items-center gap-2">
          {trial.status && (
            <span className="rounded-full bg-primary-bg px-3 py-1 text-xs font-medium text-primary-dark">
              {trial.status}
            </span>
          )}

          {trial.phase && (
            <span className="rounded-full bg-surface-alt px-3 py-1 text-xs font-medium text-text-muted">
              {trial.phase}
            </span>
          )}

          {trial.condition && (
            <span className="rounded-full bg-surface-alt px-3 py-1 text-xs font-medium text-text-muted">
              {trial.condition}
            </span>
          )}
        </div>

        {/* Brief summary */}
        {trial.brief_summary && (
          <div>
            <p className="mb-1 text-xs font-medium text-text-muted">
              Brief Summary
            </p>

            <p className="text-sm text-text">
              {trial.brief_summary}
            </p>
          </div>
        )}

        {/* Dates */}
        <div className="flex items-center gap-2 border-t border-border pt-4 text-sm text-text-muted">
          <Calendar size={14} />

          <span>
            Added{" "}
            {new Date(
              trial.created_at
            ).toLocaleDateString()}
            {" · "}
            Updated{" "}
            {new Date(
              trial.updated_at
            ).toLocaleDateString()}
          </span>
        </div>

        {/* Eligibility criteria */}
        <div className="border-t border-border pt-4">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text">
            <ListChecks size={16} />

            Eligibility Criteria (
            {trial.criteria.length})
          </h3>

          {trial.criteria.length === 0 && (
            <p className="text-sm text-text-muted">
              No criteria recorded for this trial yet.
            </p>
          )}

          {groupEntries.length > 0 && (
            <div className="space-y-4">
              {groupEntries.map(
                ([type, items]) => (
                  <div key={type}>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
                      {type}
                    </p>

                    <ul className="space-y-2">
                      {items.map((criterion) => (
                        <li
                          key={criterion.id}
                          className="rounded-lg bg-surface-alt p-3 text-sm text-text"
                        >
                          {criterion.description}
                        </li>
                      ))}
                    </ul>
                  </div>
                )
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 border-t border-border pt-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt"
          >
            Close
          </button>

          {onEdit && (
            <button
              type="button"
              onClick={onEdit}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
            >
              Edit trial
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}