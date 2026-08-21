import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../context/AuthContext";
import {
  canAccessRoute,
  getDefaultRoute,
  type AppRoute,
} from "./permissions";

interface ProtectedRouteProps {
  children: ReactNode;
  route?: AppRoute;
}

export default function ProtectedRoute({
  children,
  route,
}: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-text-muted">
        Loading...
      </div>
    );
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname }}
      />
    );
  }

  /*
   * If a route declares an explicit permission requirement,
   * enforce it using the centralized role matrix.
   */
  if (route && !canAccessRoute(user.role, route)) {
    const fallbackRoute = getDefaultRoute();

    if (fallbackRoute !== route) {
      return <Navigate to={fallbackRoute} replace />;
    }
  }

  return <>{children}</>;
}