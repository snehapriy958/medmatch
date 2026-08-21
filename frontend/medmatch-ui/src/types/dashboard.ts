export interface DashboardMetric {
  title: string;
  value: number;
  growthPercentage: number;
  comparison: string;
  icon: "USERS" | "ACTIVE_USERS" | "HOSPITAL" | string;
}

export interface TopHospital {
  hospitalId: string;
  hospitalName: string;
  totalUsers: number;
  totalPatients: number;
  activeTrials: number;
  matchesGenerated: number;
}

export interface AuditSummary {
  totalEvents: number;
  userActivities: number;
  dataAccess: number;
  configurationChanges: number;
  securityEvents: number;
}

export type ServiceStatus = "UP" | "DOWN" | "UNKNOWN";

export interface SystemHealth {
  authServiceStatus: ServiceStatus;
  aiServiceStatus: ServiceStatus;
  databaseStatus: ServiceStatus;
  redisStatus: ServiceStatus;
  vectorSearchStatus: ServiceStatus;
  overallStatus: "HEALTHY" | "DEGRADED" | "DOWN";
}

export interface SystemDashboardResponse {
  metrics: DashboardMetric[];
  topHospitals: TopHospital[];
  auditSummary: AuditSummary;
  systemHealth: SystemHealth;
}