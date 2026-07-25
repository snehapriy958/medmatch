import type { ReactElement } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface DeleteTrialDialogProps {
  onDelete: () => void;
  trigger: ReactElement;
}

export default function DeleteTrialDialog({
  onDelete,
  trigger,
}: DeleteTrialDialogProps) {
  return (
    <AlertDialog>
      <AlertDialogTrigger render={trigger} />

      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            Delete Clinical Trial?
          </AlertDialogTitle>

          <AlertDialogDescription>
            This action cannot be undone.
            The clinical trial and all associated
            eligibility criteria will be permanently deleted.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel />

          <AlertDialogAction
            variant="destructive"
            onClick={onDelete}
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}