import { AlertTriangle, User } from "lucide-react";
import { useAuth } from "../context/AuthContext";

// There is no confirmed Settings/Preferences/Profile-update API — no
// controller, no OpenAPI path, nothing to PUT/PATCH against. This page
// deliberately does NOT invent an edit form. The account fields shown below
// come entirely from the CurrentUser object already fetched via /users/me
// (see AuthContext) — no new endpoint is called here.

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-text">Settings</h1>
        <p className="text-sm text-text-muted">Account information and preferences.</p>
      </div>

      <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800 shadow-sm">
        <AlertTriangle size={18} className="mt-0.5 shrink-0" />
        <div>
          <p className="font-medium">Settings isn't backed by an API yet</p>
          <p className="mt-1 text-amber-700">
            There's currently no Settings, Preferences, or profile-update endpoint in either
            service — no controller, no OpenAPI path, nothing to save changes to. The account
            details below are read-only, sourced from data already fetched when you logged in
            (<code className="rounded bg-amber-100 px-1 py-0.5">/users/me</code>). Editing will
            be added once a real backend contract exists for it.
          </p>
        </div>
      </div>

      {user && (
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-bg text-primary">
              <User size={18} />
            </div>
            <h2 className="text-sm font-semibold text-text">Account Information</h2>
          </div>

          <div className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
            <Field label="First name" value={user.firstName} />
            <Field label="Last name" value={user.lastName} />
            <Field label="Email" value={user.email} />
            <Field label="Phone" value={user.phone} />
            <Field label="Role" value={user.role.replaceAll("_", " ")} />
            <Field label="Status" value={user.status} />
            <Field label="Hospital ID" value={user.hospitalId} mono />
            <Field label="Account enabled" value={user.enabled ? "Yes" : "No"} />
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs text-text-muted">{label}</p>
      <p className={`font-medium text-text ${mono ? "font-mono text-xs" : ""}`}>{value}</p>
    </div>
  );
}
