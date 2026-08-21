// Matches FastAPI /api/patients schemas exactly (see PatientResponse, PatientCreate,
// PatientUpdate, PatientListResponse in OpenAPI spec).

export interface PatientResponse {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  age: number;
  gender: string;
  diagnosis: string;
  cancer_type: string | null;
  stage: string | null;
  phone: string | null;
  email: string | null;
  hospital_id: string;
  status: string;
  match_count: number;
  created_at: string;
  updated_at: string;
}

export interface PatientListResponse {
  patients: PatientResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface PatientCreate {
  mrn: string;
  first_name: string;
  last_name: string;
  age: number;
  gender: string;
  diagnosis: string;
  cancer_type?: string;
  stage?: string;
  phone?: string;
  email?: string;
}

export interface PatientUpdate {
  first_name?: string;
  last_name?: string;
  age?: number;
  gender?: string;
  diagnosis?: string;
  cancer_type?: string;
  stage?: string;
  phone?: string;
  email?: string;
  status?: string;
}

export interface PatientNote {
  id: string;
  patient_id: string;
  note: string;
  created_at: string;
}

export interface PatientNoteCreate {
  note: string;
}
