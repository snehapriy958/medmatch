import { authApi } from "@/api/axios";
import type {
  LoginRequest,
  LoginResponse,
} from "@/features/auth/types/auth";

class AuthService {
  async login(
    request: LoginRequest
  ): Promise<LoginResponse> {
    const response = await authApi.post<LoginResponse>(
      "/auth/login",
      request
    );

    return response.data;
  }
}

export const authService = new AuthService();