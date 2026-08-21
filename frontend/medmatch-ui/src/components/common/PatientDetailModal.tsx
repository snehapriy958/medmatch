import { useState } from "react";
import { Sparkles, Phone, Mail, Calendar } from "lucide-react";

import Modal from "./Modal";
import type { PatientResponse, PatientNote } from "../../types/patient";

interface PatientDetailModalProps {
  isOpen: boolean;
  patient: PatientResponse | null;
  notes: PatientNote[];
  notesLoading: boolean;
  notesError: string | null;
  isAddingNote: boolean;
  addNoteError: string | null;
  onClose: () => void;
  onAddNote: (note: string) => void;
  onEdit: () => void;
}

export default function PatientDetailModal({
  isOpen,
  patient,
  notes,
  notesLoading,
  notesError,
  isAddingNote,
  addNoteError,
  onClose,
  onAddNote,
  onEdit,
}: PatientDetailModalProps) {
  const [noteText, setNoteText] = useState("");

  if (!patient) {
    return null;
  }

  const trimmed = noteText.trim();

  const noteTooShort =
    trimmed.length > 0 && trimmed.length < 10;

  function handleAddNote() {
    if (trimmed.length < 10 || isAddingNote) {
      return;
    }

    onAddNote(trimmed);
    setNoteText("");
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${patient.first_name} ${patient.last_name}`}
      widthClassName="max-w-2xl"
    >
      <div className="space-y-6">
        {/* Patient status */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-primary-bg px-3 py-1 text-xs font-medium text-primary-dark">
            {patient.status}
          </span>

          <span className="rounded-full bg-surface-alt px-3 py-1 text-xs font-medium text-text-muted">
            MRN: {patient.mrn}
          </span>

          <span className="flex items-center gap-1 rounded-full bg-surface-alt px-3 py-1 text-xs font-medium text-text-muted">
            <Sparkles size={12} />

            {patient.match_count} potential{" "}
            {patient.match_count === 1 ? "match" : "matches"}
          </span>
        </div>

        {/* Patient information */}
        <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
          <Detail
            label="Age"
            value={String(patient.age)}
          />

          <Detail
            label="Gender"
            value={patient.gender}
          />

          <Detail
            label="Diagnosis"
            value={patient.diagnosis}
          />

          <Detail
            label="Cancer type"
            value={patient.cancer_type ?? "—"}
          />

          <Detail
            label="Stage"
            value={patient.stage ?? "—"}
          />
        </div>

        {/* Contact and dates */}
        <div className="grid grid-cols-1 gap-3 border-t border-border pt-4 text-sm sm:grid-cols-2">
          <div className="flex items-center gap-2 text-text-muted">
            <Phone size={14} />

            <span>
              {patient.phone ?? "No phone on file"}
            </span>
          </div>

          <div className="flex items-center gap-2 text-text-muted">
            <Mail size={14} />

            <span>
              {patient.email ?? "No email on file"}
            </span>
          </div>

          <div className="flex items-center gap-2 text-text-muted sm:col-span-2">
            <Calendar size={14} />

            <span>
              Added{" "}
              {new Date(
                patient.created_at
              ).toLocaleDateString()}{" "}
              · Updated{" "}
              {new Date(
                patient.updated_at
              ).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Clinical notes */}
        <div className="border-t border-border pt-4">
          <h3 className="mb-3 text-sm font-semibold text-text">
            Clinical Notes
          </h3>

          {notesLoading && (
            <p className="text-sm text-text-muted">
              Loading notes...
            </p>
          )}

          {notesError && (
            <p className="text-sm text-status-down">
              {notesError}
            </p>
          )}

          {!notesLoading &&
            !notesError &&
            notes.length === 0 && (
              <p className="mb-4 text-sm text-text-muted">
                No notes yet for this patient.
              </p>
            )}

          {/* 
            No max-height and no overflow-y-auto here.
            The parent Modal handles scrolling, so the notes
            section uses the same scrollbar as the rest of the modal.
          */}
          {!notesLoading && notes.length > 0 && (
            <ul className="mb-4 space-y-3">
              {notes.map((note) => (
                <li
                  key={note.id}
                  className="rounded-lg bg-surface-alt p-3 text-sm"
                >
                  <p className="text-text">
                    {note.note}
                  </p>

                  <p className="mt-1 text-xs text-text-muted">
                    {new Date(
                      note.created_at
                    ).toLocaleString()}
                  </p>
                </li>
              ))}
            </ul>
          )}

          {/* Add clinical note */}
          <div className="space-y-2">
            <textarea
              value={noteText}
              onChange={(event) =>
                setNoteText(event.target.value)
              }
              rows={3}
              placeholder="Add a clinical note (minimum 10 characters)..."
              className="w-full rounded-lg border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />

            {noteTooShort && (
              <p className="text-xs text-status-down">
                Note must be at least 10 characters.
              </p>
            )}

            {addNoteError && (
              <p className="text-xs text-status-down">
                {addNoteError}
              </p>
            )}

            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleAddNote}
                disabled={
                  isAddingNote ||
                  trimmed.length < 10
                }
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isAddingNote
                  ? "Adding..."
                  : "Add note"}
              </button>
            </div>
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex justify-end gap-3 border-t border-border pt-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt"
          >
            Close
          </button>

          <button
            type="button"
            onClick={onEdit}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
          >
            Edit patient
          </button>
        </div>
      </div>
    </Modal>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-xs text-text-muted">
        {label}
      </p>

      <p className="font-medium text-text">
        {value}
      </p>
    </div>
  );
}