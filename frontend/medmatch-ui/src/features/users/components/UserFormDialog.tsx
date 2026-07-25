import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  createUserSchema,
  updateUserSchema,
  type CreateUserFormData,
  type UpdateUserFormData,
} from "../validation/user.schema";

import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
} from "../types/user";

import { useHospitals } from "@/features/hospitals/hooks/useHospitals";

interface UserFormDialogProps {
  open: boolean;
  user?: User;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (data: CreateUserRequest) => void;
  onUpdate: (data: UpdateUserRequest) => void;
}

export function UserFormDialog({
  open,
  user,
  loading = false,
  onOpenChange,
  onCreate,
  onUpdate,
}: UserFormDialogProps) {
  const isEdit = !!user;

  const { data: hospitals = [] } = useHospitals();

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateUserFormData | UpdateUserFormData>({
    resolver: zodResolver(
      isEdit ? updateUserSchema : createUserSchema
    ),
    defaultValues: {
      username: "",
      email: "",
      password: "",
      role: "DOCTOR",
      hospitalId: hospitals.length > 0 ? hospitals[0].id : 0,
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        username: user.username,
        email: user.email,
        role: user.role,
        hospitalId: user.hospitalId,
      } as UpdateUserFormData);
    } else {
      reset({
        username: "",
        email: "",
        password: "",
        role: "DOCTOR",
        hospitalId:
          hospitals.length > 0 ? hospitals[0].id : 0,
      } as CreateUserFormData);
    }
  }, [user, hospitals, reset]);

  const submitHandler = (
    data: CreateUserFormData | UpdateUserFormData
  ) => {
    if (isEdit) {
      const updateData = data as UpdateUserFormData;

      onUpdate({
        username: updateData.username,
        email: updateData.email,
        role: updateData.role,
        hospitalId: updateData.hospitalId,
      });
    } else {
      const createData = data as CreateUserFormData;

      onCreate({
        username: createData.username,
        email: createData.email,
        password: createData.password,
        role: createData.role,
        hospitalId: createData.hospitalId,
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Edit User" : "Create User"}
          </DialogTitle>

          <DialogDescription>
            {isEdit
              ? "Update the user information."
              : "Register a new user."}
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit(submitHandler)}
          className="space-y-5"
        >
          {/* Username */}
          <div className="space-y-2">
            <label  
              htmlFor="username" 
              className="text-sm font-medium">
                Username
            </label>

            <Input 
              id="username"
              {...register("username")} 
            />

            {errors.username && (
              <p className="text-sm text-red-500">
                {errors.username.message}
              </p>
            )}
          </div>

          {/* Email */}
          <div className="space-y-2">
            <label 
              htmlFor="email"
              className="text-sm font-medium">
              Email
            </label>

            <Input
              id="email"
              type="email"
              {...register("email")}
            />

            {errors.email && (
              <p className="text-sm text-red-500">
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Password */}
          {!isEdit && (
            <div className="space-y-2">
              <label 
                htmlFor="password"
                className="text-sm font-medium">
                Password
              </label>

              <Input
                id="password"
                type="password"
                {...register("password")}
              />

              {"password" in errors && errors.password && (
                <p className="text-sm text-red-500">
                  {String(errors.password.message)}
                </p>
              )}
            </div>
          )}

          {/* Role */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Role
            </label>

            <Controller
              control={control}
              name="role"
              render={({ field }) => (
                <Select
                  value={field.value}
                  onValueChange={field.onChange}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Role" />
                  </SelectTrigger>

                  <SelectContent>
                    <SelectItem value="ADMIN">
                      Administrator
                    </SelectItem>

                    <SelectItem value="DOCTOR">
                      Doctor
                    </SelectItem>

                    <SelectItem value="RESEARCHER">
                      Researcher
                    </SelectItem>
                  </SelectContent>
                </Select>
              )}
            />

            {errors.role && (
              <p className="text-sm text-red-500">
                {errors.role.message}
              </p>
            )}
          </div>

          {/* Hospital */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Hospital
            </label>

            <Controller
              control={control}
              name="hospitalId"
              render={({ field }) => (
                <Select
                  value={String(field.value)}
                  onValueChange={(value) =>
                    field.onChange(Number(value))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select Hospital" />
                  </SelectTrigger>

                  <SelectContent>
                    {hospitals.length === 0 ? (
                      <SelectItem value="0" disabled>
                        No hospitals available
                      </SelectItem>
                    ) : (
                      hospitals.map((hospital) => (
                        <SelectItem
                          key={hospital.id}
                          value={String(hospital.id)}
                        >
                          {hospital.name} ({hospital.code})
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              )}
            />

            {errors.hospitalId && (
              <p className="text-sm text-red-500">
                {errors.hospitalId.message}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              disabled={loading || hospitals.length === 0}
            >
              {loading
                ? "Saving..."
                : isEdit
                ? "Update User"
                : "Create User"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}