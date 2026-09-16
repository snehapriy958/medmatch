import { apiClient } from "./axios";
import type {
  TrialResponse,
  TrialCreate,
  TrialUpdate,
  TrialUploadResponse,
} from "../types/trial";

export async function listTrials(): Promise<TrialResponse[]> {
  const { data } = await apiClient.get<TrialResponse[]>("/trials");
  return data;
}

export async function getTrial(trialId: string): Promise<TrialResponse> {
  const { data } = await apiClient.get<TrialResponse>(
    `/trials/${trialId}`
  );
  return data;
}

export async function createTrial(
  payload: TrialCreate
): Promise<TrialResponse> {
  const { data } = await apiClient.post<TrialResponse>(
    "/trials",
    payload
  );
  return data;
}

export async function updateTrial(
  trialId: string,
  payload: TrialUpdate
): Promise<TrialResponse> {
  const { data } = await apiClient.put<TrialResponse>(
    `/trials/${trialId}`,
    payload
  );
  return data;
}

export async function deleteTrial(trialId: string): Promise<void> {
  await apiClient.delete(`/trials/${trialId}`);
}

export async function uploadTrialPdf(
  file: File
): Promise<TrialUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await apiClient.post<TrialUploadResponse>(
    "/trials/upload",
    formData
  );

  return data;
}