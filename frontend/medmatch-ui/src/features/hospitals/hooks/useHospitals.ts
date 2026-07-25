import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { hospitalService } from "../api/hospital.service";
import type { UpdateHospitalRequest } from "../types/hospital";

interface UpdateHospitalVariables {
  id: string;
  data: UpdateHospitalRequest;
}

export function useHospitals() {
  return useQuery({
    queryKey: ["hospitals"],
    queryFn: () => hospitalService.getHospitals(),
  });
}

export function useCreateHospital() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: hospitalService.createHospital,

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["hospitals"],
      });
    },
  });
}

export function useUpdateHospital() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: UpdateHospitalVariables) =>
      hospitalService.updateHospital(id, data),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["hospitals"],
      });
    },
  });
}

export function useDeleteHospital() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => hospitalService.deleteHospital(id),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["hospitals"],
      });
    },
  });
}