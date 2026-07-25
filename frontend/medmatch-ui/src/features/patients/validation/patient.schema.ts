import { z } from "zod";

export const createPatientSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Name is required.")
    .max(150, "Name must not exceed 150 characters."),

  age: z
    .number({
        error: "Age is required.",
    })
    .int("Age must be a whole number.")
        .min(0, "Age cannot be negative.")
    .max(150, "Age must be less than or equal to 150."),

  gender: z
    .string()
    .trim()
    .min(1, "Gender is required.")
    .max(20, "Gender must not exceed 20 characters."),

  diagnosis: z
    .string()
    .trim()
    .min(1, "Diagnosis is required.")
    .max(255, "Diagnosis must not exceed 255 characters."),
});

export const createPatientNoteSchema = z.object({
  note: z
    .string()
    .trim()
    .min(1, "Clinical note is required.")
    .max(10000, "Clinical note is too long."),
});

export type CreatePatientFormData = z.infer<
  typeof createPatientSchema
>;

export type CreatePatientNoteFormData = z.infer<
  typeof createPatientNoteSchema
>;