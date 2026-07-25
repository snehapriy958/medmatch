import { authApi } from "@/api/axios";

import type { DashboardSummary } from "../types/dashboard";

export async function getDashboardSummary() {
  const response =
    await authApi.get<DashboardSummary>(
      "/dashboard/summary"
    );

  return response.data;
}