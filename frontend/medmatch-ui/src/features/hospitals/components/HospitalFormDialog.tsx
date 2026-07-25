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

import type { Hospital } from "../types/hospital";
import {
  hospitalSchema,
  type HospitalFormData,
} from "../validation/hospital.schema";

interface HospitalFormDialogProps {
  open: boolean;
  hospital?: Hospital;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: HospitalFormData) => void;
}

export function HospitalFormDialog({
  open,
  hospital,
  loading = false,
  onOpenChange,
  onSubmit,
}: HospitalFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<HospitalFormData>({
    resolver: zodResolver(hospitalSchema),
    defaultValues: {
      code: "",
      name: "",
      address: "",
    },
  });

  useEffect(() => {
    if (hospital) {
      reset({
        code: hospital.code,
        name: hospital.name,
        address: hospital.address,
      });
    } else {
      reset({
        code: "",
        name: "",
        address: "",
      });
    }
  }, [hospital, open, reset]);

  const submitHandler = (data: HospitalFormData) => {
    onSubmit(data);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {hospital ? "Edit Hospital" : "Create Hospital"}
          </DialogTitle>

          <DialogDescription>
            {hospital
              ? "Update the hospital information."
              : "Add a new hospital to MedMatch."}
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit(submitHandler)}
          className="space-y-5"
        >
          <div className="space-y-2">
            <label
              htmlFor="code"
              className="text-sm font-medium"
            >
              Hospital Code
            </label>

            <Input
              id="code"
              placeholder="HOSP001"
              {...register("code")}
            />

            {errors.code && (
              <p className="text-sm text-red-500">
                {errors.code.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <label
              htmlFor="name"
              className="text-sm font-medium"
            >
              Hospital Name
            </label>

            <Input
              id="name"
              placeholder="Apollo Hospital"
              {...register("name")}
            />

            {errors.name && (
              <p className="text-sm text-red-500">
                {errors.name.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <label
              htmlFor="address"
              className="text-sm font-medium"
            >
              Address
            </label>

            <Input
              id="address"
              placeholder="Bangalore"
              {...register("address")}
            />

            {errors.address && (
              <p className="text-sm text-red-500">
                {errors.address.message}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Saving..."
                : hospital
                ? "Update Hospital"
                : "Create Hospital"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}