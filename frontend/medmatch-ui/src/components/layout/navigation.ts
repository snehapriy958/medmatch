import {
  Building2,
  ClipboardList,
  FileSearch,
  Home,
  Shield,
  Stethoscope,
  Users,
} from "lucide-react";

export type UserRole = "ADMIN" | "DOCTOR" | "RESEARCHER";

export interface NavigationItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

export const navigation: Record<UserRole, NavigationItem[]> = {
  ADMIN: [
    {
      label: "Dashboard",
      path: "/dashboard",
      icon: Home,
    },
    {
      label: "Hospitals",
      path: "/hospitals",
      icon: Building2,
    },
    {
      label: "Users",
      path: "/users",
      icon: Users,
    },
    {
      label: "Audit Logs",
      path: "/audit-logs",
      icon: Shield,
    },
  ],

  DOCTOR: [
    {
      label: "Dashboard",
      path: "/dashboard",
      icon: Home,
    },
    {
      label: "Patients",
      path: "/patients",
      icon: Stethoscope,
    },
    {
      label: "Matching",
      path: "/matching",
      icon: ClipboardList,
    },
  ],

  RESEARCHER: [
    {
      label: "Dashboard",
      path: "/dashboard",
      icon: Home,
    },
    {
      label: "Trials",
      path: "/trials",
      icon: FileSearch,
    },
    {
      label: "Matching",
      path: "/matching",
      icon: ClipboardList,
    },
  ],
};