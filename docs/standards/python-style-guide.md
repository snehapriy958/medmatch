# Python Style Guide

---

# Document Information

| Field | Value |
|--------|-------|
| Document | Python Style Guide |
| Document ID | PYTHON-STD-001 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | All Python Services |
| Classification | Engineering Standard |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document defines the engineering standards for developing Python applications within the MedMatch platform.

Its objective is to establish consistent architectural patterns, package organization, dependency management, coding conventions, and implementation practices across all Python services.

Following these standards improves readability, maintainability, scalability, testability, and operational consistency.

---

# Scope

These standards apply to every Python service in the repository.

Examples include:

- AI Matching Service
- Background Workers
- Celery Tasks
- Future AI Services

The standards apply to:

- Production code
- Test code
- Configuration
- Scripts
- Shared libraries

Unless explicitly documented, all Python code shall comply with this guide.

---

# Design Philosophy

Python code within MedMatch shall prioritize:

- Readability
- Explicitness
- Simplicity
- Maintainability
- Testability
- Security
- Performance
- Separation of concerns

Engineering decisions should prioritize long-term maintainability over implementation shortcuts.

---

# Project Structure

Every Python service shall follow the same high-level structure.

Example:

```text
ai-service/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── tasks/
│   ├── utils/
│   └── main.py
│
├── tests/
│
├── alembic/
│
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

Additional directories shall only be introduced when justified by project requirements.

---

# Package Organization

Packages shall be organized by responsibility.

Example:

```text
app/

├── api
│
├── core
│
├── db
│
├── models
│
├── repositories
│
├── schemas
│
├── services
│
├── tasks
│
├── utils
│
└── workers
```

Each package shall have one primary responsibility.

---

# Package Responsibilities

| Package | Responsibility |
|----------|----------------|
| api | FastAPI routers |
| core | Application configuration |
| db | Database configuration |
| models | SQLAlchemy models |
| repositories | Database access |
| schemas | Pydantic models |
| services | Business logic |
| tasks | Celery tasks |
| utils | Stateless helpers |
| workers | Background processing |

Responsibilities shall not overlap.

---

# Naming Conventions

The following naming conventions are mandatory.

| Element | Convention |
|----------|------------|
| Package | snake_case |
| Module | snake_case |
| Class | PascalCase |
| Function | snake_case |
| Variable | snake_case |
| Constant | UPPER_SNAKE_CASE |
| Enum | PascalCase |
| Enum Value | UPPER_SNAKE_CASE |

Names shall describe intent rather than implementation.

Avoid unnecessary abbreviations.

---

# Dependency Management

Python dependencies shall be explicitly declared.

Approved dependency files include:

- pyproject.toml
- requirements.txt

Dependency versions shall be pinned for production deployments.

Unused dependencies shall be removed.

Development dependencies shall remain separate from production dependencies whenever practical.

---

# Layer Responsibilities

The application shall follow a layered architecture.

```text
Router

↓

Service

↓

Repository

↓

Database
```

Each layer has one responsibility.

Routers expose HTTP APIs.

Services implement business logic.

Repositories access persistence.

Models represent database entities.

Schemas define API contracts.

Layer boundaries shall remain explicit.

---

# Python Coding Principles

Python implementations shall follow these principles:

- Explicit is better than implicit.
- Simple is better than complex.
- Prefer composition over inheritance.
- Fail fast.
- Minimize side effects.
- Avoid duplicated business logic.
- Prefer immutable data where practical.

Code should remain understandable without requiring extensive comments.

---

# Related Documents

This guide complements:

- `docs/standards/repository-standards.md`
- `docs/standards/api-guidelines.md`
- `docs/standards/definition-of-done.md`

Implementation quality requirements are defined by the Definition of Done.

---


---

# FastAPI Router Standards

Routers expose the HTTP interface of the service.

Routers are responsible only for:

- Receiving HTTP requests
- Validating request structure
- Invoking services
- Returning HTTP responses
- Declaring endpoint metadata

Routers shall not contain business logic.

Routers shall remain thin.

---

## Router Responsibilities

Routers may:

- Accept request parameters
- Validate request models
- Inject dependencies
- Return response models
- Raise HTTP exceptions when appropriate

Routers shall not:

- Access repositories directly
- Execute SQL
- Call external services
- Implement business rules
- Perform complex calculations

---

## Router Organization

Each resource shall have its own router module.

Example:

```text
api/

├── auth.py
├── patients.py
├── trials.py
├── matching.py
└── health.py
```

Routers shall remain focused on a single resource.

---

## Route Definition

Example:

```python
router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)
```

Every router shall define:

- Prefix
- Tags
- Response model
- Status codes

---

# Service Standards

Services contain business logic.

Services coordinate:

- Repository operations
- Validation
- External APIs
- AI models
- Background tasks

Services represent the application's business layer.

---

## Service Responsibilities

Services may:

- Execute business rules
- Coordinate repositories
- Call external APIs
- Invoke AI models
- Publish Celery tasks
- Manage transactions

Services shall not:

- Define HTTP routes
- Build HTTP responses
- Know FastAPI implementation details

---

## Service Design

Services should:

- Have one business responsibility.
- Be cohesive.
- Avoid duplicated logic.
- Be independently testable.

Business logic shall exist in exactly one location.

---

# Repository Standards

Repositories encapsulate persistence.

Repositories provide database access only.

Business logic shall never exist inside repositories.

---

## Repository Responsibilities

Repositories may:

- Query the database
- Insert records
- Update records
- Delete records

Repositories shall not:

- Validate business rules
- Invoke AI models
- Call external APIs
- Perform request validation

---

## Repository Organization

Example:

```text
repositories/

patient_repository.py

trial_repository.py

matching_repository.py
```

One repository should manage one aggregate.

---

# SQLAlchemy Model Standards

Models represent database tables.

Models are persistence objects.

Models shall not represent API contracts.

---

## Model Responsibilities

Models contain:

- Table mappings
- Relationships
- Constraints
- Database metadata

Models shall not contain:

- HTTP logic
- Request validation
- API serialization
- Business workflows

---

## Model Example

```python
class Patient(Base):

    __tablename__ = "patients"

    id = Column(UUID)

    first_name = Column(String)
```

Table names shall remain explicit.

---

## Relationships

Relationships shall be intentionally declared.

Examples:

```python
relationship()

ForeignKey()
```

Lazy loading should be preferred unless eager loading is justified.

---

# Pydantic Schema Standards

Pydantic models define API contracts.

Schemas separate API representation from persistence models.

SQLAlchemy models shall never be returned directly through the API.

---

## Schema Types

Separate schemas by purpose.

Examples:

```text
PatientCreate

PatientUpdate

PatientResponse

PatientSummary
```

Avoid generic names such as:

```text
PatientDTO
```

---

## Schema Design

Schemas should:

- Validate input
- Describe API contracts
- Contain only required fields
- Be immutable where practical

Business logic shall not exist inside schemas.

---

# Dependency Injection

FastAPI dependency injection shall be used consistently.

Dependencies include:

- Database sessions
- Current user
- Configuration
- Services

---

## Dependency Organization

Example:

```text
core/

dependencies.py
```

Shared dependencies shall be centralized.

---

## Dependency Rules

Dependencies shall:

- Be reusable
- Be independently testable
- Avoid hidden side effects
- Remain stateless where practical

Business logic shall not be implemented inside dependency providers.

---

---

# Async Programming Standards

FastAPI supports asynchronous request handling.

Async programming shall be used only when it provides measurable benefits.

Suitable use cases include:

- External HTTP requests
- Database drivers with async support
- File operations
- AI model APIs
- Network I/O

CPU-intensive operations shall not execute directly inside asynchronous request handlers.

---

## Async Function Definition

Asynchronous functions shall use:

```python
async def
```

Example:

```python
async def get_patient(patient_id: UUID):
    ...
```

Functions shall not be declared asynchronous unless asynchronous operations are performed.

---

## Blocking Operations

Blocking operations shall not execute inside asynchronous endpoints.

Examples include:

- Long-running AI inference
- Large file processing
- CPU-intensive preprocessing

Such work shall be delegated to background workers or Celery tasks.

---

# Celery Task Standards

Celery provides asynchronous background execution.

Tasks shall represent long-running or non-interactive operations.

Examples include:

- PDF extraction
- Embedding generation
- Trial ingestion
- Notification delivery
- Report generation

---

## Task Responsibilities

Celery tasks shall:

- Accept simple serializable inputs.
- Delegate business logic to services.
- Be retryable where appropriate.
- Produce deterministic outcomes.

Tasks shall not contain duplicated business logic.

---

## Task Organization

Example:

```text
tasks/

embedding_tasks.py

trial_tasks.py

notification_tasks.py
```

Tasks should be grouped by business capability.

---

## Retry Policy

Retry behavior shall be explicitly configured.

Transient failures may be retried.

Examples:

- Network failures
- Temporary database unavailability
- External API timeouts

Permanent business validation failures shall not be retried.

---

# Background Processing

Background processing should be used when immediate client responses are preferable.

Suitable examples include:

- Email delivery
- PDF parsing
- Embedding creation
- Cache warming

The API should return an appropriate acknowledgement when asynchronous processing begins.

---

# Validation Standards

Validation shall occur before business logic executes.

Validation includes:

- Request schema validation
- Business rule validation
- File validation
- Configuration validation

Validation failures shall produce standardized API error responses.

---

## Pydantic Validation

Validation shall primarily use Pydantic.

Examples:

```python
Field()

EmailStr()

Annotated

field_validator
```

Validation logic should remain declarative whenever possible.

---

## Business Validation

Business validation belongs in services.

Examples:

- Duplicate patient
- Duplicate trial
- Invalid hospital ownership
- Eligibility rule verification

Business validation shall not be embedded within routers.

---

# Exception Handling

Every service shall implement centralized exception handling.

Routers shall avoid repetitive try-except blocks.

---

## Global Exception Handlers

Global handlers shall convert exceptions into standardized API responses.

Responsibilities include:

- Mapping exceptions
- Logging failures
- Returning standard error structures

Implementation shall remain consistent with the API Guidelines.

---

## Exception Design

Exceptions should describe business failures.

Examples:

```text
PatientNotFoundException

TrialAlreadyExistsException

EmbeddingGenerationException

ExternalServiceException
```

Exception names shall clearly describe the failure.

---

# Logging Standards

Logging supports monitoring and production diagnostics.

Logging shall be structured and meaningful.

---

## Log Levels

Use log levels consistently.

| Level | Usage |
|--------|-------|
| DEBUG | Development diagnostics |
| INFO | Business events |
| WARNING | Recoverable issues |
| ERROR | Unexpected failures |
| CRITICAL | System failures |

Equivalent events shall always use equivalent log levels.

---

## Logging Rules

Logs should include:

- Request ID
- Task ID
- User ID
- Trial ID
- Patient ID
- Execution duration

Logs shall never contain:

- Passwords
- JWT tokens
- API keys
- Secrets
- Protected health information unless explicitly approved

---

# Configuration Management

Application configuration shall be externalized.

Configuration shall be loaded using centralized settings.

Example:

```python
BaseSettings
```

Configuration values shall not be hardcoded within business logic.

---

## Environment Variables

Configuration sources include:

- Environment variables
- .env (development only)
- Docker Compose
- Kubernetes ConfigMaps
- Kubernetes Secrets

Secrets shall always be externalized.

---

## Settings Organization

Application settings should remain centralized.

Example:

```text
core/

settings.py
```

Settings should be loaded once during application startup.

Configuration shall not be scattered throughout the codebase.

---

# Resource Management

Resources shall be properly managed throughout application execution.

Examples include:

- Database sessions
- Redis connections
- HTTP clients
- File handles

Resources shall be:

- Explicitly acquired.
- Explicitly released.
- Reused where appropriate.

Connection leaks are unacceptable.

---

---

# Testing Standards

Testing is an essential part of Python application development.

Every Python component shall be designed to be independently testable.

Testing verifies correctness, prevents regressions, and improves maintainability.

---

## Unit Testing

Unit tests validate individual modules in isolation.

Unit tests should:

- Test one unit of behavior.
- Be deterministic.
- Execute quickly.
- Avoid external dependencies.

External collaborators should be mocked where appropriate.

---

## Integration Testing

Integration tests verify interaction between multiple components.

Examples include:

- Repository tests
- API endpoint tests
- Database integration
- Redis integration
- Celery task execution

Integration tests should use production-like configurations whenever practical.

---

## Test Organization

Production and test modules should mirror each other.

Example:

```text
app/services/matching_service.py

tests/services/test_matching_service.py
```

This improves discoverability and maintainability.

---

## Test Naming

Test names should describe observable behavior.

Preferred format:

```text
test_<expected_behavior>_when_<condition>
```

Examples:

```text
test_create_patient_when_request_is_valid

test_return_not_found_when_trial_missing

test_generate_embeddings_when_pdf_uploaded
```

Test names should describe outcomes rather than implementation.

---

# Dependency Management

Dependencies shall be managed using a single dependency management strategy.

Approved options:

- pyproject.toml
- requirements.txt

Production dependency versions shall be pinned.

Unused dependencies shall be removed.

---

## Dependency Categories

Dependencies should be categorized as:

- Production
- Development
- Testing

Development-only dependencies shall not be required in production images.

---

## Dependency Updates

Dependency upgrades should:

- Use stable releases.
- Be reviewed.
- Be compatibility tested.
- Update documentation where required.

Breaking dependency upgrades shall be evaluated before adoption.

---

# Performance Guidelines

Performance optimizations shall preserve readability and correctness.

Optimization should be based on measurement rather than assumption.

---

## Database Performance

Database operations should:

- Minimize unnecessary queries.
- Avoid N+1 query problems.
- Retrieve only required columns.
- Use pagination.
- Prefer indexed lookups.

Repository implementations should avoid unnecessary database round trips.

---

## AI Model Performance

AI workloads should:

- Reuse loaded models.
- Avoid repeated initialization.
- Cache embeddings where appropriate.
- Batch operations when beneficial.

Large model initialization should occur during application startup rather than per request.

---

## Memory Management

Applications should avoid unnecessary memory consumption.

Examples include:

- Streaming large files
- Releasing temporary objects
- Avoiding duplicated datasets
- Processing data incrementally where practical

Memory usage should remain predictable under expected workloads.

---

# Security Practices

Security applies to every Python service.

Developers shall follow secure coding practices throughout implementation.

---

## Input Validation

Every external input shall be validated before processing.

Examples include:

- HTTP requests
- Uploaded files
- Environment variables
- External API responses
- Background task payloads

Invalid input shall fail before business processing.

---

## Sensitive Information

Sensitive information shall never be:

- Logged
- Returned in API responses
- Embedded in exceptions
- Hardcoded

Examples include:

- Passwords
- JWT tokens
- API keys
- Database credentials
- Encryption keys

---

## Secrets Management

Secrets shall be loaded from external configuration.

Examples:

- Environment variables
- Kubernetes Secrets
- Secret management systems

Secrets shall never be committed to source control.

---

# AI and LLM Practices

Python services implementing AI capabilities shall follow additional standards.

---

## Model Management

Models should:

- Be initialized once.
- Be reused.
- Be configurable.
- Support replacement without changing business logic.

Model loading shall remain independent of request processing.

---

## Prompt Management

Prompt templates shall:

- Be version controlled.
- Be reusable.
- Be centrally managed.
- Avoid duplication.

Prompt text shall not be scattered throughout business logic.

---

## Embedding Generation

Embedding services should:

- Batch requests where practical.
- Cache reusable embeddings.
- Handle model failures gracefully.
- Validate generated vectors before persistence.

Embedding generation shall remain isolated from repository implementations.

---

## External AI Services

External AI providers shall be accessed through service abstractions.

Business logic shall not depend directly upon vendor SDKs.

Provider-specific code shall remain isolated.

---

# Code Smells

The following indicators suggest refactoring should be considered.

Examples include:

- Large modules
- Long functions
- Deep nesting
- Duplicate logic
- Circular imports
- Excessive parameters
- Mixed responsibilities
- Global mutable state

Developers should address code smells before introducing new functionality whenever practical.

---

# Anti-Patterns

The following practices are prohibited.

---

## Business Logic in Routers

Routers shall coordinate requests only.

Business logic belongs in services.

---

## Business Logic in Repositories

Repositories shall provide persistence only.

Business rules belong in services.

---

## Blocking Operations in Async Endpoints

Long-running blocking operations shall not execute directly inside asynchronous request handlers.

Use background processing or Celery where appropriate.

---

## Global Mutable State

Global mutable variables introduce hidden coupling and unpredictable behavior.

Avoid mutable module-level state.

---

## Duplicate Prompt Definitions

Prompt templates shall exist in one location only.

Duplicate prompt definitions increase maintenance complexity.

---

## Configuration Scattering

Configuration loading shall remain centralized.

Application settings shall not be loaded independently throughout the application.

---

# Code Review Checklist

Before approving Python code, verify:

## Architecture

- [ ] Layer responsibilities respected.
- [ ] Package organization follows standards.
- [ ] Dependencies remain correct.

---

## Implementation

- [ ] Code is readable.
- [ ] Naming is meaningful.
- [ ] Business logic is centralized.
- [ ] No unnecessary complexity exists.

---

## Validation

- [ ] Input validation complete.
- [ ] Business validation complete.

---

## Persistence

- [ ] Repository responsibilities respected.
- [ ] Database interactions efficient.
- [ ] Schema migrations updated if required.

---

## AI Components

- [ ] Model loading efficient.
- [ ] Prompt templates centralized.
- [ ] Embedding generation follows standards.
- [ ] External AI providers isolated.

---

## Security

- [ ] Secrets externalized.
- [ ] Sensitive information protected.
- [ ] Authentication and authorization unaffected.

---

## Testing

- [ ] Unit tests updated.
- [ ] Integration tests updated.
- [ ] Existing tests continue to pass.

---

## Documentation

- [ ] API documentation updated if applicable.
- [ ] Architecture documentation updated if required.

---

# Related Documents

This guide complements:

- `docs/standards/repository-standards.md`
- `docs/standards/git-workflow.md`
- `docs/standards/commit-convention.md`
- `docs/standards/definition-of-done.md`
- `docs/standards/api-guidelines.md`
- `docs/standards/java-style-guide.md`

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial Python engineering standard. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All Python services within the MedMatch platform shall comply with the standards defined in this document unless superseded by a later approved revision.

---

**End of Document**