# System Overview

---

# Document Information

| Field | Value |
|--------|-------|
| Document | System Overview |
| Document ID | ARCH-001 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | Entire Platform |
| Classification | Architecture |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document provides a high-level architectural overview of the MedMatch platform.

It describes the purpose of the system, its major components, user groups, architectural principles, deployment model, and technology choices.

This document serves as the primary architectural entry point for engineers, architects, reviewers, and stakeholders.

Readers should be able to understand how the platform is organized without reviewing implementation details.

---

# Scope

This document describes the platform architecture at a conceptual level.

It intentionally excludes implementation details such as:

- Class design
- Database schemas
- API specifications
- Infrastructure manifests
- Source code

Those topics are documented separately.

---

# Vision

MedMatch is an AI-powered clinical trial matching platform designed to assist hospitals, physicians, clinical research coordinators, sponsors, and patients in identifying eligible clinical trials using structured eligibility criteria and intelligent matching.

The platform combines modern web technologies, secure backend services, vector search, and large language models to reduce manual screening effort while improving the speed and quality of clinical trial recruitment.

The system is designed to support production deployment, multi-tenancy, scalability, security, and future expansion.

---

# Goals

The platform aims to:

- Simplify clinical trial discovery.
- Reduce manual eligibility screening.
- Accelerate patient recruitment.
- Improve collaboration between hospitals and research teams.
- Provide explainable AI-assisted eligibility decisions.
- Maintain secure multi-tenant isolation.
- Support enterprise-scale deployment.
- Deliver an intuitive user experience across all supported roles.

---

# Non Goals

The current scope of MedMatch does not include:

- Electronic Health Record replacement.
- Hospital billing.
- Appointment scheduling.
- Electronic prescribing.
- Laboratory management.
- Insurance processing.
- Clinical decision support unrelated to trial matching.

Future versions may integrate with external healthcare systems, but these capabilities are outside the scope of the current platform.

---

# System Overview

MedMatch is a cloud-native, service-oriented platform composed of independent backend services, a modern React frontend, shared infrastructure components, and AI-powered matching capabilities.

At a high level, the platform consists of:

- A React web application for all user roles.
- A Spring Boot Authentication Service responsible for identity and access management.
- A FastAPI AI Service responsible for patient-trial matching and AI workflows.
- PostgreSQL as the primary relational database.
- pgvector for semantic similarity search.
- Redis for caching and asynchronous messaging.
- Celery workers for background processing.
- Kubernetes for orchestration.
- Docker for containerization.

Each component has a clearly defined responsibility and communicates through well-defined interfaces.

---

# Core Capabilities

The platform provides the following capabilities:

- Secure authentication and authorization.
- Multi-tenant hospital management.
- Clinical trial ingestion.
- AI-assisted eligibility extraction.
- Patient management.
- Semantic search using embeddings.
- AI-powered patient-trial matching.
- Explainable eligibility reports.
- Administrative dashboards.
- Audit logging.
- Reporting and analytics.
- Background task processing.

Every capability is implemented as part of the overall service-oriented architecture.

---


---

# High-Level Architecture

The MedMatch platform follows a service-oriented architecture composed of independently deployable components.

Each service owns a clearly defined business capability and communicates through well-defined interfaces.

The architecture separates:

- Presentation
- Authentication
- AI Processing
- Data Persistence
- Background Processing
- Infrastructure

This separation improves scalability, maintainability, security, and independent deployment.

---

# Technology Stack

The platform uses the following technologies.

| Layer | Technology |
|--------|------------|
| Frontend | React 19, TypeScript, Vite |
| Styling | Tailwind CSS v4, shadcn/ui |
| Backend (Authentication) | Java 21, Spring Boot |
| Backend (AI) | Python 3.13, FastAPI |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Cache | Redis |
| Background Jobs | Celery |
| Message Broker | Redis |
| Authentication | JWT (RS256) |
| Containerization | Docker |
| Orchestration | Kubernetes |
| Monitoring | Prometheus, Grafana |
| API Documentation | OpenAPI |

Each technology has been selected based on its suitability for the platform's functional and operational requirements.

---

# Major Components

The platform consists of the following primary components.

## Frontend

Provides the web-based user interface.

Responsibilities include:

- Authentication
- Dashboard rendering
- Trial management
- Patient management
- Reporting
- Administrative functions
- AI result visualization

The frontend communicates only with backend APIs.

---

## Authentication Service

The Authentication Service manages identity and access.

Responsibilities include:

- User registration
- Login
- JWT generation
- Role management
- Hospital management
- Permission enforcement
- Authentication auditing

The Authentication Service is implemented using Spring Boot.

---

## AI Service

The AI Service provides all intelligent processing capabilities.

Responsibilities include:

- Trial ingestion
- PDF processing
- Eligibility extraction
- Embedding generation
- Semantic search
- Patient matching
- LLM reasoning
- Eligibility reporting

The AI Service is implemented using FastAPI.

---

## PostgreSQL

PostgreSQL serves as the primary transactional database.

It stores:

- Users
- Hospitals
- Patients
- Trials
- Trial criteria
- Audit logs
- Matching results

Relational integrity is maintained through normalized schemas and controlled migrations.

---

## pgvector

pgvector extends PostgreSQL with vector similarity search.

Responsibilities include:

- Embedding storage
- Cosine similarity search
- Top-K retrieval
- Semantic candidate selection

Vector search reduces the search space before AI reasoning.

---

## Redis

Redis provides in-memory infrastructure services.

Responsibilities include:

- Caching
- Celery message broker
- Temporary application state
- Performance optimization

Redis is not used as the primary system of record.

---

## Celery Workers

Celery workers execute asynchronous processing.

Examples include:

- PDF extraction
- Embedding generation
- Trial ingestion
- AI preprocessing
- Report generation

Background execution improves responsiveness for end users.

---

## Kubernetes

Kubernetes orchestrates the deployment of platform services.

Responsibilities include:

- Service discovery
- Scaling
- Health monitoring
- Rolling deployments
- Secret management
- Configuration management

Kubernetes provides the production execution environment.

---

# User Roles

The platform supports multiple user roles.

| Role | Responsibility |
|------|----------------|
| System Administrator | Platform administration |
| Hospital Administrator | Hospital management |
| Clinical Research Coordinator | Trial management and patient screening |
| Physician | Patient review and trial recommendations |
| Patient | View eligibility and trial matches |
| Sponsor | Monitor trial recruitment and analytics |

Each role has access only to the capabilities required for its responsibilities.

---

# System Boundaries

The MedMatch platform interacts with external users and supporting infrastructure.

Internal responsibilities include:

- Authentication
- Authorization
- Trial management
- Patient management
- AI matching
- Reporting

External systems may include:

- Identity providers
- Email providers
- Cloud object storage
- Monitoring platforms
- Future Electronic Health Record integrations

External integrations communicate through documented interfaces.

---

# Deployment Overview

The platform is designed for containerized deployment.

Each major component executes within its own container.

A typical deployment consists of:

- React Frontend
- Authentication Service
- AI Service
- PostgreSQL
- Redis
- Celery Worker
- Prometheus
- Grafana
- Kubernetes Ingress Controller

Each component can be updated independently while preserving overall platform availability.

---

---

# High-Level Data Flow

The MedMatch platform processes data through a sequence of well-defined interactions between users, services, and supporting infrastructure.

A typical patient-trial matching workflow follows these stages:

```text
User

↓

React Frontend

↓

Authentication Service

↓

AI Service

↓

PostgreSQL / pgvector

↓

LLM Reasoning

↓

Eligibility Result

↓

Frontend Dashboard
```

Background processing is delegated to Celery workers where long-running operations are required.

The architecture minimizes synchronous dependencies to improve responsiveness and scalability.

---

# Security Overview

Security is a foundational architectural principle.

The platform implements security through multiple layers.

## Authentication

User authentication is provided by the Authentication Service using JWT access tokens signed with asymmetric cryptography (RS256).

Authentication is required before accessing protected platform resources.

---

## Authorization

Authorization is enforced using Role-Based Access Control (RBAC).

Authorization decisions consider:

- User role
- Hospital ownership
- Resource ownership
- Business permissions

Every protected endpoint validates authorization before executing business logic.

---

## Multi-Tenancy

The platform supports logical multi-tenancy.

Hospital data is isolated to ensure that users can access only resources belonging to their organization unless explicitly authorized.

Multi-tenant isolation is enforced consistently across:

- API access
- Database queries
- Search operations
- Caching
- Reporting

---

## Data Protection

Sensitive information is protected through:

- HTTPS
- JWT authentication
- Password hashing
- Externalized secrets
- Input validation
- Centralized exception handling
- Audit logging

Security controls apply across the entire platform.

---

# Scalability Overview

The platform is designed for horizontal scalability.

Stateless application services allow additional instances to be deployed as demand increases.

Scalable components include:

- React frontend
- Authentication Service
- AI Service
- Celery workers

Infrastructure components support scaling through Kubernetes.

Redis and PostgreSQL may be scaled using deployment-specific strategies appropriate to the target environment.

---

## Horizontal Scaling

Application services are designed to support multiple running instances.

Horizontal scaling improves:

- Throughput
- Availability
- Fault tolerance

Session state is not stored within application instances.

---

## Background Processing Scalability

Background workloads are processed independently from user requests.

Additional Celery workers may be deployed to increase throughput for:

- PDF ingestion
- Embedding generation
- AI processing
- Report generation

Worker scaling does not require frontend or authentication service changes.

---

# Availability Goals

The platform aims to provide reliable access during normal operation.

Availability is supported through:

- Stateless services
- Health checks
- Kubernetes self-healing
- Rolling deployments
- Centralized monitoring
- Graceful failure handling

Individual service failures should be isolated wherever practical.

---

# Architectural Principles

The MedMatch architecture follows the following principles.

## Separation of Concerns

Each component has one clearly defined responsibility.

Responsibilities are not shared across unrelated services.

---

## Service Independence

Each service may be developed, tested, deployed, and scaled independently.

Service boundaries minimize coupling.

---

## API-First Design

All communication between frontend and backend occurs through documented APIs.

Service interfaces are treated as stable contracts.

---

## Security by Default

Security controls are incorporated into every architectural layer rather than added after implementation.

Authentication, authorization, validation, and auditing are integral platform capabilities.

---

## Cloud-Native Design

The platform is designed for containerized deployment and orchestration.

Infrastructure components are externalized from application logic.

---

## Observability

Operational visibility is provided through:

- Structured logging
- Metrics
- Health endpoints
- Distributed tracing
- Audit logs

Observability supports maintenance, troubleshooting, and operational monitoring.

---

## Maintainability

Clear service boundaries, standardized engineering practices, and comprehensive documentation improve long-term maintainability.

Architectural decisions prioritize simplicity and consistency.

---

# Future Expansion

The architecture is designed to accommodate future capabilities without significant structural changes.

Potential future enhancements include:

- Electronic Health Record integration
- FHIR interoperability
- Multi-region deployment
- Real-time notifications
- Additional AI models
- Federated search
- Clinical analytics
- Mobile applications
- Sponsor collaboration portals
- External research organization integration

Future capabilities should integrate through existing architectural principles and service boundaries.

---

# Related Documents

This document provides the architectural overview for the platform.

Additional architectural details are documented separately.

Related documents include:

- `docs/architecture/backend-architecture.md`
- `docs/architecture/frontend-architecture.md`
- `docs/architecture/database-architecture.md`
- `docs/architecture/ai-architecture.md`
- `docs/database/schema.md`

Engineering implementation standards are defined in:

- `docs/standards/api-guidelines.md`
- `docs/standards/java-style-guide.md`
- `docs/standards/python-style-guide.md`
- `docs/standards/frontend-style-guide.md`

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial system architecture overview. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All architectural decisions for the MedMatch platform shall align with the principles and constraints described in this document unless superseded by a later approved revision.

---

                Browser
                    │
                    ▼
                React Frontend
                    │
                ┌────┴────┐
                ▼         ▼
                Auth     AI Service
                │          │
                ├──────┐   │
                ▼      ▼   ▼
                Postgres Redis pgvector
                        │
                    Celery Worker

**End of Document**