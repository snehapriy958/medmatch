import { jwtDecode } from "jwt-decode";

export type UserRole = "ADMIN" | "DOCTOR" | "RESEARCHER";

export interface JwtPayload {
  /**
   * User ID
   * Comes from JwtClaimsSet.subject(...)
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
   * Hospital ID
   */
  hospital_id: number;

  /**
   * Issued At (Unix timestamp)
   */
  iat: number;

  /**
   * Expiration Time (Unix timestamp)
   */
  exp: number;
}

/**
 * Decode the JWT payload.
 */
export function decodeToken(token: string): JwtPayload {
  return jwtDecode<JwtPayload>(token);
}

/**
 * Returns true if the JWT has expired.
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeToken(token);

  return payload.exp * 1000 <= Date.now();
}