# Java Style Guide

---

# Document Information

| Field | Value |
|--------|-------|
| Document | Java Style Guide |
| Document ID | JAVA-STD-001 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | All Spring Boot Services |
| Classification | Engineering Standard |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document defines the engineering standards for developing Java applications within the MedMatch platform.

Its objective is to establish consistent architectural patterns, coding conventions, package organization, dependency management, and implementation practices across all Spring Boot services.

Following these standards improves readability, maintainability, testability, scalability, and long-term project consistency.

---

# Scope

These standards apply to every Java-based backend service within the repository.

Examples include:

- Authentication Service
- Notification Service
- Audit Service
- Future Java microservices

The standards apply to:

- Production code
- Test code
- Configuration
- Build configuration
- Shared libraries

Unless explicitly documented, all Java code shall comply with this guide.

---

# Design Philosophy

Java code within MedMatch shall prioritize:

- Readability
- Simplicity
- Consistency
- Testability
- Maintainability
- Security
- Explicitness
- Separation of concerns

Engineering decisions should favor long-term maintainability over short-term convenience.

---

# Project Structure

Every Java service shall follow the same high-level directory structure.

Example:

```text
auth-service/
│
├── src/
│   ├── main/
│   │   ├── java/
│   │   └── resources/
│   │
│   └── test/
│       ├── java/
│       └── resources/
│
├── target/
├── pom.xml
├── Dockerfile
└── README.md
```

Additional directories shall only be introduced when justified by project requirements.

---

# Package Organization

Packages shall be organized by feature rather than technical artifact whenever practical.

Example:

```text
com.medmatch.auth

├── auth
│   ├── controller
│   ├── dto
│   ├── mapper
│   ├── repository
│   ├── service
│   └── validation
│
├── hospital
│   ├── controller
│   ├── dto
│   ├── mapper
│   ├── repository
│   └── service
│
├── common
│
├── config
│
├── exception
│
├── security
│
└── util
```

Feature-oriented organization improves discoverability and reduces coupling between unrelated functionality.

---

# Package Responsibilities

Each package shall have a single responsibility.

| Package | Responsibility |
|----------|----------------|
| controller | HTTP endpoints |
| service | Business logic |
| repository | Data access |
| dto | Request and response models |
| entity | Persistence models |
| mapper | Object mapping |
| validation | Custom validation |
| config | Framework configuration |
| security | Authentication and authorization |
| exception | Exception hierarchy and handlers |
| util | Pure utility classes |

Responsibilities shall not overlap.

---

# Naming Conventions

Naming shall prioritize clarity over brevity.

The following conventions are mandatory.

| Element | Convention |
|----------|------------|
| Package | lowercase |
| Class | PascalCase |
| Interface | PascalCase |
| Method | camelCase |
| Variable | camelCase |
| Constant | UPPER_SNAKE_CASE |
| Enum | PascalCase |
| Enum Value | UPPER_SNAKE_CASE |

Names shall describe intent rather than implementation.

Avoid abbreviations unless universally understood.

---

# Class Design

Every class shall have one primary responsibility.

Classes should:

- Be cohesive.
- Be understandable.
- Avoid unrelated responsibilities.
- Minimize public surface area.

Large "God classes" are prohibited.

When a class becomes difficult to understand, it should be decomposed into smaller components.

---

# Dependency Injection

Dependency Injection shall be used for all service dependencies.

Constructor injection is the standard approach.

Example:

```java
@Service
public class PatientService {

    private final PatientRepository repository;

    public PatientService(PatientRepository repository) {
        this.repository = repository;
    }

}
```

Field injection shall not be used in production code.

Constructor injection:

- Improves immutability.
- Simplifies testing.
- Makes dependencies explicit.

---

# Configuration Management

Application configuration shall be externalized.

Configuration sources include:

- application.yml
- application-dev.yml
- application-prod.yml
- Environment variables
- Kubernetes ConfigMaps
- Kubernetes Secrets

Configuration values shall never be hardcoded within business logic.

Sensitive configuration shall always be externalized.

---

# Layer Responsibilities

The application shall follow a layered architecture.

```text
Controller

↓

Service

↓

Repository

↓

Database
```

Each layer has one responsibility.

Controllers shall not contain business logic.

Repositories shall not contain business rules.

Services coordinate business behavior.

Layer boundaries shall remain explicit.

---

# Coding Principles

Java implementations shall follow these principles:

- Single Responsibility Principle
- Dependency Inversion Principle
- Composition over inheritance
- Fail fast
- Explicit behavior
- Immutable data where practical
- Minimize side effects

Code should be easy to understand without requiring extensive comments.

---

# Related Documents

This guide complements:

- `docs/standards/repository-standards.md`
- `docs/standards/api-guidelines.md`
- `docs/standards/definition-of-done.md`

Implementation quality requirements are defined by the Definition of Done.

---


---

# Controller Standards

Controllers expose the HTTP API of the service.

Controllers are responsible only for:

- Receiving HTTP requests
- Validating request structure
- Calling the appropriate service
- Returning HTTP responses

Controllers shall not contain business logic.

Controllers shall remain thin.

---

## Controller Responsibilities

Controllers may:

- Accept request parameters
- Validate input
- Invoke services
- Convert HTTP responses
- Return status codes

Controllers shall not:

- Access repositories directly
- Perform business calculations
- Execute database queries
- Implement authorization logic
- Construct SQL queries

---

## REST Annotations

Controllers shall use Spring MVC annotations consistently.

Example:

```java
@RestController
@RequestMapping("/api/v1/patients")
@RequiredArgsConstructor
public class PatientController {
}
```

Every controller shall define a root resource path.

---

## Method Design

Each endpoint should implement one responsibility.

Good:

```java
@GetMapping("/{id}")

@PostMapping

@PutMapping("/{id}")

@DeleteMapping("/{id}")
```

Avoid multiple unrelated operations within a single endpoint.

---

# Service Standards

Services contain business logic.

Services coordinate:

- Validation
- Business rules
- Transactions
- Repository interaction
- External service communication

Services represent the core business layer.

---

## Service Responsibilities

Services may:

- Execute business rules
- Coordinate multiple repositories
- Invoke external APIs
- Publish events
- Execute transactions

Services shall not:

- Accept HTTP requests
- Build HTTP responses
- Access request objects
- Know about controller implementation

---

## Service Annotation

Every service shall be annotated.

Example:

```java
@Service
@RequiredArgsConstructor
public class PatientService {
}
```

---

## Service Design

Services should:

- Have one business responsibility.
- Be cohesive.
- Avoid duplicated logic.
- Prefer composition over inheritance.

Business rules shall exist in one location only.

---

# Repository Standards

Repositories encapsulate persistence.

Repositories provide data access abstractions.

Business logic shall never exist inside repositories.

---

## Repository Responsibilities

Repositories may:

- Execute queries
- Persist entities
- Delete entities
- Retrieve entities

Repositories shall not:

- Validate business rules
- Call external APIs
- Implement workflows

---

## Repository Definition

Example:

```java
@Repository
public interface PatientRepository
        extends JpaRepository<Patient, UUID> {
}
```

Repositories should extend the appropriate Spring Data interface whenever possible.

---

## Custom Queries

Custom queries shall only be introduced when derived queries are insufficient.

Prefer:

```java
findByEmail()

findByHospitalId()
```

before introducing custom JPQL or native SQL.

Native SQL should be limited to cases where JPQL cannot satisfy the requirement.

---

# Entity Standards

Entities represent persistence models.

Entities map directly to database tables.

Entities should not represent API contracts.

---

## Entity Responsibilities

Entities contain:

- Persistence mappings
- Relationships
- Database constraints

Entities shall not contain:

- Request validation
- HTTP concerns
- API documentation
- Presentation formatting

---

## Entity Annotation

Example:

```java
@Entity
@Table(name = "patients")
public class Patient {
}
```

Table names shall remain explicit.

---

## Identifier Strategy

Every entity shall define a primary key.

Example:

```java
@Id
@GeneratedValue
private UUID id;
```

Identifier generation strategy shall remain consistent within a service.

---

## Relationships

Relationships shall be explicit.

Examples:

```java
@OneToMany

@ManyToOne

@OneToOne

@ManyToMany
```

Fetch strategy shall be selected intentionally.

Lazy loading should be preferred unless eager loading is justified.

---

# DTO Standards

DTOs define API contracts.

DTOs separate external representations from persistence models.

Entities shall never be exposed directly through APIs.

---

## DTO Types

Separate DTOs by responsibility.

Examples:

```text
CreatePatientRequest

UpdatePatientRequest

PatientResponse

PatientSummaryResponse
```

Avoid generic DTO names.

---

## DTO Design

DTOs should:

- Be immutable where practical.
- Contain validation annotations.
- Expose only required fields.

DTOs shall not contain business logic.

---

# Mapper Standards

Mappers convert between:

- Entity → DTO
- DTO → Entity

Mapping logic shall remain centralized.

Controllers and services shall not duplicate mapping code.

---

## Mapper Organization

Example:

```java
PatientMapper

TrialMapper

HospitalMapper
```

Each mapper handles one aggregate.

---

## Mapping Rules

Mappings should be:

- Deterministic
- Readable
- Reusable
- Easy to test

Complex mapping logic should be encapsulated within mapper implementations rather than scattered throughout the application.

---

---

# Validation Standards

Validation ensures that incoming data satisfies structural and business requirements before processing.

Validation shall occur as early as possible in the request lifecycle.

---

## Bean Validation

DTOs shall use Jakarta Bean Validation annotations.

Example:

```java
public record CreatePatientRequest(

    @NotBlank
    String firstName,

    @NotBlank
    String lastName,

    @Email
    String email,

    @Min(18)
    Integer age

) {}
```

Validation annotations belong on request DTOs rather than entities whenever practical.

---

## Custom Validation

Business-specific validation shall use custom validators.

Examples:

- Trial eligibility rules
- Hospital code format
- Medical identifier validation

Custom validators shall be reusable and independently testable.

---

## Validation Responsibilities

Validation should verify:

- Required fields
- Length constraints
- Numeric ranges
- Date ranges
- Enum values
- Identifier format
- Business preconditions where appropriate

Validation shall fail before business logic executes.

---

# Exception Handling

Every service shall implement centralized exception handling.

Controllers shall not contain repetitive try-catch blocks.

---

## Global Exception Handler

Each service shall define one global exception handler.

Example:

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
}
```

The global handler is responsible for:

- Mapping exceptions
- Returning standardized API errors
- Logging unexpected failures

---

## Exception Hierarchy

Exceptions should follow a consistent hierarchy.

Example:

```text
ApplicationException
│
├── ValidationException
├── ResourceNotFoundException
├── ConflictException
├── UnauthorizedException
├── ForbiddenException
└── ExternalServiceException
```

Exceptions should describe business failures rather than implementation failures.

---

## Exception Messages

Exception messages shall:

- Be concise
- Be understandable
- Avoid framework terminology
- Avoid SQL errors
- Avoid stack traces

Messages returned to API clients shall follow the API Guidelines.

---

# Logging Standards

Logging supports monitoring, debugging, and incident investigation.

Logging shall be structured and meaningful.

---

## Logger Declaration

Every class requiring logging shall declare a single logger.

Example:

```java
private static final Logger log =
        LoggerFactory.getLogger(PatientService.class);
```

When Lombok is used:

```java
@Slf4j
```

is the preferred approach.

---

## Log Levels

Use log levels consistently.

| Level | Usage |
|--------|-------|
| TRACE | Detailed execution tracing |
| DEBUG | Development diagnostics |
| INFO | Normal business events |
| WARN | Recoverable issues |
| ERROR | Unexpected failures |

The same event shall always use the same log level.

---

## Logging Rules

Logs should include meaningful context.

Examples:

- Request ID
- User ID
- Resource ID
- Hospital ID
- Operation name

Logs shall never contain:

- Passwords
- JWT tokens
- Secrets
- API keys
- Personal health information unless explicitly approved

---

# Transaction Management

Transactions ensure database consistency.

Business transactions belong in the service layer.

---

## Transaction Boundaries

Transactions shall be declared at service methods.

Example:

```java
@Transactional
public PatientResponse createPatient(...) {
}
```

Repositories shall not define transaction boundaries.

---

## Read-Only Transactions

Read-only operations should declare:

```java
@Transactional(readOnly = true)
```

This improves intent and may improve performance depending on the persistence provider.

---

## Transaction Scope

Transactions should:

- Be as short as practical
- Avoid remote service calls
- Avoid unnecessary processing
- Minimize lock duration

Long-running transactions should be avoided.

---

# Configuration Classes

Configuration classes define framework behavior.

Configuration shall be isolated from business logic.

---

## Configuration Annotation

Configuration classes shall use:

```java
@Configuration
```

Configuration beans should be grouped by responsibility.

Examples:

- SecurityConfig
- OpenApiConfig
- JacksonConfig
- CacheConfig
- DatabaseConfig

Avoid large configuration classes with unrelated responsibilities.

---

# Utility Classes

Utility classes contain stateless helper functionality.

Utility classes shall:

- Contain only static methods
- Have no mutable state
- Be independent of Spring

Examples:

```text
DateUtils

StringUtils

FileUtils

ValidationUtils
```

Utility classes shall not contain business logic.

---

# Constants

Constants shall be declared only when values are reused or represent stable domain concepts.

Example:

```java
public final class ApiConstants {

    public static final int MAX_PAGE_SIZE = 100;

}
```

Avoid magic numbers and duplicated literal values.

---

# Enum Standards

Enums represent fixed domain values.

Example:

```java
public enum Role {

    ADMIN,

    DOCTOR,

    RESEARCHER,

    PATIENT

}
```

Enum values shall:

- Use UPPER_SNAKE_CASE
- Represent stable domain concepts
- Avoid presentation-specific formatting

Business logic inside enums should remain minimal.

---

---

# Testing Standards

Testing is an integral part of application development.

Every Java component shall be designed to be testable.

Testing verifies correctness, prevents regressions, and improves maintainability.

---

## Unit Testing

Unit tests validate individual classes in isolation.

Unit tests should:

- Test one unit of behavior.
- Be deterministic.
- Execute quickly.
- Avoid external dependencies.

Mocks should be used only for external collaborators.

---

## Integration Testing

Integration tests verify collaboration between multiple application components.

Examples include:

- Repository tests
- Service integration tests
- REST API tests
- Database integration

Integration tests should use production-like configurations whenever practical.

---

## Test Naming

Test method names should clearly describe the expected behavior.

Preferred format:

```text
should<Action>When<Condition>
```

Examples:

```text
shouldCreatePatientWhenRequestIsValid

shouldReturnNotFoundWhenPatientDoesNotExist

shouldRejectInvalidEmail
```

Test names should describe observable behavior rather than implementation details.

---

## Test Organization

Production and test packages should mirror each other.

Example:

```text
src/main/java/com/medmatch/auth/service/PatientService.java

src/test/java/com/medmatch/auth/service/PatientServiceTest.java
```

This improves discoverability and maintenance.

---

# Dependency Management

Dependencies shall be managed using Maven.

Dependencies should be:

- Explicit
- Current
- Well maintained
- Necessary

Unused dependencies shall be removed.

---

## Dependency Versioning

Application dependencies should use stable released versions.

Snapshot dependencies shall not be used in production unless explicitly approved.

Version upgrades should include compatibility testing.

---

## Dependency Scope

Use Maven scopes appropriately.

| Scope | Usage |
|--------|-------|
| compile | Production dependency |
| runtime | Runtime-only dependency |
| provided | Container-provided dependency |
| test | Test-only dependency |

Scopes shall accurately represent dependency usage.

---

# Performance Guidelines

Performance optimizations shall preserve readability and correctness.

Optimization should be driven by measurement rather than assumption.

---

## Database Access

Database interactions should:

- Minimize unnecessary queries.
- Avoid N+1 query problems.
- Retrieve only required data.
- Use pagination for collections.
- Prefer indexed lookups where applicable.

Repository methods should be designed with performance in mind.

---

## Object Allocation

Avoid unnecessary object creation in performance-sensitive code.

Reuse immutable objects where appropriate.

Premature optimization shall be avoided.

---

## Collections

Choose collection implementations intentionally.

Examples:

| Collection | Preferred Usage |
|------------|-----------------|
| List | Ordered collections |
| Set | Unique values |
| Map | Key-value lookup |
| Queue | Sequential processing |

The chosen collection should match the intended behavior.

---

# Security Practices

Security requirements apply to all Java code.

Developers shall follow secure coding principles throughout implementation.

---

## Input Validation

All external input shall be validated before use.

Sources include:

- HTTP requests
- File uploads
- Message queues
- Environment variables
- External APIs

Validation shall occur before business processing.

---

## Sensitive Information

Sensitive information shall never be:

- Logged
- Returned to clients
- Embedded in exceptions
- Hardcoded

Examples include:

- Passwords
- API keys
- JWT tokens
- Database credentials
- Encryption keys

---

## Secrets

Secrets shall be obtained from external configuration.

Examples:

- Environment variables
- Kubernetes Secrets
- Secret management systems

Secrets shall never be committed to source control.

---

# Code Smells

The following indicators suggest that refactoring should be considered.

Examples:

- Large classes
- Long methods
- Deep nesting
- Duplicate logic
- Excessive parameters
- Circular dependencies
- Feature envy
- Primitive obsession

Developers should address code smells before introducing new functionality whenever practical.

---

# Anti-Patterns

The following practices are prohibited.

## Business Logic in Controllers

Controllers shall coordinate requests only.

Business rules belong in services.

---

## Repository Business Logic

Repositories shall provide persistence only.

Business decisions belong in the service layer.

---

## Field Injection

Example:

```java
@Autowired
private PatientRepository repository;
```

Field injection shall not be used.

Constructor injection is mandatory.

---

## Static Mutable State

Static mutable state introduces hidden coupling and concurrency risks.

Avoid mutable global variables.

---

## Generic Exception Catching

Avoid:

```java
catch (Exception ex)
```

Catch the most specific exception appropriate to the context.

---

## Large Service Classes

Large services should be decomposed into smaller cohesive components.

A service should represent one business capability.

---

# Code Review Checklist

Before approving Java code, verify:

## Architecture

- [ ] Layer responsibilities are respected.
- [ ] Package organization follows standards.
- [ ] Dependencies remain correct.

---

## Implementation

- [ ] Code is readable.
- [ ] Naming is meaningful.
- [ ] No duplicated business logic.
- [ ] No unnecessary complexity.

---

## Validation

- [ ] Input validation complete.
- [ ] Business validation complete.

---

## Persistence

- [ ] Repository responsibilities respected.
- [ ] Transactions correctly defined.
- [ ] Flyway migration added if schema changed.

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

Additional implementation guidance is provided by:

- `docs/standards/python-style-guide.md`
- `docs/standards/frontend-style-guide.md`

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial Java engineering standard. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All Java services within the MedMatch platform shall comply with the standards defined in this document unless superseded by a later approved revision.

---

**End of Document**