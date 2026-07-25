import type { UserRole } from "@/auth/jwt";

/**
 * POST /auth/login
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * Response returned by Spring Boot.
 */
export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
}

/**
 * Authenticated user extracted from the JWT.
 */
export interface AuthenticatedUser {
  id: number;
  email: string;
  role: UserRole;
  hospitalId: number;
}