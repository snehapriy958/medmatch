// Matches the confirmed GET /audit-logs/user/{userId} response exactly.
// `action` is a free string, NOT a confirmed enum — observed values include
// CREATE_TRIAL, DELETE_TRIAL, ELIGIBILITY_EVALUATED, LOGIN_SUCCESS,
// PATIENT_CREATED, PATIENT_DELETED, PATIENT_NOTE_CREATED, PATIENT_UPDATED,
// UPDATE_TRIAL, USER_REGISTERED — but these are DB observations, not a schema
// contract, so they are not hard-coded as a TS union type here.

export interface AuditLog {
  id: string;
  performedById: string;
  action: string;
  resourceType: string;
  resourceId: string;
  ipAddress: string;
  details: string;
  createdAt: string;
}
