import { toast } from "sonner";

import TrialTable from "../components/TrialTable";
import TrialUploadDialog from "../components/TrialUploadDialog";

import type { Trial } from "../types/trial";

import {
  useDeleteTrial,
  useTrials,
} from "../hooks/useTrials";

export default function TrialsPage() {
  const {
    data: trials = [],
    isLoading,
    isError,
  } = useTrials();

  const deleteTrial = useDeleteTrial();

  const handleDelete = (trial: Trial) => {
    if (
      !window.confirm(
        `Delete "${trial.title}"?`
      )
    )
      return;

    deleteTrial.mutate(trial.id, {
      onSuccess: () => {
        toast.success(
          "Clinical trial deleted."
        );
      },

      onError: () => {
        toast.error(
          "Failed to delete trial."
        );
      },
    });
  };

  if (isLoading) {
    return (
      <div>Loading clinical trials...</div>
    );
  }

  if (isError) {
    return (
      <div>
        Failed to load clinical trials.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Clinical Trials
          </h1>

          <p className="text-muted-foreground">
            Manage clinical trials.
          </p>
        </div>

        <TrialUploadDialog />
      </div>

      <TrialTable
        trials={trials}
        isLoading={false}
        onView={(id) => {
          console.log("View trial:", id);
        }}
        onDelete={(id) => {
          const trial = trials.find(
            (t) => t.id === id
          );

          if (trial) {
            handleDelete(trial);
          }
        }}
      />
    </div>
  );
}