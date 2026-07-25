import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

import { UserTable } from "../components/UserTable";
import { UserFormDialog } from "../components/UserFormDialog";

import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
} from "../types/user";

import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
} from "../hooks/useUsers";

export function UsersPage() {
  const { data: users = [], isLoading, isError } = useUsers();

  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const [open, setOpen] = useState(false);
  const [selectedUser, setSelectedUser] =
    useState<User>();

  const handleCreate = (
    data: CreateUserRequest
  ) => {
    createUser.mutate(data, {
      onSuccess: () => {
        toast.success("User created successfully.");
        setOpen(false);
      },

      onError: () => {
        toast.error("Failed to create user.");
      },
    });
  };

  const handleUpdate = (
    data: UpdateUserRequest
  ) => {
    if (!selectedUser) return;

    updateUser.mutate(
      {
        id: selectedUser.id,
        data,
      },
      {
        onSuccess: () => {
          toast.success("User updated successfully.");
          setSelectedUser(undefined);
          setOpen(false);
        },

        onError: () => {
          toast.error("Failed to update user.");
        },
      }
    );
  };

  const handleDelete = (user: User) => {
    if (
      !window.confirm(
        `Delete ${user.username}?`
      )
    )
      return;

    deleteUser.mutate(user.id, {
      onSuccess: () => {
        toast.success("User deleted.");
      },

      onError: () => {
        toast.error("Failed to delete user.");
      },
    });
  };

  if (isLoading) {
  return (
    <div className="rounded-xl border bg-card p-8 shadow-sm">
      <div className="flex items-center justify-center">
        <p className="text-muted-foreground">
          Loading users...
        </p>
      </div>
    </div>
  );
}

  if (isError) {
  return (
    <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-8 shadow-sm">
      <div className="text-center">
        <h2 className="font-semibold text-destructive">
          Failed to load users
        </h2>

        <p className="mt-2 text-sm text-muted-foreground">
          Please try refreshing the page.
        </p>
      </div>
    </div>
  );
}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Users
          </h1>

          <p className="text-muted-foreground">
            Manage system users.
          </p>
        </div>

        <Button
          onClick={() => {
            setSelectedUser(undefined);
            setOpen(true);
          }}
        >
          Create User
        </Button>
      </div>

      <UserTable
        users={users}
        onEdit={(user) => {
          setSelectedUser(user);
          setOpen(true);
        }}
        onDelete={handleDelete}
      />

      <UserFormDialog
        open={open}
        user={selectedUser}
        loading={
          createUser.isPending ||
          updateUser.isPending
        }
        onOpenChange={(value) => {
          setOpen(value);

          if (!value) {
            setSelectedUser(undefined);
          }
        }}
        onCreate={handleCreate}
        onUpdate={handleUpdate}
      />
    </div>
  );
}