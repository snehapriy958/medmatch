import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { decodeToken, isTokenExpired } from "@/auth/jwt";
import {
  getAccessToken,
  removeAccessToken,
  setAccessToken,
} from "@/auth/token";
import { authService } from "@/features/auth/api/auth.service";

import type {
  AuthenticatedUser,
  LoginRequest,
} from "@/features/auth/types/auth";

interface AuthContextType {
  user: AuthenticatedUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login(request: LoginRequest): Promise<void>;
  logout(): void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Restore authentication state from JWT.
   */
  const restoreSession = useCallback(() => {
    const token = getAccessToken();

    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    if (isTokenExpired(token)) {
      removeAccessToken();
      setUser(null);
      setIsLoading(false);
      return;
    }

    const payload = decodeToken(token);

    setUser({
      id: payload.sub,
      email: payload.email,
      role: payload.role,
      hospitalId: payload.hospital_id,
    });

    setIsLoading(false);
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  const login = useCallback(
    async (request: LoginRequest) => {
      const response = await authService.login(request);

      setAccessToken(response.accessToken);

      const payload = decodeToken(response.accessToken);

      setUser({
        id: payload.sub,
        email: payload.email,
        role: payload.role,
        hospitalId: payload.hospital_id,
      });
    },
    []
  );

  const logout = useCallback(() => {
    removeAccessToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout,
    }),
    [user, isLoading, login, logout]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}