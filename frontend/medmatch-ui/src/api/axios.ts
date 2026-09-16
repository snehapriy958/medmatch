import axios, { type InternalAxiosRequestConfig } from "axios";

const AUTH_BASE_URL =
  import.meta.env.VITE_AUTH_API_URL ?? "/api/auth";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "/api";

const AI_BASE_URL =
  import.meta.env.VITE_AI_API_URL ?? "/api/ai";

const TOKEN_KEY = "medmatch_access_token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

function attachAuthHeader(
  config: InternalAxiosRequestConfig
): InternalAxiosRequestConfig {
  const token = getStoredToken();

  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }

  return config;
}

function handleAuthError(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.status === 401) {
    clearStoredToken();

    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }

  return Promise.reject(error);
}

/**
 * Spring Boot authentication endpoints.
 *
 * Example:
 * /api/auth/login
 */
export const authApiClient = axios.create({
  baseURL: AUTH_BASE_URL,
});

/**
 * Spring Boot application endpoints.
 *
 * Example:
 * /api/patients
 * /api/trials
 *
 * API modules using this client should NOT include
 * "/api" again in their endpoint paths.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

/**
 * FastAPI AI service endpoints.
 *
 * Example:
 * /api/ai/api/matching/search
 */
export const aiApiClient = axios.create({
  baseURL: AI_BASE_URL,
});

for (const client of [
  authApiClient,
  apiClient,
  aiApiClient,
]) {
  client.interceptors.request.use(attachAuthHeader);

  client.interceptors.response.use(
    (response) => response,
    handleAuthError
  );
}