import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { userService } from "../api/user.service";
import type {
  CreateUserRequest,
  UpdateUserRequest,
} from "../types/user";

interface UpdateUserVariables {
  id: string;
  data: UpdateUserRequest;
}

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: () => userService.getUsers(),
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateUserRequest) =>
      userService.createUser(data),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["users"],
      });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: UpdateUserVariables) =>
      userService.updateUser(id, data),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["users"],
      });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      userService.deleteUser(id),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["users"],
      });
    },
  });
}