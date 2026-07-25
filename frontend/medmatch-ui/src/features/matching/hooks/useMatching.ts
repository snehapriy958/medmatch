import { useMutation } from "@tanstack/react-query";

import { matchingService } from "../api/matching.service";

import type {
  MatchingRequest,
  MatchingResponse,
  EligibilityResponse,
} from "../types/matching";

export function useSearchMatching() {
  return useMutation<MatchingResponse, Error, MatchingRequest>({
    mutationFn: (request) =>
      matchingService.searchMatching(request),
  });
}

export function useEvaluatePatient() {
  return useMutation<EligibilityResponse, Error, MatchingRequest>({
    mutationFn: (request) =>
      matchingService.evaluatePatient(request),
  });
}