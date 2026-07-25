import { z } from "zod";

export const createUserSchema = z.object({
  username: z.string().min(1, "Username is required"),

  email: z.string().email("Invalid email address"),

  password: z.string().min(6, "Password must be at least 6 characters"),

  role: z.enum(["ADMIN", "DOCTOR", "RESEARCHER"]),

  hospitalId: z.number().min(1, "Hospital is required"),
});

export const updateUserSchema = z.object({
  username: z.string().min(1, "Username is required"),

  email: z.string().email("Invalid email address"),

  role: z.enum(["ADMIN", "DOCTOR", "RESEARCHER"]),

  hospitalId: z.number().min(1, "Hospital is required"),
});

export type CreateUserFormData = z.infer<typeof createUserSchema>;

export type UpdateUserFormData = z.infer<typeof updateUserSchema>;