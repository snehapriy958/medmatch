import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import {
  createPatientNoteSchema,
  type CreatePatientNoteFormData,
} from "../validation/patient.schema";

import type {
  CreatePatientNoteRequest,
  Patient,
} from "../types/patient";

interface PatientNoteDialogProps {
  open: boolean;
  patient?: Patient;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (
    patientId: string,
    data: CreatePatientNoteRequest
  ) => void;
}

export function PatientNoteDialog({
  open,
  patient,
  loading = false,
  onOpenChange,
  onCreate,
}: PatientNoteDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreatePatientNoteFormData>({
    resolver: zodResolver(createPatientNoteSchema),
    defaultValues: {
      note: "",
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        note: "",
      });
    }
  }, [open, reset]);

  const submitHandler = (
    data: CreatePatientNoteFormData
  ) => {
    if (!patient) return;

    onCreate(patient.id, data);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            Add Clinical Note
          </DialogTitle>

          <DialogDescription>
            {patient
              ? `Add a clinical note for ${patient.name}.`
              : "Add a clinical note."}
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit(submitHandler)}
          className="space-y-5"
        >
          <div>
            <label className="text-sm font-medium">
              Clinical Note
            </label>

            <Textarea
              rows={8}
              placeholder="Enter patient's clinical notes..."
              {...register("note")}
            />

            {errors.note && (
              <p className="text-sm text-red-500">
                {errors.note.message}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                onOpenChange(false)
              }
            >
              Cancel
            </Button>

            <Button
              type="submit"
              disabled={
                loading || !patient
              }
            >
              {loading
                ? "Saving..."
                : "Save Note"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}