# Backend Architecture

---

# Document Information

| Field | Value |
|--------|-------|
| Document | Backend Architecture |
| Document ID | ARCH-002 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | Backend Services |
| Classification | Architecture |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document describes the internal architecture of the MedMatch backend platform.

It defines how backend services are organized, how they communicate, how responsibilities are separated, and how requests are processed throughout the system.

The objective is to provide a consistent architectural model for all backend services while allowing individual services to evolve independently.

---

# Scope

This document applies to every backend service within the MedMatch platform.

Examples include:

- Authentication Service
- AI Service
- Future Notification Service
- Future Reporting Service
- Future Integration Services

The document focuses on architectural organization rather than implementation details.

Implementation standards are documented separately.

---

# Backend Overview

The backend is composed of independent services that collaborate to deliver platform functionality.

Each service owns a single business capability and communicates through stable interfaces.

The backend architecture emphasizes:

- Separation of concerns
- Independent deployment
- Stateless processing
- Horizontal scalability
- Secure communication
- Clear ownership of business capabilities

No backend service shall assume responsibility for another service's domain.

---

# Backend Services

The current platform consists of the following backend services.

| Service | Technology | Primary Responsibility |
|----------|------------|------------------------|
| Authentication Service | Spring Boot | Identity, authentication, authorization, hospital management |
| AI Service | FastAPI | Trial ingestion, AI processing, patient matching |

Future services may be introduced as the platform evolves.

Examples include:

- Notification Service
- Reporting Service
- Audit Service
- Integration Service
- Search Service

Each service shall own its domain and remain independently deployable.

---

# Service Responsibilities

Every backend service shall satisfy the following architectural responsibilities.

A service shall:

- Own its business domain.
- Expose well-defined APIs.
- Validate incoming requests.
- Protect its resources.
- Persist its own data.
- Publish operational telemetry.
- Remain independently testable.

A service shall not:

- Implement another service's business rules.
- Access another service's internal database directly.
- Assume knowledge of another service's implementation.

Business ownership shall remain explicit.

---

# Service Communication

Services communicate through documented interfaces.

The primary communication mechanism is synchronous HTTP APIs.

Communication principles include:

- Stable contracts
- Explicit versioning
- Standardized error responses
- Secure authentication
- Idempotent behavior where appropriate

Direct database access between services is prohibited.

Future asynchronous communication mechanisms may be introduced without changing service ownership boundaries.

---

# Backend Responsibilities

Collectively, the backend platform provides:

- User authentication
- Authorization
- Hospital management
- Patient management
- Trial management
- AI-assisted eligibility extraction
- Semantic search
- Eligibility evaluation
- Background processing
- Audit logging
- Reporting

Responsibilities are distributed across services according to business ownership.

---

# Architectural Style

The backend follows a service-oriented architecture.

Within each service, a layered architecture is used.

At the platform level:

```text
Frontend

↓

Authentication Service

↓

AI Service

↓

Infrastructure
```

Within each service:

```text
Controller / Router

↓

Service

↓

Repository

↓

Database
```

These architectural layers are consistent across backend services, regardless of implementation language.

---

---

# Request Lifecycle

Every backend request follows a consistent processing lifecycle regardless of the target service.

A request shall pass through the following stages:

```text
Client Request

↓

Authentication

↓

Authorization

↓

Validation

↓

Business Logic

↓

Persistence

↓

Response Serialization

↓

HTTP Response
```

Each stage has a clearly defined responsibility.

Cross-cutting concerns such as authentication, logging, and validation shall execute before business logic.

---

# Authentication Flow

Authentication verifies the identity of the caller.

The Authentication Service is responsible for issuing signed JWT access tokens.

The authentication flow consists of:

```text
User Login

↓

Authentication Service

↓

Credential Verification

↓

JWT Generation

↓

Client Stores Access Token

↓

Authenticated API Requests
```

Protected backend services validate JWT signatures before processing requests.

Authentication state is not stored within backend service instances.

---

## JWT Claims

JWT access tokens shall include the claims required by downstream services.

Examples include:

- User identifier
- Email
- Role
- Hospital identifier
- Expiration time
- Issuer
- Subject

Services shall validate token integrity before trusting any claim.

---

## Token Validation

Every protected request shall validate:

- Signature
- Expiration
- Issuer
- Required claims

Requests failing validation shall be rejected before business processing begins.

---

# Authorization Model

Authorization determines whether an authenticated user may perform a requested action.

Authorization is enforced after successful authentication.

Authorization decisions consider:

- User role
- Hospital ownership
- Resource ownership
- Business permissions

Authorization failures shall return appropriate error responses without exposing internal implementation details.

---

## Role-Based Access Control

The platform implements Role-Based Access Control (RBAC).

Current roles include:

- System Administrator
- Hospital Administrator
- Clinical Research Coordinator
- Physician
- Patient
- Sponsor

Each role is granted only the permissions required for its responsibilities.

Additional roles may be introduced without altering the overall authorization model.

---

# Multi-Tenancy

The platform supports logical multi-tenancy.

Each hospital represents an isolated tenant.

Tenant isolation applies to:

- Users
- Patients
- Trials
- Matching results
- Reports
- Audit logs

A request shall access only resources belonging to the authenticated tenant unless elevated administrative privileges explicitly allow broader access.

---

## Tenant Context

Tenant information is established during authentication.

The authenticated tenant context is propagated throughout request processing.

Business logic shall rely on the authenticated tenant context rather than client-provided tenant identifiers.

---

## Data Isolation

Data isolation shall be enforced at every layer.

Isolation includes:

- Repository queries
- Service logic
- Cache entries
- Search results
- Reports

Tenant isolation shall never rely solely on frontend controls.

---

# Layered Architecture

Each backend service follows the same layered architecture.

```text
Controller / Router

↓

Service

↓

Repository

↓

Database
```

Each layer has one primary responsibility.

---

## Controller / Router Layer

Responsibilities include:

- Receive HTTP requests
- Validate request structure
- Invoke services
- Return HTTP responses

Controllers and routers shall remain thin.

Business logic shall not be implemented in this layer.

---

## Service Layer

The service layer contains business logic.

Responsibilities include:

- Business validation
- Workflow orchestration
- Transaction coordination
- External service interaction
- Domain rules

Business rules shall exist only within the service layer.

---

## Repository Layer

Repositories encapsulate persistence.

Responsibilities include:

- Query execution
- Persistence
- Updates
- Deletions

Repositories shall not implement business rules.

---

## Persistence Layer

The persistence layer manages durable application data.

Responsibilities include:

- Relational storage
- Vector storage
- Schema evolution
- Transaction consistency

Database implementation details remain isolated from higher application layers.

---

# Shared Libraries

Shared functionality shall be implemented through reusable libraries where appropriate.

Examples include:

- Authentication utilities
- Common exception models
- Shared DTOs
- Validation utilities
- Logging utilities

Shared libraries shall avoid introducing unnecessary coupling between services.

Business logic shall remain inside the owning service.

---

# Database Access

Every service owns the data for its business domain.

Database access shall occur only through repositories.

Services shall not bypass repository abstractions.

Direct SQL execution outside repository implementations shall be avoided unless explicitly justified.

---

## Transaction Boundaries

Business transactions belong within the service layer.

Each transaction shall represent one complete business operation.

Transactions should:

- Be short-lived.
- Be deterministic.
- Avoid remote service calls.
- Minimize lock duration.

---

## Schema Evolution

Database schema changes shall be managed through versioned migrations.

Schema evolution shall be:

- Repeatable
- Auditable
- Backward compatible whenever practical

Manual production schema modifications are prohibited.

---

---

# Background Processing

Background processing is used for operations that are time-consuming or do not require an immediate response to the client.

The platform delegates asynchronous workloads to Celery workers.

Background processing improves:

- User experience
- Request latency
- System throughput
- Resource utilization

---

## Background Workloads

The following operations shall execute asynchronously where appropriate:

- Trial PDF ingestion
- PDF text extraction
- Eligibility criteria extraction
- Embedding generation
- Vector indexing
- Notification delivery
- Report generation
- Cache warming

Interactive API requests should remain short-lived.

---

## Task Lifecycle

A typical background task follows this lifecycle:

```text
Client Request

↓

API Validation

↓

Task Queued

↓

Celery Worker

↓

Business Processing

↓

Database Update

↓

Task Completion
```

Clients may poll task status or receive updates through future notification mechanisms.

---

## Retry Strategy

Transient failures may be retried automatically.

Examples include:

- Network interruptions
- Temporary database failures
- External AI provider timeouts

Permanent business validation failures shall not be retried.

Retry policies shall be explicitly configured.

---

# Caching Strategy

Caching improves application performance by reducing repeated computation and unnecessary database access.

Redis serves as the primary caching layer.

Caching shall improve performance without becoming the authoritative source of business data.

---

## Cacheable Data

Suitable cache candidates include:

- Trial search results
- Embedding retrieval results
- Frequently accessed reference data
- User permissions
- Configuration values

Caching decisions shall be based on access patterns and performance measurements.

---

## Cache Invalidation

Cached data shall remain consistent with the underlying system of record.

Invalidation strategies may include:

- Time-based expiration
- Explicit invalidation
- Event-driven invalidation

Cache invalidation shall be deterministic and documented.

---

## Cache Isolation

Multi-tenant environments shall isolate cached data.

Cache keys should include sufficient context to prevent cross-tenant access.

Examples include:

- Tenant identifier
- Resource identifier
- User identifier (where appropriate)

---

# Error Handling Strategy

The backend shall implement a consistent error handling strategy across all services.

Errors shall be:

- Predictable
- Structured
- Logged
- Traceable
- Safe for clients

---

## Error Classification

Errors are categorized as:

| Category | Examples |
|----------|----------|
| Validation | Invalid request data |
| Authentication | Missing or invalid credentials |
| Authorization | Insufficient permissions |
| Business | Domain rule violations |
| Infrastructure | Database or Redis failures |
| External | AI provider or third-party failures |
| Unexpected | Unhandled application failures |

Each category shall map to standardized API responses.

---

## Error Responses

Error responses shall comply with the platform API Guidelines.

Responses should include:

- Error code
- Error message
- Correlation identifier
- Timestamp

Internal implementation details shall never be exposed.

---

## Failure Isolation

Failures should remain isolated whenever practical.

Examples include:

- AI service failure shall not affect authentication.
- Cache failure shall not prevent database access when recovery is possible.
- Background worker failure shall not terminate API services.

Failure isolation improves overall platform resilience.

---

# Observability

Observability enables engineers to understand system behavior during development and production.

The backend shall provide sufficient telemetry to diagnose operational issues.

---

## Logging

All backend services shall produce structured logs.

Logs should include:

- Timestamp
- Log level
- Service name
- Correlation ID
- User ID (when applicable)
- Tenant ID (when applicable)
- Request path
- Execution duration

Sensitive information shall never be logged.

---

## Metrics

Services shall expose operational metrics.

Examples include:

- Request count
- Request latency
- Error rate
- Database latency
- Cache hit ratio
- Queue depth
- Task execution duration

Metrics support monitoring and capacity planning.

---

## Health Checks

Every backend service shall expose health endpoints.

Health checks should verify:

- Application readiness
- Database connectivity
- Redis connectivity
- External dependency status (where appropriate)

Health endpoints support orchestration and automated recovery.

---

## Distributed Tracing

Request correlation shall be preserved across service boundaries.

Every request should include a correlation identifier propagated through:

- HTTP requests
- Background tasks
- Logs
- Metrics

Distributed tracing improves root-cause analysis.

---

# Deployment Model

Backend services are designed for containerized deployment.

Each service executes independently within its own container.

Containerization provides:

- Environment consistency
- Deployment portability
- Operational isolation

---

## Kubernetes Deployment

Production deployments use Kubernetes.

Responsibilities include:

- Service discovery
- Scheduling
- Horizontal scaling
- Rolling updates
- Self-healing
- Secret management
- Configuration management

Application services remain independent of deployment infrastructure.

---

## Stateless Services

Application services shall remain stateless.

Persistent state belongs in:

- PostgreSQL
- Redis
- External storage

Stateless services enable horizontal scaling and simplified recovery.

---

# Architectural Principles

The backend architecture follows these principles.

## Domain Ownership

Each service owns its business domain.

No service shall modify another service's domain data directly.

---

## Loose Coupling

Services communicate through documented interfaces.

Internal implementation details remain private.

Loose coupling enables independent evolution.

---

## High Cohesion

Each service focuses on one primary business capability.

Responsibilities unrelated to the service domain shall remain outside the service.

---

## API-First Development

Backend functionality shall be exposed through documented APIs.

API contracts shall remain stable and versioned.

---

## Security by Design

Security considerations are incorporated into every architectural layer.

Authentication, authorization, validation, auditing, and secure configuration are mandatory platform capabilities.

---

## Operational Simplicity

Operational complexity shall be minimized through:

- Standardized service structure
- Consistent deployment
- Shared engineering standards
- Automated health monitoring

Operational practices should remain predictable across all services.

---

# Related Documents

This document complements:

- `docs/architecture/system-overview.md`
- `docs/architecture/database-architecture.md`
- `docs/architecture/ai-architecture.md`
- `docs/architecture/frontend-architecture.md`

Implementation standards are defined in:

- `docs/standards/api-guidelines.md`
- `docs/standards/java-style-guide.md`
- `docs/standards/python-style-guide.md`

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial backend architecture document. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All backend services within the MedMatch platform shall conform to the architectural principles and constraints defined in this document unless superseded by a later approved revision.

---

**End of Document**