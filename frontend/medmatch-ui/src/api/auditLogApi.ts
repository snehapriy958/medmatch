import { authApiClient } from "./axios";
import type { AuditLog } from "../types/auditLog";

// GET /audit-logs/user/{userId} — the ONLY confirmed audit-log endpoint.
// No query parameters exist (no date range, no action filter, no pagination).
// Requires SYSTEM_ADMIN or HOSPITAL_ADMIN role (enforced server-side).
// Per-user only — there is no hospital-wide audit endpoint.
export async function getUserAuditLogs(userId: string): Promise<AuditLog[]> {
  const { data } = await authApiClient.get<AuditLog[]>(`/audit-logs/user/${userId}`);
  return data;
}
