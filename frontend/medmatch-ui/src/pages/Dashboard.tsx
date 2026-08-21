import { useEffect, useState } from "react";
import {
  Activity,
  BarChart3,
  ClipboardCheck,
  FileText,
  FlaskConical,
  Hospital,
  Search,
  ShieldCheck,
  Stethoscope,
  TrendingDown,
  TrendingUp,
  Upload,
  Users,
} from "lucide-react";

import { listPatients } from "../api/patientApi";
import { listTrials } from "../api/trialApi";
import { getSystemDashboard } from "../api/dashboardApi";
import { useAuth } from "../context/AuthContext";

import Card from "../components/ui/Card";

import type {
  ServiceStatus,
  SystemDashboardResponse,
} from "../types/dashboard";

import type { UserRole } from "../types/auth";

const metricIcons = {
  USERS: Users,
  ACTIVE_USERS: Activity,
  HOSPITAL: Hospital,
} as const;

const statusColor: Record<ServiceStatus, string> = {
  UP: "bg-status-up",
  DOWN: "bg-status-down",
  UNKNOWN: "bg-status-unknown",
};

type ServiceHealthKey = Exclude<
  keyof SystemDashboardResponse["systemHealth"],
  "overallStatus"
>;

const serviceLabels: {
  key: ServiceHealthKey;
  label: string;
}[] = [
  { key: "authServiceStatus", label: "Spring Boot Auth" },
  { key: "aiServiceStatus", label: "FastAPI AI Service" },
  { key: "databaseStatus", label: "PostgreSQL" },
  { key: "redisStatus", label: "Redis" },
  { key: "vectorSearchStatus", label: "Vector Search" },
];

function getRoleTitle(role: UserRole): string {
  switch (role) {
    case "SYSTEM_ADMIN":
      return "System Overview";

    case "HOSPITAL_ADMIN":
      return "Hospital Overview";

    case "RESEARCH_COORDINATOR":
      return "Research Coordinator Dashboard";

    case "PHYSICIAN":
      return "Physician Dashboard";

    case "TRIAL_SPONSOR":
      return "Trial Sponsor Dashboard";

    case "PATIENT":
      return "Patient Dashboard";

    default:
      return "Dashboard";
  }
}

function getRoleSubtitle(role: UserRole): string {
  switch (role) {
    case "SYSTEM_ADMIN":
      return "Monitor and manage the entire MedMatch platform.";

    case "HOSPITAL_ADMIN":
      return "Manage your hospital's users, trials, patients, and activity.";

    case "RESEARCH_COORDINATOR":
      return "Manage clinical trials, patients, matching, and research activity.";

    case "PHYSICIAN":
      return "Review your patients and find relevant clinical trials.";

    case "TRIAL_SPONSOR":
      return "Monitor your clinical trials and enrollment activity.";

    case "PATIENT":
      return "Find clinical trials that may be relevant to you.";

    default:
      return "Welcome to MedMatch.";
  }
}

function RoleMetric({
  title,
  value,
  description,
  icon: Icon,
}: {
  title: string;
  value: string;
  description: string;
  icon: typeof Users;
}) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <p className="text-sm text-text-muted">{title}</p>

        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-bg text-primary">
          <Icon size={18} />
        </div>
      </div>

      <p className="mt-2 text-2xl font-semibold text-text">{value}</p>

      <p className="mt-1 text-xs text-text-muted">{description}</p>
    </Card>
  );
}

function QuickAction({
  title,
  description,
  icon: Icon,
}: {
  title: string;
  description: string;
  icon: typeof Search;
}) {
  return (
    <div className="rounded-lg border border-border p-4 transition hover:bg-surface-alt">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-bg text-primary">
          <Icon size={18} />
        </div>

        <div>
          <p className="text-sm font-medium text-text">{title}</p>

          <p className="mt-1 text-xs text-text-muted">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * System Administrator dashboard.
 *
 * This is the only role that requests the system-level dashboard endpoint.
 * Other roles get their own role-specific dashboard UI and therefore do
 * not attempt to access /dashboard/system.
 */
function SystemAdminDashboard({
  data,
}: {
  data: SystemDashboardResponse;
}) {
  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.metrics.map((metric) => {
          const Icon =
            metricIcons[
              metric.icon as keyof typeof metricIcons
            ] ?? Users;

          const isPositive = metric.growthPercentage >= 0;

          return (
            <Card key={metric.title}>
              <div className="flex items-center justify-between">
                <p className="text-sm text-text-muted">
                  {metric.title}
                </p>

                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-bg text-primary">
                  <Icon size={18} />
                </div>
              </div>

              <p className="mt-2 text-2xl font-semibold text-text">
                {metric.value}
              </p>

              <div
                className={`mt-1 flex items-center gap-1 text-xs ${
                  isPositive
                    ? "text-status-up"
                    : "text-status-down"
                }`}
              >
                {isPositive ? (
                  <TrendingUp size={14} />
                ) : (
                  <TrendingDown size={14} />
                )}

                {metric.growthPercentage}% ·{" "}
                {metric.comparison}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Top hospitals */}
      <Card className="overflow-x-auto p-0">
        <div className="border-b border-border p-5">
          <h2 className="text-sm font-semibold text-text">
            Top Hospitals
          </h2>
        </div>

        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs uppercase text-text-muted">
              <th className="px-5 py-3">Hospital</th>
              <th className="px-5 py-3">Users</th>
              <th className="px-5 py-3">Patients</th>
              <th className="px-5 py-3">Active Trials</th>
              <th className="px-5 py-3">Matches</th>
            </tr>
          </thead>

          <tbody>
            {data.topHospitals.map((hospital) => (
              <tr
                key={hospital.hospitalId}
                className="border-t border-border"
              >
                <td className="px-5 py-3 font-medium text-text">
                  {hospital.hospitalName}
                </td>

                <td className="px-5 py-3 text-text-muted">
                  {hospital.totalUsers}
                </td>

                <td className="px-5 py-3 text-text-muted">
                  {hospital.totalPatients}
                </td>

                <td className="px-5 py-3 text-text-muted">
                  {hospital.activeTrials}
                </td>

                <td className="px-5 py-3 text-text-muted">
                  {hospital.matchesGenerated}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Audit + system health */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-sm font-semibold text-text">
            Audit Summary
          </h2>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-text-muted">Total Events</p>

              <p className="text-lg font-semibold text-text">
                {data.auditSummary.totalEvents}
              </p>
            </div>

            <div>
              <p className="text-text-muted">User Activities</p>

              <p className="text-lg font-semibold text-text">
                {data.auditSummary.userActivities}
              </p>
            </div>

            <div>
              <p className="text-text-muted">Data Access</p>

              <p className="text-lg font-semibold text-text">
                {data.auditSummary.dataAccess}
              </p>
            </div>

            <div>
              <p className="text-text-muted">
                Security Events
              </p>

              <p className="text-lg font-semibold text-text">
                {data.auditSummary.securityEvents}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-text">
              System Health
            </h2>

            <span className="rounded-full bg-primary-bg px-2 py-0.5 text-xs font-medium text-primary-dark">
              {data.systemHealth.overallStatus}
            </span>
          </div>

          <div className="space-y-3">
            {serviceLabels.map(({ key, label }) => (
              <div
                key={key}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-text-muted">
                  {label}
                </span>

                <span className="flex items-center gap-2">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      statusColor[data.systemHealth[key]]
                    }`}
                  />

                  {data.systemHealth[key]}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

/**
 * Role-specific dashboard.
 *
 * Real patient/trial counts are loaded only for roles that
 * are allowed to access the corresponding backend endpoints.
 *
 * Backend remains the actual authorization and tenant-isolation
 * boundary.
 */
function RoleDashboard({
  role,
}: {
  role: UserRole;
}) {
  const [patientCount, setPatientCount] = useState<number | null>(
    null
  );

  const [activeTrialCount, setActiveTrialCount] = useState<
    number | null
  >(null);

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboardData() {
      const canLoadPatients =
        role === "HOSPITAL_ADMIN" ||
        role === "RESEARCH_COORDINATOR" ||
        role === "PHYSICIAN";

      const canLoadTrials =
        role === "HOSPITAL_ADMIN" ||
        role === "RESEARCH_COORDINATOR" ||
        role === "PHYSICIAN" ||
        role === "TRIAL_SPONSOR";

      try {
        const patientPromise = canLoadPatients
          ? listPatients()
          : Promise.resolve(null);

        const trialPromise = canLoadTrials
          ? listTrials()
          : Promise.resolve(null);

        const [patientsResponse, trialsResponse] =
          await Promise.all([
            patientPromise,
            trialPromise,
          ]);

        if (cancelled) {
          return;
        }

        if (patientsResponse) {
          setPatientCount(patientsResponse.total);
        }

        if (trialsResponse) {
          setActiveTrialCount(
            trialsResponse.filter((trial) => {
              const status = trial.status?.trim().toUpperCase();

              return (
                status === "RECRUITING" ||
                status === "ACTIVE"
              );
            }).length
          );
        }

        setIsLoading(false);
      } catch {
        if (cancelled) {
          return;
        }

        setPatientCount(null);
        setActiveTrialCount(null);
        setIsLoading(false);
      }
    }

    loadDashboardData();

    return () => {
      cancelled = true;
    };
  }, [role]);

  const patientMetricValue = isLoading
    ? "..."
    : patientCount === null
      ? "—"
      : String(patientCount);

  const trialMetricValue = isLoading
    ? "..."
    : activeTrialCount === null
      ? "—"
      : String(activeTrialCount);

  switch (role) {
    case "HOSPITAL_ADMIN":
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <RoleMetric
              title="Hospital Users"
              value="—"
              description="Users in your hospital"
              icon={Users}
            />

            <RoleMetric
              title="Patients"
              value={patientMetricValue}
              description="Patients in your hospital"
              icon={Users}
            />

            <RoleMetric
              title="Active Trials"
              value={trialMetricValue}
              description="Recruiting or active trials"
              icon={FlaskConical}
            />

            <RoleMetric
              title="Matches Generated"
              value="—"
              description="AI matching activity"
              icon={Activity}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Hospital Management
              </h2>

              <div className="space-y-3">
                <QuickAction
                  title="Manage Users"
                  description="Manage hospital users and roles."
                  icon={Users}
                />

                <QuickAction
                  title="Manage Patients"
                  description="Review patients belonging to your hospital."
                  icon={Users}
                />

                <QuickAction
                  title="Manage Clinical Trials"
                  description="Review and manage available trials."
                  icon={FlaskConical}
                />
              </div>
            </Card>

            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Hospital Activity
              </h2>

              <div className="space-y-3">
                <QuickAction
                  title="Matching Activity"
                  description="Review AI-powered matching activity."
                  icon={Search}
                />

                <QuickAction
                  title="Reports"
                  description="Review hospital reports and analytics."
                  icon={FileText}
                />

                <QuickAction
                  title="Audit Logs"
                  description="Review hospital-level audit activity."
                  icon={ShieldCheck}
                />
              </div>
            </Card>
          </div>
        </div>
      );

    case "RESEARCH_COORDINATOR":
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <RoleMetric
              title="Patients"
              value={patientMetricValue}
              description="Patients available for review"
              icon={Users}
            />

            <RoleMetric
              title="Active Trials"
              value={trialMetricValue}
              description="Recruiting or active trials"
              icon={FlaskConical}
            />

            <RoleMetric
              title="Matches"
              value="—"
              description="AI matching results"
              icon={Search}
            />

            <RoleMetric
              title="Reports"
              value="—"
              description="Generated research reports"
              icon={FileText}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Research Actions
              </h2>

              <div className="space-y-3">
                <QuickAction
                  title="Upload Trial Protocol"
                  description="Upload a clinical trial PDF for processing."
                  icon={Upload}
                />

                <QuickAction
                  title="Find Trial Matches"
                  description="Evaluate patient eligibility against trials."
                  icon={Search}
                />

                <QuickAction
                  title="Review Trials"
                  description="View and manage clinical trial criteria."
                  icon={FlaskConical}
                />
              </div>
            </Card>

            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Research Overview
              </h2>

              <div className="space-y-3">
                <QuickAction
                  title="Patients"
                  description="Review patients available for matching."
                  icon={Users}
                />

                <QuickAction
                  title="Matching Results"
                  description="Review AI eligibility evaluations."
                  icon={ClipboardCheck}
                />

                <QuickAction
                  title="Reports"
                  description="Review available research reports."
                  icon={BarChart3}
                />
              </div>
            </Card>
          </div>
        </div>
      );

    case "PHYSICIAN":
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <RoleMetric
              title="Patients"
              value={patientMetricValue}
              description="Patients in your hospital"
              icon={Users}
            />

            <RoleMetric
              title="Trial Matches"
              value="—"
              description="Potential clinical trial matches"
              icon={Search}
            />

            <RoleMetric
              title="Clinical Trials"
              value={trialMetricValue}
              description="Recruiting or active trials"
              icon={FlaskConical}
            />

            <RoleMetric
              title="Reports"
              value="—"
              description="Patient and matching reports"
              icon={FileText}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Clinical Actions
              </h2>

              <div className="space-y-3">
                <QuickAction
                  title="My Patients"
                  description="Review your patients and clinical information."
                  icon={Users}
                />

                <QuickAction
                  title="Find Trial Matches"
                  description="Search for potentially suitable trials."
                  icon={Search}
                />

                <QuickAction
                  title="Clinical Trials"
                  description="Review available clinical trials."
                  icon={FlaskConical}
                />
              </div>
            </Card>

            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Matching Overview
              </h2>

              <QuickAction
                title="AI Eligibility Evaluation"
                description="Evaluate patient notes against relevant trial criteria."
                icon={Stethoscope}
              />
            </Card>
          </div>
        </div>
      );

    case "TRIAL_SPONSOR":
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <RoleMetric
              title="My Trials"
              value={trialMetricValue}
              description="Recruiting or active trials"
              icon={FlaskConical}
            />

            <RoleMetric
              title="Sites"
              value="—"
              description="Participating hospital sites"
              icon={Hospital}
            />

            <RoleMetric
              title="Patients"
              value="—"
              description="Patients across your trials"
              icon={Users}
            />

            <RoleMetric
              title="Reports"
              value="—"
              description="Trial reports"
              icon={FileText}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Trial Management
              </h2>

              <div className="space-y-3">
                <QuickAction
                  title="Clinical Trials"
                  description="Review your clinical trials."
                  icon={FlaskConical}
                />

                <QuickAction
                  title="Trial Reports"
                  description="Review trial performance and reports."
                  icon={FileText}
                />
              </div>
            </Card>

            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Trial Activity
              </h2>

              <QuickAction
                title="Trial Overview"
                description="Monitor trial activity and available information."
                icon={BarChart3}
              />
            </Card>
          </div>
        </div>
      );

    case "PATIENT":
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <RoleMetric
              title="Potential Matches"
              value="—"
              description="Trials that may be relevant to you"
              icon={Search}
            />

            <RoleMetric
              title="High Confidence"
              value="—"
              description="Strong potential matches"
              icon={ClipboardCheck}
            />

            <RoleMetric
              title="Under Review"
              value="—"
              description="Matches awaiting review"
              icon={Activity}
            />

            <RoleMetric
              title="Saved Trials"
              value="—"
              description="Trials saved for later"
              icon={FlaskConical}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                Find Clinical Trials
              </h2>

              <div className="space-y-3">
                <QuickAction
                  title="Find Trials"
                  description="Discover clinical trials that may be relevant to your profile."
                  icon={Search}
                />

                <QuickAction
                  title="My Matches"
                  description="Review your clinical trial matches."
                  icon={ClipboardCheck}
                />

                <QuickAction
                  title="Recommended Trials"
                  description="View recommended trials based on your available information."
                  icon={FlaskConical}
                />
              </div>
            </Card>

            <Card>
              <h2 className="mb-4 text-sm font-semibold text-text">
                My Information
              </h2>

              <QuickAction
                title="My Profile"
                description="Review and maintain your personal information."
                icon={Users}
              />
            </Card>
          </div>
        </div>
      );

    default:
      return null;
  }
}

export default function Dashboard() {
  const { user } = useAuth();

  const [systemData, setSystemData] =
    useState<SystemDashboardResponse | null>(null);

  const [isLoading, setIsLoading] = useState(
    user?.role === "SYSTEM_ADMIN"
  );

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.role !== "SYSTEM_ADMIN") {
      return;
    }

    let cancelled = false;

    async function loadSystemDashboard() {
      try {
        const dashboard = await getSystemDashboard();

        if (cancelled) {
          return;
        }

        setSystemData(dashboard);
        setError(null);
        setIsLoading(false);
      } catch {
        if (cancelled) {
          return;
        }

        setError("Could not load system dashboard data.");
        setIsLoading(false);
      }
    }

    loadSystemDashboard();

    return () => {
      cancelled = true;
    };
  }, [user?.role]);

  if (!user) {
    return null;
  }

  const role = user.role;

  return (
    <div className="space-y-6">
      {/* Dashboard heading */}
      <div>
        <h1 className="text-xl font-semibold text-text">
          {getRoleTitle(role)}
        </h1>

        <p className="mt-1 text-sm text-text-muted">
          {getRoleSubtitle(role)}
        </p>
      </div>

      {/* System Administrator dashboard */}
      {role === "SYSTEM_ADMIN" && (
        <>
          {isLoading && (
            <p className="text-sm text-text-muted">
              Loading system dashboard...
            </p>
          )}

          {error && (
            <Card>
              <p className="text-sm text-status-down">
                {error}
              </p>
            </Card>
          )}

          {!isLoading && !error && systemData && (
            <SystemAdminDashboard data={systemData} />
          )}
        </>
      )}

      {/* All other role dashboards */}
      {role !== "SYSTEM_ADMIN" && (
        <RoleDashboard role={role} />
      )}
    </div>
  );
}