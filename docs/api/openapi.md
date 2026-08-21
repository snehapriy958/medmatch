# MedMatch API Specification

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch API Specification |
| Document ID | API-001 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Backend REST APIs |
| Classification | Technical API Contract |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document defines the official API contract for the MedMatch platform.

It specifies:

- Available REST endpoints
- Request and response structures
- Authentication requirements
- Authorization rules
- Validation requirements
- Error handling standards
- API evolution guidelines

This document acts as the single source of truth between:

- Frontend applications
- Backend services
- AI services
- External integrations

All API implementations must follow this specification.

---

# 3. Scope

This specification covers all public APIs exposed by the MedMatch platform.

Current API domains include:

- Authentication
- Hospitals
- Users
- Patients
- Patient Notes
- Clinical Trials
- Trial Criteria
- Matching
- Background Tasks
- Audit Logs

Future APIs must follow the same design principles defined in this document.

---

# 4. API Design Principles

## 4.1 Resource-Oriented Design

The MedMatch API follows REST principles.

Endpoints represent business resources.

Examples:

```
GET /api/v1/patients

POST /api/v1/patients

GET /api/v1/trials/{trialId}
```

Operations are represented through HTTP methods.

---

## 4.2 Consistency

All APIs follow consistent conventions for:

- Naming
- Authentication
- Authorization
- Validation
- Response structures
- Error handling
- Pagination

---

## 4.3 Backward Compatibility

Breaking API changes should be avoided.

New capabilities should be introduced through:

- New endpoints
- Optional fields
- New API versions

Existing clients should continue working whenever possible.

---

## 4.4 Stateless Communication

Each API request must contain all required information for processing.

Authentication state is maintained through JWT tokens.

Servers should not depend on previous client requests.

---

## 4.5 Tenant Isolation

MedMatch follows a multi-tenant architecture.

All hospital-owned resources must respect hospital boundaries.

Examples:

- Patients
- Clinical Trials
- Patient Notes
- Matching Results
- Audit Records

A user must never access another hospital's data unless explicitly authorized.

---

## 4.6 Security First

All APIs must enforce:

- Authentication
- Authorization
- Input validation
- Audit logging
- Secure error handling

Sensitive healthcare information must never be exposed through error messages.

---

# 5. Base URLs

MedMatch APIs are organized using versioned REST endpoints.

Base path:

```
/api/v1/
```

Service ownership:

| Service | Responsibility |
|---|---|
| Authentication Service | Identity, JWT, user security |
| AI Service | Trial matching, embeddings, AI processing |
| Backend Services | Business resources and workflows |

---

## API Ownership

| API Domain | Owner Service |
|---|---|
| Authentication | Spring Boot Auth Service |
| Users | Spring Boot Backend |
| Hospitals | Spring Boot Backend |
| Patients | Spring Boot Backend |
| Patient Notes | Spring Boot Backend |
| Trials | Spring Boot Backend |
| Trial Criteria | FastAPI AI Service + Backend |
| Matching | Backend + AI Service |
| Tasks | Backend + Celery Worker |
| Audit Logs | Spring Boot Backend |

# 6. Authentication

MedMatch uses JWT-based authentication for securing API access.

The Authentication Service is responsible for:

- User identity verification
- Token generation
- Token validation
- Role-based authorization information

Protected APIs require a valid JWT access token.

---

## Authentication Header

Protected requests must include:

```http
Authorization: Bearer <access-token>
```

Example:

```http
GET /api/v1/patients

Authorization: Bearer eyJhbGciOiJSUzI1Ni...
```

---

## Authentication Flow

The authentication flow is:

```
User Login

↓

Authentication Service

↓

Validate Credentials

↓

Generate JWT Token

↓

Client Stores Token

↓

Client Sends Token With Requests

↓

Backend Validates Token

↓

Request Processed
```

---

## Public Endpoints

The following endpoints do not require authentication:

- Login
- Health checks
- Public documentation endpoints

All other endpoints require authentication unless explicitly stated.

---

## Authorization

Authentication verifies identity.

Authorization verifies permissions.

MedMatch uses role-based access control (RBAC).

Example roles:

| Role | Responsibility |
|---|---|
| SYSTEM_ADMIN | Platform administration |
| HOSPITAL_ADMIN | Hospital management |
| PHYSICIAN | Patient and clinical workflows |
| RESEARCH_COORDINATOR | Trial management |
| PATIENT | Patient portal access |

---
# Health API

Health endpoints provide service availability checks.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Service health status |


## Response

200 OK

Example:

{
 "status": "UP",
 "services": {
   "database": "UP",
   "redis": "UP"
 }
}

# 7. Standard Headers

All MedMatch APIs follow common HTTP header conventions.

These headers provide:

- Authentication
- Content negotiation
- Request tracing
- Duplicate request prevention

---

## Supported Headers

| Header | Required | Description |
|---|---|---|
| Authorization | Yes | JWT Bearer authentication token |
| Content-Type | Yes | Request payload format |
| Accept | Optional | Expected response format |
| X-Correlation-ID | Optional | Request tracing identifier |
| Idempotency-Key | Conditional | Prevent duplicate asynchronous operations |

---

## Authorization

Format:

```http
Authorization: Bearer <access-token>
```

Invalid or expired tokens return:

```http
401 Unauthorized
```

---

## Content-Type

JSON requests:

```http
Content-Type: application/json
```

File uploads:

```http
Content-Type: multipart/form-data
```

---

## X-Correlation-ID

Used for distributed request tracing.

Example:

```http
X-Correlation-ID: 7c9f1d8a-xxxx-xxxx
```

The value should be propagated through:

- Backend logs
- AI service logs
- Audit records

---

## Idempotency-Key

Used for operations that create asynchronous jobs.

Examples:

- Trial protocol upload
- Matching request
- Bulk processing

Example:

```http
Idempotency-Key: request-unique-id
```

Repeated requests with the same key must not create duplicate operations.

---

# 8. API Versioning

MedMatch APIs use URL-based versioning.

Current version:

```
/api/v1/
```

Example:

```
GET /api/v1/patients
```

---

## Version Rules

Breaking changes require a new API version.

Example:

```
/api/v2/
```

Non-breaking changes should use:

- Optional request fields
- Optional response fields
- New endpoints

---

# 9. Request Standards

All API requests must follow these rules:

- JSON format unless otherwise specified.
- UTF-8 encoding.
- Validated before processing.
- Required fields must be present.
- Invalid requests must return meaningful errors.

---

## Request Validation

Validation occurs in the following order:

```
Request Received

↓

Authentication Check

↓

Authorization Check

↓

Schema Validation

↓

Business Validation

↓

Processing
```

---

# 10. Response Standards

All successful API responses use a common structure.

Standard response:

```json
{
  "data": {},
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---
## Delete Operations

Permanent deletion is not supported for healthcare resources.

Resources use lifecycle operations:

- Activate
- Deactivate
- Archive

Historical and audit data must remain preserved.

## Collection Response

List endpoints return:

```json
{
  "data": [],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 100,
    "totalPages": 5,
    "requestId": "uuid"
  }
}
```

---

## Empty Response

Operations without response bodies return:

```
204 No Content
```

Examples:

- Activate user
- Deactivate hospital
- Archive trial

---

# 11. Error Model

All API errors follow a common structure.

Example:

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

## Error Rules

Errors must:

- Be machine-readable.
- Not expose internal implementation details.
- Include request identifiers for debugging.
- Provide actionable messages.

---

## Error Categories

| Prefix | Category |
|---|---|
| AUTH | Authentication errors |
| USER | User management errors |
| PATIENT | Patient errors |
| TRIAL | Trial errors |
| MATCH | Matching errors |
| TASK | Background processing errors |
| SYSTEM | Internal system errors |

---

## Common HTTP Status Codes

| Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 202 | Request accepted for processing |
| 204 | Successful operation without response body |
| 400 | Invalid request |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 409 | Business conflict |
| 413 | Payload too large |
| 415 | Unsupported media type |
| 422 | Business validation failure |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable |

---

---

# 12. Authentication API

The Authentication API manages user identity, login, and access token generation.

Authentication is handled centrally by the Authentication Service.

Other services must validate the JWT token but must not implement independent authentication logic.

---

## Authentication Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | Authenticate user |
| GET | `/api/v1/auth/me` | Retrieve current user |
| POST | `/api/v1/auth/logout` | Logout user |

User creation is managed through the User API and requires administrative authorization.

---

# POST /api/v1/auth/login

## Purpose

Authenticates a user using email and password credentials.

A successful login returns a JWT access token.

---

## Authentication

Not Required

---

## Authorization

Public

---

## Request Body

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

---

## Validation

The request must satisfy:

- Email is provided.
- Password is provided.
- User account exists.
- User account is active.

---

## Success Response

**200 OK**

```json
{
  "data": {
    "accessToken": "jwt-token",
    "tokenType": "Bearer",
    "expiresIn": 3600
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Login successful |
| 400 | Invalid request |
| 401 | Invalid credentials |
| 403 | Account inactive |

---

# GET /api/v1/auth/me

## Purpose

Returns information about the currently authenticated user.

---

## Authentication

Required

---

## Authorization

Authenticated User

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "hospitalId": "uuid",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "role": "PHYSICIAN"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | User information returned |
| 401 | Authentication required |

---

# POST /api/v1/auth/logout

## Purpose

Terminates the current user session.

The client must remove the stored access token after successful logout.

---

## Authentication

Required

---

## Authorization

Authenticated User

---

## Request Body

No request body required.

---

## Success Response

**204 No Content**

---

## Possible Responses

| Status | Meaning |
|---|---|
| 204 | Logout successful |
| 401 | Authentication required |

---

# Authentication API Summary

| Endpoint | Description |
|---|---|
| POST `/auth/login` | Authenticate user |
| GET `/auth/me` | Get current user |
| POST `/auth/logout` | Logout user |

---

## Authentication API Rules

- JWT tokens are generated only by the Authentication Service.
- Other services must validate tokens using the configured public key.
- Passwords must never be returned through APIs.
- Authentication failures must not reveal sensitive account information.
- All authentication-related events should generate audit records.

---

---

# 13. Hospital API

The Hospital API manages hospital tenants within the MedMatch platform.

A hospital represents the primary tenant boundary.

All hospital-owned resources must belong to a hospital.

Examples:

- Users
- Patients
- Clinical Trials
- Patient Notes
- Matching Results
- Audit Records

Hospitals are never permanently deleted.

The lifecycle is managed through activation and deactivation to preserve historical data integrity.

---

## Hospital Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/hospitals` | Create hospital |
| GET | `/api/v1/hospitals` | List hospitals |
| GET | `/api/v1/hospitals/{hospitalId}` | Retrieve hospital |
| PATCH | `/api/v1/hospitals/{hospitalId}` | Update hospital |
| POST | `/api/v1/hospitals/{hospitalId}/activate` | Activate hospital |
| POST | `/api/v1/hospitals/{hospitalId}/deactivate` | Deactivate hospital |

---

# POST /api/v1/hospitals

## Purpose

Creates a new hospital tenant in the MedMatch platform.

---

## Authentication

Required

---

## Authorization

System Administrator

---

## Request Body

```json
{
  "code": "CITY001",
  "name": "City General Hospital",
  "address": "123 Main Street"
}
```

---

## Validation

The request must satisfy:

- Hospital code is unique.
- Hospital name is provided.
- Required fields are present.

---

## Success Response

**201 Created**

```json
{
  "data": {
    "id": "uuid",
    "code": "CITY001",
    "name": "City General Hospital",
    "active": true
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 201 | Hospital created |
| 400 | Validation failed |
| 401 | Authentication required |
| 403 | Permission denied |
| 409 | Hospital code already exists |

---

# GET /api/v1/hospitals

## Purpose

Returns hospitals accessible to the authenticated administrator.

System Administrators can access all hospitals.

Hospital Administrators can access only their assigned hospital.

---

## Authentication

Required

---

## Authorization

Administrator

---

## Query Parameters

| Parameter | Description |
|---|---|
| page | Page number |
| size | Page size |
| search | Search by hospital name |
| active | Filter active status |
| sort | Sort field |

---

## Success Response

**200 OK**

```json
{
  "data": [
    {
      "id": "uuid",
      "code": "CITY001",
      "name": "City General Hospital",
      "active": true
    }
  ],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 10,
    "totalPages": 1,
    "requestId": "uuid"
  }
}
```

---

# GET /api/v1/hospitals/{hospitalId}

## Purpose

Retrieves details of a specific hospital.

---

## Authentication

Required

---

## Authorization

System Administrator

Hospital Administrator

---

## Path Parameters

| Parameter | Description |
|---|---|
| hospitalId | Hospital identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "code": "CITY001",
    "name": "City General Hospital",
    "address": "123 Main Street",
    "active": true
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Hospital returned |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Hospital not found |

---

# PATCH /api/v1/hospitals/{hospitalId}

## Purpose

Updates hospital information.

Only mutable fields can be updated.

---

## Mutable Fields

Allowed:

- Name
- Address

Not allowed:

- Hospital ID
- Hospital Code
- Creation metadata

---

## Request Body

```json
{
  "name": "Updated Hospital Name",
  "address": "Updated Address"
}
```

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "name": "Updated Hospital Name"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

# POST /api/v1/hospitals/{hospitalId}/activate

## Purpose

Reactivates a previously deactivated hospital.

A reactivated hospital can resume normal platform operations.

---

## Authentication

Required

---

## Authorization

System Administrator

---

## Success Response

**204 No Content**

---

## Business Rules

Hospital activation:

- Allows user login.
- Allows new patient creation.
- Allows new trial creation.
- Preserves existing records.
- Preserves audit history.

---

## Possible Responses

| Status | Meaning |
|---|---|
| 204 | Hospital activated |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Hospital not found |

---

# POST /api/v1/hospitals/{hospitalId}/deactivate

## Purpose

Deactivates a hospital.

Deactivation prevents new activity while preserving historical records.

---

## Authentication

Required

---

## Authorization

System Administrator

---

## Success Response

**204 No Content**

---

## Business Rules

Hospital deactivation:

- Prevents future user login.
- Prevents new patient creation.
- Prevents new trial creation.
- Preserves historical data.
- Preserves audit records.

---

## Possible Responses

| Status | Meaning |
|---|---|
| 204 | Hospital deactivated |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Hospital not found |

---

# Hospital API Summary

| Endpoint | Description |
|---|---|
| POST `/hospitals` | Create hospital |
| GET `/hospitals` | List hospitals |
| GET `/hospitals/{hospitalId}` | Retrieve hospital |
| PATCH `/hospitals/{hospitalId}` | Update hospital |
| POST `/hospitals/{hospitalId}/activate` | Activate hospital |
| POST `/hospitals/{hospitalId}/deactivate` | Deactivate hospital |

---

## Hospital API Rules

- Hospitals are tenant boundaries.
- Hospitals are never permanently deleted.
- All hospital-owned resources must maintain tenant isolation.
- Hospital lifecycle changes must generate audit records.

---

---

# 14. User API

The User API manages platform users, account lifecycle, and role assignments.

Users belong to exactly one hospital and operate within that hospital's tenant boundary.

User authentication is handled by the Authentication Service.

User authorization is controlled through Role-Based Access Control (RBAC).

---

## User Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/users` | Create user |
| GET | `/api/v1/users` | List users |
| GET | `/api/v1/users/{userId}` | Retrieve user |
| PATCH | `/api/v1/users/{userId}` | Update user |
| POST | `/api/v1/users/{userId}/activate` | Activate user |
| POST | `/api/v1/users/{userId}/deactivate` | Deactivate user |
| POST | `/api/v1/users/{userId}/change-role` | Change user role |
| POST | `/api/v1/users/{userId}/reset-password` | Reset user password |
| POST | `/api/v1/users/change-password` | Change own password |

---

# POST /api/v1/users

## Purpose

Creates a new user account within a hospital.

---

## Authentication

Required

---

## Authorization

System Administrator

Hospital Administrator

---

## Request Body

```json
{
  "hospitalId": "uuid",
  "role": "PHYSICIAN",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  "password": "password"
}
```

---

## Validation

The request must satisfy:

- Hospital exists.
- Role is valid.
- Email is unique.
- Password meets security requirements.
- User belongs to an accessible hospital.

---

## Success Response

**201 Created**

```json
{
  "data": {
    "id": "uuid",
    "email": "john@example.com",
    "role": "PHYSICIAN"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 201 | User created |
| 400 | Validation failed |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Hospital not found |
| 409 | Email already exists |

---

# GET /api/v1/users

## Purpose

Returns users accessible to the authenticated administrator.

System Administrators may access users across hospitals.

Hospital Administrators may access only users within their hospital.

---

## Authentication

Required

---

## Authorization

Administrator

---

## Query Parameters

| Parameter | Description |
|---|---|
| page | Page number |
| size | Page size |
| search | Search by name or email |
| hospitalId | Filter by hospital |
| role | Filter by role |
| active | Filter active status |
| sort | Sort field |

---

## Success Response

**200 OK**

```json
{
  "data": [
    {
      "id": "uuid",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com",
      "role": "PHYSICIAN",
      "active": true
    }
  ],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 100,
    "totalPages": 5,
    "requestId": "uuid"
  }
}
```

---

# GET /api/v1/users/{userId}

## Purpose

Retrieves details of a specific user.

---

## Authentication

Required

---

## Authorization

Administrator

or

Current User

---

## Path Parameters

| Parameter | Description |
|---|---|
| userId | User identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "hospitalId": "uuid",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "role": "PHYSICIAN",
    "active": true
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

# PATCH /api/v1/users/{userId}

## Purpose

Updates mutable user information.

---

## Mutable Fields

Allowed:

- First Name
- Last Name
- Email

Managed separately:

- Role
- Password
- Account Status

---

## Request Body

```json
{
  "firstName": "Jonathan",
  "lastName": "Doe"
}
```

---

## Success Response

**200 OK**

---

# POST /api/v1/users/{userId}/activate

## Purpose

Activates a previously deactivated user account.

---

## Authentication

Required

---

## Authorization

Administrator

---

## Success Response

**204 No Content**

---

## Business Rules

User activation:

- Allows authentication.
- Restores platform access.
- Preserves historical records.
- Preserves audit history.

---

# POST /api/v1/users/{userId}/deactivate

## Purpose

Deactivates a user account.

The user record remains preserved for historical and audit purposes.

---

## Authentication

Required

---

## Authorization

Administrator

---

## Success Response

**204 No Content**

---

## Business Rules

User deactivation:

- Prevents login.
- Does not delete user data.
- Preserves created records.
- Preserves audit history.

---

# POST /api/v1/users/{userId}/change-role

## Purpose

Changes the assigned role of a user.

---

## Authentication

Required

---

## Authorization

System Administrator

Hospital Administrator

---

## Request Body

```json
{
  "role": "RESEARCH_COORDINATOR"
}
```

---

## Success Response

**204 No Content**

---

## Business Rules

Role changes must:

- Be recorded in audit logs.
- Preserve previous role history.
- Follow RBAC rules.

Additional RBAC restrictions:

SYSTEM_ADMIN:

- Can assign any valid role.

HOSPITAL_ADMIN:

- Can assign only:
    - PHYSICIAN
    - RESEARCH_COORDINATOR
    - PATIENT

- Cannot assign SYSTEM_ADMIN.
- Cannot assign another HOSPITAL_ADMIN.

---

# POST /api/v1/users/{userId}/reset-password

## Purpose

Allows administrators to reset another user's password.

---

## Authentication

Required

---

## Authorization

Administrator

---

## Request Body

```json
{
  "temporaryPassword": "temporary-password"
}
```

---

## Success Response

**204 No Content**

---

# POST /api/v1/users/change-password

## Purpose

Allows an authenticated user to change their own password.

---

## Authentication

Required

---

## Request Body

```json
{
  "currentPassword": "old-password",
  "newPassword": "new-password"
}
```

---

## Validation

The request must verify:

- Current password is correct.
- New password satisfies security requirements.
- New password differs from old password.

---

## Success Response

**204 No Content**

---

# User API Summary

| Endpoint | Description |
|---|---|
| POST `/users` | Create user |
| GET `/users` | List users |
| GET `/users/{userId}` | Retrieve user |
| PATCH `/users/{userId}` | Update user |
| POST `/users/{userId}/activate` | Activate user |
| POST `/users/{userId}/deactivate` | Deactivate user |
| POST `/users/{userId}/change-role` | Change role |
| POST `/users/{userId}/reset-password` | Reset password |
| POST `/users/change-password` | Change own password |

---

## User API Rules

- Users belong to one hospital.
- User access is restricted by tenant boundaries.
- Passwords are never returned.
- Role changes require authorization.
- Account lifecycle changes generate audit records.

---

---

# 15. Patient API

The Patient API manages patient demographic and administrative information within the MedMatch platform.

Patients belong to exactly one hospital and are isolated using hospital tenant boundaries.

Clinical information such as notes, diagnoses, medications, and laboratory data are managed through separate APIs.

This separation keeps the Patient API stable while allowing future healthcare integrations.

## Protected Health Information Rules

Patient-related APIs must follow healthcare data protection rules.

Requirements:

- Sensitive patient information must not appear in logs.
- API errors must not expose clinical information.
- Access to patient data must generate audit records.
- Responses should follow minimum necessary disclosure principles.
- Unauthorized cross-hospital access must always be blocked.

---

## Patient Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/patients` | Create patient |
| GET | `/api/v1/patients` | List patients |
| GET | `/api/v1/patients/{patientId}` | Retrieve patient |
| PATCH | `/api/v1/patients/{patientId}` | Update patient |
| POST | `/api/v1/patients/{patientId}/activate` | Activate patient |
| POST | `/api/v1/patients/{patientId}/deactivate` | Deactivate patient |

---

# POST /api/v1/patients

## Purpose

Creates a new patient record within the authenticated user's hospital.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Physician
- Research Coordinator
- Hospital Administrator

---

## Request Body

```json
{
  "medicalRecordNumber": "MRN-100234",
  "firstName": "John",
  "lastName": "Doe",
  "dateOfBirth": "1990-01-15",
  "gender": "MALE",
  "phone": "+91XXXXXXXXXX",
  "email": "john@example.com"
}
```

---

## Validation

The request must satisfy:

- Medical record number is unique within hospital.
- Required demographic fields are present.
- Date of birth is valid.
- Email format is valid if provided.
- Patient belongs to authenticated hospital.

---

## Success Response

**201 Created**

```json
{
  "data": {
    "id": "uuid",
    "medicalRecordNumber": "MRN-100234",
    "firstName": "John",
    "lastName": "Doe"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 201 | Patient created |
| 400 | Validation failed |
| 401 | Authentication required |
| 403 | Permission denied |
| 409 | Medical record number already exists |

---

# GET /api/v1/patients

## Purpose

Returns patients accessible to the authenticated user.

Results are automatically restricted to the user's hospital.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Query Parameters

| Parameter | Description |
|---|---|
| page | Page number |
| size | Page size |
| search | Search by name or medical record number |
| active | Filter active status |
| sort | Sort field |

---

## Success Response

**200 OK**

```json
{
  "data": [
    {
      "id": "uuid",
      "medicalRecordNumber": "MRN-100234",
      "firstName": "John",
      "lastName": "Doe",
      "dateOfBirth": "1990-01-15",
      "active": true
    }
  ],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 100,
    "totalPages": 5,
    "requestId": "uuid"
  }
}
```

---

# GET /api/v1/patients/{patientId}

## Purpose

Retrieves detailed information about a patient.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Path Parameters

| Parameter | Description |
|---|---|
| patientId | Patient identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "medicalRecordNumber": "MRN-100234",
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "1990-01-15",
    "gender": "MALE",
    "phone": "+91XXXXXXXXXX",
    "email": "john@example.com",
    "active": true
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Patient returned |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Patient not found |

---

# PATCH /api/v1/patients/{patientId}

## Purpose

Updates mutable patient demographic information.

---

## Mutable Fields

Allowed:

- First Name
- Last Name
- Phone
- Email

Not allowed:

- Patient ID
- Hospital
- Medical Record Number
- Creation metadata

---

## Request Body

```json
{
  "phone": "+91XXXXXXXXXX",
  "email": "updated@example.com"
}
```

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "phone": "+91XXXXXXXXXX",
    "email": "updated@example.com"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

# POST /api/v1/patients/{patientId}/activate

## Purpose

Activates a previously deactivated patient record.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Physician
- Research Coordinator
- Hospital Administrator

---

## Success Response

**204 No Content**

---

## Business Rules

Patient activation:

- Allows new matching requests.
- Allows new clinical notes.
- Preserves historical records.
- Preserves audit history.

---

# POST /api/v1/patients/{patientId}/deactivate

## Purpose

Deactivates a patient record.

The patient remains stored for historical and audit purposes.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Hospital Administrator
- Research Coordinator

---

## Success Response

**204 No Content**

---

## Business Rules

Patient deactivation:

- Prevents new matching requests.
- Prevents new clinical notes.
- Preserves previous AI evaluations.
- Preserves audit history.

---

# Patient API Summary

| Endpoint | Description |
|---|---|
| POST `/patients` | Create patient |
| GET `/patients` | List patients |
| GET `/patients/{patientId}` | Retrieve patient |
| PATCH `/patients/{patientId}` | Update patient |
| POST `/patients/{patientId}/activate` | Activate patient |
| POST `/patients/{patientId}/deactivate` | Deactivate patient |

---

## Patient API Rules

- Patients are always scoped to a hospital.
- Patient records are never permanently deleted.
- Clinical data is separated into dedicated APIs.
- All patient lifecycle changes generate audit records.
- Future healthcare interoperability should use separate integration APIs.

---


---

# 16. Patient Notes API

The Patient Notes API manages clinical notes associated with patients.

Patient notes contain unstructured clinical information used by the AI matching pipeline.

Examples:

- Clinical observations
- Physician notes
- Research notes
- Eligibility-related information

Patient notes are separate from the Patient API to maintain clear domain boundaries.

---

## Patient Notes Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/patient-notes` | Create patient note |
| GET | `/api/v1/patient-notes` | List patient notes |
| GET | `/api/v1/patient-notes/{noteId}` | Retrieve patient note |
| PATCH | `/api/v1/patient-notes/{noteId}` | Update note metadata |
| POST | `/api/v1/patient-notes/{noteId}/archive` | Archive patient note |

---

# POST /api/v1/patient-notes

## Purpose

Creates a new clinical note for a patient.

A newly created note may become available for AI processing.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Physician
- Research Coordinator
- Hospital Administrator

---

## Request Body

```json
{
  "patientId": "uuid",
  "noteType": "PROGRESS_NOTE",
  "content": "Patient diagnosed with Stage II breast cancer..."
}
```

---

## Validation

The request must satisfy:

- Patient exists.
- Patient belongs to authenticated hospital.
- Note type is valid.
- Note content is not empty.

---

## Success Response

**201 Created**

```json
{
  "data": {
    "id": "uuid",
    "patientId": "uuid",
    "noteType": "PROGRESS_NOTE"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 201 | Note created |
| 400 | Validation failed |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Patient not found |

---

# GET /api/v1/patient-notes

## Purpose

Returns clinical notes accessible to the authenticated user.

Results are automatically restricted to the user's hospital.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Query Parameters

| Parameter | Description |
|---|---|
| patientId | Filter by patient |
| noteType | Filter by note type |
| page | Page number |
| size | Page size |
| sort | Sort field |

---

## Success Response

**200 OK**

```json
{
  "data": [
    {
      "id": "uuid",
      "patientId": "uuid",
      "noteType": "PROGRESS_NOTE",
      "createdAt": "2026-08-08T10:30:00Z"
    }
  ],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 50,
    "totalPages": 3,
    "requestId": "uuid"
  }
}
```

---

# GET /api/v1/patient-notes/{noteId}

## Purpose

Retrieves a specific clinical note.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Path Parameters

| Parameter | Description |
|---|---|
| noteId | Patient note identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "patientId": "uuid",
    "noteType": "PROGRESS_NOTE",
    "content": "Patient diagnosed with...",
    "createdAt": "2026-08-08T10:30:00Z"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Note returned |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Note not found |

---

# PATCH /api/v1/patient-notes/{noteId}

## Purpose

Updates non-clinical metadata associated with a note.

Clinical content should not be modified after being used in AI processing.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Physician
- Hospital Administrator

---

## Mutable Fields

Allowed:

- Note Type
- Metadata

Not allowed:

- Patient association
- Original clinical content
- Creation timestamp

---

## Request Body

```json
{
  "noteType": "FOLLOW_UP_NOTE"
}
```

---

## Success Response

**200 OK**

---

# POST /api/v1/patient-notes/{noteId}/archive

## Purpose

Archives a patient note.

Archived notes remain available for historical reference and AI audit purposes but are excluded from active workflows.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Physician
- Hospital Administrator

---

## Success Response

**204 No Content**

---

## Business Rules

Note archival:

- Does not delete the note.
- Preserves AI evaluation history.
- Preserves audit records.
- Prevents normal workflow usage.

---

# Patient Notes API Summary

| Endpoint | Description |
|---|---|
| POST `/patient-notes` | Create patient note |
| GET `/patient-notes` | List patient notes |
| GET `/patient-notes/{noteId}` | Retrieve patient note |
| PATCH `/patient-notes/{noteId}` | Update note metadata |
| POST `/patient-notes/{noteId}/archive` | Archive note |

---

## Patient Notes API Rules

- Notes are always scoped to a hospital through the patient relationship.
- Clinical content should remain immutable after AI processing.
- Notes are never permanently deleted.
- All note lifecycle changes generate audit records.
- Future integrations such as FHIR and EHR imports should use dedicated services.

---

---

# 17. Trial API

The Trial API manages clinical trial information within the MedMatch platform.

A trial represents a clinical study that contains eligibility requirements used by the AI matching pipeline.

Trial metadata is managed through this API.

Trial documents, eligibility criteria extraction, embeddings, and AI processing are handled through dedicated workflows.

---

## Trial Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/trials` | Create trial |
| GET | `/api/v1/trials` | List trials |
| GET | `/api/v1/trials/{trialId}` | Retrieve trial |
| PATCH | `/api/v1/trials/{trialId}` | Update trial metadata |
| POST | `/api/v1/trials/{trialId}/upload-protocol` | Upload trial protocol |
| POST | `/api/v1/trials/{trialId}/archive` | Archive trial |

---

# POST /api/v1/trials

## Purpose

Creates a new clinical trial record.

The trial starts in draft state until the protocol document is uploaded and processed.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Research Coordinator
- Hospital Administrator

---

## Request Body

```json
{
  "title": "Phase II Breast Cancer Study",
  "protocolNumber": "BC-2026-001",
  "clinicalTrialId": "NCT12345678",
  "phase": "PHASE_II",
  "sponsor": "Example Pharma",
  "diseaseArea": "Breast Cancer",
  "summary": "Clinical trial summary"
}
```

---

## Validation

The request must satisfy:

- Trial title is provided.
- Protocol number is unique within hospital.
- Trial phase is valid.
- Required fields are present.

---

## Success Response

**201 Created**

```json
{
  "data": {
    "id": "uuid",
    "title": "Phase II Breast Cancer Study",
    "protocolNumber": "BC-2026-001",
    "status": "DRAFT"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 201 | Trial created |
| 400 | Validation failed |
| 401 | Authentication required |
| 403 | Permission denied |
| 409 | Protocol number already exists |

---

# GET /api/v1/trials

## Purpose

Returns clinical trials accessible to the authenticated user.

Results are restricted according to hospital tenant boundaries.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Query Parameters

| Parameter | Description |
|---|---|
| page | Page number |
| size | Page size |
| search | Search by title or protocol number |
| phase | Filter trial phase |
| status | Filter trial status |
| diseaseArea | Filter disease area |
| sort | Sort field |

---

## Success Response

**200 OK**

```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Phase II Breast Cancer Study",
      "phase": "PHASE_II",
      "status": "RECRUITING"
    }
  ],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 75,
    "totalPages": 4,
    "requestId": "uuid"
  }
}
```

---

# GET /api/v1/trials/{trialId}

## Purpose

Retrieves details of a specific clinical trial.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Path Parameters

| Parameter | Description |
|---|---|
| trialId | Trial identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "title": "Phase II Breast Cancer Study",
    "protocolNumber": "BC-2026-001",
    "clinicalTrialId": "NCT12345678",
    "phase": "PHASE_II",
    "status": "RECRUITING",
    "sponsor": "Example Pharma",
    "diseaseArea": "Breast Cancer"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Trial returned |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Trial not found |

---

# PATCH /api/v1/trials/{trialId}

## Purpose

Updates mutable trial metadata.

Protocol content and extracted eligibility criteria are managed separately.

---

## Mutable Fields

Allowed:

- Title
- Summary
- Sponsor
- Disease Area
- Recruitment Status

Not allowed:

- Trial ID
- Protocol Number
- Hospital ownership
- Creation metadata

---

## Request Body

```json
{
  "summary": "Updated trial summary",
  "status": "RECRUITING"
}
```

---

## Success Response

**200 OK**

---

# POST /api/v1/trials/{trialId}/upload-protocol

## Purpose

Uploads the official trial protocol document.

The upload triggers asynchronous AI processing.

Processing includes:

```
Upload PDF

↓

Store Document

↓

Create Task

↓

Extract Text

↓

Extract Eligibility Criteria

↓

Generate Embeddings
```

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Research Coordinator
- Hospital Administrator

---

## Content Type

```http
multipart/form-data
```

---

## Request

| Field | Type | Required |
|---|---|---|
| file | PDF | Yes |

---

## File Requirements

| Rule | Value |
|---|---|
| Supported Type | application/pdf |
| Maximum Size | 20 MB |

---

## Success Response

**202 Accepted**

```json
{
  "data": {
    "taskId": "uuid",
    "status": "PROCESSING"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 202 | Upload accepted |
| 400 | Invalid file |
| 401 | Authentication required |
| 403 | Permission denied |
| 413 | File too large |
| 415 | Unsupported media type |

---

# POST /api/v1/trials/{trialId}/archive

## Purpose

Archives a clinical trial.

Archived trials remain available for historical reporting and audit purposes.

Archived trials are excluded from new matching workflows.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Research Coordinator
- Hospital Administrator

---

## Success Response

**204 No Content**

---

## Business Rules

Trial archival:

- Preserves AI evaluation history.
- Preserves extracted criteria.
- Preserves audit records.
- Prevents new matching requests.

---

# Trial API Summary

| Endpoint | Description |
|---|---|
| POST `/trials` | Create trial |
| GET `/trials` | List trials |
| GET `/trials/{trialId}` | Retrieve trial |
| PATCH `/trials/{trialId}` | Update trial metadata |
| POST `/trials/{trialId}/upload-protocol` | Upload protocol |
| POST `/trials/{trialId}/archive` | Archive trial |

# 18. Trial Criteria API

Trial criteria are generated by AI processing and are owned by the Trial domain.

The API provides read-only access to extracted criteria.

Eligibility criteria are generated through AI processing workflows.

The API provides access to structured criteria used by the matching pipeline.


## Trial Criteria Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/trials/{trialId}/criteria` | List trial criteria |
| GET | `/api/v1/trials/{trialId}/criteria/{criteriaId}` | Retrieve criterion |


# GET /api/v1/trials/{trialId}/criteria


## Purpose

Returns structured eligibility criteria extracted from a trial protocol.


## Authentication

Required


## Authorization

Authenticated Clinical User


## Success Response

200 OK


Example:

{
 "data": [
   {
     "id": "uuid",
     "type": "INCLUSION",
     "criterion": "Patient age must be above 18"
   }
 ],
 "metadata": {
   "requestId": "uuid"
 }
}


## Rules

- Criteria are generated by AI processing workflows.
- Criteria should not be manually modified after extraction.
- Criteria changes require a new trial version.
- Criteria embeddings must remain traceable to the original criterion.

---

## Trial API Rules

- Trials are scoped to hospitals.
- Trials are never permanently deleted.
- Protocol processing happens asynchronously.
- AI extraction results must preserve traceability.
- Future protocol versions should be introduced through versioning APIs.

---

---

# 19. Matching API

The Matching API provides AI-assisted clinical trial matching for patients.

It manages the business workflow of evaluating patient eligibility against clinical trials.

The API does not expose internal AI implementation details.

The following remain internal to the AI Service:

- Embedding generation
- Vector similarity search
- Retrieval pipeline
- Prompt construction
- LLM execution
- Response validation

AI Service APIs are internal APIs.
AI Service communication must use service-to-service authentication.

Direct public exposure of AI endpoints is prohibited.

Allowed communication:

Backend Service
      |
      |
Authenticated Internal Request
      |
      ↓
AI Service

Frontend applications must never directly call AI Service endpoints.

All AI workflows must be accessed through Backend APIs.

Request flow:

Frontend
    |
    ↓
Backend API
    |
    ↓
AI Service
    |
    ↓
Vector Database / LLM / Processing Pipeline

---

## Matching Workflow

The matching workflow follows this process:

```
Patient Selected

↓

Matching Request Created

↓

Background Task Created

↓

Patient Notes Retrieved

↓

Embeddings Generated

↓

Trial Criteria Retrieved

↓

AI Evaluation Performed

↓

Matching Result Generated
```

---

## Matching Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/matching/requests` | Create matching request |
| GET | `/api/v1/matching/requests` | List matching requests |
| GET | `/api/v1/matching/requests/{requestId}` | Retrieve matching request |
| GET | `/api/v1/matching/results/{resultId}` | Retrieve matching result |

---

# POST /api/v1/matching/requests

## Purpose

Creates a new AI matching request for a patient.

The request evaluates patient eligibility against available clinical trials.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- Physician
- Research Coordinator
- Hospital Administrator

---

## Request Body

```json
{
  "patientId": "uuid",
  "topK": 10
}
```

---

## Validation

The request must satisfy:

- Patient exists.
- Patient belongs to authenticated hospital.
- Patient has active clinical notes.
- `topK` is within supported limits.
- User has permission to access patient data.

---

## Processing

Matching is executed asynchronously.

Flow:

```
Create Matching Request

↓

Create Background Task

↓

Queue AI Processing

↓

Return Request ID and Task ID

↓

Process Evaluation
```

---

## Success Response

**202 Accepted**

```json
{
  "data": {
    "requestId": "uuid",
    "taskId": "uuid",
    "status": "PROCESSING"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 202 | Matching request accepted |
| 400 | Validation failed |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Patient not found |
| 409 | Matching request already running |

---

# GET /api/v1/matching/requests

## Purpose

Returns matching requests accessible to the authenticated user.

Results are restricted by hospital tenant boundaries.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Query Parameters

| Parameter | Description |
|---|---|
| patientId | Filter by patient |
| status | Filter by processing status |
| page | Page number |
| size | Page size |
| sort | Sort field |

---

## Success Response

**200 OK**

```json
{
  "data": [
    {
      "requestId": "uuid",
      "patientId": "uuid",
      "status": "COMPLETED",
      "createdAt": "2026-08-08T10:30:00Z"
    }
  ],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 50,
    "totalPages": 3,
    "requestId": "uuid"
  }
}
```

---

# GET /api/v1/matching/requests/{requestId}

## Purpose

Retrieves the current state of a matching request.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Path Parameters

| Parameter | Description |
|---|---|
| requestId | Matching request identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "requestId": "uuid",
    "patientId": "uuid",
    "taskId": "uuid",
    "status": "PROCESSING"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:30:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Request returned |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Request not found |

---

# GET /api/v1/matching/results/{resultId}

## Purpose

Returns a completed AI matching evaluation.

The result contains eligible trials, confidence scores, and AI explanations.

---

## Authentication

Required

---

## Authorization

Authenticated Clinical User

---

## Path Parameters

| Parameter | Description |
|---|---|
| resultId | Matching result identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "requestId": "uuid",
    "patientId": "uuid",
    "status": "COMPLETED",
    "generatedAt": "2026-08-08T12:00:00Z",
    "results": [
      {
        "trialId": "uuid",
        "eligibilityStatus": "ELIGIBLE",
        "confidence": 0.91,
        "explanation": "Patient satisfies eligibility criteria.",
        "missingInformation": []
      }
    ]
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T12:00:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Result returned |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Result not found |

---

# Matching API Summary

| Endpoint | Description |
|---|---|
| POST `/matching/requests` | Create matching request |
| GET `/matching/requests` | List matching requests |
| GET `/matching/requests/{requestId}` | Retrieve matching request |
| GET `/matching/results/{resultId}` | Retrieve matching result |

---

## Matching API Rules

- Matching requests are immutable after creation.
- Matching results are preserved for auditability.
- AI explanations must be stored with generated results.
- Historical results must remain reproducible.
- Model changes should create new evaluation versions instead of modifying previous results.
- All matching operations generate audit records.

Each matching result must store AI execution metadata:

Example:

{
  "modelVersion": "medmatch-v1",
  "embeddingModel": "all-MiniLM-L6-v2",
  "promptVersion": "eligibility-v1",
  "generatedAt": "2026-08-08T12:00:00Z"
}

This ensures previous AI decisions remain reproducible.

---

---

# 20. Task API

The Task API manages asynchronous operations executed by background workers.

MedMatch uses asynchronous processing for long-running operations such as:

- Trial protocol processing
- PDF extraction
- Eligibility criteria extraction
- Embedding generation
- AI matching execution
- Future bulk operations

The Task API provides a common interface for tracking these operations.

---

## Task Lifecycle

All asynchronous tasks follow this lifecycle:

```
REQUESTED

↓

QUEUED

↓

PROCESSING

↓

COMPLETED

or

FAILED

or

CANCELLED
```

---

## Task Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/tasks` | List tasks |
| GET | `/api/v1/tasks/{taskId}` | Retrieve task status |

---

# GET /api/v1/tasks

## Purpose

Returns asynchronous tasks accessible to the authenticated user.

Tasks are restricted according to hospital tenant boundaries.

---

## Authentication

Required

---

## Authorization

Authenticated User

---

## Query Parameters

| Parameter | Description |
|---|---|
| page | Page number |
| size | Page size |
| status | Filter task status |
| taskType | Filter task type |
| createdBy | Filter by user |
| sort | Sort field |

---

## Success Response

**200 OK**

```json
{
  "data": [
    {
      "id": "uuid",
      "taskType": "TRIAL_PROTOCOL_PROCESSING",
      "status": "PROCESSING",
      "createdAt": "2026-08-08T10:30:00Z"
    }
  ],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 25,
    "totalPages": 2,
    "requestId": "uuid"
  }
}
```

---

## Task Types

| Task Type | Description | Worker |
|---|---|---|
| TRIAL_PROTOCOL_PROCESSING | Extract trial information from protocol | Celery Worker |
| CRITERIA_EXTRACTION | Extract eligibility criteria | Celery Worker |
| EMBEDDING_GENERATION | Generate vector embeddings | Celery Worker |
| MATCHING_EXECUTION | Execute AI matching workflow | Celery Worker |
| BULK_PROCESSING | Future bulk operations | Celery Worker |

---

# GET /api/v1/tasks/{taskId}

## Purpose

Retrieves the current status and details of an asynchronous task.

---

## Authentication

Required

---

## Authorization

Authenticated User

---

## Path Parameters

| Parameter | Description |
|---|---|
| taskId | Task identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "taskType": "MATCHING_EXECUTION",
    "status": "COMPLETED",
    "progress": 100,
    "createdAt": "2026-08-08T10:30:00Z",
    "completedAt": "2026-08-08T10:32:00Z"
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T10:32:00Z"
  }
}
```

---

## Failed Task Response Example

```json
{
  "data": {
    "id": "uuid",
    "taskType": "TRIAL_PROTOCOL_PROCESSING",
    "status": "FAILED",
    "errorCode": "TASK_PROCESSING_FAILED",
    "errorMessage": "Unable to extract protocol content."
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Task returned |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Task not found |

---

# Task API Rules

- Tasks are immutable after completion.
- Task status changes must be recorded.
- Failed tasks must preserve error information.
- Task ownership follows hospital tenant isolation.
- Clients should poll task status instead of directly accessing worker systems.
- Task execution details remain internal to backend services.

---

# Task API Summary

| Endpoint | Description |
|---|---|
| GET `/tasks` | List tasks |
| GET `/tasks/{taskId}` | Retrieve task status |

---


# 21. Audit API

The Audit API provides access to immutable audit records generated throughout the MedMatch platform.

Audit records provide traceability for:

- Authentication events
- Authorization events
- Patient data access
- Trial operations
- Matching operations
- Administrative actions

Audit records are generated automatically by backend services.

Clients cannot create, update, or delete audit records.

---

## Audit Principles

Audit records must:

- Remain immutable.
- Preserve historical activity.
- Support compliance investigation.
- Respect hospital tenant isolation.
- Include sufficient context for troubleshooting.

---

## Audit Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/audit/logs` | List audit logs |
| GET | `/api/v1/audit/logs/{auditId}` | Retrieve audit record |

---

# GET /api/v1/audit/logs

## Purpose

Returns audit records accessible to the authenticated administrator.

Access is restricted based on tenant boundaries.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- System Administrator
- Hospital Administrator

---

## Query Parameters

| Parameter | Description |
|---|---|
| page | Page number |
| size | Page size |
| userId | Filter by user |
| hospitalId | Filter by hospital (System Administrator only) |
| entityType | Filter by resource type |
| entityId | Filter by resource identifier |
| action | Filter by action |
| eventType | Filter by event category |
| from | Start timestamp |
| to | End timestamp |
| sort | Sort field |

---

## Success Response

**200 OK**

```json
{
  "data": [
    {
      "id": "uuid",
      "occurredAt": "2026-08-08T12:15:00Z",
      "userId": "uuid",
      "hospitalId": "uuid",
      "action": "CREATE_PATIENT",
      "entityType": "PATIENT",
      "entityId": "uuid",
      "eventType": "BUSINESS"
    }
  ],
  "metadata": {
    "page": 1,
    "size": 20,
    "totalElements": 200,
    "totalPages": 10,
    "requestId": "uuid"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Audit logs returned |
| 401 | Authentication required |
| 403 | Permission denied |

---

# GET /api/v1/audit/logs/{auditId}

## Purpose

Retrieves a single immutable audit record.

---

## Authentication

Required

---

## Authorization

Allowed roles:

- System Administrator
- Hospital Administrator

---

## Path Parameters

| Parameter | Description |
|---|---|
| auditId | Audit record identifier |

---

## Success Response

**200 OK**

```json
{
  "data": {
    "id": "uuid",
    "occurredAt": "2026-08-08T12:15:00Z",
    "hospitalId": "uuid",
    "userId": "uuid",
    "action": "CREATE_PATIENT",
    "entityType": "PATIENT",
    "entityId": "uuid",
    "eventType": "BUSINESS",
    "correlationId": "uuid",
    "metadata": {}
  },
  "metadata": {
    "requestId": "uuid",
    "timestamp": "2026-08-08T12:15:00Z"
  }
}
```

---

## Possible Responses

| Status | Meaning |
|---|---|
| 200 | Audit record returned |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Audit record not found |

---

# Audit Event Types

| Event Type | Description |
|---|---|
| AUTHENTICATION | Login and authentication events |
| AUTHORIZATION | Permission and access events |
| BUSINESS | Business operation events |
| SYSTEM | Internal system events |

---

# Common Audit Actions

Examples:

| Action | Entity |
|---|---|
| CREATE_USER | USER |
| UPDATE_USER | USER |
| CREATE_PATIENT | PATIENT |
| ACCESS_PATIENT_NOTE | PATIENT_NOTE |
| CREATE_TRIAL | TRIAL |
| UPLOAD_PROTOCOL | TRIAL |
| CREATE_MATCHING_REQUEST | MATCHING_REQUEST |

---

# Audit API Summary

| Endpoint | Description |
|---|---|
| GET `/audit/logs` | List audit records |
| GET `/audit/logs/{auditId}` | Retrieve audit record |

---

## Audit API Rules

- Audit records are read-only.
- Audit records cannot be deleted.
- Audit records cannot be modified.
- All sensitive operations should generate audit events.
- Audit access itself may generate audit records.

---

---

# 22. Pagination

Collection endpoints support pagination to efficiently handle large datasets.

Examples:

- Patients
- Users
- Trials
- Matching Requests
- Audit Logs
- Tasks

---

## Pagination Parameters

All paginated endpoints support:

| Parameter | Description | Default |
|---|---|---|
| page | Page number (0-based) | 0 |
| size | Number of records per page | 20 |
| sort | Sorting expression | createdAt,desc |

---

## Example Request

```http
GET /api/v1/patients?page=0&size=20&sort=createdAt,desc
```

---

## Paginated Response Format

```json
{
  "data": [],
  "metadata": {
    "page": 0,
    "size": 20,
    "totalElements": 250,
    "totalPages": 13,
    "requestId": "uuid"
  }
}
```

---

# 23. Filtering

Collection endpoints may support filtering based on resource attributes.

Filtering parameters are optional.

---

## Filtering Rules

Filters must:

- Be explicitly documented per endpoint.
- Use predictable parameter names.
- Respect tenant boundaries.
- Not expose unauthorized data.

---

## Examples

Patients:

```http
GET /api/v1/patients?active=true
```

Trials:

```http
GET /api/v1/trials?phase=PHASE_II
```

Tasks:

```http
GET /api/v1/tasks?status=PROCESSING
```

---

# 24. Sorting

Collection endpoints support sorting where applicable.

---

## Sorting Format

Single field:

```http
?sort=createdAt,desc
```

Multiple fields:

```http
?sort=status,asc&sort=createdAt,desc
```

---

## Sorting Rules

Supported sorting fields must be documented by each endpoint.

Clients must not assume unsupported fields are sortable.

---

# 25. Idempotency

Idempotency prevents duplicate execution of operations caused by:

- Network retries
- Client retries
- Timeout recovery

---

## Idempotency Header

Long-running operations may support:

```http
Idempotency-Key: unique-request-id
```

---

## Operations Requiring Idempotency

Examples:

- Trial protocol upload
- Matching request creation
- Bulk processing
- Report generation

---

## Idempotency Behavior

When the same idempotency key is received:

First request:

```
Operation Created
```

Repeated request:

```
Existing Operation Returned
```

The system must not create duplicate resources or background tasks.

---

# 26. Rate Limiting

MedMatch may enforce API rate limits to protect system stability.

---

## Rate Limit Response

When a client exceeds limits:

```http
429 Too Many Requests
```

---

## Rate Limit Headers

Future implementations may provide:

```http
X-RateLimit-Limit

X-RateLimit-Remaining

X-RateLimit-Reset
```

---

## Rate Limiting Applies To

Examples:

- Authentication attempts
- AI matching requests
- File uploads
- Search operations
- Public APIs

---

# 27. Future API Expansion

The MedMatch API is designed for additive evolution.

Future capabilities should be introduced through new resources rather than breaking existing contracts.

---

## Planned Future APIs

| API | Purpose |
|---|---|
| Task API Extensions | Advanced workflow management |
| Notification API | User notifications |
| Attachment API | Medical document storage |
| Report API | Generated reports |
| Trial Version API | Protocol version management |
| Sponsor API | Trial sponsor management |
| FHIR API | Healthcare interoperability |
| Diagnosis API | Clinical diagnoses |
| Medication API | Medication records |
| Laboratory API | Lab results |
| AI Feedback API | Human feedback for AI improvement |
| Model Evaluation API | AI model performance tracking |
| Analytics API | Platform analytics |

---

# 28. Related Documents

This API specification works together with:

| Document | Purpose |
|---|---|
| `docs/architecture/backend-architecture.md` | Backend system design |
| `docs/architecture/ai-architecture.md` | AI pipeline design |
| `docs/database/schema.md` | Database structure |
| `docs/standards/api-guidelines.md` | API development standards |
| `docs/security/security-policy.md` | Security requirements |

---

# 29. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | 2026-08-08 | Initial production API contract |

---

# 30. Approval

This document represents the official API contract for the MedMatch platform.

All services exposing REST APIs must follow this specification.

Any changes affecting API behavior require:

- Documentation update
- Backward compatibility review
- Engineering approval
- Version update if required

---

# End of Document