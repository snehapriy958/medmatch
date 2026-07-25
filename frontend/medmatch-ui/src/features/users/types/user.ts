export type Role = "ADMIN" | "DOCTOR" | "RESEARCHER";

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
  hospitalId: number;
  hospitalCode: string;
  hospitalName: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role: Role;
  hospitalId: number;
}

export interface UpdateUserRequest {
  username: string;
  email: string;
  role: Role;
  hospitalId: number;
}