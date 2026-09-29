# Phase 13.2 — Database & Schema Ownership Specification

**Document Status:** Complete (Corrected Audit Baseline)  
**Execution Phase:** Phase 13.2  
**Implementation Status:** Not Started (Audit Gate Active)  
**Checkpoint:** `0d64976`  
**Branch:** `capstone/phase-13-production-engineering`  

---

## 1. Physical Architecture

MedMatch deploys a single PostgreSQL 17 database instance with `pgvector` extension enabled:
- **Database Name:** `medmatch`
- **Default Schema:** `public`
- **Host Port:** `5434:5432` (Docker Compose) / `5432` (Kubernetes Service: `postgres-service.medmatch.svc.cluster.local`)
- **Shared Access:** Both `auth-service` (Spring Boot) and `ai-service` (FastAPI) connect to this identical database and schema.

---

## 2. Table-by-Table Ownership Matrix

To establish precise engineering boundaries, three distinct dimensions of ownership are documented below:
1. **Table Domain Ownership:** Which business service functionally owns the data entities.
2. **DDL / Migration Ownership:** Which migration framework and service manages table creation and schema modifications.
3. **Runtime Access:** Which services read or write to the table during normal operation.

| Table Name | Domain Owner | DDL / Migration Owner | Runtime Read Access | Runtime Write Access | Key Columns & Types | External Foreign Keys |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `roles` | `auth-service` | `auth-service` (Flyway `V1`) | `auth-service` | `auth-service` | `id` (UUID PK), `name` (VARCHAR 255), `created_at` (TIMESTAMP) | None |
| `hospitals` | `auth-service` | `auth-service` (Flyway `V2`) | `auth-service`, `ai-service` | `auth-service` | `id` (UUID PK), `code` (VARCHAR 255 UNIQUE), `name`, `address`, `active`, `created_at`, `updated_at` | Referenced by `users`, `patients`, `trials`, `matches` |
| `users` | `auth-service` | `auth-service` (Flyway `V3`) | `auth-service` | `auth-service` | `id` (UUID PK), `email` (VARCHAR 255 UNIQUE), `password`, `first_name`, `last_name`, `role_id` (FK), `hospital_id` (FK), `status` | `role_id -> roles.id`<br>`hospital_id -> hospitals.id` |
| `audit_logs` | `auth-service` | `auth-service` (Flyway `V4`)* | `auth-service`, `ai-service` | `auth-service`, `ai-service` | `id` (UUID PK), `performed_by_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `details`, `created_at`, `performed_by_username`, `performed_by_role`, `hospital_id`, `hospital_name` | None (Loose coupling by design) |
| `patients` | `ai-service` | `ai-service` (Alembic `0001`)| `ai-service` | `ai-service` | `id` (UUID PK), `mrn` (VARCHAR 50), `first_name`, `last_name`, `diagnosis`, `cancer_type`, `stage`, `hospital_id` (FK) | `hospital_id -> hospitals.id` (RESTRICT) |
| `trials` | `ai-service` | `ai-service` (Alembic `0002`)| `ai-service` | `ai-service` | `id` (UUID PK), `title` (VARCHAR 500), `brief_summary`, `condition`, `phase`, `status`, `hospital_id` (FK) | `hospital_id -> hospitals.id` (RESTRICT) |
| `patient_notes` | `ai-service` | `ai-service` (Alembic `0003`)| `ai-service` | `ai-service` | `id` (UUID PK), `patient_id` (FK), `note_text` (TEXT), `created_at`, `updated_at` | `patient_id -> patients.id` (CASCADE) |
| `trial_criteria`| `ai-service` | `ai-service` (Alembic `0004`)| `ai-service` | `ai-service` | `id` (UUID PK), `trial_id` (FK), `criteria_type` (VARCHAR 50), `description` (TEXT) | `trial_id -> trials.id` (CASCADE) |
| `criteria_embeddings` | `ai-service` | `ai-service` (Alembic `0005`)| `ai-service` | `ai-service` | `id` (UUID PK), `criteria_id` (FK), `embedding` (Vector 384), `model_name` | `criteria_id -> trial_criteria.id` (CASCADE) |
| `patient_note_embeddings` | `ai-service` | `ai-service` (Alembic `0006`)| `ai-service` | `ai-service` | `id` (UUID PK), `patient_note_id` (FK), `embedding` (Vector 384), `model_name` | `patient_note_id -> patient_notes.id` (CASCADE) |
| `trial_embeddings` | `ai-service` | `ai-service` (Alembic `0007`)| `ai-service` | `ai-service` | `id` (UUID PK), `trial_id` (FK), `embedding` (Vector 384), `model_name` | `trial_id -> trials.id` (CASCADE) |
| `matches` | `ai-service` | `ai-service` (Alembic `0008`)| `ai-service` | `ai-service` | `id` (UUID PK), `patient_id` (FK), `trial_id` (FK), `hospital_id` (FK), `confidence`, `overall_status`, `matched_criteria` (JSONB) | `patient_id -> patients.id`<br>`trial_id -> trials.id`<br>`hospital_id -> hospitals.id` |
| `flyway_schema_history` | `auth-service` | Flyway | Flyway CLI / Spring Boot | Flyway CLI / Spring Boot | Flyway metadata table | None |
| `alembic_version` | `ai-service` | Alembic | Alembic CLI | Alembic CLI | Alembic metadata table | None |

*\* DDL is owned strictly by `auth-service` (Lineage B `V4__create_audit_logs_table.sql`). Runtime writes are issued by both services.*

---

## 3. Shared Runtime Access vs. Migration Ownership

### 3.1 Shared Runtime Access is an Architecture Pattern (Not a Migration Defect)

- **`hospitals` Table (Read-Only in AI Service):**
  The AI service maps `hospitals` via `app/models/hospital.py` for read-only lookups (e.g. validating tenant hospital presence and displaying hospital names). The AI service does not mutate this table.
- **`audit_logs` Table (Shared Dual-Write):**
  The table schema contains 12 columns. Spring Boot maps 8 columns; FastAPI maps all 12 columns (populating actor details from JWT claims). Both services write audit records directly to this shared table.
- **Audit Clarification:** Shared runtime read/write access is an application-level architectural pattern. It is **not in itself a database migration defect**.

### 3.2 The Historical DDL Migration Defect

The actual migration defect occurred in untracked local Alembic revision `01efd2b23442_schema_validation.py`:
- When Alembic was run with `--autogenerate`, it generated DDL statements (`op.add_column`, `op.create_index`) modifying `audit_logs` and `hospitals`.
- This was an uncoordinated cross-service DDL mutation.
- The team subsequently added `AUTH_SERVICE_OWNED_TABLES = {"roles", "hospitals", "users", "audit_logs"}` to `services/ai-service/alembic/env.py` to prevent future autogenerated alterations.
- In Git-tracked state at `0d64976`, revision `01efd2b23442` is untracked/uncommitted, but merge head `6f0604b23df6` references its child `3f3884863f27`.

---

## 4. Foreign Key Boundaries & Coupling

The AI service entities enforce physical foreign keys to `auth-service`'s `hospitals` table:
1. `patients.hospital_id -> hospitals.id` (`ondelete="RESTRICT"`)
2. `trials.hospital_id -> hospitals.id` (`ondelete="RESTRICT"`)
3. `matches.hospital_id -> hospitals.id` (`ondelete="RESTRICT"`)

### Operational Consequences:
- **Startup Ordering Dependency:** Alembic migrations `0001`, `0002`, and `0008` require `hospitals` table to exist in the database before they can run.
- **Deletion Protection:** Auth service cannot delete a hospital entity if active patients, trials, or match records reference it.

---

## 5. Schema Partitioning Architecture Assessment

| Strategy | Architecture Description | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Option 1: Status Quo (Single DB, `public` schema)** | Both services share `medmatch.public`. | Simple connection strings; native FK constraints. | Dual migration engines in same schema; race conditions during rollout. | **Unacceptable for Production** |
| **Option 2: Schema Isolation (`auth` & `clinical` schemas)** | Single DB `medmatch`, partitioned into PostgreSQL schemas `auth` (Flyway) and `clinical` (Alembic). | Strong DDL isolation; independent metadata tables; cross-schema FKs supported. | Requires connection URL search_path updates; cross-schema permissions. | **Recommended Interim Target (Phase 13.2.1)** |
| **Option 3: Database Isolation (`medmatch_auth` & `medmatch_clinical`)** | Two physically separate databases. | Absolute failure domain isolation; independent backups. | Cross-database FKs impossible; distributed transactions required. | **Long-term Architecture (Phase 14+)** |
