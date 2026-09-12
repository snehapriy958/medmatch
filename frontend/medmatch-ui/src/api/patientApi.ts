import { apiClient } from "./axios";
import type {
  PatientListResponse,
  PatientResponse,
  PatientCreate,
  PatientUpdate,
  PatientNote,
  PatientNoteCreate,
} from "../types/patient";

export async function listPatients(): Promise<PatientListResponse> {
  const { data } = await apiClient.get<PatientListResponse>("/patients");
  return data;
}

export async function getPatient(patientId: string): Promise<PatientResponse> {
  const { data } = await apiClient.get<PatientResponse>(`/patients/${patientId}`);
  return data;
}

export async function createPatient(
  payload: PatientCreate
): Promise<PatientResponse> {
  const { data } = await apiClient.post<PatientResponse>(
    "/patients",
    payload
  );
  return data;
}

export async function updatePatient(
  patientId: string,
  payload: PatientUpdate
): Promise<PatientResponse> {
  const { data } = await apiClient.put<PatientResponse>(
    `/patients/${patientId}`,
    payload
  );
  return data;
}

export async function deletePatient(patientId: string): Promise<void> {
  await apiClient.delete(`/patients/${patientId}`);
}

export async function addPatientNote(
  patientId: string,
  payload: PatientNoteCreate
): Promise<PatientNote> {
  const { data } = await apiClient.post<PatientNote>(
    `/patients/${patientId}/notes`,
    payload
  );

  return data;
}

export async function listPatientNotes(
  patientId: string
): Promise<PatientNote[]> {
  const { data } = await apiClient.get<PatientNote[]>(
    `/patients/${patientId}/notes`
  );

  return data;
}