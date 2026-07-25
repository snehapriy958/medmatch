import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import ProtectedRoute from "@/auth/ProtectedRoute";

import LoginPage from "@/features/auth/pages/LoginPage";
import DashboardPage from "@/features/dashboard/pages/DashboardPage";
import HospitalsPage from "@/features/hospitals/pages/HospitalsPage";
import { MatchingPage } from "@/features/matching/pages/MatchingPage";
import TrialsPage from "@/features/trials/pages/TrialsPage";
import { UsersPage } from "@/features/users/pages/UsersPage";
import { PatientsPage } from "@/features/patients/pages/PatientsPage";
import { DashboardLayout } from "@/layouts/DashboardLayout";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Route */}
        <Route
          path="/login"
          element={<LoginPage />}
        />

        {/* Dashboard */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <DashboardPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* Users */}
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <UsersPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* Hospitals */}
        <Route
          path="/hospitals"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <HospitalsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* Clinical Trials */}
        <Route
          path="/trials"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TrialsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />


        
        {/* Patients */}
        <Route
          path="/patients"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PatientsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />


        {/* AI Matching */}
        <Route
          path="/matching"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MatchingPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* Redirects */}
        <Route
          path="/"
          element={<Navigate replace to="/dashboard" />}
        />

        <Route
          path="*"
          element={<Navigate replace to="/" />}
        />
      </Routes>
    </BrowserRouter>
  );
}