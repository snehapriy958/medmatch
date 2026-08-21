# MedMatch Error Code Specification

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch Error Code Specification |
| Document ID | ERR-001 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Backend REST APIs |
| Classification | Technical Error Contract |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document defines the standard error codes used by MedMatch APIs.

It provides:

- Error code definitions
- Error categories
- HTTP status mappings
- Resolution guidance

This document acts as the single source of truth for API error handling.

All backend services must use these error codes when returning failures.

---

# 3. Error Response Format

All API errors follow the standard format:

```json
{
  "error": {
    "code": "PATIENT_NOT_FOUND",
    "message": "Patient does not exist.",
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z",
    "details": []
  }
}
```

---

# 4. Error Code Naming Convention

Format:

```
CATEGORY_SPECIFIC_ERROR
```

Examples:

```
AUTH_INVALID_CREDENTIALS

PATIENT_NOT_FOUND

TRIAL_PROTOCOL_INVALID
```

Rules:

- Codes must be uppercase.
- Words must be separated by `_`.
- Codes must remain backward compatible.
- Existing codes must never be reused for different meanings.

---

# 5. Error Categories

| Prefix | Category |
|---|---|
| AUTH | Authentication errors |
| USER | User management errors |
| PATIENT | Patient errors |
| TRIAL | Clinical trial errors |
| MATCH | AI matching errors |
| TASK | Background processing errors |
| SYSTEM | Internal system errors |

---

# 6. Authentication Errors (AUTH)

| Code | HTTP Status | Description |
|---|---|---|
| AUTH_INVALID_CREDENTIALS | 401 | Invalid email or password |
| AUTH_TOKEN_MISSING | 401 | JWT token not provided |
| AUTH_TOKEN_INVALID | 401 | Invalid JWT token |
| AUTH_TOKEN_EXPIRED | 401 | JWT token expired |
| AUTH_ACCOUNT_DISABLED | 403 | User account disabled |
| AUTH_ACCESS_DENIED | 403 | User does not have permission |

---

# 7. User Errors (USER)

| Code | HTTP Status | Description |
|---|---|---|
| USER_NOT_FOUND | 404 | User does not exist |
| USER_ALREADY_EXISTS | 409 | Email already registered |
| USER_INVALID_ROLE | 400 | Invalid user role |
| USER_HOSPITAL_REQUIRED | 400 | Hospital association required |
| USER_INACTIVE | 403 | User account inactive |
| USER_PASSWORD_INVALID | 400 | Password validation failed |
| USER_PASSWORD_MISMATCH | 400 | Current password incorrect |

---

# 8. Patient Errors (PATIENT)

| Code | HTTP Status | Description |
|---|---|---|
| PATIENT_NOT_FOUND | 404 | Patient does not exist |
| PATIENT_ALREADY_EXISTS | 409 | Patient already exists |
| PATIENT_INVALID_DATA | 400 | Patient validation failed |
| PATIENT_INACTIVE | 403 | Patient record inactive |
| PATIENT_ACCESS_DENIED | 403 | User cannot access patient |
| PATIENT_HOSPITAL_MISMATCH | 403 | Patient belongs to another hospital |

---

# 9. Trial Errors (TRIAL)

| Code | HTTP Status | Description |
|---|---|---|
| TRIAL_NOT_FOUND | 404 | Trial does not exist |
| TRIAL_ALREADY_EXISTS | 409 | Trial already exists |
| TRIAL_INVALID_DATA | 400 | Trial validation failed |
| TRIAL_PROTOCOL_REQUIRED | 400 | Protocol document required |
| TRIAL_PROTOCOL_INVALID | 400 | Invalid protocol file |
| TRIAL_PROTOCOL_TOO_LARGE | 413 | Protocol file exceeds size limit |
| TRIAL_ACCESS_DENIED | 403 | User cannot access trial |

---

# 10. Matching Errors (MATCH)

| Code | HTTP Status | Description |
|---|---|---|
| MATCH_REQUEST_INVALID | 400 | Invalid matching request |
| MATCH_PATIENT_NOT_FOUND | 404 | Patient unavailable |
| MATCH_ALREADY_RUNNING | 409 | Matching already in progress |
| MATCH_PROCESSING_FAILED | 500 | AI matching failed |
| MATCH_RESULT_NOT_FOUND | 404 | Matching result unavailable |
| MATCH_ACCESS_DENIED | 403 | User cannot access result |

---

# 11. Task Errors (TASK)

| Code | HTTP Status | Description |
|---|---|---|
| TASK_NOT_FOUND | 404 | Task does not exist |
| TASK_ALREADY_COMPLETED | 409 | Task already completed |
| TASK_PROCESSING_FAILED | 500 | Task execution failed |
| TASK_CANCEL_FAILED | 400 | Task cancellation failed |
| TASK_TIMEOUT | 504 | Task exceeded execution time |

---

# 12. System Errors (SYSTEM)

| Code | HTTP Status | Description |
|---|---|---|
| SYSTEM_INTERNAL_ERROR | 500 | Unexpected server error |
| SYSTEM_DATABASE_ERROR | 500 | Database operation failed |
| SYSTEM_SERVICE_UNAVAILABLE | 503 | Dependent service unavailable |
| SYSTEM_TIMEOUT | 504 | Request timeout |
| SYSTEM_RATE_LIMITED | 429 | Too many requests |

---

# 13. Validation Errors

Validation failures use:

```
400 Bad Request
```

Example:

```json
{
  "error": {
    "code": "PATIENT_INVALID_DATA",
    "message": "Required field missing.",
    "details": [
      {
        "field": "dateOfBirth",
        "reason": "required"
      }
    ]
  }
}
```

---

# 14. Error Handling Rules

All services must:

- Return documented error codes.
- Never expose stack traces.
- Include request identifiers.
- Log internal details securely.
- Avoid exposing patient information.
- Maintain consistent HTTP status mappings.

---

# 15. Service Ownership

| Error Category | Owner Service |
|---|---|
| AUTH | Authentication Service |
| USER | Backend Service |
| PATIENT | Backend Service |
| TRIAL | Backend Service |
| MATCH | AI Service + Backend |
| TASK | Celery Worker + Backend |
| SYSTEM | All Services |

---

# 16. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial error code specification |

---

# End of Document