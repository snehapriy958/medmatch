import { aiApi } from "@/api/axios";

import type {
  CreatePatientNoteRequest,
  CreatePatientRequest,
  Patient,
  PatientListResponse,
  PatientNote,
} from "../types/patient";

export const patientService = {
  async getPatients(): Promise<Patient[]> {
    const response =
      await aiApi.get<PatientListResponse>("/patients");

    return response.data.patients;
  },

  async getPatient(id: string): Promise<Patient> {
    const response =
      await aiApi.get<Patient>(`/patients/${id}`);

    return response.data;
  },

  async createPatient(
    data: CreatePatientRequest
  ): Promise<Patient> {
    const response =
      await aiApi.post<Patient>("/patients", data);

    return response.data;
  },

  async deletePatient(id: string): Promise<void> {
    await aiApi.delete(`/patients/${id}`);
  },

  async addPatientNote(
    patientId: string,
    data: CreatePatientNoteRequest
  ): Promise<PatientNote> {
    const response =
      await aiApi.post<PatientNote>(
        `/patients/${patientId}/notes`,
        data
      );

    return response.data;
  },
};