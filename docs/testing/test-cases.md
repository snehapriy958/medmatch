# MedMatch Test Cases

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch Test Cases |
| Document ID | TEST-002 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Functional Testing |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document defines functional test scenarios for the MedMatch platform.

The test cases validate:

- Authentication
- Authorization
- Multi-tenancy
- Patient management
- Trial management
- AI matching workflow
- Background processing
- Audit logging

---

# 3. Authentication Test Cases

## TC-AUTH-001: Successful Login

| Field | Value |
|---|---|
| Scenario | User logs in with valid credentials |
| Input | Valid email and password |
| Expected Result | JWT token returned |
| Status | Pass |

---

## TC-AUTH-002: Invalid Password

| Field | Value |
|---|---|
| Scenario | User enters incorrect password |
| Input | Invalid password |
| Expected Result | 401 Unauthorized |
| Status | Pass |

---

## TC-AUTH-003: Disabled User Login

| Field | Value |
|---|---|
| Scenario | Disabled user attempts login |
| Input | Disabled account credentials |
| Expected Result | 403 Forbidden |
| Status | Pass |

---

# 4. Authorization Test Cases

## TC-RBAC-001: Unauthorized Resource Access

| Field | Value |
|---|---|
| Scenario | User accesses restricted endpoint |
| Input | Invalid role |
| Expected Result | 403 Forbidden |

---

## TC-RBAC-002: Hospital Isolation

| Field | Value |
|---|---|
| Scenario | User accesses another hospital data |
| Input | Different hospital resource |
| Expected Result | Access denied |

---

# 5. Hospital Management Test Cases

## TC-HOSPITAL-001: Create Hospital

| Field | Value |
|---|---|
| Scenario | Admin creates hospital |
| Input | Valid hospital details |
| Expected Result | Hospital created |

---

## TC-HOSPITAL-002: Duplicate Hospital Code

| Field | Value |
|---|---|
| Scenario | Create hospital with existing code |
| Input | Duplicate code |
| Expected Result | 409 Conflict |

---

# 6. User Management Test Cases

## TC-USER-001: Create User

| Field | Value |
|---|---|
| Scenario | Admin creates user |
| Input | Valid user information |
| Expected Result | User created |

---

## TC-USER-002: Change User Role

| Field | Value |
|---|---|
| Scenario | Administrator changes user role |
| Input | Valid role |
| Expected Result | Role updated and audit generated |

---

# 7. Patient Management Test Cases

## TC-PATIENT-001: Create Patient

| Field | Value |
|---|---|
| Scenario | Clinical user creates patient |
| Input | Valid patient information |
| Expected Result | Patient created |

---

## TC-PATIENT-002: Duplicate Medical Record Number

| Field | Value |
|---|---|
| Scenario | Duplicate MRN creation |
| Input | Existing MRN |
| Expected Result | 409 Conflict |

---

## TC-PATIENT-003: Cross Hospital Patient Access

| Field | Value |
|---|---|
| Scenario | Access patient from another hospital |
| Input | Different hospital patient |
| Expected Result | Access denied |

---

# 8. Patient Notes Test Cases

## TC-NOTE-001: Create Clinical Note

| Field | Value |
|---|---|
| Scenario | Physician creates note |
| Input | Valid patient note |
| Expected Result | Note created |

---

## TC-NOTE-002: Access Patient Note

| Field | Value |
|---|---|
| Scenario | Authorized user views note |
| Input | Valid note ID |
| Expected Result | Note returned |

---

# 9. Trial Management Test Cases

## TC-TRIAL-001: Create Trial

| Field | Value |
|---|---|
| Scenario | Research coordinator creates trial |
| Input | Valid trial information |
| Expected Result | Trial created |

---

## TC-TRIAL-002: Upload Trial Protocol

| Field | Value |
|---|---|
| Scenario | Upload protocol PDF |
| Input | Valid PDF file |
| Expected Result | Processing task created |

---

## TC-TRIAL-003: Invalid Protocol Upload

| Field | Value |
|---|---|
| Scenario | Upload invalid file |
| Input | Unsupported format |
| Expected Result | 415 Unsupported Media Type |

---

# 10. AI Matching Test Cases

## TC-MATCH-001: Create Matching Request

| Field | Value |
|---|---|
| Scenario | User requests trial matching |
| Input | Valid patient ID |
| Expected Result | Matching task created |

---

## TC-MATCH-002: Matching Processing

| Field | Value |
|---|---|
| Scenario | Worker processes matching request |
| Input | Patient note and trials |
| Expected Result | Matching result generated |

---

## TC-MATCH-003: Matching Result Retrieval

| Field | Value |
|---|---|
| Scenario | User retrieves AI result |
| Input | Valid result ID |
| Expected Result | Result returned |

---

# 11. Background Task Test Cases

## TC-TASK-001: Task Creation

| Field | Value |
|---|---|
| Scenario | Async operation starts |
| Input | Valid workflow request |
| Expected Result | Task created |

---

## TC-TASK-002: Failed Task Handling

| Field | Value |
|---|---|
| Scenario | Worker failure occurs |
| Input | Processing failure |
| Expected Result | Task marked FAILED |

---

# 12. Audit Test Cases

## TC-AUDIT-001: Audit Generation

| Field | Value |
|---|---|
| Scenario | Sensitive operation performed |
| Input | Patient access |
| Expected Result | Audit record created |

---

## TC-AUDIT-002: Audit Immutability

| Field | Value |
|---|---|
| Scenario | Attempt audit modification |
| Input | Update request |
| Expected Result | Operation rejected |

---

# 13. Regression Checklist

Before release verify:

## Authentication

- [ ] Login works
- [ ] JWT validation works
- [ ] Role permissions work

## Data Isolation

- [ ] Hospital isolation verified
- [ ] Unauthorized access blocked

## Core Workflow

- [ ] Trial upload works
- [ ] Criteria extraction works
- [ ] Embeddings generated
- [ ] Matching completes

## Infrastructure

- [ ] Redis connected
- [ ] Celery worker running
- [ ] Database available

---

# 14. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial test cases |

---

# End of Document