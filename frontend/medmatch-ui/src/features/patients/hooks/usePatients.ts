import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { patientService } from "../api/patient.service";

import type {
  CreatePatientNoteRequest,
  CreatePatientRequest,
} from "../types/patient";

const QUERY_KEY = ["patients"];

export function usePatients() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => patientService.getPatients(),
  });
}

export function usePatient(id: string) {
  return useQuery({
    queryKey: [...QUERY_KEY, id],
    queryFn: () => patientService.getPatient(id),
    enabled: !!id,
  });
}

export function useCreatePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePatientRequest) =>
      patientService.createPatient(data),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEY,
      });
    },
  });
}

export function useDeletePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      patientService.deletePatient(id),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEY,
      });
    },
  });
}

interface AddPatientNoteMutation {
  patientId: string;
  data: CreatePatientNoteRequest;
}

export function useAddPatientNote() {
  return useMutation({
    mutationFn: ({
      patientId,
      data,
    }: AddPatientNoteMutation) =>
      patientService.addPatientNote(
        patientId,
        data
      ),
  });
}