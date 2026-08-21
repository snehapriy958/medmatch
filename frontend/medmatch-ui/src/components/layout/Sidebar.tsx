import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  FlaskConical,
  Search,
  FileText,
  ShieldCheck,
  Settings,
  Cross,
  X,
} from "lucide-react";

import { useAuth } from "../../context/AuthContext";
import {
  canAccessRoute,
  type AppRoute,
} from "../../auth/permissions";
import type { UserRole } from "../../types/auth";

interface NavItem {
  label: string;
  icon: typeof LayoutDashboard;
  to: AppRoute;
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    to: "/",
  },
  {
    label: "Patients",
    icon: Users,
    to: "/patients",
  },
  {
    label: "Clinical Trials",
    icon: FlaskConical,
    to: "/trials",
  },
  {
    label: "Matching",
    icon: Search,
    to: "/matching",
  },
  {
    label: "Reports",
    icon: FileText,
    to: "/reports",
  },
  {
    label: "Audit Logs",
    icon: ShieldCheck,
    to: "/audit",
  },
  {
    label: "Settings",
    icon: Settings,
    to: "/settings",
  },
];

function getDashboardLabel(role: UserRole): string {
  switch (role) {
    case "SYSTEM_ADMIN":
      return "System Overview";

    case "HOSPITAL_ADMIN":
      return "Hospital Overview";

    case "RESEARCH_COORDINATOR":
      return "Dashboard";

    case "PHYSICIAN":
      return "Dashboard";

    case "TRIAL_SPONSOR":
      return "Dashboard";

    case "PATIENT":
      return "Dashboard";

    default:
      return "Dashboard";
  }
}

export default function Sidebar({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const { user } = useAuth();

  /*
   * Only authenticated users can reach the protected application,
   * but keeping this guard makes the component safe if rendered
   * before authentication has finished restoring.
   */
  if (!user) {
    return null;
  }

  /*
   * The permissions matrix is the single source of truth.
   *
   * Sidebar visibility:
   *     role -> permissions.ts -> accessible routes
   *
   * Route protection:
   *     role -> ProtectedRoute -> accessible routes
   *
   * Therefore hiding an item here does not replace actual
   * authorization; it only prevents users from seeing links
   * they cannot access.
   */
  const visibleNavItems = navItems.filter((item) =>
    canAccessRoute(user.role, item.to)
  );

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/30 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 transform border-r border-border bg-surface p-6 transition-transform duration-200 md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-bg text-primary">
              <Cross size={18} />
            </div>

            <div>
              <p className="text-base font-semibold text-text">
                MedMatch
              </p>

              <p className="text-xs text-text-muted">
                Clinical Trial Matching
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-text-muted md:hidden"
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav
          className="space-y-1"
          aria-label="Main navigation"
        >
          {visibleNavItems.map(
            ({ label, icon: Icon, to }) => {
              const displayLabel =
                to === "/"
                  ? getDashboardLabel(user.role)
                  : label;

              return (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                      isActive
                        ? "bg-primary-bg text-primary-dark"
                        : "text-text-muted hover:bg-surface-alt hover:text-text"
                    }`
                  }
                >
                  <Icon size={18} />
                  {displayLabel}
                </NavLink>
              );
            }
          )}
        </nav>
      </aside>
    </>
  );
}