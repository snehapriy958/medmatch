import { useState, type ChangeEvent } from "react";
import axios from "axios";
import { UploadCloud, CheckCircle2, AlertCircle } from "lucide-react";
import Modal from "./Modal";
import { uploadTrialPdf } from "../../api/trialApi";
import type { TrialUploadResponse } from "../../types/trial";

interface TrialUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  // Called once the file is successfully queued, so the page can refresh the
  // trial list. There's no endpoint to poll the Celery task_id for completion,
  // so this is a one-shot refresh trigger, not real progress tracking.
  onQueued: () => void;
}

export default function TrialUploadModal({
  isOpen,
  onClose,
  onQueued,
}: TrialUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TrialUploadResponse | null>(null);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    setError(null);
    setResult(null);
    if (selected && selected.type !== "application/pdf") {
      setError("Only PDF files are accepted.");
      setFile(null);
      return;
    }
    setFile(selected);
  }

  async function handleUpload() {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const res = await uploadTrialPdf(file);
      setResult(res);
      onQueued();
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 415) {
        setError("Only PDF files are accepted.");
      } else {
        setError("Upload failed. Please try again.");
      }
    } finally {
      setIsUploading(false);
    }
  }

  function handleClose() {
    setFile(null);
    setResult(null);
    setError(null);
    onClose();
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Upload Trial PDF" widthClassName="max-w-lg">
      <div className="space-y-4">
        {!result && (
          <>
            <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border p-8 text-center hover:border-primary">
              <UploadCloud size={28} className="text-primary" />
              <span className="text-sm font-medium text-text">
                {file ? file.name : "Click to select a PDF"}
              </span>
              <span className="text-xs text-text-muted">PDF files only</span>
              <input
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={handleFileChange}
              />
            </label>

            {error && (
              <p className="flex items-center gap-2 text-sm text-status-down">
                <AlertCircle size={14} />
                {error}
              </p>
            )}

            <div className="flex justify-end gap-3">
              <button
                onClick={handleClose}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={!file || isUploading}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark disabled:opacity-60"
              >
                {isUploading ? "Uploading..." : "Upload"}
              </button>
            </div>
          </>
        )}

        {result && (
          <div className="space-y-3 rounded-xl bg-primary-bg p-4">
            <div className="flex items-center gap-2 text-primary-dark">
              <CheckCircle2 size={18} />
              <p className="text-sm font-medium">File queued for processing</p>
            </div>
            <p className="text-xs text-text-muted">
              Task ID: <span className="font-mono">{result.task_id}</span> · Status:{" "}
              {result.status}
            </p>
            <p className="text-xs text-text-muted">
              Extraction runs asynchronously in the background. There's currently no
              status-check endpoint for this task, so refresh the trial list in a moment
              to see the trial once processing completes.
            </p>
            <div className="flex justify-end">
              <button
                onClick={handleClose}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
