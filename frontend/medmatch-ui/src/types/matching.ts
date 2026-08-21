// Matches FastAPI /api/matching/{search,evaluate} schemas exactly.
// Both endpoints share the same request body (MatchingRequest) and are
// synchronous — no task_id/polling flow like the trial PDF upload.

export interface MatchingRequest {
  patient_note: string; // required, 20–10,000 chars
  limit?: number; // 1–100, backend default if omitted
}

// Confirmed backend enum — not a free-form string.
export type EligibilityStatus = "Eligible" | "Not Eligible" | "Possibly Eligible";

export interface EligibilityResponse {
  eligibility: EligibilityStatus;
  confidence: number; // 0.0–1.0
  trial_ids_evaluated: string[]; // max 50
  summary: string; // max 1000
  matched_inclusion: string[]; // max 50
  failed_inclusion: string[]; // max 50
  satisfied_exclusion: string[]; // max 50
  triggered_exclusion: string[]; // max 50
  missing_information: string[]; // max 50
  recommendation: string; // max 1500
  matched_criteria: string[]; // max 50 — legacy/backward compatibility
  failed_criteria: string[]; // max 50 — legacy/backward compatibility
  reasoning: string; // required, 1–3000 chars
}

export interface EligibilityEvaluationResponse {
  results: EligibilityResponse[];
}

export interface MatchingResult {
  id: string; // UUID
  trial_id: string; // UUID
  title: string;
  condition?: string | null;
  phase?: string | null;
  status?: string | null;
  brief_summary?: string | null;
  criteria_type: string;
  description: string;
  distance: number; // cosine distance, 0–2 — NOT a confidence/similarity %
}

export interface MatchingResponse {
  query: string;
  total_matches: number;
  returned_matches: number;
  similarity_threshold: number;
  matches: MatchingResult[];
}
