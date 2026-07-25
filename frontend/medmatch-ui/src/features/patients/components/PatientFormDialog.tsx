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
import { Input } from "@/components/ui/input";

import {
  createPatientSchema,
  type CreatePatientFormData,
} from "../validation/patient.schema";

import type { CreatePatientRequest } from "../types/patient";

interface PatientFormDialogProps {
  open: boolean;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (data: CreatePatientRequest) => void;
}

export function PatientFormDialog({
  open,
  loading = false,
  onOpenChange,
  onCreate,
}: PatientFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreatePatientFormData>({
    resolver: zodResolver(createPatientSchema),
    defaultValues: {
      name: "",
      age: 0,
      gender: "",
      diagnosis: "",
    },
  });

  useEffect(() => {
    if (!open) {
      reset({
        name: "",
        age: 0,
        gender: "",
        diagnosis: "",
      });
    }
  }, [open, reset]);

  const submitHandler = (
    data: CreatePatientFormData
  ) => {
    onCreate(data);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            Create Patient
          </DialogTitle>

          <DialogDescription>
            Register a new patient.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit(submitHandler)}
          className="space-y-5"
        >
          <div>
            <label className="text-sm font-medium">
              Name
            </label>

            <Input
              {...register("name")}
            />

            {errors.name && (
              <p className="text-sm text-red-500">
                {errors.name.message}
              </p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium">
              Age
            </label>

            <Input
              type="number"
              {...register("age", {
                valueAsNumber: true,
              })}
            />

            {errors.age && (
              <p className="text-sm text-red-500">
                {errors.age.message}
              </p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium">
              Gender
            </label>

            <Input
              placeholder="Male / Female / Other"
              {...register("gender")}
            />

            {errors.gender && (
              <p className="text-sm text-red-500">
                {errors.gender.message}
              </p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium">
              Diagnosis
            </label>

            <Input
              {...register("diagnosis")}
            />

            {errors.diagnosis && (
              <p className="text-sm text-red-500">
                {errors.diagnosis.message}
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
              disabled={loading}
            >
              {loading
                ? "Saving..."
                : "Create Patient"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}