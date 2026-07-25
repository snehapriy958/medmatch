export type EligibilityStatus =
  | "Eligible"
  | "Not Eligible"
  | "Possibly Eligible";

export interface MatchingResult {
  id: string;
  trial_id: string;
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
  eligibility: EligibilityStatus;

  confidence: number;

  matched_criteria: string[];

  failed_criteria: string[];

  reasoning: string;
}

export interface MatchingRequest {
  patient_note: string;
  limit: number;
}