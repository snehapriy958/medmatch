export type Role = "ADMIN" | "DOCTOR" | "RESEARCHER";

export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  hospitalId: string;
  hospitalCode: string;
  hospitalName: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role: Role;
  hospitalId: string;
}

export interface UpdateUserRequest {
  username: string;
  email: string;
  role: Role;
  hospitalId: string;
}