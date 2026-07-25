import { NavLink } from "react-router-dom";

import { useAuth } from "@/auth/useAuth";

interface SidebarItem {
  label: string;
  path: string;
}

const adminMenu: SidebarItem[] = [
  {
    label: "Dashboard",
    path: "/dashboard",
  },
  {
    label: "Hospitals",
    path: "/hospitals",
  },
  {
    label: "Users",
    path: "/users",
  },
  {
    label: "Patients",
    path: "/patients",
  },
  {
    label: "Clinical Trials",
    path: "/trials",
  },
  {
    label: "AI Matching",
    path: "/matching",
  },
];

const doctorMenu: SidebarItem[] = [
  {
    label: "Dashboard",
    path: "/dashboard",
  },
  {
    label: "Patients",
    path: "/patients",
  },
  {
    label: "Matching",
    path: "/matching",
  },
];

const researcherMenu: SidebarItem[] = [
  {
    label: "Dashboard",
    path: "/dashboard",
  },
  {
    label: "Clinical Trials",
    path: "/trials",
  },
  {
    label: "Matching",
    path: "/matching",
  },
];

export function Sidebar() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  const menu =
    user.role === "ADMIN"
      ? adminMenu
      : user.role === "DOCTOR"
      ? doctorMenu
      : researcherMenu;

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-white">
      <div className="border-b px-6 py-5">
        <h1 className="text-2xl font-bold text-blue-600">
          MedMatch
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          Clinical Trial Platform
        </p>
      </div>

      <nav className="flex-1 space-y-2 p-4">
        {menu.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              [
                "block rounded-lg px-4 py-3 font-medium transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900",
              ].join(" ")
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}