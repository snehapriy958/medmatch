import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createTrial,
  deleteTrial,
  getTrial,
  listTrials,
  uploadTrialPdf,
} from "../api/trial.service";

export function useTrials() {
  return useQuery({
    queryKey: ["trials"],
    queryFn: listTrials,
  });
}

export function useTrial(id: string) {
  return useQuery({
    queryKey: ["trial", id],
    queryFn: () => getTrial(id),
    enabled: !!id,
  });
}

export function useCreateTrial() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: createTrial,

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["trials"],
      });
    },
  });
}

export function useDeleteTrial() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: deleteTrial,

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["trials"],
      });
    },
  });
}

export function useUploadTrial() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: uploadTrialPdf,

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["trials"],
      });
    },
  });
}