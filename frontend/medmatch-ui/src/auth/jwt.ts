import { jwtDecode } from "jwt-decode";

export type UserRole = "ADMIN" | "DOCTOR" | "RESEARCHER";

export interface JwtPayload {
  /**
   * User ID (UUID)
   */
  sub: string;

  /**
   * User email
   */
  email: string;

  /**
   * User role
   */
  role: UserRole;

  /**
   * Hospital ID (UUID)
   */
  hospital_id: string;

  /**
   * Issued At (Unix timestamp)
   */
  iat: number;

  /**
   * Expiration Time (Unix timestamp)
   */
  exp: number;
}

export function decodeToken(token: string): JwtPayload {
  return jwtDecode<JwtPayload>(token);
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeToken(token);
  return payload.exp * 1000 <= Date.now();
}