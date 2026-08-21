// Matches FastAPI /api/trials schemas exactly (TrialResponse, TrialCreate,
// TrialUpdate, CriterionResponse, upload response). GET /api/trials returns
// list[TrialResponse] directly — there is no list-wrapper type.

export interface CriterionResponse {
  id: string;
  criteria_type: string;
  description: string;
}

export interface TrialResponse {
  id: string;
  title: string;
  brief_summary: string | null;
  condition: string | null;
  phase: string | null;
  status: string | null;
  created_at: string;
  updated_at: string;
  criteria: CriterionResponse[];
}

export interface TrialCreate {
  title: string;
  brief_summary?: string;
  condition?: string;
  phase?: string;
  status?: string;
}

export interface TrialUpdate {
  title?: string;
  brief_summary?: string;
  condition?: string;
  phase?: string;
  status?: string;
}

// Response from POST /api/trials/upload. Extraction is async (Celery
// process_trial task) — this response does NOT contain a created trial.
export interface TrialUploadResponse {
  task_id: string;
  status: string;
}
