import Modal from "./Modal";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDanger?: boolean;
  isSubmitting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isDanger = false,
  isSubmitting = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} title={title} widthClassName="max-w-sm">
      <p className="text-sm text-text-muted">{message}</p>
      <div className="mt-6 flex justify-end gap-3">
        <button
          onClick={onCancel}
          disabled={isSubmitting}
          className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt disabled:opacity-60"
        >
          {cancelLabel}
        </button>
        <button
          onClick={onConfirm}
          disabled={isSubmitting}
          className={`rounded-lg px-4 py-2 text-sm font-medium text-white transition disabled:opacity-60 ${
            isDanger ? "bg-status-down hover:bg-red-700" : "bg-primary hover:bg-primary-dark"
          }`}
        >
          {isSubmitting ? "Please wait..." : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
