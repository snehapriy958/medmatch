import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/auth/AuthProvider";

import { PatientTable } from "../components/PatientTable";
import { PatientFormDialog } from "../components/PatientFormDialog";
import { PatientNoteDialog } from "../components/PatientNoteDialog";

import type {
  Patient,
  CreatePatientRequest,
  CreatePatientNoteRequest,
} from "../types/patient";

import {
  usePatients,
  useCreatePatient,
  useDeletePatient,
  useAddPatientNote,
} from "../hooks/usePatients";

export function PatientsPage() {
  const { user } = useAuth();

  const {
    data: patients = [],
    isLoading,
    isError,
  } = usePatients();

  const createPatient = useCreatePatient();
  const deletePatient = useDeletePatient();
  const addPatientNote = useAddPatientNote();

  const [formOpen, setFormOpen] =
    useState(false);

  const [noteOpen, setNoteOpen] =
    useState(false);

  const [selectedPatient, setSelectedPatient] =
    useState<Patient>();

  const canDelete =
    user?.role === "ADMIN";

  const handleCreate = (
    data: CreatePatientRequest
  ) => {
    createPatient.mutate(data, {
      onSuccess: () => {
        toast.success(
          "Patient created successfully."
        );

        setFormOpen(false);
      },

      onError: () => {
        toast.error(
          "Failed to create patient."
        );
      },
    });
  };

  const handleDelete = (
    patient: Patient
  ) => {
    if (
      !window.confirm(
        `Delete patient "${patient.name}"?`
      )
    ) {
      return;
    }

    deletePatient.mutate(patient.id, {
      onSuccess: () => {
        toast.success(
          "Patient deleted."
        );
      },

      onError: () => {
        toast.error(
          "Failed to delete patient."
        );
      },
    });
  };

  const handleAddNote = (
    patientId: string,
    data: CreatePatientNoteRequest
  ) => {
    addPatientNote.mutate(
      {
        patientId,
        data,
      },
      {
        onSuccess: () => {
          toast.success(
            "Clinical note added."
          );

          setNoteOpen(false);
          setSelectedPatient(undefined);
        },

        onError: () => {
          toast.error(
            "Failed to add clinical note."
          );
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div>
        Loading patients...
      </div>
    );
  }

  if (isError) {
    return (
      <div>
        Failed to load patients.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Patients
          </h1>

          <p className="text-muted-foreground">
            Manage patient records and
            clinical notes.
          </p>
        </div>

        <Button
          onClick={() =>
            setFormOpen(true)
          }
        >
          Create Patient
        </Button>
      </div>

      <PatientTable
        patients={patients}
        canDelete={canDelete}
        onAddNote={(patient) => {
          setSelectedPatient(patient);
          setNoteOpen(true);
        }}
        onDelete={handleDelete}
      />

      <PatientFormDialog
        open={formOpen}
        loading={
          createPatient.isPending
        }
        onOpenChange={setFormOpen}
        onCreate={handleCreate}
      />

      <PatientNoteDialog
        open={noteOpen}
        patient={selectedPatient}
        loading={
          addPatientNote.isPending
        }
        onOpenChange={(open) => {
          setNoteOpen(open);

          if (!open) {
            setSelectedPatient(
              undefined
            );
          }
        }}
        onCreate={handleAddNote}
      />
    </div>
  );
}