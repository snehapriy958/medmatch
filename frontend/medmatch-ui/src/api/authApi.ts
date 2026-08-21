import { authApiClient } from "./axios";
import type { LoginRequest, LoginResponse, CurrentUser } from "../types/auth";

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const { data } = await authApiClient.post<LoginResponse>("/auth/login", payload);
  return data;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const { data } = await authApiClient.get<CurrentUser>("/users/me");
  return data;
}