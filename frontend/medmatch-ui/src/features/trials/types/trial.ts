export interface Criterion {
  id: string;
  criteria_type: string;
  description: string;
}

export interface Trial {
  id: string;
  title: string;
  brief_summary: string | null;
  condition: string | null;
  phase: string | null;
  status: string | null;
  created_at: string;
  updated_at: string;
  criteria: Criterion[];
}

export interface TrialCreateRequest {
  title: string;
  brief_summary?: string;
  condition?: string;
  phase?: string;
  status?: string;
}

export interface UploadTrialResponse {
  task_id: string;
  status: string;
}