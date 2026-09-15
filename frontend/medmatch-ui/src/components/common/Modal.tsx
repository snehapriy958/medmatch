import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  widthClassName?: string;
  /**
   * Optional footer content (e.g. Cancel/Save actions). When provided, it is
   * rendered outside the scrollable body so it stays visible while the body
   * scrolls ("sticky footer"). Existing callers that don't pass this prop
   * keep the previous behavior unchanged.
   */
  footer?: ReactNode;
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  widthClassName = "max-w-lg",
  footer,
}: ModalProps) {
  useEffect(() => {
    if (!isOpen) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 pt-12 sm:pt-20">
      <div
        className={`flex max-h-[85vh] w-full ${widthClassName} flex-col rounded-2xl border border-border bg-surface shadow-lg`}
      >
        <div className="flex shrink-0 items-center justify-between border-b border-border p-5">
          <h2 className="text-base font-semibold text-text">{title}</h2>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-5">{children}</div>
        {footer && (
          <div className="shrink-0 border-t border-border bg-surface p-5">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
