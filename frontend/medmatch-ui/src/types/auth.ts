export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
}

export type UserRole =
  | "SYSTEM_ADMIN"
  | "HOSPITAL_ADMIN"
  | "RESEARCH_COORDINATOR"
  | "PHYSICIAN"
  | "TRIAL_SPONSOR"
  | "PATIENT";

export interface CurrentUser {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  role: UserRole;
  hospitalId: string;
  status: string;
  enabled: boolean;
}