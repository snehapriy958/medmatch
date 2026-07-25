import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

import { HospitalTable } from "../components/HospitalTable";
import { HospitalFormDialog } from "../components/HospitalFormDialog";

import {
  useHospitals,
  useCreateHospital,
  useUpdateHospital,
  useDeleteHospital,
} from "../hooks/useHospitals";

import type { Hospital } from "../types/hospital";
import type { HospitalFormData } from "../validation/hospital.schema";

export default function HospitalsPage() {
  const { data: hospitals = [], isLoading, isError } = useHospitals();

  const createHospital = useCreateHospital();
  const updateHospital = useUpdateHospital();
  const deleteHospital = useDeleteHospital();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedHospital, setSelectedHospital] =
    useState<Hospital | undefined>();

  const handleCreate = () => {
    setSelectedHospital(undefined);
    setDialogOpen(true);
  };

  const handleEdit = (hospital: Hospital) => {
    setSelectedHospital(hospital);
    setDialogOpen(true);
  };

  const handleDelete = async (hospital: Hospital) => {
    const confirmed = window.confirm(
      `Delete "${hospital.name}"?`
    );

    if (!confirmed) return;

    try {
      await deleteHospital.mutateAsync(hospital.id);

      toast.success("Hospital deleted successfully.");
    } catch {
      toast.error("Failed to delete hospital.");
    }
  };

  const handleSubmit = async (data: HospitalFormData) => {
    try {
      if (selectedHospital) {
        await updateHospital.mutateAsync({
          id: selectedHospital.id,
          data,
        });

        toast.success("Hospital updated successfully.");
      } else {
        await createHospital.mutateAsync(data);

        toast.success("Hospital created successfully.");
      }

      setDialogOpen(false);
      setSelectedHospital(undefined);
    } catch {
      toast.error("Failed to save hospital.");
    }
  };

  if (isLoading) {
    return (
      <div className="rounded-xl bg-white p-8 shadow-sm">
        Loading hospitals...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl bg-white p-8 shadow-sm text-red-600">
        Failed to load hospitals.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="flex items-center justify-between rounded-xl bg-white p-8 shadow-sm">
        <div>
          <h1 className="text-4xl font-bold text-slate-900">
            Hospitals
          </h1>

          <p className="mt-2 text-slate-600">
            Manage hospitals available in MedMatch.
          </p>
        </div>

        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Create Hospital
        </Button>
      </section>

      <section className="rounded-xl bg-white p-6 shadow-sm">
        <HospitalTable
          hospitals={hospitals}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </section>

      <HospitalFormDialog
        open={dialogOpen}
        hospital={selectedHospital}
        loading={
          createHospital.isPending || updateHospital.isPending
        }
        onOpenChange={setDialogOpen}
        onSubmit={handleSubmit}
      />
    </div>
  );
}