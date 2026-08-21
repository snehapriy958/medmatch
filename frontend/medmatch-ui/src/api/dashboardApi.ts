import { authApiClient } from "./axios";
import type { SystemDashboardResponse } from "../types/dashboard";

export async function getSystemDashboard(): Promise<SystemDashboardResponse> {
  const { data } = await authApiClient.get<SystemDashboardResponse>("/dashboard/system");
  return data;
}