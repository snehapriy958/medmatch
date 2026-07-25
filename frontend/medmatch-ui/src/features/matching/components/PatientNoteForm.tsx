import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

interface PatientNoteFormProps {
  loading?: boolean;
  onEvaluate: (patientNote: string, limit: number) => void;
}

export function PatientNoteForm({
  loading = false,
  onEvaluate,
}: PatientNoteFormProps) {
  const [patientNote, setPatientNote] = useState("");
  const [limit, setLimit] = useState(10);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const note = patientNote.trim();

    if (!note) return;

    onEvaluate(note, limit);
  };

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Patient Evaluation</CardTitle>
      </CardHeader>

      <CardContent>
        <form
          onSubmit={handleSubmit}
          className="space-y-6"
        >
          <div className="space-y-2">
            <label
              htmlFor="patient-note"
              className="text-sm font-medium"
            >
              Patient Clinical Note
            </label>

            <Textarea
              id="patient-note"
              rows={8}
              className="resize-y"
              placeholder="Paste the patient's complete clinical note here..."
              value={patientNote}
              onChange={(e) =>
                setPatientNote(e.target.value)
              }
            />

            <p className="text-sm text-muted-foreground">
              Paste the patient's clinical note. The AI will
              retrieve relevant clinical trial criteria and
              evaluate eligibility.
            </p>
          </div>

          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Top Results
              </label>

              <Select
                value={String(limit)}
                onValueChange={(value) =>
                  setLimit(Number(value))
                }
              >
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="5">
                    5 Results
                  </SelectItem>

                  <SelectItem value="10">
                    10 Results
                  </SelectItem>

                  <SelectItem value="15">
                    15 Results
                  </SelectItem>

                  <SelectItem value="20">
                    20 Results
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              type="submit"
              size="lg"
              disabled={
                loading ||
                patientNote.trim().length === 0
              }
              className="min-w-[180px]"
            >
              {loading
                ? "Evaluating..."
                : "Evaluate Patient"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}