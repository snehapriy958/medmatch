export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  diagnosis: string;
  hospital_id: string;
}

export interface PatientListResponse {
  patients: Patient[];
}

export interface CreatePatientRequest {
  name: string;
  age: number;
  gender: string;
  diagnosis: string;
}

export interface PatientNote {
  id: string;
  patient_id: string;
  note: string;
  created_at: string;
}

export interface CreatePatientNoteRequest {
  note: string;
}