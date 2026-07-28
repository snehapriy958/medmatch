export type EligibilityStatus =
  | "Eligible"
  | "Not Eligible"
  | "Possibly Eligible";

export interface MatchingResult {
  id: string;

  trial_id: string;

  title: string;

  condition: string | null;

  phase: string | null;

  status: string | null;

  brief_summary: string | null;

  criteria_type: string;

  description: string;

  distance: number;
}

export interface MatchingResponse {
  query: string;
  total_matches: number;
  returned_matches: number;
  similarity_threshold: number;
  matches: MatchingResult[];
}

export interface EligibilityResponse {
  eligibility:
    | "Eligible"
    | "Not Eligible"
    | "Possibly Eligible";

  confidence: number;

  summary: string;

  matched_inclusion: string[];

  failed_inclusion: string[];

  satisfied_exclusion: string[];

  triggered_exclusion: string[];

  missing_information: string[];

  recommendation: string;

  reasoning: string;
}

export interface MatchingRequest {
  patient_note: string;
  limit: number;
}