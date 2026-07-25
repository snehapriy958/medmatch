import { aiApi } from "@/api/axios";

import type {
  MatchingRequest,
  MatchingResponse,
  EligibilityResponse,
} from "../types/matching";

class MatchingService {
  async searchMatching(
    request: MatchingRequest
  ): Promise<MatchingResponse> {
    const response = await aiApi.post<MatchingResponse>(
      "/matching/search",
      request
    );

    return response.data;
  }

  async evaluatePatient(
    request: MatchingRequest
  ): Promise<EligibilityResponse> {
    const response = await aiApi.post<EligibilityResponse>(
      "/matching/evaluate",
      request
    );

    return response.data;
  }
}

export const matchingService = new MatchingService();