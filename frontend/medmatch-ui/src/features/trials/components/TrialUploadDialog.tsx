import { useState } from "react";
import { Upload } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import { useUploadTrial } from "../hooks/useTrials";

export default function TrialUploadDialog() {
  const [file, setFile] = useState<File | null>(null);

  const uploadMutation = useUploadTrial();

  async function handleUpload() {
    if (!file) {
      toast.error("Please select a PDF.");
      return;
    }

    try {
      await uploadMutation.mutateAsync(file);

      toast.success("Clinical trial upload started.");

      setFile(null);
    } catch {
      toast.error("Failed to upload PDF.");
    }
  }

  return (
    <Dialog>
      <DialogTrigger
        render={
          <Button>
            <Upload className="mr-2 h-4 w-4" />
            Upload Trial PDF
          </Button>
        }
      />

      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            Upload Clinical Trial
          </DialogTitle>

          <DialogDescription>
            Upload a PDF. The document will be processed
            asynchronously by the AI service.
          </DialogDescription>
        </DialogHeader>

        <Input
          type="file"
          accept=".pdf"
          onChange={(e) =>
            setFile(e.target.files?.[0] ?? null)
          }
        />

        <DialogFooter showCloseButton>
          <Button
            onClick={handleUpload}
            disabled={
              uploadMutation.isPending || !file
            }
          >
            {uploadMutation.isPending
              ? "Uploading..."
              : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}