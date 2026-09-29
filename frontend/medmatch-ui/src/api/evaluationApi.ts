import { aiApiClient } from "./axios";
import type {
  EvaluationAblationsResponse,
  EvaluationOverviewResponse,
  EvaluationPerformanceResponse,
  EvaluationSafetyResponse,
} from "../types/evaluation";

/**
 * GET /api/evaluation/overview
 * Executive coverage, key highlights, and evidence classifications.
 */
export async function getEvaluationOverview(): Promise<EvaluationOverviewResponse> {
  const { data } = await aiApiClient.get<EvaluationOverviewResponse>(
    "/api/evaluation/overview"
  );
  return data;
}

/**
 * GET /api/evaluation/performance
 * Phase 14.1 frozen baseline reference, Phase 14.2 controlled same-run
 * N+1 criteria loading optimization, PostgreSQL metrics, and vector retrieval scaling.
 */
export async function getEvaluationPerformance(): Promise<EvaluationPerformanceResponse> {
  const { data } = await aiApiClient.get<EvaluationPerformanceResponse>(
    "/api/evaluation/performance"
  );
  return data;
}

/**
 * GET /api/evaluation/safety
 * Phase 12 error injection (14/14 scenarios intercepted), safety gate ablations,
 * and Phase 9 human review triage on synthetic fixtures.
 */
export async function getEvaluationSafety(): Promise<EvaluationSafetyResponse> {
  const { data } = await aiApiClient.get<EvaluationSafetyResponse>(
    "/api/evaluation/safety"
  );
  return data;
}

/**
 * GET /api/evaluation/ablations
 * Phase 11 experimental comparisons (E0–E4) and component ablations (A1–A5)
 * on development test fixtures (n=6).
 */
export async function getEvaluationAblations(): Promise<EvaluationAblationsResponse> {
  const { data } = await aiApiClient.get<EvaluationAblationsResponse>(
    "/api/evaluation/ablations"
  );
  return data;
}
