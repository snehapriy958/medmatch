import { authApi } from "@/api/axios";
import type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
} from "../types/user";

class UserService {
  /**
   * Get all users.
   */
  async getUsers(): Promise<User[]> {
    const response = await authApi.get<User[]>("/users");
    return response.data;
  }

  /**
   * Get a user by ID.
   */
  async getUser(id: number): Promise<User> {
    const response = await authApi.get<User>(`/users/${id}`);
    return response.data;
  }

  /**
   * Register a new user.
   */
  async createUser(
    request: CreateUserRequest
  ): Promise<void> {
    await authApi.post(
      "/register",
      request
    );
  }

  /**
   * Update an existing user.
   */
  async updateUser(
    id: number,
    request: UpdateUserRequest
  ): Promise<User> {
    const response = await authApi.put<User>(
      `/users/${id}`,
      request
    );

    return response.data;
  }

  /**
   * Delete a user.
   */
  async deleteUser(id: number): Promise<void> {
    await authApi.delete(`/users/${id}`);
  }
}

export const userService = new UserService();