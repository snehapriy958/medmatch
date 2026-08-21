import { useEffect, useState, type FormEvent } from "react";
import axios from "axios";
import {
  ShieldAlert,
  AlertCircle,
  Search,
  User,
} from "lucide-react";

import { getUserAuditLogs } from "../api/auditLogApi";
import { useAuth } from "../context/AuthContext";
import TableCard from "../components/common/TableCard";
import type { AuditLog } from "../types/auditLog";

const ADMIN_ROLES = ["SYSTEM_ADMIN", "HOSPITAL_ADMIN"];

function extractErrorMessage(
  err: unknown,
  fallback: string
): string {
  if (axios.isAxiosError(err)) {
    if (err.response?.status === 403) {
      return "You don't have permission to view audit logs.";
    }

    if (err.response?.status === 404) {
      return "No user found with that ID.";
    }
  }

  return fallback;
}

export default function AuditLogs() {
  const { user } = useAuth();

  const isAuthorized = user
    ? ADMIN_ROLES.includes(user.role)
    : false;

  const [lookupUserId, setLookupUserId] = useState<string>(
    user?.id ?? ""
  );

  const [inputValue, setInputValue] = useState<string>(
    user?.id ?? ""
  );

  const [logs, setLogs] = useState<AuditLog[]>([]);

  /*
   * If an authorized user already exists when this page mounts,
   * the first API request is expected immediately.
   */
  const [isLoading, setIsLoading] = useState<boolean>(
    Boolean(user?.id && isAuthorized)
  );

  const [loadError, setLoadError] = useState<string | null>(
    null
  );

  /*
   * Load audit logs whenever the selected user ID changes.
   *
   * Important:
   * This effect does NOT synchronously call setState before
   * starting the request. The state updates happen only when
   * the asynchronous API request resolves/rejects.
   */
  useEffect(() => {
    if (!isAuthorized || !lookupUserId) {
      return;
    }

    let cancelled = false;

    getUserAuditLogs(lookupUserId)
      .then((result) => {
        if (cancelled) {
          return;
        }

        setLogs(result);
        setLoadError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) {
          return;
        }

        setLogs([]);
        setLoadError(
          extractErrorMessage(
            err,
            "Could not load audit logs."
          )
        );
      })
      .finally(() => {
        if (cancelled) {
          return;
        }

        setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isAuthorized, lookupUserId]);

  function handleLookupSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const trimmed = inputValue.trim();

    if (!trimmed) {
      return;
    }

    /*
     * These state updates happen from the user event handler,
     * not synchronously inside an effect.
     */
    setIsLoading(true);
    setLoadError(null);
    setLogs([]);

    setLookupUserId(trimmed);
  }

  function viewUser(userId: string) {
    const trimmed = userId.trim();

    if (!trimmed) {
      return;
    }

    /*
     * These updates happen from a click event.
     */
    setInputValue(trimmed);
    setIsLoading(true);
    setLoadError(null);
    setLogs([]);

    setLookupUserId(trimmed);
  }

  if (!isAuthorized) {
    return (
      <div className="flex items-start gap-3 rounded-2xl border border-border bg-surface p-10 shadow-sm">
        <ShieldAlert
          size={20}
          className="mt-0.5 shrink-0 text-status-down"
        />

        <div>
          <p className="text-sm font-medium text-text">
            You don't have access to Audit Logs
          </p>

          <p className="mt-1 text-sm text-text-muted">
            This page requires the System Administrator or
            Hospital Administrator role.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="text-xl font-semibold text-text">
          Audit Logs
        </h1>

        <p className="text-sm text-text-muted">
          Showing audit history for a specific user ID. There is
          currently no hospital-wide audit endpoint — this always
          reflects one user's actions at a time, defaulting to
          your own.
        </p>
      </div>

      {/* User lookup */}
      <form
        onSubmit={handleLookupSubmit}
        className="flex flex-wrap items-end gap-3 rounded-2xl border border-border bg-surface p-5 shadow-sm"
      >
        <div className="min-w-[280px] flex-1">
          <label
            htmlFor="audit-user-id"
            className="mb-1 block text-sm font-medium text-text"
          >
            User ID
          </label>

          <input
            id="audit-user-id"
            name="audit-user-id"
            value={inputValue}
            onChange={(e) =>
              setInputValue(e.target.value)
            }
            placeholder="User UUID"
            autoComplete="off"
            className="w-full rounded-lg border border-border px-3 py-2 font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <button
          type="submit"
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark"
        >
          <Search size={16} />
          Look up
        </button>

        {user && (
          <button
            type="button"
            onClick={() => viewUser(user.id)}
            className="flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-surface-alt"
          >
            <User size={16} />
            My own logs
          </button>
        )}
      </form>

      {/* Loading */}
      {isLoading && (
        <div className="rounded-2xl border border-border bg-surface p-10 text-center text-sm text-text-muted shadow-sm">
          Loading audit logs...
        </div>
      )}

      {/* Error */}
      {!isLoading && loadError && (
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface p-10 text-sm text-status-down shadow-sm">
          <AlertCircle size={18} />
          {loadError}
        </div>
      )}

      {/* Empty state */}
      {!isLoading &&
        !loadError &&
        logs.length === 0 && (
          <div className="rounded-2xl border border-border bg-surface p-10 text-center shadow-sm">
            <p className="text-sm font-medium text-text">
              No audit log entries
            </p>

            <p className="mt-1 text-sm text-text-muted">
              This user has no recorded actions yet.
            </p>
          </div>
        )}

      {/* Audit table */}
      {!isLoading &&
        !loadError &&
        logs.length > 0 && (
          <TableCard
            title={`Audit Log Entries (${logs.length})`}
          >
            <div className="overflow-x-auto">
              <table className="w-full min-w-[960px] text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase text-text-muted">
                    <th className="px-5 py-3">
                      Timestamp
                    </th>

                    <th className="px-5 py-3">
                      Action
                    </th>

                    <th className="px-5 py-3">
                      Resource
                    </th>

                    <th className="px-5 py-3">
                      Performed By
                    </th>

                    <th className="px-5 py-3">
                      IP Address
                    </th>

                    <th className="px-5 py-3">
                      Details
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {logs.map((log) => (
                    <tr
                      key={log.id}
                      className="border-t border-border align-top"
                    >
                      <td className="whitespace-nowrap px-5 py-3 text-text-muted">
                        {new Date(
                          log.createdAt
                        ).toLocaleString()}
                      </td>

                      <td className="px-5 py-3">
                        <span className="rounded-full bg-surface-alt px-2 py-0.5 text-xs font-medium text-text">
                          {log.action}
                        </span>
                      </td>

                      <td className="px-5 py-3 text-text-muted">
                        <p className="text-text">
                          {log.resourceType}
                        </p>

                        <p className="font-mono text-xs text-text-muted">
                          {log.resourceId}
                        </p>
                      </td>

                      <td className="px-5 py-3">
                        <button
                          type="button"
                          onClick={() =>
                            viewUser(log.performedById)
                          }
                          title="View this user's audit history"
                          className="font-mono text-xs text-primary hover:underline"
                        >
                          {log.performedById}
                        </button>
                      </td>

                      <td className="px-5 py-3 text-text-muted">
                        {log.ipAddress}
                      </td>

                      <td className="max-w-xs whitespace-pre-wrap break-words px-5 py-3 text-text-muted">
                        {log.details}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </TableCard>
        )}
    </div>
  );
}