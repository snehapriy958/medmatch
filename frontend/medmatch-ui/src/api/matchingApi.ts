import { aiApiClient } from "./axios";
import type {
  MatchingRequest,
  MatchingResponse,
  EligibilityEvaluationResponse,
} from "../types/matching";

// POST /api/matching/search — embedding + vector retrieval only, no Gemini
// dependency. Synchronous.
export async function searchTrials(payload: MatchingRequest): Promise<MatchingResponse> {
  const { data } = await aiApiClient.post<MatchingResponse>("/api/matching/search", payload);
  return data;
}

// POST /api/matching/evaluate — retrieval + Gemini-based eligibility
// evaluation. Synchronous, but depends on the Gemini API being available/within
// quota; a quota/rate-limit failure surfaces as a normal request error, not a
// queued task.
export async function evaluateEligibility(
  payload: MatchingRequest
): Promise<EligibilityEvaluationResponse> {
  const { data } = await aiApiClient.post<EligibilityEvaluationResponse>(
    "/api/matching/evaluate",
    payload
  );
  return data;
}