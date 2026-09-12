import { authApiClient } from "./axios";
import type { AuditLog } from "../types/auditLog";

export async function getUserAuditLogs(
  userId: string
): Promise<AuditLog[]> {
  const { data } = await authApiClient.get<AuditLog[]>(
    `/audit-logs/user/${userId}`
  );

  return data;
}