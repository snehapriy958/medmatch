import { useState } from "react";
import { toast } from "sonner";

import { PatientNoteForm } from "../components/PatientNoteForm";
import { EligibilityCard } from "../components/EligibilityCard";
import { SearchResultsTable } from "../components/SearchResultsTable";

import {
  useEvaluatePatient,
  useSearchMatching,
} from "../hooks/useMatching";

import type {
  EligibilityResponse,
  MatchingResult,
} from "../types/matching";

export function MatchingPage() {
  const evaluateMutation = useEvaluatePatient();
  const searchMutation = useSearchMatching();

  const [eligibility, setEligibility] =
    useState<EligibilityResponse | null>(null);

  const [matches, setMatches] = useState<
    MatchingResult[]
  >([]);

  const handleEvaluate = async (
    patientNote: string,
    limit: number
  ) => {
    try {
      const [evaluation, search] =
        await Promise.all([
          evaluateMutation.mutateAsync({
            patient_note: patientNote,
            limit,
          }),
          searchMutation.mutateAsync({
            patient_note: patientNote,
            limit,
          }),
        ]);

      setEligibility(evaluation);
      setMatches(search.matches);

      toast.success(
        "Patient evaluated successfully."
      );
    } catch (error) {
      console.error(error);

      toast.error(
        "Failed to evaluate patient."
      );
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">
          AI Trial Matching
        </h1>

        <p className="text-muted-foreground">
          Evaluate a patient against clinical
          trials using semantic search and LLM
          reasoning.
        </p>
      </div>

      <PatientNoteForm
        loading={
          evaluateMutation.isPending ||
          searchMutation.isPending
        }
        onEvaluate={handleEvaluate}
      />

      {eligibility && (
        <EligibilityCard
          result={eligibility}
        />
      )}

      {matches.length > 0 && (
        <SearchResultsTable
          results={matches}
        />
      )}
    </div>
  );
}