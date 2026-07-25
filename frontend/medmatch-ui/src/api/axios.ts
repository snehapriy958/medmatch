import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

import { getAccessToken, removeAccessToken } from "@/auth/token";

const DEFAULT_HEADERS = {
  "Content-Type": "application/json",
};

export const authApi = axios.create({
  baseURL: import.meta.env.VITE_AUTH_API,
  timeout: 10000,
  headers: DEFAULT_HEADERS,
});

export const aiApi = axios.create({
  baseURL: import.meta.env.VITE_AI_API,
  timeout: 30000,
});

console.log("========== AXIOS ==========");
console.log("ENV AUTH =", import.meta.env.VITE_AUTH_API);
console.log("ENV AI   =", import.meta.env.VITE_AI_API);
console.log("AUTH API =", authApi.defaults.baseURL);
console.log("AI API   =", aiApi.defaults.baseURL);
console.log("===========================");

/**
 * Adds the JWT access token to every request.
 */
const attachAccessToken = (
  config: InternalAxiosRequestConfig
): InternalAxiosRequestConfig => {
  const token = getAccessToken();

  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }

  return config;
};

/**
 * Handles unauthorized responses globally.
 */
const handleUnauthorized = (error: AxiosError) => {
  if (error.response?.status === 401) {
    removeAccessToken();

    window.location.replace("/login");
  }

  return Promise.reject(error);
};

/* ------------------------- */
/* Request Interceptors       */
/* ------------------------- */

authApi.interceptors.request.use(attachAccessToken);

aiApi.interceptors.request.use(attachAccessToken);

/* ------------------------- */
/* Response Interceptors      */
/* ------------------------- */

authApi.interceptors.response.use(
  (response) => response,
  handleUnauthorized
);

aiApi.interceptors.response.use(
  (response) => response,
  handleUnauthorized
);