# Database Architecture

---

# Document Information

| Field | Value |
|--------|-------|
| Document | Database Architecture |
| Document ID | ARCH-004 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | Database Layer |
| Classification | Architecture |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document defines the architectural design of the MedMatch data layer.

It describes how application data is organized, how ownership is established, how schemas are structured, and how persistence supports the platform's functional and non-functional requirements.

The objective is to provide a consistent database architecture that supports correctness, scalability, maintainability, security, and future growth.

---

# Scope

This document applies to every persistent data store used by the MedMatch platform.

It covers:

- Relational data
- Vector data
- Schema organization
- Entity ownership
- Transactions
- Migrations
- Indexing
- Data lifecycle

Implementation details such as SQL statements, ORM mappings, and migration scripts are documented separately.

---

# Database Overview

The MedMatch platform uses PostgreSQL as its primary relational database.

The database serves as the authoritative source of business data for the platform.

Vector similarity search capabilities are provided through the pgvector extension.

Redis is used exclusively for caching and asynchronous messaging and is not considered part of the persistent data layer.

The database architecture prioritizes:

- Data integrity
- Referential consistency
- Multi-tenancy
- Performance
- Scalability
- Operational simplicity

---

# Architectural Goals

The database architecture is designed to achieve the following goals.

- Maintain a single source of truth.
- Preserve transactional consistency.
- Support multi-tenant isolation.
- Enable efficient analytical queries.
- Support semantic search.
- Allow independent schema evolution.
- Minimize redundant data.
- Simplify operational maintenance.

Architectural decisions shall prioritize long-term maintainability over short-term implementation convenience.

---

# Database Technologies

The platform uses the following technologies.

| Component | Technology |
|------------|------------|
| Relational Database | PostgreSQL |
| Vector Database | pgvector |
| Cache | Redis |
| Migration Tool | Flyway (Spring Boot) |
| ORM (Java) | Spring Data JPA / Hibernate |
| ORM (Python) | SQLAlchemy |

Each technology has a clearly defined responsibility within the persistence architecture.

---

# Database Topology

The platform currently uses a shared PostgreSQL database.

Application services access the same database while maintaining strict ownership of their respective domains.

High-level topology:

```text
Authentication Service

        │

        ▼

      PostgreSQL

        ▲

        │

      AI Service

        │

        ▼

      pgvector
```

Redis operates independently as an infrastructure component.

The topology may evolve into physically separated databases in future versions without changing service responsibilities.

---

# Schema Organization

Application data is organized into logical domains.

Examples include:

- Authentication
- Hospitals
- Patients
- Trials
- Trial Criteria
- Embeddings
- Matching
- Audit Logs

Schemas shall remain cohesive.

Business domains shall not share unrelated tables.

Future domain separation shall preserve logical ownership.

---

# Domain Ownership

Every persistent entity belongs to one business domain.

Examples include:

| Domain | Example Entities |
|---------|------------------|
| Authentication | Users, Roles |
| Hospital | Hospitals |
| Patient | Patients |
| Trial | Trials, Trial Criteria |
| Matching | Eligibility Results |
| Audit | Audit Logs |

Ownership determines:

- Schema evolution
- Business validation
- Repository ownership
- API ownership

No domain shall modify another domain's entities outside documented interfaces.

---

---

# Entity Relationships

The MedMatch data model is organized around business domains rather than individual application features.

Relationships between entities shall reflect real-world business relationships while maintaining normalization and referential integrity.

A simplified conceptual model is shown below.

```text
Hospital
    │
    ├────────────┐
    │            │
    ▼            ▼
 User        Patient
                  │
                  │
                  ▼
            Patient Notes
                  │
                  ▼
              Matching
                  │
                  ▼
         Trial Criteria
                  │
                  ▼
               Trial
                  │
                  ▼
          Criteria Embedding
```

Foreign key relationships shall enforce consistency between related entities.

Circular dependencies shall be avoided.

---

# Multi-Tenancy Strategy

MedMatch implements logical multi-tenancy.

Each hospital represents one tenant.

All tenant-owned business data shall be associated with a hospital.

Examples include:

- Users
- Patients
- Trials
- Matching Results
- Audit Logs

Platform-wide reference data may exist outside tenant ownership where appropriate.

---

## Tenant Isolation

Tenant isolation shall be enforced through:

- Authentication
- Authorization
- Repository filtering
- Database queries
- Cache isolation
- API responses

No request shall access another tenant's resources without explicit authorization.

---

## Shared Reference Data

Some reference data may be globally shared.

Examples include:

- Trial phases
- Medical specialties
- Countries
- Standard classifications

Shared reference data shall remain read-only for tenant users.

---

# Transaction Model

Transactions ensure database consistency during business operations.

Business transactions belong to the service layer.

Every transaction shall represent one complete business operation.

Examples include:

- Create Patient
- Upload Trial
- Register User
- Record Match Result

Partial business operations shall not be committed.

---

## Transaction Scope

Transactions should:

- Be short-lived.
- Minimize lock duration.
- Avoid external service calls.
- Remain deterministic.

Long-running AI workflows shall execute outside transactional boundaries.

---

## Consistency Model

The platform uses strong consistency for relational business data.

Background processing may introduce eventual consistency for:

- Embedding generation
- AI matching
- Report generation
- Cache population

Eventual consistency shall never compromise transactional correctness.

---

# Indexing Strategy

Indexes improve query performance.

Indexes shall be designed according to application access patterns.

Common index candidates include:

- Primary keys
- Foreign keys
- Hospital identifiers
- User email
- Trial status
- Matching status
- Created timestamps

Indexes shall be periodically reviewed as query patterns evolve.

---

## Composite Indexes

Composite indexes may be introduced where queries frequently filter on multiple columns.

Examples include:

- Hospital + Status
- Hospital + Created Date
- Trial + Version

Composite indexes shall be justified by measured query performance.

---

## Vector Indexes

Embedding vectors shall use vector indexes appropriate for similarity search.

Vector indexes shall support:

- Top-K retrieval
- Cosine similarity
- Efficient nearest-neighbor search

Vector indexing strategy shall remain configurable as dataset size grows.

---

# Vector Storage Architecture

Semantic search is implemented using pgvector.

Embeddings are stored independently from transactional business entities.

Conceptual organization:

```text
Trial

↓

Trial Criteria

↓

Embedding

↓

Vector Search

↓

Candidate Selection

↓

LLM Evaluation
```

This separation allows embeddings to be regenerated without modifying business records.

---

## Embedding Ownership

Embeddings belong to the AI domain.

Business services interact with embeddings only through documented APIs.

Embedding generation shall not be tightly coupled to relational persistence.

---

## Embedding Lifecycle

Embedding records follow this lifecycle:

```text
Criteria Created

↓

Embedding Generated

↓

Stored

↓

Indexed

↓

Queried

↓

Updated (if criteria changes)
```

Embedding regeneration shall preserve consistency between business data and vector representations.

---

# Migration Strategy

Database schema evolution shall be managed through version-controlled migrations.

Manual schema changes in shared environments are prohibited.

Every schema modification shall:

- Be versioned.
- Be repeatable.
- Be auditable.
- Be reversible where practical.

---

## Migration Ownership

Each service owns migrations for its business domain.

Responsibilities include:

- Creating migrations
- Reviewing migrations
- Testing migrations
- Maintaining compatibility

Schema ownership follows domain ownership.

---

## Backward Compatibility

Schema evolution should remain backward compatible whenever practical.

Breaking schema changes shall be planned, documented, and coordinated across affected services.

---

---

# Backup and Recovery

Business data is a critical platform asset.

The database architecture shall support reliable backup and recovery procedures to minimize data loss and downtime.

Backup and recovery processes shall be documented, tested, and automated where practical.

---

## Backup Strategy

The platform shall maintain regular backups of persistent data.

Backup types may include:

- Full backups
- Incremental backups
- Transaction log backups

Backup frequency shall be determined according to operational requirements and recovery objectives.

---

## Recovery Objectives

Recovery planning shall define:

- Recovery Point Objective (RPO)
- Recovery Time Objective (RTO)

Recovery procedures shall support restoration of:

- Entire databases
- Individual schemas
- Individual tables
- Point-in-time recovery where supported

Recovery procedures shall be periodically validated.

---

## Backup Verification

Backups shall be verified regularly.

Verification includes:

- Successful backup completion
- Restoration testing
- Data integrity validation

An unverified backup shall not be considered a valid recovery mechanism.

---

# Data Lifecycle

Business data progresses through defined lifecycle stages.

Lifecycle management improves maintainability and operational efficiency.

---

## Lifecycle Stages

Typical lifecycle:

```text
Created

↓

Validated

↓

Active

↓

Updated

↓

Archived

↓

Deleted (where permitted)
```

Each business entity shall define its expected lifecycle.

---

## Soft Deletion

Business entities should use soft deletion where historical records are required.

Examples include:

- Patients
- Trials
- Users

Soft-deleted records shall remain excluded from normal business operations.

---

## Archival

Historical records may be archived according to operational requirements.

Examples include:

- Audit logs
- Historical reports
- Completed trials
- Old matching results

Archival shall preserve historical integrity while improving operational performance.

---

## Data Retention

Data retention policies shall be defined according to business and regulatory requirements.

Retention policies should specify:

- Retention duration
- Archival strategy
- Deletion policy
- Recovery requirements

Retention decisions shall remain independent of application implementation.

---

# Security Considerations

The database architecture incorporates multiple security controls.

Security applies to both relational and vector data.

---

## Access Control

Database access shall follow the principle of least privilege.

Application services shall receive only the permissions required for their responsibilities.

Administrative access shall be restricted and auditable.

---

## Credential Management

Database credentials shall:

- Be externally managed.
- Never be committed to source control.
- Be rotated according to operational policy.
- Be unique for each deployment environment.

Credential management shall remain independent of application code.

---

## Data Protection

Sensitive business information shall be protected through appropriate database controls.

Examples include:

- Access restrictions
- Encryption in transit
- Audit logging
- Authentication
- Authorization

Security controls shall apply consistently across all database interactions.

---

## Auditability

Critical database operations shall support auditing.

Examples include:

- User creation
- Role assignment
- Trial modification
- Patient updates
- Administrative actions

Audit records shall remain immutable once created.

---

# Scalability Strategy

The database architecture shall support future platform growth.

Scalability shall be achieved while preserving data integrity.

---

## Vertical Scaling

The platform shall support increasing database resources.

Examples include:

- CPU
- Memory
- Storage
- I/O capacity

Vertical scaling provides an immediate capacity increase without application changes.

---

## Horizontal Scaling

Future architecture may introduce:

- Read replicas
- Analytical replicas
- Geographic replicas
- Database partitioning

Horizontal scaling shall remain transparent to application business logic whenever practical.

---

## Partitioning

Large datasets may be partitioned using business-appropriate strategies.

Examples include:

- Hospital
- Date
- Trial status

Partitioning decisions shall be based on measured operational requirements.

---

## Vector Scaling

As embedding volume increases, vector indexing strategies may evolve.

Potential future improvements include:

- Approximate nearest-neighbor indexing
- Dedicated vector infrastructure
- Distributed vector search

Business services shall remain independent of vector storage implementation details.

---

# Architectural Principles

The database architecture follows these principles.

---

## Single Source of Truth

Relational data stored in PostgreSQL represents the authoritative business record.

Cached and derived data shall never replace transactional business data.

---

## Domain Ownership

Every entity belongs to one business domain.

Ownership determines:

- Schema evolution
- Validation
- Repository ownership
- API ownership

---

## Data Integrity

Referential integrity shall be preserved through:

- Constraints
- Transactions
- Controlled schema evolution

Data integrity shall not depend upon frontend validation.

---

## Separation of Concerns

Business rules belong in application services.

Persistence responsibilities belong in the database layer.

Database implementation shall remain independent of application presentation.

---

## Operational Simplicity

Database operations should remain:

- Predictable
- Observable
- Repeatable
- Automated where practical

Operational procedures shall be documented and standardized.

---

## Future Compatibility

The architecture shall support future capabilities without requiring significant redesign.

Examples include:

- Multi-region deployment
- Additional AI services
- Data warehouse integration
- Advanced analytics
- External healthcare integrations

Architectural evolution shall preserve existing business ownership boundaries.

---

# Related Documents

This document complements:

- `docs/architecture/system-overview.md`
- `docs/architecture/backend-architecture.md`
- `docs/architecture/frontend-architecture.md`
- `docs/architecture/ai-architecture.md`

Implementation standards are defined in:

- `docs/standards/java-style-guide.md`
- `docs/standards/python-style-guide.md`

Database schema definitions are documented in:

- `docs/database/schema.md`

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial database architecture document. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All database design, schema evolution, migration planning, and persistence strategies within the MedMatch platform shall conform to the architectural principles and constraints defined in this document unless superseded by a later approved revision.

---

**End of Document**