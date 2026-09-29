# Phase 13.2 — Database & Migration Engineering Audit

**Document Status:** Complete (Corrected Audit Baseline)  
**Execution Phase:** Phase 13.2  
**Implementation Status:** Not Started (Audit Gate Active)  
**Checkpoint:** `0d64976 — feat: complete phase 13.1 security remediation`  
**Branch:** `capstone/phase-13-production-engineering`  
**Audit Date:** September 2026  

---

## 1. Executive Summary & Critical Baseline Distinctions

Phase 13.2 establishes an empirical, evidence-based engineering audit of all database schemas, migration engines, runtime configurations, deployment packaging, and execution lifecycles in MedMatch.

A foundational finding of this audit is the **critical distinction between the Git-tracked repository state and the local developer working tree**:

```
+---------------------------------------------------------------------------------------------------------+
|                                    REPOSITORY VS. WORKING TREE BASELINE                                 |
+------------------------------+------------------------------------+-------------------------------------+
| Dimension                    | Git-Tracked Repository (0d64976)   | Local Working Tree (Current State)  |
+------------------------------+------------------------------------+-------------------------------------+
| Auth Service (Flyway)        | Exactly 4 files tracked:           | 20 files physically present:        |
|                              | V1-V4 Lineage B (Consolidated).    | 4 tracked Lineage B + 16 untracked  |
|                              | NO duplicate versions in Git!      | Lineage A files (V1-V16). Duplicate |
|                              | Clean clones see a clean lineage.  | V1-V4 collision occurs locally.     |
+------------------------------+------------------------------------+-------------------------------------+
| AI Service (Alembic)         | 9 files tracked (0001-0008,        | 12 files physically present:        |
|                              | 6f0604b23df6). 3 parent revisions  | Includes untracked Branch B files   |
|                              | (2248598b8f7e, 01efd2b23442,       | (2248598b8f7e, 01efd2b23442,       |
|                              | 3f3884863f27) are UNTRACKED!       | 3f3884863f27). Merge head resolves |
|                              | Clean clones fail graph resolution.| locally, but collides on fresh DB.  |
+------------------------------+------------------------------------+-------------------------------------+
| Kubernetes Manifests         | ConfigMap packages only the 4      | Matches Git-tracked Flyway files.   |
|                              | tracked Lineage B files.           | Ignores local untracked Lineage A.  |
+------------------------------+------------------------------------+-------------------------------------+
| Docker Compose               | Volume-mounts host migration dir.  | Mounts all 20 local files,          |
|                              | On clean clone: mounts 4 files.    | causing immediate Flyway collision. |
+------------------------------+------------------------------------+-------------------------------------+
```

---

## 2. Migration Ownership Audit

### 2.1 Service-to-Database Mapping

| Dimension | Auth Service | AI Service | Celery Worker |
| :--- | :--- | :--- | :--- |
| **Primary Framework** | Flyway 10.x | Alembic 1.14.x | None (Reads/writes DB) |
| **Runtime Language** | Java 21 (Temurin) | Python 3.12/3.13 | Python 3.12/3.13 |
| **Target Database** | `medmatch` | `medmatch` | `medmatch` |
| **Target Schema** | `public` (default) | `public` (default) | `public` (default) |
| **Connection Configuration** | `SPRING_DATASOURCE_URL` | `DATABASE_URL` | `DATABASE_URL` |
| **Migration Source Path** | `services/auth-service/src/main/resources/db/migration/` | `services/ai-service/alembic/versions/` | N/A |
| **Schema Tracking Table** | `public.flyway_schema_history` | `public.alembic_version` | N/A |

### 2.2 Core Architectural Determinations

#### A. Which service owns which database/schema?
There is **no database-level or schema-level isolation**. Both services connect to the exact same PostgreSQL database (`medmatch`) and the `public` schema. Table ownership is logical rather than physical:
- `auth-service` owns: `roles`, `hospitals`, `users`, `audit_logs` (Flyway DDL).
- `ai-service` owns: `patients`, `trials`, `patient_notes`, `trial_criteria`, `criteria_embeddings`, `patient_note_embeddings`, `trial_embeddings`, `matches` (Alembic DDL).

#### B. Which migration framework owns each database?
Two independent frameworks target the **same** database:
- Flyway owns DDL for the four auth/admin tables.
- Alembic owns DDL for the eight clinical/matching/vector tables.
- No central migration orchestrator coordinates schema lock acquisition or DDL sequencing between them.

#### C. Where are migrations executed?
Migrations are executed in **four competing locations**:
1. **Docker Compose `auth-migrate`**: One-shot container using `flyway/flyway:10-alpine` mounting `./services/auth-service/src/main/resources/db/migration:/flyway/sql:ro`.
2. **Docker Compose `ai-migrate`**: One-shot container executing `alembic upgrade head`.
3. **Kubernetes Jobs**: `auth-migrate` Job (mounting ConfigMap `auth-migration-sql`) and `ai-migrate` Job (`alembic upgrade head`).
4. **Spring Boot Application Startup (`auth-service`)**: `application.yml` and `application-production.yml` configure `spring.flyway.enabled: true`. When `auth-service` boots, Spring Boot's `FlywayAutoConfiguration` executes migrations from `classpath:db/migration`.

#### D. Whether migrations can execute more than once?
- **Flyway**: Versioned migrations (`V__`) record SHA-256 checksums in `flyway_schema_history`. Once recorded, they do not execute again unless the schema is dropped or cleared.
- **Alembic**: Unapplied revisions execute once until reaching `head`.
- **Concurrency Issue**: Because `auth-service` runs `spring.flyway.enabled: true` with `replicas: 2` in Kubernetes alongside `job/auth-migrate`, **three separate processes attempt Flyway migration concurrently** on deployment.

#### E. Whether two migration systems can target the same database/schema?
**Yes, and they currently do.** Flyway and Alembic operate side-by-side in `public`. Cross-service dependencies exist: `patients.hospital_id` has a foreign key to `hospitals.id` (RESTRICT), and `trials.hospital_id` has a foreign key to `hospitals.id` (RESTRICT). If Alembic runs before Flyway creates `hospitals`, Alembic immediately fails with `relation "hospitals" does not exist`.

#### F. Whether application startup depends on migrations completing?
- **In Docker Compose**: Declared via `depends_on: { auth-migrate: { condition: service_completed_successfully } }` and `depends_on: { ai-migrate: { condition: service_completed_successfully } }`.
- **In Kubernetes**: **No manifest-level dependency exists.** Kubernetes has no built-in primitive to prevent a Deployment from scheduling while a Job is running. `deploy.sh` procedurally executes `kubectl wait --for=condition=complete job/...`, but if a cluster operator runs `kubectl apply -k .`, application pods and migration jobs start simultaneously.

---

## 3. Flyway Audit — Auth Service

### 3.1 Tracked Repository State vs. Local Working-Tree State

A precise audit of Git tracking at checkpoint `0d64976` reveals:

1. **Git-Tracked Migration Files (Tracked Repository State):**
   ```bash
   $ git ls-files "services/auth-service/src/main/resources/db/migration"
   services/auth-service/src/main/resources/db/migration/V1__create_roles_table.sql
   services/auth-service/src/main/resources/db/migration/V2__create_hospitals_table.sql
   services/auth-service/src/main/resources/db/migration/V3__create_users_table.sql
   services/auth-service/src/main/resources/db/migration/V4__create_audit_logs_table.sql
   ```
   **Finding:** The Git repository tracks **exactly 4 migration files** (Lineage B, added in commit `1ffe92a`).
   **CRITICAL DISTINCTION:** **There are NO duplicate version prefixes in the Git repository.**

2. **Untracked Local Files (Working-Tree State):**
   16 files are physically present on disk in the current working tree but are uncommitted:
   `V1__create_hospitals.sql`, `V2__create_roles.sql`, `V3__create_users.sql`, `V4__create_audit_logs.sql`, and `V5` through `V16`.
   These files represent legacy Lineage A. They are **hidden from Git status** by line 13 of `.git/info/exclude`:
   ```
   services/auth-service/src/main/resources/db/migration/
   ```

### 3.2 Impact Analysis by Environment

#### Scenario 1: Clean Git Clone (e.g. CI/CD Pipeline, New Developer Machine)
- `db/migration/` contains **only the 4 tracked files** (`V1`–`V4` Lineage B).
- **Duplicate Version Collisions:** **DO NOT OCCUR.**
- **Docker Compose:** Mounts only the 4 tracked files. `auth-migrate` runs V1 to V4 cleanly.
- **Docker Build / JAR:** Maven packages only the 4 tracked files. Spring Boot classpath contains only V1 to V4.
- **Kubernetes Job:** Matches the ConfigMap perfectly.

#### Scenario 2: Current Local Working Tree
- `db/migration/` contains **all 20 files** (Lineage A + Lineage B).
- **Duplicate Version Collisions:** **OCCURS LOCALLY.**
  - `V1`: `V1__create_hospitals.sql` vs `V1__create_roles_table.sql`
  - `V2`: `V2__create_roles.sql` vs `V2__create_hospitals_table.sql`
  - `V3`: `V3__create_users.sql` vs `V3__create_users_table.sql`
  - `V4`: `V4__create_audit_logs.sql` vs `V4__create_audit_logs_table.sql`
- **Docker Compose:** Host bind-mount pulls in all 20 files. Flyway crashes with:
  `org.flywaydb.core.api.FlywayException: Found more than one migration with version 1`.
- **Local Docker Build:** `COPY services/auth-service/src ./src` bakes all 20 files into `app.jar`. When Spring Boot boots with `spring.flyway.enabled: true`, the application pod crashes on boot.

### 3.3 Flyway Configuration Matrix

| Configuration Property | Configured Value | Flyway Default | Classification | Operational Assessment |
| :--- | :--- | :--- | :--- | :--- |
| `spring.flyway.enabled` | `true` | `true` | CONFIGURATION | Runs migrations on app startup inside Spring Boot |
| `spring.flyway.locations` | `classpath:db/migration` | `classpath:db/migration` | CONFIGURATION | Scans classpath (fails in local dirty tree; succeeds on clean clone) |
| `validate-on-migrate` | Not set | `true` | CONFIGURATION | Validates applied migrations against disk/classpath |
| `clean-disabled` | Not set | `true` | CONFIGURATION | Prevents accidental destructive clean |
| `clean-on-validation-error`| Not set | `false` | CONFIGURATION | Safe: will not wipe database on validation failure |
| `baseline-on-migrate` | Not set | `false` | CONFIGURATION | Fails if non-empty schema exists without history |
| `out-of-order` | Not set | `false` | CONFIGURATION | Rejects retroactive out-of-order migrations |

---

## 4. Kubernetes Flyway Packaging Audit

### 4.1 Packaging Mechanism & Alignment with Git State

In [kustomization.yaml](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/kustomization.yaml) (lines 102–109):
```yaml
configMapGenerator:
  - name: auth-migration-sql
    files:
      - services/auth-service/src/main/resources/db/migration/V1__create_roles_table.sql
      - services/auth-service/src/main/resources/db/migration/V2__create_hospitals_table.sql
      - services/auth-service/src/main/resources/db/migration/V3__create_users_table.sql
      - services/auth-service/src/main/resources/db/migration/V4__create_audit_logs_table.sql
```

The `auth-migrate` Job ([infra/kubernetes/auth-service/migrate-job.yaml](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/auth-service/migrate-job.yaml)) mounts this ConfigMap:
```yaml
volumeMounts:
  - name: flyway-sql
    mountPath: /flyway/sql
    readOnly: true
```

### 4.2 Audit Determinations:
1. **Kubernetes Packages the Tracked Repository Lineage:**
   `kustomization.yaml` explicitly packages the **exact four files tracked by Git**. It was authored to use Lineage B.
2. **Local Working-Tree Masking:**
   In the local developer working tree, this configuration avoids the duplicate prefix error for `job/auth-migrate` by mounting only the 4 files instead of the full directory.
3. **Packaging Mechanism Inconsistency & Future Staleness Risk:**
   - Docker Compose mounts the migration directory dynamically, while Kubernetes explicitly enumerates migration files in `kustomization.yaml`.
   - On a clean clone, both environments currently contain the exact same four tracked migrations.
   - However, the Kubernetes mechanism can become stale if future tracked migrations (`V5+`) are added without updating `kustomization.yaml`.
   - In the current local working tree, the apparent mismatch is caused by local ignored/untracked historical migration files that Docker Compose sees through its dynamic directory mount.

---

## 5. Alembic Audit — AI Service

### 5.1 Tracked vs. Untracked Revision Audit

Verification with `git ls-files` establishes the exact Git-tracked status of all Alembic revisions:

```
Tracked in Git (0d64976):
  0001_create_patients_table.py
  0002_create_trials_table.py
  0003_create_patient_notes_table.py
  0004_create_trial_criteria_table.py
  0005_create_criteria_embeddings_table.py
  0006_create_patient_note_embeddings_table.py
  0007_create_trial_embeddings_table.py
  0008_create_matches_table.py
  6f0604b23df6_merge_schema_heads.py

Untracked / Ignored (.git/info/exclude):
  2248598b8f7e_initial_schema.py
  01efd2b23442_schema_validation.py
  3f3884863f27_add_trial_embeddings.py
```

### 5.2 Clean-Clone Failure: Broken Revision Graph (TRACKED_REPOSITORY Defect)

The tracked file `6f0604b23df6_merge_schema_heads.py` defines:
```python
revision: str = '6f0604b23df6'
down_revision: Union[str, Sequence[str], None] = ('0008', '3f3884863f27')
```

**Clean-Clone Impact:**
On any clean Git clone:
- Revisions `0001` through `0008` and `6f0604b23df6` exist.
- Revision `3f3884863f27` **does not exist**.
- When `alembic upgrade head` is invoked, Alembic attempts to load the graph and immediately crashes:
  ```
  alembic.util.exc.CommandError: Can't locate revision identified by '3f3884863f27'
  ```
This is a **critical tracked repository defect** preventing CI builds, clean clone deployments, and automated testing.

### 5.3 Local Working-Tree Failure: Duplicate Schema Collisions (LOCAL_WORKING_TREE Defect)

In the **current working tree**, all 12 revisions exist on disk.
Alembic successfully builds the merge graph:
```
0001 -> 0002 -> 0003 -> 0004 -> 0005 -> 0006 -> 0007 (branchpoint)
Branch A: 0007 -> 0008
Branch B: 0007 -> 2248598b8f7e -> 01efd2b23442 -> 3f3884863f27
Merge:    (0008, 3f3884863f27) -> 6f0604b23df6
```

**Working-Tree Blank-Database Impact:**
If `alembic upgrade head` is executed against a clean database in the current working tree:
1. `0001`–`0007` execute successfully.
2. Branch B begins execution:
   - `2248598b8f7e` attempts to create `uq_trials_hospital_title_condition_phase`, which `0002` already created.
   - `3f3884863f27` attempts to create table `trial_embeddings`, which `0007` already created.
3. Execution aborts due to PostgreSQL duplicate relation/constraint errors.

**Summary:** The duplicate constraint/table collision is a defect of the **local working-tree Branch B graph**, whereas a clean clone fails earlier due to the **missing parent revision**.

---

## 6. Database Schema Ownership

### 6.1 Distinction Between Table Ownership, DDL Ownership, and Runtime Access

| Table Name | Logical Domain | DDL / Migration Ownership | Runtime Access | External Foreign Keys |
| :--- | :--- | :--- | :--- | :--- |
| `roles` | Auth | `auth-service` (Flyway) | Auth (RW) | None |
| `hospitals` | Auth | `auth-service` (Flyway) | Auth (RW), AI (Read-Only) | Referenced by `users`, `patients`, `trials`, `matches` |
| `users` | Auth | `auth-service` (Flyway) | Auth (RW) | `role_id -> roles.id`, `hospital_id -> hospitals.id` |
| `audit_logs` | Shared | `auth-service` (Flyway)* | Auth (RW), AI (RW) | None (Loose coupling by design) |
| `patients` | Clinical | `ai-service` (Alembic) | AI (RW) | `hospital_id -> hospitals.id` (RESTRICT) |
| `trials` | Clinical | `ai-service` (Alembic) | AI (RW) | `hospital_id -> hospitals.id` (RESTRICT) |
| `patient_notes` | Clinical | `ai-service` (Alembic) | AI (RW) | `patient_id -> patients.id` (CASCADE) |
| `trial_criteria` | Clinical | `ai-service` (Alembic) | AI (RW) | `trial_id -> trials.id` (CASCADE) |
| `criteria_embeddings` | Clinical | `ai-service` (Alembic) | AI (RW) | `criteria_id -> trial_criteria.id` (CASCADE) |
| `patient_note_embeddings` | Clinical | `ai-service` (Alembic) | AI (RW) | `patient_note_id -> patient_notes.id` (CASCADE) |
| `trial_embeddings` | Clinical | `ai-service` (Alembic) | AI (RW) | `trial_id -> trials.id` (CASCADE) |
| `matches` | Clinical | `ai-service` (Alembic) | AI (RW) | `patient_id -> patients.id`, `trial_id -> trials.id`, `hospital_id -> hospitals.id` |

*\* DDL is owned by `auth-service` via Flyway `V4__create_audit_logs_table.sql`. Both services write directly to this table at runtime.*

### 6.2 Clarification on Shared Runtime Access vs. Migration Defect

- **Shared Runtime Access (Architecture Design):**
  `ai-service` reads `hospitals` for tenant validation and writes to `audit_logs` for compliance tracking. This shared runtime access is an application-level architectural pattern, **not a database migration defect**.
- **Cross-Service Migration Defect (Historical DDL Violation):**
  The actual migration defect occurred in untracked local Alembic revision `01efd2b23442_schema_validation.py`, where Alembic autogenerated DDL modifying `audit_logs` and `hospitals`. This was mitigated in `services/ai-service/alembic/env.py` by registering `AUTH_SERVICE_OWNED_TABLES`, but the revision remains in the local working-tree graph.

---

## 7. Migration Startup Order & Race Conditions

| Race Condition | Scope | Operational Trace & Failure Mode |
| :--- | :--- | :--- |
| **A. App starts before migrations finish** | DEPLOYMENT | When `kubectl apply -k .` runs, `auth-service` pods schedule immediately. Hibernate's `ddl-auto: validate` crashes the pod if tables do not exist yet. |
| **B. Worker starts before AI migrations finish** | DEPLOYMENT | In Kubernetes, `worker` deployment schedules concurrently with `job/ai-migrate`. Tasks querying unmigrated tables fail. |
| **C. Multiple replicas attempt migrations concurrently** | CONFIGURATION | `auth-service` deployment has `replicas: 2` with `spring.flyway.enabled: true`. Along with `job/auth-migrate`, 3 separate runners invoke Flyway migrate simultaneously. |
| **D. Auth and AI service migrations interfere** | DEPLOYMENT | `job/ai-migrate` and `job/auth-migrate` launch in parallel. `ai-migrate` references `hospitals` table; if Flyway has not created it yet, Alembic crashes. |
| **E. K8s rollout starts pods before Job completion** | DEPLOYMENT | Manifests in `kustomization.yaml` are applied in a single flat pass. Procedural wait loops in `deploy.sh` mitigate this only if the script is strictly used. |
| **F. Migration failure still allows app traffic** | ARCHITECTURE | Application pods fail readiness probes if the database connection or schema is invalid, preventing Service traffic routing. However, partial DDL application leaves tables inconsistent. |

---

## 8. Migration Safety Configuration Audit

| Safety Area | Configured Setting | Scope | Operational Assessment |
| :--- | :--- | :--- | :--- |
| **Flyway Clean in Prod** | Default (`clean-disabled: true`) | CONFIGURATION | Prevents accidental database clean |
| **Flyway Validation** | Enabled (`validate-on-migrate: true`) | CONFIGURATION | Ensures checksums match |
| **Flyway Baseline** | Disabled (`baseline-on-migrate: false`) | CONFIGURATION | Fails if non-empty schema exists without history |
| **Flyway Out of Order** | Disabled (`out-of-order: false`) | CONFIGURATION | Rejects out-of-order migrations |
| **Alembic Transactions** | `with context.begin_transaction():` | CONFIGURATION | Transactional DDL in PostgreSQL |
| **Destructive SQL in Tracked Migrations** | None in tracked `V1`–`V4` | TRACKED_REPOSITORY | Clean (Tracked repo has no destructive SQL) |
| **Destructive SQL in Untracked Migrations** | `V10` has `DELETE FROM roles;` | LOCAL_WORKING_TREE | Present in untracked local file only |
| **Destructive Drops in Untracked Migrations**| `V15` drops `user_id`, `V16` drops `resource`| LOCAL_WORKING_TREE | Present in untracked local files only |

---

## 9. Reproducibility & Environment Consistency

```
+---------------------+-----------------------------+-----------------------------+-----------------------------+
| Environment         | Git Tracking State          | Local Working-Tree State    | Clean Clone State           |
+---------------------+-----------------------------+-----------------------------+-----------------------------+
| Flyway Migrations   | Exactly 4 files (V1-V4 B)   | 20 files (V1-V16 A + V1-V4 B)| Exactly 4 files (V1-V4 B)   |
| Flyway Result       | Clean sequential lineage    | Collision (Duplicate V1-V4) | Runs V1-V4 cleanly          |
| Alembic Migrations  | 9 files (Missing 3 parents) | 12 files (Full local graph) | 9 files (Missing 3 parents) |
| Alembic Result      | Broken revision graph       | Graph builds; collides on DB| Fails graph resolution      |
| Kubernetes Job      | Packages 4 files            | Packages 4 files            | Packages 4 files            |
| Docker Compose      | Mounts migration dir        | Mounts 20 files (Fails)     | Mounts 4 files (Succeeds)   |
+---------------------+-----------------------------+-----------------------------+-----------------------------+
```

---

## 10. Test Coverage Audit

Existing migration tests in [tests/production_engineering/test_production_engineering_baseline.py](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/tests/production_engineering/test_production_engineering_baseline.py):
- `test_alembic_single_head_in_ai_service`: Asserts `6f0604b23df6` exists. (Passes, but does not test clean-clone graph resolution).
- `test_root_alembic_disconnected_versions`: Asserts root contains 3 disconnected files. (Passes).
- `test_flyway_version_collision_hazard`: Asserts that duplicate version prefixes exist on disk. (Passes, verifying local working-tree collision hazard).

### Gaps:
- Zero integration tests testing `flyway migrate` or `alembic upgrade head` in a real container.
- Zero tests validating clean-database migration idempotency.
- Zero tests verifying Spring Boot starts up with Flyway enabled.

---

## 11. Conclusion & Phase Gate

> [!CAUTION]
> **Audit Gate Statement:**
> **Phase 13.2 Audit Corrected — Implementation Not Started**
> No production code, migration scripts, or configurations have been altered. Remediation must be planned in Phase 13.2.1/13.3.
