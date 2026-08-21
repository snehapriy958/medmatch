# Database Schema Specification

---

# Document Information

| Field | Value |
|--------|-------|
| Document | Database Schema Specification |
| Document ID | DB-001 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | MedMatch Engineering Team |
| Applies To | PostgreSQL Database |
| Classification | Database Specification |
| Last Updated | YYYY-MM-DD |

---

# Purpose

This document defines the canonical database schema for the MedMatch platform.

It specifies the logical entities, relationships, ownership boundaries, naming conventions, and persistence rules used throughout the platform.

This document serves as the single source of truth for database design.

All schema evolution shall begin with updates to this document before implementation.

---

# Scope

This specification applies to all persistent relational data managed by the MedMatch platform.

It includes:

- Authentication
- Hospitals
- Users
- Patients
- Clinical Trials
- Trial Criteria
- AI Matching
- Audit Logging

Implementation-specific SQL definitions are maintained separately through Flyway migration scripts.

---

# Database Overview

The MedMatch platform stores transactional business data in PostgreSQL.

Semantic vector representations are stored using pgvector within PostgreSQL.

Redis is excluded from this specification because it is an infrastructure component rather than a persistent datastore.

The schema is organized around business domains.

Each domain owns its entities independently.

---

# Database Design Principles

The schema follows the principles below.

## Single Source of Truth

Every business entity shall have one authoritative representation.

Duplicate business data shall be avoided unless explicitly required for performance.

---

## Domain Ownership

Every table belongs to one business domain.

Only the owning service may modify the table.

Ownership determines:

- Repository ownership
- Migration ownership
- API ownership
- Validation ownership

---

## Stable Primary Keys

Primary keys shall never change.

Business identifiers shall remain independent from implementation details.

Relationships shall reference immutable identifiers.

---

## Normalization

Business entities shall be normalized.

Redundant data shall be avoided.

Derived values may be introduced only when justified by measurable operational requirements.

---

## Referential Integrity

Relationships shall be enforced through foreign keys.

Orphaned records shall not exist.

Database constraints shall preserve consistency independently of application code.

---

## Extensibility

The schema shall support future platform capabilities without redesigning existing entities.

Future modules should extend the schema through additive changes rather than incompatible modifications.

Examples include:

- Notifications
- Messaging
- Research Collaboration
- EHR Integration
- Mobile Applications
- Advanced Analytics

---

# Naming Standards

Database objects shall use snake_case.

Examples:

```text
users

patient_notes

trial_criteria

criteria_embeddings

audit_logs
```

---

## Column Naming

Columns shall describe business meaning.

Examples:

```text
created_at

updated_at

hospital_id

trial_id

patient_id

eligibility_status
```

Abbreviations shall be avoided unless universally understood.

---

## Constraint Naming

Constraint names shall remain descriptive.

Examples:

```text
pk_users

fk_patients_hospital

fk_trials_creator

idx_patient_email

uq_user_email
```

Constraint names shall remain stable across migrations.

---

# Primary Key Strategy

Every table shall contain one immutable primary key.

Primary keys shall:

- Never change
- Never encode business meaning
- Never depend on external systems

Foreign keys shall reference only primary keys.

Business identifiers may exist independently where appropriate.

---

# Common Audit Columns

Every business entity shall contain a consistent audit structure.

Standard audit columns include:

| Column | Description |
|----------|-------------|
| id | Primary key |
| created_at | Creation timestamp |
| updated_at | Last modification timestamp |
| created_by | Creator |
| updated_by | Last modifier |

Entities supporting logical deletion shall additionally include:

| Column | Description |
|----------|-------------|
| deleted_at | Soft deletion timestamp |
| deleted_by | User performing deletion |

Audit fields shall remain consistent across the platform.

---

---

# Entity Groups

The MedMatch database is organized into logical business domains.

Each domain owns a cohesive set of entities and is responsible for their lifecycle.

Current domains include:

| Domain | Primary Purpose |
|----------|----------------|
| Authentication | Identity and access management |
| Hospital | Tenant management |
| Patient | Patient information |
| Trial | Clinical trial management |
| AI Matching | Semantic search and eligibility evaluation |
| Audit | Platform auditing |

Future domains shall be introduced without modifying existing ownership boundaries.

Examples include:

- Notifications
- Messaging
- Reporting
- Analytics
- Integrations

---

# Authentication Domain

The Authentication Domain manages identity and platform access.

Entities:

- Users
- Roles
- Hospitals

Authentication entities are owned by the Authentication Service.

---

## Entity: Hospitals

### Purpose

Represents an organization participating in the MedMatch platform.

Hospitals are the tenant boundary for multi-tenant isolation.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | Hospital |
| Owner Service | Authentication Service |
| Mutable | Yes |
| Soft Delete | No |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| code | VARCHAR | Yes | Unique hospital code |
| name | VARCHAR | Yes | Hospital name |
| address | TEXT | No | Address |
| created_at | TIMESTAMP | Yes | Creation timestamp |
| updated_at | TIMESTAMP | Yes | Last modification timestamp |

---

### Relationships

Hospital

↓

Users

↓

Patients

↓

Trials

↓

Audit Logs

Every tenant-owned entity references one hospital.

---

### Constraints

- Primary key on id
- Unique code
- Name required

---

### Indexes

- Primary key
- Unique(code)
- Index(name)

---

### Lifecycle

```text
Created

↓

Active

↓

Updated
```

Hospitals are never physically deleted.

---

# Entity: Users

### Purpose

Represents authenticated platform users.

Users belong to one hospital and one role.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | Authentication |
| Owner Service | Authentication Service |
| Mutable | Yes |
| Soft Delete | Yes |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| hospital_id | UUID | Yes | Owning hospital |
| role_id | UUID | Yes | Assigned role |
| first_name | VARCHAR | Yes | First name |
| last_name | VARCHAR | Yes | Last name |
| email | VARCHAR | Yes | Login email |
| password_hash | VARCHAR | Yes | BCrypt password |
| is_active | BOOLEAN | Yes | Account status |
| last_login | TIMESTAMP | No | Last successful login |
| created_at | TIMESTAMP | Yes | Creation timestamp |
| updated_at | TIMESTAMP | Yes | Modification timestamp |
| deleted_at | TIMESTAMP | No | Soft deletion timestamp |

---

### Relationships

Hospital

↓

Users

↓

Audit Logs

---

### Constraints

- Primary key
- Foreign key to Hospitals
- Foreign key to Roles
- Unique email
- Email required

---

### Indexes

- Primary key
- Unique(email)
- Index(hospital_id)
- Index(role_id)

---

### Lifecycle

```text
Registered

↓

Active

↓

Suspended

↓

Soft Deleted
```

Soft deletion preserves audit history.

---

# Entity: Roles

### Purpose

Defines authorization roles used by RBAC.

Roles describe permissions but do not directly contain permission definitions.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | Authentication |
| Owner Service | Authentication Service |
| Mutable | Rarely |
| Soft Delete | No |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| name | VARCHAR | Yes | Role name |
| description | TEXT | No | Description |
| created_at | TIMESTAMP | Yes | Creation timestamp |

---

### Initial Roles

- System Administrator
- Hospital Administrator
- Clinical Research Coordinator
- Physician
- Patient
- Sponsor

Future roles may be added without modifying existing users.

---

### Relationships

Roles

↓

Users

---

### Constraints

- Primary key
- Unique role name

---

### Indexes

- Primary key
- Unique(name)

---

### Lifecycle

```text
Created

↓

Available

↓

Deprecated (future)

↓

Archived (future)
```

Roles shall not be physically deleted while referenced by users.

---

---

# Patient Domain

The Patient Domain manages patient information used throughout the MedMatch platform.

Entities:

- Patients
- Patient Notes

Future entities may include:

- Diagnoses
- Allergies
- Medications
- Laboratory Results
- Vital Signs
- Medical Documents
- FHIR Resources
- Encounter History

The Patient Domain is owned by the AI Service.

---

# Entity: Patients

### Purpose

Represents an individual patient within a hospital.

The Patients entity stores demographic and administrative information only.

Clinical observations, notes, and medical documents are stored separately.

This separation minimizes future schema changes while supporting healthcare interoperability standards.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | Patient |
| Owner Service | AI Service |
| Mutable | Yes |
| Soft Delete | Yes |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| hospital_id | UUID | Yes | Owning hospital |
| medical_record_number | VARCHAR | Yes | Hospital MRN |
| first_name | VARCHAR | Yes | First name |
| last_name | VARCHAR | Yes | Last name |
| date_of_birth | DATE | Yes | Date of birth |
| gender | VARCHAR | Yes | Administrative gender |
| phone | VARCHAR | No | Contact number |
| email | VARCHAR | No | Email address |
| created_at | TIMESTAMP | Yes | Creation timestamp |
| updated_at | TIMESTAMP | Yes | Last modification timestamp |
| created_by | UUID | Yes | Creator |
| updated_by | UUID | Yes | Last modifier |
| deleted_at | TIMESTAMP | No | Soft deletion timestamp |
| deleted_by | UUID | No | User performing deletion |

---

### Relationships

Hospital

↓

Patients

↓

Patient Notes

↓

Match Results

Future:

↓

Diagnoses

↓

Medications

↓

Laboratory Results

↓

Documents

---

### Constraints

- Primary key
- Foreign key → Hospitals
- Medical Record Number required
- Date of birth required
- Gender required

---

### Indexes

- Primary key
- Index(hospital_id)
- Unique(hospital_id, medical_record_number)
- Index(last_name)
- Index(date_of_birth)

---

### Lifecycle

```text
Registered

↓

Active

↓

Updated

↓

Inactive

↓

Soft Deleted
```

Patient records shall never be physically removed while referenced by business entities.

---

# Entity: Patient Notes

### Purpose

Stores clinical narratives used for AI-based trial matching.

Patient Notes contain the unstructured medical information that serves as input for semantic retrieval and LLM reasoning.

The patient entity intentionally does not contain clinical narrative data.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | Patient |
| Owner Service | AI Service |
| Mutable | Yes |
| Soft Delete | Yes |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| patient_id | UUID | Yes | Associated patient |
| hospital_id | UUID | Yes | Tenant |
| note | TEXT | Yes | Clinical note |
| note_type | VARCHAR | Yes | Progress, Admission, Discharge, etc. |
| authored_at | TIMESTAMP | Yes | Clinical timestamp |
| created_at | TIMESTAMP | Yes | Creation timestamp |
| updated_at | TIMESTAMP | Yes | Modification timestamp |
| created_by | UUID | Yes | Creator |
| updated_by | UUID | Yes | Last modifier |
| deleted_at | TIMESTAMP | No | Soft deletion timestamp |

---

### Relationships

Patients

↓

Patient Notes

↓

Embedding Generation

↓

Vector Search

↓

Matching

Each note may participate in multiple AI evaluations over time.

---

### Constraints

- Primary key
- Foreign key → Patients
- Foreign key → Hospitals
- Note required
- Note type required

---

### Indexes

- Primary key
- Index(patient_id)
- Index(hospital_id)
- Index(authored_at)
- Composite(patient_id, authored_at)

---

### Lifecycle

```text
Created

↓

Validated

↓

Available

↓

Updated

↓

Archived (future)

↓

Soft Deleted
```

Clinical notes remain immutable from a business perspective after use in completed matching workflows. Subsequent corrections should be represented through new notes or explicit revision mechanisms rather than destructive modification.

---

# Patient Domain Summary

| Entity | Purpose |
|----------|---------|
| Patients | Demographic and administrative patient information |
| Patient Notes | Unstructured clinical information used by AI |

Future entities shall extend the Patient Domain without modifying these foundational entities unless required by a documented architectural decision.

---

---

# Trial Domain

The Trial Domain manages all information related to clinical trials.

Entities:

- Trials
- Trial Criteria

Future entities may include:

- Trial Versions
- Trial Sites
- Sponsors
- Protocol Amendments
- Trial Documents
- Recruitment Status
- Trial Arms
- Outcomes
- Investigators

The Trial Domain is owned by the AI Service.

---

# Entity: Trials

### Purpose

Represents a clinical trial registered within the MedMatch platform.

The Trials entity stores administrative and study-level information.

Eligibility criteria, embeddings, and AI artifacts are intentionally stored separately.

This separation allows protocol revisions and AI processing to evolve independently.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | Trial |
| Owner Service | AI Service |
| Mutable | Yes |
| Soft Delete | Yes |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| hospital_id | UUID | Yes | Owning hospital |
| title | VARCHAR | Yes | Trial title |
| protocol_number | VARCHAR | Yes | Internal protocol identifier |
| clinical_trial_id | VARCHAR | No | External registry identifier |
| phase | VARCHAR | Yes | Trial phase |
| status | VARCHAR | Yes | Recruitment status |
| sponsor | VARCHAR | No | Sponsor organization |
| disease_area | VARCHAR | No | Primary disease area |
| summary | TEXT | No | Trial summary |
| source_document | VARCHAR | No | Original uploaded document |
| created_at | TIMESTAMP | Yes | Creation timestamp |
| updated_at | TIMESTAMP | Yes | Last modification timestamp |
| created_by | UUID | Yes | Creator |
| updated_by | UUID | Yes | Last modifier |
| deleted_at | TIMESTAMP | No | Soft deletion timestamp |
| deleted_by | UUID | No | User performing deletion |

---

### Relationships

Hospital

↓

Trials

↓

Trial Criteria

↓

Criteria Embeddings

↓

Match Results

Future

↓

Trial Versions

↓

Sponsors

↓

Sites

↓

Protocol Documents

---

### Constraints

- Primary key
- Foreign key → Hospitals
- Trial title required
- Phase required
- Status required
- Protocol number unique within hospital

---

### Indexes

- Primary key
- Index(hospital_id)
- Index(status)
- Index(phase)
- Index(disease_area)
- Unique(hospital_id, protocol_number)

---

### Lifecycle

```text
Draft

↓

Uploaded

↓

Processed

↓

Available

↓

Updated

↓

Completed

↓

Archived

↓

Soft Deleted
```

Business history shall be preserved through future version entities rather than destructive updates.

---

# Entity: Trial Criteria

### Purpose

Represents structured eligibility criteria extracted from a clinical trial.

Criteria are stored independently from the parent trial to support AI processing, semantic search, and future protocol versioning.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | Trial |
| Owner Service | AI Service |
| Mutable | Yes |
| Soft Delete | Yes |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| trial_id | UUID | Yes | Associated trial |
| hospital_id | UUID | Yes | Tenant |
| criteria_type | VARCHAR | Yes | Inclusion or Exclusion |
| criteria_text | TEXT | Yes | Structured eligibility criterion |
| sequence_number | INTEGER | Yes | Display order |
| extraction_version | VARCHAR | No | AI extraction version |
| created_at | TIMESTAMP | Yes | Creation timestamp |
| updated_at | TIMESTAMP | Yes | Last modification timestamp |
| created_by | UUID | Yes | Creator |
| updated_by | UUID | Yes | Last modifier |
| deleted_at | TIMESTAMP | No | Soft deletion timestamp |

---

### Relationships

Trial

↓

Trial Criteria

↓

Criteria Embeddings

↓

Vector Search

↓

Eligibility Matching

Each criterion may generate one or more embeddings during its lifetime.

---

### Constraints

- Primary key
- Foreign key → Trials
- Foreign key → Hospitals
- Criteria required
- Criteria type required

---

### Indexes

- Primary key
- Index(trial_id)
- Index(hospital_id)
- Index(criteria_type)
- Composite(trial_id, sequence_number)

---

### Lifecycle

```text
Extracted

↓

Validated

↓

Available

↓

Updated

↓

Embedding Generated

↓

Archived

↓

Soft Deleted
```

Criteria revisions should preserve historical versions through future protocol versioning rather than replacing existing records.

---

# Trial Domain Summary

| Entity | Purpose |
|----------|---------|
| Trials | Administrative information for a clinical study |
| Trial Criteria | Structured eligibility criteria extracted from trial documents |

Future capabilities shall extend this domain through additional entities rather than modifying these foundational entities unless required by an approved architectural decision.

---


---

# AI Domain

The AI Domain manages all AI-generated artifacts used during semantic retrieval and eligibility evaluation.

Entities:

- Criteria Embeddings
- Match Results

Future entities may include:

- Prompt Templates
- Prompt Versions
- Model Registry
- AI Evaluations
- Human Review
- Benchmark Results
- Feedback
- Model Performance

The AI Domain is owned by the AI Service.

---

# Entity: Criteria Embeddings

### Purpose

Represents the vector embedding generated from an individual trial eligibility criterion.

Embeddings are stored independently from business entities to support semantic retrieval without coupling embedding models to clinical data.

Embeddings are considered derived data and may be regenerated whenever embedding models improve.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | AI |
| Owner Service | AI Service |
| Mutable | Yes |
| Soft Delete | No |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| criteria_id | UUID | Yes | Associated trial criterion |
| embedding_model | VARCHAR | Yes | Embedding model identifier |
| model_version | VARCHAR | Yes | Embedding model version |
| embedding_dimension | INTEGER | Yes | Vector dimension |
| embedding | VECTOR | Yes | Vector representation |
| generated_at | TIMESTAMP | Yes | Generation timestamp |
| created_at | TIMESTAMP | Yes | Creation timestamp |

---

### Relationships

Trial Criteria

↓

Criteria Embeddings

↓

Vector Search

↓

Candidate Retrieval

Each trial criterion may have multiple embeddings over time to support model upgrades and experimentation.

---

### Constraints

- Primary key
- Foreign key → Trial Criteria
- Embedding required
- Model identifier required
- Model version required

---

### Indexes

- Primary key
- Index(criteria_id)
- Index(embedding_model)
- Index(model_version)
- Vector similarity index
- Composite(criteria_id, model_version)

---

### Lifecycle

```text
Generated

↓

Stored

↓

Indexed

↓

Retrieved

↓

Regenerated (Future Model)

↓

Archived (Future)
```

Embeddings are derived artifacts and may be regenerated without modifying the underlying clinical criterion.

---

# Entity: Match Results

### Purpose

Represents the outcome of an AI-assisted patient-to-trial eligibility evaluation.

Each record captures the evaluated patient, trial, AI decision, explanation, and processing metadata.

Historical match results are preserved to support auditing, explainability, and future model comparisons.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | AI |
| Owner Service | AI Service |
| Mutable | No (Business Record) |
| Soft Delete | No |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| patient_id | UUID | Yes | Evaluated patient |
| trial_id | UUID | Yes | Evaluated trial |
| hospital_id | UUID | Yes | Tenant |
| eligibility_status | VARCHAR | Yes | Eligible, Not Eligible, Possibly Eligible |
| confidence_score | DECIMAL | No | AI confidence score |
| explanation | TEXT | Yes | Human-readable explanation |
| supporting_criteria | JSONB | No | Criteria supporting the decision |
| missing_information | JSONB | No | Missing information identified during evaluation |
| llm_provider | VARCHAR | Yes | Language model provider |
| llm_model | VARCHAR | Yes | Language model name |
| model_version | VARCHAR | Yes | Model version |
| prompt_version | VARCHAR | Yes | Prompt template version |
| evaluated_at | TIMESTAMP | Yes | Evaluation timestamp |
| processing_time_ms | INTEGER | No | Processing duration |
| created_at | TIMESTAMP | Yes | Creation timestamp |

---

### Relationships

Patients

↓

Match Results

↑

Trials

Each patient may have many evaluations.

Each trial may be evaluated for many patients.

Historical evaluations remain immutable after creation.

---

### Constraints

- Primary key
- Foreign key → Patients
- Foreign key → Trials
- Foreign key → Hospitals
- Eligibility status required
- Explanation required
- LLM model required
- Prompt version required

---

### Indexes

- Primary key
- Index(patient_id)
- Index(trial_id)
- Index(hospital_id)
- Index(eligibility_status)
- Index(evaluated_at)
- Composite(patient_id, trial_id)
- Composite(hospital_id, evaluated_at)

---

### Lifecycle

```text
Created

↓

Validated

↓

Available

↓

Referenced

↓

Archived (Future)
```

Match results are immutable business records.

Future evaluations create new records rather than modifying historical evaluations.

---

# AI Domain Summary

| Entity | Purpose |
|----------|---------|
| Criteria Embeddings | Semantic vector representations of trial eligibility criteria |
| Match Results | Immutable AI-assisted patient-trial eligibility evaluations |

The AI Domain stores only AI-generated artifacts.

Clinical business data remains within the Patient and Trial domains.

Future AI capabilities shall extend this domain through additional entities rather than modifying existing business entities.

---

---

# Audit Domain

The Audit Domain records security-sensitive and business-critical activities performed within the MedMatch platform.

Entities:

- Audit Logs

Future entities may include:

- Login History
- Security Events
- Data Access Logs
- API Request Logs
- System Events
- Compliance Reports

The Audit Domain is owned by the Authentication Service.

---

# Entity: Audit Logs

### Purpose

Records significant business and security events occurring within the platform.

Audit logs provide traceability, accountability, operational monitoring, and regulatory support.

Audit records are immutable.

---

### Ownership

| Property | Value |
|----------|-------|
| Domain | Audit |
| Owner Service | Authentication Service |
| Mutable | No |
| Soft Delete | No |

---

### Columns

| Column | Type | Required | Description |
|----------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| hospital_id | UUID | No | Tenant associated with the event |
| user_id | UUID | No | User performing the action |
| entity_type | VARCHAR | Yes | Business entity affected |
| entity_id | UUID | No | Identifier of affected entity |
| action | VARCHAR | Yes | Business action performed |
| event_type | VARCHAR | Yes | Authentication, Authorization, Business, System |
| ip_address | VARCHAR | No | Client IP address |
| user_agent | TEXT | No | Client user agent |
| correlation_id | UUID | Yes | Request correlation identifier |
| metadata | JSONB | No | Additional event information |
| occurred_at | TIMESTAMP | Yes | Event timestamp |
| created_at | TIMESTAMP | Yes | Record creation timestamp |

---

### Relationships

Users

↓

Audit Logs

Hospital

↓

Audit Logs

Every business entity may generate audit records.

Audit logs never become the owner of business entities.

---

### Constraints

- Primary key
- Foreign key → Users (nullable)
- Foreign key → Hospitals (nullable)
- Action required
- Event type required
- Correlation ID required

---

### Indexes

- Primary key
- Index(user_id)
- Index(hospital_id)
- Index(entity_type)
- Index(entity_id)
- Index(action)
- Index(event_type)
- Index(occurred_at)
- Composite(entity_type, entity_id)
- Composite(hospital_id, occurred_at)

---

### Lifecycle

```text
Generated

↓

Stored

↓

Queried

↓

Archived (Future)
```

Audit records shall never be modified or deleted.

---

# Audit Domain Summary

| Entity | Purpose |
|----------|---------|
| Audit Logs | Immutable record of business and security events |

Future audit capabilities shall extend this domain through new entities rather than altering existing audit records.

---

# Relationship Summary

The logical relationships between primary entities are shown below.

```text
Hospital
│
├───────────────┐
│               │
▼               ▼
Users        Patients
│               │
│               ▼
│        Patient Notes
│               │
│               ▼
│         Match Results
│            ▲     ▲
│            │     │
▼            │     │
Audit Logs   │     │
             │     │
Trials────────┘     │
│                   │
▼                   │
Trial Criteria      │
│                   │
▼                   │
Criteria Embeddings─┘
```

Business entities shall communicate through foreign key relationships rather than duplicated information.

---

# Global Constraints

The following constraints apply throughout the database.

## Entity Integrity

Every entity shall have:

- One immutable primary key
- Defined ownership
- Referential integrity
- Audit fields

---

## Foreign Keys

Foreign keys shall enforce:

- Parent-child relationships
- Tenant consistency
- Business integrity

Orphaned records shall not exist.

---

## Uniqueness

Unique constraints shall protect business identifiers.

Examples include:

- Hospital Code
- User Email
- Hospital + Medical Record Number
- Hospital + Protocol Number

---

# Global Index Strategy

Indexes shall support the application's primary access patterns.

Categories include:

- Primary keys
- Foreign keys
- Business identifiers
- Search fields
- Tenant filtering
- Date filtering
- Vector similarity

Indexes shall be reviewed as application usage evolves.

---

# Soft Delete Strategy

Soft deletion preserves historical integrity.

The following entities support soft deletion:

- Users
- Patients
- Patient Notes
- Trials
- Trial Criteria

The following entities do not support soft deletion:

- Hospitals
- Roles
- Criteria Embeddings
- Match Results
- Audit Logs

Historical AI evaluations and audit records remain permanently available.

---

# Versioning Strategy

Schema evolution shall be additive whenever practical.

Preferred changes include:

- New tables
- New nullable columns
- New indexes
- New constraints
- New relationships

Breaking schema changes shall require:

- Architectural review
- Migration planning
- Backward compatibility assessment
- Updated documentation

---

# Future Expansion Strategy

The current schema is intentionally designed to support future growth.

Potential future domains include:

- Notifications
- Messaging
- Reporting
- Analytics
- Sponsors
- Trial Sites
- Trial Versions
- Medical Documents
- Laboratory Results
- Diagnoses
- Medications
- FHIR Resources
- External Integrations
- Human AI Review
- AI Benchmarking

New capabilities should extend the schema by introducing new entities rather than modifying established business entities whenever practical.

---

# Related Documents

This specification complements:

- `docs/architecture/database-architecture.md`
- `docs/architecture/backend-architecture.md`
- `docs/architecture/ai-architecture.md`

Implementation artifacts include:

- Flyway migration scripts
- JPA entities
- SQLAlchemy models
- Repository implementations

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0 | YYYY-MM-DD | Initial database schema specification. |

---

# Approval

This document becomes effective immediately upon approval by the engineering team.

All database entities, relationships, migrations, and schema evolution within the MedMatch platform shall conform to this specification unless superseded by a later approved revision.

---

**End of Document**