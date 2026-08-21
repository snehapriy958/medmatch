/* eslint-disable react-refresh/only-export-components */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  login as loginRequest,
  getCurrentUser,
} from "../api/authApi";

import {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
} from "../api/axios";

import type { CurrentUser } from "../types/auth";

interface AuthContextValue {
  user: CurrentUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);

  const [isLoading, setIsLoading] = useState(
    () => getStoredToken() !== null
  );

  useEffect(() => {
    const token = getStoredToken();

    if (!token) {
      return;
    }

    async function restoreSession() {
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch {
        clearStoredToken();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    restoreSession();
  }, []);

  async function login(email: string, password: string) {
    const { accessToken } = await loginRequest({
      email,
      password,
    });

    setStoredToken(accessToken);

    const currentUser = await getCurrentUser();

    setUser(currentUser);
  }

  function logout() {
    clearStoredToken();
    setUser(null);
    window.location.href = "/login";
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within AuthProvider"
    );
  }

  return context;
}