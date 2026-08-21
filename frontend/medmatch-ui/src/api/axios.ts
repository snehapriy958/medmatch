import axios, { type InternalAxiosRequestConfig } from "axios";

const AUTH_BASE_URL = import.meta.env.VITE_AUTH_API_URL ?? "http://localhost:8081";
const AI_BASE_URL = import.meta.env.VITE_AI_API_URL ?? "http://127.0.0.1:8000";

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

function attachAuthHeader(config: InternalAxiosRequestConfig) {
  const token = getStoredToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
}

function handleAuthError(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.status === 401) {
    clearStoredToken();
    // Hard redirect (not react-router navigate) since this runs outside
    // the component tree. Avoids infinite redirect loop by checking path.
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }
  return Promise.reject(error);
}

export const authApiClient = axios.create({ baseURL: AUTH_BASE_URL });
export const aiApiClient = axios.create({ baseURL: AI_BASE_URL });

for (const client of [authApiClient, aiApiClient]) {
  client.interceptors.request.use(attachAuthHeader);
  client.interceptors.response.use((res) => res, handleAuthError);
}