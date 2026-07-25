import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { useAuth } from "@/auth/useAuth";

export function Topbar() {
  const navigate = useNavigate();

  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-8 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">
          MedMatch Clinical Trial Platform
        </h2>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-right">
          <p className="font-medium text-slate-900">
            {user?.email}
          </p>

          <div className="mt-1 flex justify-end">
            <Badge variant="secondary">
              {user?.role}
            </Badge>
          </div>
        </div>

        <Button
          variant="destructive"
          onClick={handleLogout}
        >
          Logout
        </Button>
      </div>
    </header>
  );
}