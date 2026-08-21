import {
  useCallback,
  useEffect,
  useState,
} from "react";
import axios from "axios";
import {
  Users,
  UserCheck,
  Sparkles,
  Plus,
  Eye,
  Pencil,
  Trash2,
  AlertCircle,
} from "lucide-react";

import {
  listPatients,
  getPatient,
  createPatient,
  updatePatient,
  deletePatient,
  addPatientNote,
  listPatientNotes,
} from "../api/patientApi";

import { useAuth } from "../context/AuthContext";

import StatCard from "../components/common/StatCard";
import TableCard from "../components/common/TableCard";
import ConfirmDialog from "../components/common/ConfirmDialog";
import PatientFormModal, {
  type CreateFormValues,
  type EditFormValues,
} from "../components/common/PatientFormModal";
import PatientDetailModal from "../components/common/PatientDetailModal";

import { toApiAge } from "../utils/patientFormUtils";

import type {
  PatientResponse,
  PatientCreate,
  PatientUpdate,
  PatientNote,
} from "../types/patient";

const ADMIN_ROLES = [
  "SYSTEM_ADMIN",
  "HOSPITAL_ADMIN",
];

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
      return "Patient not found. It may have been removed.";
    }
  }

  return fallback;
}

export default function Patients() {
  const { user } = useAuth();

  const canDelete = user
    ? ADMIN_ROLES.includes(user.role)
    : false;

  const [patients, setPatients] =
    useState<PatientResponse[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [loadError, setLoadError] =
    useState<string | null>(null);

  // ------------------------------------------------------------
  // Create / Edit state
  // ------------------------------------------------------------

  const [formOpen, setFormOpen] =
    useState(false);

  const [formMode, setFormMode] =
    useState<"create" | "edit">("create");

  const [formSubmitting, setFormSubmitting] =
    useState(false);

  const [formError, setFormError] =
    useState<string | null>(null);

  // ------------------------------------------------------------
  // Patient detail state
  // ------------------------------------------------------------

  const [selectedPatient, setSelectedPatient] =
    useState<PatientResponse | null>(null);

  const [detailOpen, setDetailOpen] =
    useState(false);

  // ------------------------------------------------------------
  // Clinical notes state
  // ------------------------------------------------------------

  const [notes, setNotes] =
    useState<PatientNote[]>([]);

  const [notesLoading, setNotesLoading] =
    useState(false);

  const [notesError, setNotesError] =
    useState<string | null>(null);

  const [isAddingNote, setIsAddingNote] =
    useState(false);

  const [addNoteError, setAddNoteError] =
    useState<string | null>(null);

  // ------------------------------------------------------------
  // Delete state
  // ------------------------------------------------------------

  const [deleteTarget, setDeleteTarget] =
    useState<PatientResponse | null>(null);

  const [isDeleting, setIsDeleting] =
    useState(false);

  const [deleteError, setDeleteError] =
    useState<string | null>(null);

  // ------------------------------------------------------------
  // Load patients
  // ------------------------------------------------------------

  useEffect(() => {
    let cancelled = false;

    async function loadPatients() {
      try {
        const res = await listPatients();

        if (cancelled) {
          return;
        }

        setPatients(res.patients);
        setLoadError(null);
      } catch (err) {
        if (cancelled) {
          return;
        }

        setLoadError(
          extractErrorMessage(
            err,
            "Could not load patients."
          )
        );
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadPatients();

    return () => {
      cancelled = true;
    };
  }, []);

  // ------------------------------------------------------------
  // Create / Edit
  // ------------------------------------------------------------

  function openCreateForm() {
    setFormMode("create");
    setSelectedPatient(null);
    setFormError(null);
    setFormOpen(true);
  }

  function openEditForm(
    patient: PatientResponse
  ) {
    setSelectedPatient(patient);
    setFormMode("edit");
    setFormError(null);
    setFormOpen(true);
  }

  async function handleCreateSubmit(
    values: CreateFormValues
  ) {
    setFormSubmitting(true);
    setFormError(null);

    try {
      const cleaned: PatientCreate = {
        mrn: values.mrn,
        first_name: values.first_name,
        last_name: values.last_name,
        age: toApiAge(values.age),
        gender: values.gender,
        diagnosis: values.diagnosis,
        cancer_type:
          values.cancer_type || undefined,
        stage:
          values.stage || undefined,
        phone:
          values.phone || undefined,
        email:
          values.email || undefined,
      };

      const created =
        await createPatient(cleaned);

      setPatients((prev) => [
        created,
        ...prev,
      ]);

      setFormOpen(false);
    } catch (err) {
      setFormError(
        extractErrorMessage(
          err,
          "Could not create patient."
        )
      );
    } finally {
      setFormSubmitting(false);
    }
  }

  async function handleEditSubmit(
    values: EditFormValues
  ) {
    if (!selectedPatient) {
      return;
    }

    setFormSubmitting(true);
    setFormError(null);

    try {
      const cleaned: PatientUpdate = {
        first_name: values.first_name,
        last_name: values.last_name,
        age: toApiAge(values.age),
        gender: values.gender,
        diagnosis: values.diagnosis,
        status: values.status,
        cancer_type:
          values.cancer_type || undefined,
        stage:
          values.stage || undefined,
        phone:
          values.phone || undefined,
        email:
          values.email || undefined,
      };

      const updated =
        await updatePatient(
          selectedPatient.id,
          cleaned
        );

      setPatients((prev) =>
        prev.map((p) =>
          p.id === updated.id
            ? updated
            : p
        )
      );

      setSelectedPatient((current) =>
        current?.id === updated.id
          ? updated
          : current
      );

      setFormOpen(false);
    } catch (err) {
      setFormError(
        extractErrorMessage(
          err,
          "Could not update patient."
        )
      );
    } finally {
      setFormSubmitting(false);
    }
  }

  // ------------------------------------------------------------
  // Patient details + notes
  // ------------------------------------------------------------

  const openDetail = useCallback(
    async (patient: PatientResponse) => {
      setSelectedPatient(patient);
      setDetailOpen(true);

      setNotes([]);
      setNotesError(null);
      setNotesLoading(true);
      setAddNoteError(null);

      try {
        const [
          fresh,
          patientNotes,
        ] = await Promise.all([
          getPatient(patient.id),
          listPatientNotes(patient.id),
        ]);

        setSelectedPatient(fresh);

        setPatients((prev) =>
          prev.map((p) =>
            p.id === fresh.id
              ? fresh
              : p
          )
        );

        setNotes(patientNotes);
      } catch (err) {
        setNotesError(
          extractErrorMessage(
            err,
            "Could not load patient details or clinical notes."
          )
        );
      } finally {
        setNotesLoading(false);
      }
    },
    []
  );

  // ------------------------------------------------------------
  // Open patient selected from global search
  //
  // Navbar stores the selected patient ID in:
  // sessionStorage:
  // "medmatch_selected_patient"
  //
  // This effect reads that ID after the Patients page
  // has loaded and opens the existing detail modal.
  // ------------------------------------------------------------

  useEffect(() => {
    const selectedPatientId =
      sessionStorage.getItem(
        "medmatch_selected_patient"
      );

    if (
      !selectedPatientId ||
      isLoading ||
      patients.length === 0
    ) {
      return;
    }

    const patient = patients.find(
      (p) =>
        p.id === selectedPatientId
    );

    if (!patient) {
      sessionStorage.removeItem(
        "medmatch_selected_patient"
      );

      return;
    }

    // Consume the selection immediately so
    // the modal does not reopen after later
    // patient state updates.
    sessionStorage.removeItem(
      "medmatch_selected_patient"
    );

    // Wait until the current effect/render cycle
    // completes before changing modal state.
    const timer = window.setTimeout(() => {
      void openDetail(patient);
    }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    isLoading,
    patients,
    openDetail,
  ]);

  // ------------------------------------------------------------
  // Add clinical note
  // ------------------------------------------------------------

  async function handleAddNote(
    note: string
  ) {
    if (!selectedPatient) {
      return;
    }

    setIsAddingNote(true);
    setAddNoteError(null);

    try {
      const created =
        await addPatientNote(
          selectedPatient.id,
          { note }
        );

      setNotes((prev) => [
        created,
        ...prev,
      ]);
    } catch (err) {
      setAddNoteError(
        extractErrorMessage(
          err,
          "Could not add note."
        )
      );
    } finally {
      setIsAddingNote(false);
    }
  }

  // ------------------------------------------------------------
  // Delete
  // ------------------------------------------------------------

  function requestDelete(
    patient: PatientResponse
  ) {
    setDeleteError(null);
    setDeleteTarget(patient);
  }

  async function confirmDelete() {
    if (!deleteTarget) {
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deletePatient(
        deleteTarget.id
      );

      setPatients((prev) =>
        prev.filter(
          (p) =>
            p.id !== deleteTarget.id
        )
      );

      setDeleteTarget(null);

      if (
        selectedPatient?.id ===
        deleteTarget.id
      ) {
        setDetailOpen(false);
        setSelectedPatient(null);
      }
    } catch (err) {
      setDeleteError(
        extractErrorMessage(
          err,
          "Could not delete patient."
        )
      );
    } finally {
      setIsDeleting(false);
    }
  }

  // ------------------------------------------------------------
  // Derived statistics
  // ------------------------------------------------------------

  const totalPatients =
    patients.length;

  const activeCount =
    patients.filter(
      (p) =>
        p.status === "ACTIVE"
    ).length;

  const totalMatches =
    patients.reduce(
      (sum, p) =>
        sum + p.match_count,
      0
    );

  // ------------------------------------------------------------
  // Render
  // ------------------------------------------------------------

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">
            Patients
          </h1>

          <p className="text-sm text-text-muted">
            Manage patient records for
            your hospital
          </p>
        </div>

        <button
          type="button"
          onClick={openCreateForm}
          className="flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
        >
          <Plus size={16} />
          Add Patient
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Total Patients"
          value={totalPatients}
          icon={<Users size={18} />}
        />

        <StatCard
          label="Active Patients"
          value={activeCount}
          icon={<UserCheck size={18} />}
        />

        <StatCard
          label="AI Matches Generated"
          value={totalMatches}
          icon={<Sparkles size={18} />}
        />
      </div>

      {isLoading && (
        <div className="rounded-2xl border border-border bg-surface p-10 text-center text-sm text-text-muted shadow-sm">
          Loading patients...
        </div>
      )}

      {!isLoading &&
        loadError && (
          <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface p-10 text-sm text-status-down shadow-sm">
            <AlertCircle size={18} />
            {loadError}
          </div>
        )}

      {!isLoading &&
        !loadError &&
        patients.length === 0 && (
          <div className="rounded-2xl border border-border bg-surface p-10 text-center shadow-sm">
            <p className="text-sm font-medium text-text">
              No patients yet
            </p>

            <p className="mt-1 text-sm text-text-muted">
              Add your first patient to
              start generating AI trial
              matches.
            </p>

            <button
              type="button"
              onClick={openCreateForm}
              className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
            >
              Add Patient
            </button>
          </div>
        )}

      {!isLoading &&
        !loadError &&
        patients.length > 0 && (
          <TableCard
            title={`All Patients (${totalPatients})`}
          >
            <table className="w-full min-w-[860px] text-left text-sm">
              <thead>
                <tr className="text-xs uppercase text-text-muted">
                  <th className="px-5 py-3">
                    MRN
                  </th>

                  <th className="px-5 py-3">
                    Patient
                  </th>

                  <th className="px-5 py-3">
                    Age/Gender
                  </th>

                  <th className="px-5 py-3">
                    Diagnosis
                  </th>

                  <th className="px-5 py-3">
                    Stage
                  </th>

                  <th className="px-5 py-3">
                    Status
                  </th>

                  <th className="px-5 py-3">
                    Potential Matches
                  </th>

                  <th className="px-5 py-3 text-right">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody>
                {patients.map((p) => (
                  <tr
                    key={p.id}
                    className="border-t border-border"
                  >
                    <td className="px-5 py-3 text-text-muted">
                      {p.mrn}
                    </td>

                    <td className="px-5 py-3 font-medium text-text">
                      {p.first_name}{" "}
                      {p.last_name}
                    </td>

                    <td className="px-5 py-3 text-text-muted">
                      {p.age} /{" "}
                      {p.gender}
                    </td>

                    <td className="px-5 py-3 text-text-muted">
                      {p.diagnosis}
                    </td>

                    <td className="px-5 py-3 text-text-muted">
                      {p.stage ?? "—"}
                    </td>

                    <td className="px-5 py-3">
                      <span className="rounded-full bg-primary-bg px-2 py-0.5 text-xs font-medium text-primary-dark">
                        {p.status}
                      </span>
                    </td>

                    <td className="px-5 py-3 text-text-muted">
                      {p.match_count}
                    </td>

                    <td className="px-5 py-3">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            openDetail(p)
                          }
                          title="View"
                          className="rounded-lg p-1.5 text-text-muted hover:bg-surface-alt hover:text-primary"
                        >
                          <Eye size={16} />
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            openEditForm(p)
                          }
                          title="Edit"
                          className="rounded-lg p-1.5 text-text-muted hover:bg-surface-alt hover:text-primary"
                        >
                          <Pencil size={16} />
                        </button>

                        {canDelete && (
                          <button
                            type="button"
                            onClick={() =>
                              requestDelete(p)
                            }
                            title="Delete"
                            className="rounded-lg p-1.5 text-text-muted hover:bg-surface-alt hover:text-status-down"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>
        )}

      <PatientFormModal
        isOpen={formOpen}
        mode={formMode}
        patient={selectedPatient}
        isSubmitting={formSubmitting}
        errorMessage={formError}
        onClose={() =>
          setFormOpen(false)
        }
        onSubmitCreate={
          handleCreateSubmit
        }
        onSubmitEdit={
          handleEditSubmit
        }
      />

      <PatientDetailModal
        isOpen={detailOpen}
        patient={selectedPatient}
        notes={notes}
        notesLoading={notesLoading}
        notesError={notesError}
        isAddingNote={isAddingNote}
        addNoteError={addNoteError}
        onClose={() =>
          setDetailOpen(false)
        }
        onAddNote={handleAddNote}
        onEdit={() => {
          if (selectedPatient) {
            setDetailOpen(false);
            openEditForm(
              selectedPatient
            );
          }
        }}
      />

      <ConfirmDialog
        isOpen={
          deleteTarget !== null
        }
        title="Delete patient"
        message={
          deleteTarget
            ? `This will permanently delete ${deleteTarget.first_name} ${deleteTarget.last_name} (MRN ${deleteTarget.mrn}). This action cannot be undone.${
                deleteError
                  ? ` ${deleteError}`
                  : ""
              }`
            : ""
        }
        confirmLabel="Delete"
        isDanger
        isSubmitting={isDeleting}
        onConfirm={confirmDelete}
        onCancel={() =>
          setDeleteTarget(null)
        }
      />
    </div>
  );
}