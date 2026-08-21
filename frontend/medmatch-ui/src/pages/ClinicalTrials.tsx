import { useEffect, useState } from "react";
import axios from "axios";
import {
  FlaskConical,
  ListChecks,
  FileText,
  Plus,
  Upload,
  Eye,
  Pencil,
  Trash2,
  AlertCircle,
} from "lucide-react";

import {
  listTrials,
  getTrial,
  createTrial,
  updateTrial,
  deleteTrial,
} from "../api/trialApi";

import { useAuth } from "../context/AuthContext";

import {
  canCreateTrial,
  canUploadTrial,
  canEditTrial,
  canDeleteTrial,
} from "../auth/permissions";

import StatCard from "../components/common/StatCard";
import TableCard from "../components/common/TableCard";
import ConfirmDialog from "../components/common/ConfirmDialog";

import TrialFormModal, {
  type TrialFormValues,
} from "../components/common/TrialFormModal";

import TrialDetailModal from "../components/common/TrialDetailModal";
import TrialUploadModal from "../components/common/TrialUploadModal";

import type {
  TrialResponse,
  TrialCreate,
  TrialUpdate,
} from "../types/trial";

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

    if (err.response?.status === 404) {
      return "Trial not found. It may have been removed.";
    }

    if (err.response?.status === 415) {
      return "Only PDF files are accepted.";
    }

    if (err.response?.status === 401) {
      return "Your session has expired. Please log in again.";
    }
  }

  return fallback;
}

export default function ClinicalTrials() {
  const { user } = useAuth();

  const [trials, setTrials] = useState<TrialResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] =
    useState<"create" | "edit">("create");

  const [formSubmitting, setFormSubmitting] =
    useState(false);

  const [formError, setFormError] =
    useState<string | null>(null);

  const [selectedTrial, setSelectedTrial] =
    useState<TrialResponse | null>(null);

  const [detailOpen, setDetailOpen] =
    useState(false);

  const [uploadOpen, setUploadOpen] =
    useState(false);

  const [deleteTarget, setDeleteTarget] =
    useState<TrialResponse | null>(null);

  const [isDeleting, setIsDeleting] =
    useState(false);

  const [deleteError, setDeleteError] =
    useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Permissions
  // ---------------------------------------------------------------------------

  const canCreate = user
    ? canCreateTrial(user.role)
    : false;

  const canUpload = user
    ? canUploadTrial(user.role)
    : false;

  const canEdit = user
    ? canEditTrial(user.role)
    : false;

  const canDelete = user
    ? canDeleteTrial(user.role)
    : false;

  // ---------------------------------------------------------------------------
  // Load trials
  // ---------------------------------------------------------------------------

  async function fetchTrials() {
    setIsLoading(true);
    setLoadError(null);

    try {
      const data = await listTrials();
      setTrials(data);
    } catch (err) {
      setLoadError(
        extractErrorMessage(
          err,
          "Could not load trials."
        )
      );
    } finally {
      setIsLoading(false);
    }
  }

  // Initial page load
  useEffect(() => {
    let cancelled = false;

    async function loadInitialTrials() {
      setIsLoading(true);
      setLoadError(null);

      try {
        const data = await listTrials();

        if (!cancelled) {
          setTrials(data);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            extractErrorMessage(
              err,
              "Could not load trials."
            )
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadInitialTrials();

    return () => {
      cancelled = true;
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Create / Edit
  // ---------------------------------------------------------------------------

  function openCreateForm() {
    if (!canCreate) {
      return;
    }

    setFormMode("create");
    setSelectedTrial(null);
    setFormError(null);
    setFormOpen(true);
  }

  function openEditForm(trial: TrialResponse) {
    if (!canEdit) {
      return;
    }

    setSelectedTrial(trial);
    setFormMode("edit");
    setFormError(null);
    setFormOpen(true);
  }

  async function handleFormSubmit(
    values: TrialFormValues
  ) {
    setFormSubmitting(true);
    setFormError(null);

    try {
      if (formMode === "create") {
        if (!canCreate) {
          setFormError(
            "You don't have permission to create trials."
          );
          return;
        }

        const payload: TrialCreate = {
          title: values.title,
          brief_summary:
            values.brief_summary || undefined,
          condition:
            values.condition || undefined,
          phase:
            values.phase || undefined,
          status:
            values.status || undefined,
        };

        const created =
          await createTrial(payload);

        setTrials((prev) => [
          created,
          ...prev,
        ]);
      } else {
        if (!canEdit) {
          setFormError(
            "You don't have permission to edit trials."
          );
          return;
        }

        if (!selectedTrial) {
          return;
        }

        const payload: TrialUpdate = {
          title:
            values.title || undefined,
          brief_summary:
            values.brief_summary || undefined,
          condition:
            values.condition || undefined,
          phase:
            values.phase || undefined,
          status:
            values.status || undefined,
        };

        const updated =
          await updateTrial(
            selectedTrial.id,
            payload
          );

        setTrials((prev) =>
          prev.map((trial) =>
            trial.id === updated.id
              ? updated
              : trial
          )
        );

        setSelectedTrial(updated);
      }

      setFormOpen(false);
    } catch (err) {
      setFormError(
        extractErrorMessage(
          err,
          "Could not save trial."
        )
      );
    } finally {
      setFormSubmitting(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Detail
  // ---------------------------------------------------------------------------

  async function openDetail(
    trial: TrialResponse
  ) {
    setSelectedTrial(trial);
    setDetailOpen(true);

    try {
      const fresh =
        await getTrial(trial.id);

      setSelectedTrial(fresh);

      setTrials((prev) =>
        prev.map((item) =>
          item.id === fresh.id
            ? fresh
            : item
        )
      );
    } catch {
      // Keep displaying the trial already loaded from the list.
    }
  }

  // ---------------------------------------------------------------------------
  // Delete
  // ---------------------------------------------------------------------------

  function requestDelete(
    trial: TrialResponse
  ) {
    if (!canDelete) {
      return;
    }

    setDeleteError(null);
    setDeleteTarget(trial);
  }

  async function confirmDelete() {
    if (!canDelete) {
      return;
    }

    if (!deleteTarget) {
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deleteTrial(
        deleteTarget.id
      );

      setTrials((prev) =>
        prev.filter(
          (trial) =>
            trial.id !==
            deleteTarget.id
        )
      );

      setDeleteTarget(null);

      if (
        selectedTrial?.id ===
        deleteTarget.id
      ) {
        setDetailOpen(false);
        setSelectedTrial(null);
      }
    } catch (err) {
      setDeleteError(
        extractErrorMessage(
          err,
          "Could not delete trial."
        )
      );
    } finally {
      setIsDeleting(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Derived statistics
  // ---------------------------------------------------------------------------

  const totalTrials =
    trials.length;

  const trialsWithCriteria =
    trials.filter(
      (trial) =>
        trial.criteria.length > 0
    ).length;

  const totalCriteria =
    trials.reduce(
      (sum, trial) =>
        sum + trial.criteria.length,
      0
    );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">

      {/* Header */}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">
            Clinical Trials
          </h1>

          <p className="text-sm text-text-muted">
            Manage trials for your hospital
          </p>
        </div>

        {(canUpload || canCreate) && (
          <div className="flex gap-2">

            {canUpload && (
              <button
                type="button"
                onClick={() =>
                  setUploadOpen(true)
                }
                className="flex items-center justify-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt"
              >
                <Upload size={16} />
                Upload PDF
              </button>
            )}

            {canCreate && (
              <button
                type="button"
                onClick={openCreateForm}
                className="flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
              >
                <Plus size={16} />
                Add Trial
              </button>
            )}

          </div>
        )}
      </div>

      {/* Statistics */}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">

        <StatCard
          label="Total Trials"
          value={totalTrials}
          icon={
            <FlaskConical size={18} />
          }
        />

        <StatCard
          label="Trials With Criteria"
          value={trialsWithCriteria}
          icon={
            <ListChecks size={18} />
          }
        />

        <StatCard
          label="Total Criteria"
          value={totalCriteria}
          icon={
            <FileText size={18} />
          }
        />

      </div>

      {/* Loading */}

      {isLoading && (
        <div className="rounded-2xl border border-border bg-surface p-10 text-center text-sm text-text-muted shadow-sm">
          Loading trials...
        </div>
      )}

      {/* Error */}

      {!isLoading && loadError && (
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface p-10 text-sm text-status-down shadow-sm">
          <AlertCircle size={18} />
          {loadError}
        </div>
      )}

      {/* Empty state */}

      {!isLoading &&
        !loadError &&
        trials.length === 0 && (
          <div className="rounded-2xl border border-border bg-surface p-10 text-center shadow-sm">

            <p className="text-sm font-medium text-text">
              No trials yet
            </p>

            <p className="mt-1 text-sm text-text-muted">
              {canCreate || canUpload
                ? "Add a trial manually or upload a trial PDF to get started."
                : "There are currently no clinical trials available."}
            </p>

            {(canCreate ||
              canUpload) && (
              <div className="mt-4 flex justify-center gap-3">

                {canUpload && (
                  <button
                    type="button"
                    onClick={() =>
                      setUploadOpen(true)
                    }
                    className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt"
                  >
                    Upload PDF
                  </button>
                )}

                {canCreate && (
                  <button
                    type="button"
                    onClick={
                      openCreateForm
                    }
                    className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
                  >
                    Add Trial
                  </button>
                )}

              </div>
            )}

          </div>
        )}

      {/* Trial table */}

      {!isLoading &&
        !loadError &&
        trials.length > 0 && (
          <TableCard
            title={`All Trials (${totalTrials})`}
          >
            <table className="w-full min-w-[860px] text-left text-sm">

              <thead>
                <tr className="text-xs uppercase text-text-muted">

                  <th className="px-5 py-3">
                    Title
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
                    Criteria
                  </th>

                  <th className="px-5 py-3 text-right">
                    Actions
                  </th>

                </tr>
              </thead>

              <tbody>

                {trials.map(
                  (trial) => (
                    <tr
                      key={trial.id}
                      className="border-t border-border"
                    >

                      <td className="px-5 py-3 font-medium text-text">
                        {trial.title}
                      </td>

                      <td className="px-5 py-3 text-text-muted">
                        {trial.condition ??
                          "—"}
                      </td>

                      <td className="px-5 py-3 text-text-muted">
                        {trial.phase ??
                          "—"}
                      </td>

                      <td className="px-5 py-3">

                        {trial.status ? (
                          <span className="rounded-full bg-primary-bg px-2 py-0.5 text-xs font-medium text-primary-dark">
                            {trial.status}
                          </span>
                        ) : (
                          <span className="text-text-muted">
                            —
                          </span>
                        )}

                      </td>

                      <td className="px-5 py-3 text-text-muted">
                        {trial.criteria.length}
                      </td>

                      <td className="px-5 py-3">

                        <div className="flex justify-end gap-2">

                          <button
                            type="button"
                            onClick={() =>
                              openDetail(
                                trial
                              )
                            }
                            title="View"
                            aria-label={`View ${trial.title}`}
                            className="rounded-lg p-1.5 text-text-muted hover:bg-surface-alt hover:text-primary"
                          >
                            <Eye size={16} />
                          </button>

                          {canEdit && (
                            <button
                              type="button"
                              onClick={() =>
                                openEditForm(
                                  trial
                                )
                              }
                              title="Edit"
                              aria-label={`Edit ${trial.title}`}
                              className="rounded-lg p-1.5 text-text-muted hover:bg-surface-alt hover:text-primary"
                            >
                              <Pencil
                                size={16}
                              />
                            </button>
                          )}

                          {canDelete && (
                            <button
                              type="button"
                              onClick={() =>
                                requestDelete(
                                  trial
                                )
                              }
                              title="Delete"
                              aria-label={`Delete ${trial.title}`}
                              className="rounded-lg p-1.5 text-text-muted hover:bg-surface-alt hover:text-status-down"
                            >
                              <Trash2
                                size={16}
                              />
                            </button>
                          )}

                        </div>

                      </td>

                    </tr>
                  )
                )}

              </tbody>

            </table>
          </TableCard>
        )}

      {/* Modals */}

      {(canCreate ||
        canEdit) && (
        <TrialFormModal
          isOpen={formOpen}
          mode={formMode}
          trial={selectedTrial}
          isSubmitting={
            formSubmitting
          }
          errorMessage={formError}
          onClose={() =>
            setFormOpen(false)
          }
          onSubmit={
            handleFormSubmit
          }
        />
      )}

      <TrialDetailModal
        isOpen={detailOpen}
        trial={selectedTrial}
        onClose={() =>
          setDetailOpen(false)
        }
        onEdit={
          canEdit
            ? () => {
                if (
                  selectedTrial
                ) {
                  setDetailOpen(false);
                  openEditForm(
                    selectedTrial
                  );
                }
              }
            : undefined
        }
      />

      {canUpload && (
        <TrialUploadModal
          isOpen={uploadOpen}
          onClose={() =>
            setUploadOpen(false)
          }
          onQueued={
            fetchTrials
          }
        />
      )}

      {canDelete && (
        <ConfirmDialog
          isOpen={
            deleteTarget !== null
          }
          title="Delete trial"
          message={
            deleteTarget
              ? `This will permanently delete "${deleteTarget.title}". This action cannot be undone.${
                  deleteError
                    ? ` ${deleteError}`
                    : ""
                }`
              : ""
          }
          confirmLabel="Delete"
          isDanger
          isSubmitting={
            isDeleting
          }
          onConfirm={
            confirmDelete
          }
          onCancel={() =>
            setDeleteTarget(null)
          }
        />
      )}

    </div>
  );
}