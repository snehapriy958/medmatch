import type { UserRole } from "../types/auth";

export type AppRoute =
  | "/"
  | "/patients"
  | "/trials"
  | "/matching"
  | "/reports"
  | "/audit"
  | "/settings";

/*
 * Centralized frontend route-access matrix.
 *
 * Route access determines whether a role can open a page.
 * Action permissions determine what a role can do inside
 * an accessible page.
 *
 * The backend remains the actual security boundary and must
 * continue enforcing authentication, authorization, and
 * hospital/tenant isolation.
 */
const ROUTE_ACCESS: Record<AppRoute, readonly UserRole[]> = {
  /*
   * Every authenticated role has a Dashboard.
   * Dashboard.tsx renders different content depending on role.
   */
  "/": [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "RESEARCH_COORDINATOR",
    "PHYSICIAN",
    "TRIAL_SPONSOR",
    "PATIENT",
  ],

  /*
   * Patient management.
   */
  "/patients": [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "PHYSICIAN",
    "RESEARCH_COORDINATOR",
  ],

  /*
   * Clinical trial management/discovery.
   */
  "/trials": [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "PHYSICIAN",
    "RESEARCH_COORDINATOR",
    "TRIAL_SPONSOR",
  ],

  /*
   * AI clinical-trial matching.
   */
  "/matching": [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "PHYSICIAN",
    "RESEARCH_COORDINATOR",
  ],

  /*
   * Reports and analytics.
   */
  "/reports": [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "PHYSICIAN",
    "RESEARCH_COORDINATOR",
    "TRIAL_SPONSOR",
  ],

  /*
   * Security and audit information.
   */
  "/audit": [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
  ],

  /*
   * Account/application settings.
   */
  "/settings": [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "RESEARCH_COORDINATOR",
    "PHYSICIAN",
    "TRIAL_SPONSOR",
    "PATIENT",
  ],
};

/*
 * ---------------------------------------------------------------------------
 * Clinical Trial Action Permissions
 * ---------------------------------------------------------------------------
 *
 * These are separate from route permissions.
 *
 * A user may be allowed to OPEN /trials without being allowed
 * to create, upload, edit, or delete trials.
 *
 * Current intended behavior:
 *
 * SYSTEM_ADMIN
 *   View    ✓
 *   Create  ✓
 *   Upload  ✓
 *   Edit    ✓
 *   Delete  ✓
 *
 * HOSPITAL_ADMIN
 *   View    ✓
 *   Create  ✓
 *   Upload  ✓
 *   Edit    ✓
 *   Delete  ✓
 *
 * RESEARCH_COORDINATOR
 *   View    ✓
 *   Create  ✓
 *   Upload  ✓
 *   Edit    ✓
 *   Delete  ✗
 *
 * PHYSICIAN
 *   View    ✓
 *   Create  ✗
 *   Upload  ✗
 *   Edit    ✗
 *   Delete  ✗
 *
 * TRIAL_SPONSOR
 *   View    ✓
 *   Create  ✗
 *   Upload  ✗
 *   Edit    ✗
 *   Delete  ✗
 *
 * PATIENT
 *   Does not have /trials route access.
 */
export type TrialAction =
  | "view"
  | "create"
  | "upload"
  | "edit"
  | "delete";

const TRIAL_ACTION_ACCESS: Record<
  TrialAction,
  readonly UserRole[]
> = {
  view: [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "PHYSICIAN",
    "RESEARCH_COORDINATOR",
    "TRIAL_SPONSOR",
  ],

  create: [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "RESEARCH_COORDINATOR",
  ],

  upload: [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "RESEARCH_COORDINATOR",
  ],

  edit: [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
    "RESEARCH_COORDINATOR",
  ],

  delete: [
    "SYSTEM_ADMIN",
    "HOSPITAL_ADMIN",
  ],
};

/**
 * Check whether a role can access a specific application route.
 */
export function canAccessRoute(
  role: UserRole,
  route: AppRoute
): boolean {
  return ROUTE_ACCESS[route].includes(role);
}

/**
 * Check whether a role can perform a specific clinical-trial action.
 */
export function canAccessTrialAction(
  role: UserRole,
  action: TrialAction
): boolean {
  return TRIAL_ACTION_ACCESS[action].includes(role);
}

/**
 * Convenience helper:
 * Can the user create a clinical trial?
 */
export function canCreateTrial(role: UserRole): boolean {
  return canAccessTrialAction(role, "create");
}

/**
 * Convenience helper:
 * Can the user upload a clinical-trial PDF?
 */
export function canUploadTrial(role: UserRole): boolean {
  return canAccessTrialAction(role, "upload");
}

/**
 * Convenience helper:
 * Can the user edit a clinical trial?
 */
export function canEditTrial(role: UserRole): boolean {
  return canAccessTrialAction(role, "edit");
}

/**
 * Convenience helper:
 * Can the user delete a clinical trial?
 */
export function canDeleteTrial(role: UserRole): boolean {
  return canAccessTrialAction(role, "delete");
}

/**
 * Every authenticated role starts from the role-specific Dashboard.
 *
 * Dashboard.tsx is responsible for deciding which dashboard
 * content to render for the authenticated user's role.
 */
export function getDefaultRoute(): AppRoute {
  return "/";
}