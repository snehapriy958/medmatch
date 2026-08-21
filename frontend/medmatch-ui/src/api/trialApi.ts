import { aiApiClient } from "./axios";
import type {
  TrialResponse,
  TrialCreate,
  TrialUpdate,
  TrialUploadResponse,
} from "../types/trial";

// GET /api/trials returns list[TrialResponse] directly — no wrapper object.
export async function listTrials(): Promise<TrialResponse[]> {
  const { data } = await aiApiClient.get<TrialResponse[]>("/api/trials");
  return data;
}

export async function getTrial(trialId: string): Promise<TrialResponse> {
  const { data } = await aiApiClient.get<TrialResponse>(`/api/trials/${trialId}`);
  return data;
}

export async function createTrial(payload: TrialCreate): Promise<TrialResponse> {
  const { data } = await aiApiClient.post<TrialResponse>("/api/trials", payload);
  return data;
}

export async function updateTrial(
  trialId: string,
  payload: TrialUpdate
): Promise<TrialResponse> {
  const { data } = await aiApiClient.put<TrialResponse>(`/api/trials/${trialId}`, payload);
  return data;
}

export async function deleteTrial(trialId: string): Promise<void> {
  await aiApiClient.delete(`/api/trials/${trialId}`);
}

// multipart/form-data, field name "file", application/pdf only (backend
// returns 415 otherwise). Deliberately NOT setting a Content-Type header here:
// axios/the browser must generate the multipart boundary itself when the body
// is a FormData instance — setting "multipart/form-data" manually strips the
// boundary parameter and breaks the request.
export async function uploadTrialPdf(file: File): Promise<TrialUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await aiApiClient.post<TrialUploadResponse>(
    "/api/trials/upload",
    formData
  );
  return data;
}
