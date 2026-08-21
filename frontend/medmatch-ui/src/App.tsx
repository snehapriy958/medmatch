import { BrowserRouter, Routes, Route } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import DashboardLayout from "./components/layout/DashboardLayout";

import Dashboard from "./pages/Dashboard";
import Patients from "./pages/Patients";
import ClinicalTrials from "./pages/ClinicalTrials";
import Matching from "./pages/Matching";
import Reports from "./pages/Reports";
import AuditLogs from "./pages/AuditLogs";
import Settings from "./pages/Settings";
import Login from "./pages/Login";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<Login />} />

          {/* System dashboard */}
          <Route
            path="/"
            element={
              <ProtectedRoute route="/">
                <DashboardLayout>
                  <Dashboard />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />

          {/* Patients */}
          <Route
            path="/patients"
            element={
              <ProtectedRoute route="/patients">
                <DashboardLayout>
                  <Patients />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />

          {/* Clinical trials */}
          <Route
            path="/trials"
            element={
              <ProtectedRoute route="/trials">
                <DashboardLayout>
                  <ClinicalTrials />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />

          {/* AI matching */}
          <Route
            path="/matching"
            element={
              <ProtectedRoute route="/matching">
                <DashboardLayout>
                  <Matching />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />

          {/* Reports */}
          <Route
            path="/reports"
            element={
              <ProtectedRoute route="/reports">
                <DashboardLayout>
                  <Reports />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />

          {/* Audit logs */}
          <Route
            path="/audit"
            element={
              <ProtectedRoute route="/audit">
                <DashboardLayout>
                  <AuditLogs />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />

          {/* Account settings */}
          <Route
            path="/settings"
            element={
              <ProtectedRoute route="/settings">
                <DashboardLayout>
                  <Settings />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;