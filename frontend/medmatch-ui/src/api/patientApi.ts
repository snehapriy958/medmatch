import { aiApiClient } from "./axios";
import type {
  PatientListResponse,
  PatientResponse,
  PatientCreate,
  PatientUpdate,
  PatientNote,
  PatientNoteCreate,
} from "../types/patient";

// GET /api/patients — no query params supported by the backend; returns all
// patients for the authenticated user's hospital. Do not add page/search params.
export async function listPatients(): Promise<PatientListResponse> {
  const { data } = await aiApiClient.get<PatientListResponse>("/api/patients");
  return data;
}

export async function getPatient(patientId: string): Promise<PatientResponse> {
  const { data } = await aiApiClient.get<PatientResponse>(`/api/patients/${patientId}`);
  return data;
}

export async function createPatient(payload: PatientCreate): Promise<PatientResponse> {
  const { data } = await aiApiClient.post<PatientResponse>("/api/patients", payload);
  return data;
}

export async function updatePatient(
  patientId: string,
  payload: PatientUpdate
): Promise<PatientResponse> {
  const { data } = await aiApiClient.put<PatientResponse>(`/api/patients/${patientId}`, payload);
  return data;
}

// Backend restricts this to administrators; a non-admin caller will get a 403,
// which the UI surfaces rather than pre-blocking (see handling in Patients.tsx).
export async function deletePatient(patientId: string): Promise<void> {
  await aiApiClient.delete(`/api/patients/${patientId}`);
}

export async function addPatientNote(
  patientId: string,
  payload: PatientNoteCreate
): Promise<PatientNote> {
  const { data } = await aiApiClient.post<PatientNote>(
    `/api/patients/${patientId}/notes`,
    payload
  );

  return data;
}

export async function listPatientNotes(
  patientId: string
): Promise<PatientNote[]> {
  const { data } = await aiApiClient.get<PatientNote[]>(
    `/api/patients/${patientId}/notes`
  );

  return data;
}