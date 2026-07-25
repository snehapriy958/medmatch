package com.medmatch.auth.audit;

/**
 * Defines all auditable actions performed within the system.
 *
 * Using an enum prevents typos, improves type safety,
 * and makes filtering audit logs significantly easier.
 */
public enum AuditAction {

    // Authentication
    LOGIN,
    LOGOUT,

    // Hospital Management
    CREATE_HOSPITAL,
    UPDATE_HOSPITAL,
    DELETE_HOSPITAL,

    // User Management
    CREATE_USER,
    UPDATE_USER,
    DELETE_USER,

    // Patient Management
    CREATE_PATIENT,
    UPDATE_PATIENT,
    DELETE_PATIENT,

    ADD_PATIENT_NOTE,

    // Trial Management
    CREATE_TRIAL,
    UPDATE_TRIAL,
    DELETE_TRIAL,

    // AI Matching
    RUN_MATCHING,
    SEARCH_TRIALS
}