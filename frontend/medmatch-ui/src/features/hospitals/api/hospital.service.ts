import { authApi } from "@/api/axios";
import type {
  Hospital,
  CreateHospitalRequest,
  UpdateHospitalRequest,
} from "../types/hospital";

class HospitalService {
  /**
   * Get all hospitals.
   */
  async getHospitals(): Promise<Hospital[]> {
    const response = await authApi.get<Hospital[]>("/hospitals");
    return response.data;
  }

  /**
   * Get a hospital by ID.
   */
  async getHospital(id: string): Promise<Hospital> {
    const response = await authApi.get<Hospital>(`/hospitals/${id}`);
    return response.data;
  }

  /**
   * Create a new hospital.
   */
  async createHospital(
    request: CreateHospitalRequest
  ): Promise<Hospital> {
    const response = await authApi.post<Hospital>(
      "/hospitals",
      request
    );

    return response.data;
  }

  /**
   * Update an existing hospital.
   */
  async updateHospital(
    id: string,
    request: UpdateHospitalRequest
  ): Promise<Hospital> {
    const response = await authApi.put<Hospital>(
      `/hospitals/${id}`,
      request
    );

    return response.data;
  }

  /**
   * Delete a hospital.
   */
  async deleteHospital(id: string): Promise<void> {
    await authApi.delete(`/hospitals/${id}`);
  }
}

export const hospitalService = new HospitalService();