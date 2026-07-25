import { z } from "zod";

export const hospitalSchema = z.object({
  code: z
    .string()
    .trim()
    .min(1, "Hospital code is required"),

  name: z
    .string()
    .trim()
    .min(1, "Hospital name is required"),

  address: z
    .string()
    .trim()
    .min(1, "Hospital address is required"),
});

export type HospitalFormData = z.infer<typeof hospitalSchema>;