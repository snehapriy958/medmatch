import { aiApi } from "@/api/axios";

import type {
  Trial,
  TrialCreateRequest,
  UploadTrialResponse,
} from "../types/trial";

export async function listTrials() {
  const response =
    await aiApi.get<Trial[]>("/api/trials");

  return response.data;
}

export async function getTrial(id: string) {
  const response =
    await aiApi.get<Trial>(
      `/api/trials/${id}`
    );

  return response.data;
}

export async function createTrial(
  data: TrialCreateRequest
) {
  const response =
    await aiApi.post<Trial>(
      "/api/trials",
      data
    );

  return response.data;
}

export async function deleteTrial(
  id: string
) {
  await aiApi.delete(
    `/api/trials/${id}`
  );
}

export async function uploadTrialPdf(
  file: File
) {
  const formData = new FormData();

  formData.append("file", file);

  const response =
    await aiApi.post<UploadTrialResponse>(
      "/api/trials/upload",
      formData,
      {
        headers: {
          "Content-Type":
            "multipart/form-data",
        },
      }
    );

  return response.data;
}