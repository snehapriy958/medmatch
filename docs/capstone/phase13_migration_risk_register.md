# Phase 13.2 — Database & Migration Risk Register

**Document Status:** Complete (Corrected Audit Baseline)  
**Execution Phase:** Phase 13.2  
**Implementation Status:** Not Started (Audit Gate Active)  
**Checkpoint:** `0d64976`  
**Branch:** `capstone/phase-13-production-engineering`  

---

## Risk Summary Matrix

| Risk ID | Title | Severity | Scope Classification | Component | Affected Environments |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MIG-01** | Duplicate `V1`–`V4` Prefixes in Local Working Tree | **CRITICAL** | **LOCAL_WORKING_TREE** | `auth-service` / Flyway | Local Dev, Docker Compose, Local JAR Build |
| **MIG-02** | Alembic Merge Head References Missing Revision on Clean Clone | **CRITICAL** | **TRACKED_REPOSITORY** | `ai-service` / Alembic | Clean Git Clones, CI/CD, Production Deployment |
| **MIG-03** | Alembic Duplicate Schema Collisions on Blank DB in Local Tree | **CRITICAL** | **LOCAL_WORKING_TREE** | `ai-service` / Alembic | Local Dev Blank Database Initialization |
| **MIG-04** | Migration Packaging Mechanism Inconsistency / Future Staleness Risk | **MEDIUM** | **CONFIGURATION** | Kubernetes / Compose | Production Kubernetes vs Docker Compose |
| **MIG-05** | Unsynchronized Concurrent Job Rollout in Kubernetes | **HIGH** | **DEPLOYMENT** | `infra/kubernetes` | Kubernetes Rollout (`deploy.sh` & `apply`) |
| **MIG-06** | Triple Concurrent Flyway Execution on K8s Startup | **HIGH** | **CONFIGURATION** | `auth-service` | Kubernetes Deployment (`replicas: 2`) |
| **MIG-07** | Cross-Service Table DDL Mutation in Untracked Alembic Revision | **HIGH** | **LOCAL_WORKING_TREE** | `ai-service` / Alembic | Local Working Tree Schema State |
| **MIG-08** | Shared `public` Schema & Cross-Service FK Coupling | **HIGH** | **ARCHITECTURE** | PostgreSQL Architecture | All Environments |
| **MIG-09** | Destructive Table Wipe in Untracked Migration `V10` | **MEDIUM** | **LOCAL_WORKING_TREE** | `auth-service` / Flyway | Local Dev, Docker Compose |
| **MIG-10** | Destructive Column Drops in Untracked Migrations `V15` and `V16` | **MEDIUM** | **LOCAL_WORKING_TREE** | `auth-service` / Flyway | Local Dev, Docker Compose |
| **MIG-11** | Zero Integration Test Coverage for DB Migrations | **MEDIUM** | **TRACKED_REPOSITORY** | Test Infrastructure | CI Pipeline, Pre-flight Verification |
| **MIG-12** | Local Git Exclude Masking Untracked Migration Files | **LOW** | **LOCAL_WORKING_TREE** | Repository Hygiene | Local Developer Working Clones |
| **MIG-13** | Orphan Alembic Directory at Repository Root | **LOW** | **LOCAL_WORKING_TREE** | Repository Hygiene | Local Repository Root |
| **MIG-14** | Untracked Alembic Backup Directory in AI Service | **LOW** | **LOCAL_WORKING_TREE** | Repository Hygiene | Local AI Service Directory |
| **MIG-15** | Empty Operational Migration Script `migrate.sh` (0 Bytes) | **INFORMATIONAL** | **TRACKED_REPOSITORY** | Operational Tooling | Operator Tooling |

---

## Detailed Risk Assessments

### MIG-01: Duplicate `V1`–`V4` Prefixes in Local Working Tree
- **Severity:** **CRITICAL**
- **Scope Classification:** **LOCAL_WORKING_TREE**
- **Component:** `auth-service` (Flyway)
- **Description:** The local working tree contains 20 files in `services/auth-service/src/main/resources/db/migration/`: 4 tracked Lineage B files and 16 untracked Lineage A files. This creates 4 duplicate version collisions (`V1`, `V2`, `V3`, `V4`). In contrast, a clean Git clone has ONLY the 4 tracked files and NO duplicate versions.
- **Evidence:** `git ls-files` shows 4 tracked files. `Get-ChildItem` shows 20 files. `.git/info/exclude` hides the 16 local files.
- **Risk Impact:** In the current working tree, Docker Compose bind-mounts all 20 files and crashes immediately with `FlywayException`. Docker builds package all 20 files into the JAR, crashing Spring Boot on startup. (Clean clones are unaffected by duplicate versions).
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-02: Alembic Merge Head References Missing Revision on Clean Clone
- **Severity:** **CRITICAL**
- **Scope Classification:** **TRACKED_REPOSITORY**
- **Component:** `ai-service` (Alembic)
- **Description:** The Git-tracked merge head `6f0604b23df6_merge_schema_heads.py` specifies `down_revision = ('0008', '3f3884863f27')`. The revision `3f3884863f27` is uncommitted and excluded by `.git/info/exclude`.
- **Evidence:** Tracked file `6f0604b23df6` references untracked `3f3884863f27`.
- **Risk Impact:** On any clean Git clone (CI runners, new developers, staging/production deployments), running `alembic upgrade head` aborts with `Can't locate revision identified by '3f3884863f27'`.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-03: Alembic Duplicate Schema Collisions on Blank DB in Local Tree
- **Severity:** **CRITICAL**
- **Scope Classification:** **LOCAL_WORKING_TREE**
- **Component:** `ai-service` (Alembic)
- **Description:** In the current working tree, Branch B revisions duplicate DDL already executed in main trunk revisions `0001`–`0007`:
  - `2248598b8f7e` creates `uq_trials_hospital_title_condition_phase` (already created by `0002`).
  - `3f3884863f27` creates table `trial_embeddings` (already created by `0007`).
- **Evidence:** Source code analysis of `0002` vs `2248598b8f7e` and `0007` vs `3f3884863f27`.
- **Risk Impact:** Running `alembic upgrade head` from a blank database in the current working tree fails with PostgreSQL duplicate relation/constraint errors.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-04: Migration Packaging Mechanism Inconsistency / Future Staleness Risk
- **Severity:** **MEDIUM**
- **Scope Classification:** **CONFIGURATION**
- **Component:** `infra/kubernetes` / `docker-compose.yml`
- **Description:** Docker Compose mounts the migration directory dynamically, while Kubernetes explicitly enumerates migration files in `kustomization.yaml`. They currently contain the same tracked four migrations on a clean clone, but the Kubernetes mechanism can become stale if future tracked migrations are added without updating `kustomization.yaml`.
- **Evidence:** `kustomization.yaml` lines 102-109 vs `docker-compose.yml` lines 107-108.
- **Risk Impact:** Adding future tracked migrations (`V5+`) will automatically apply in Docker Compose but will be silently omitted from Kubernetes unless `kustomization.yaml` is manually updated.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-05: Unsynchronized Concurrent Job Rollout in Kubernetes
- **Severity:** **HIGH**
- **Scope Classification:** **DEPLOYMENT**
- **Component:** `infra/kubernetes`
- **Description:** Kubernetes Jobs have no manifest-level dependency primitive. Applying manifests via `kubectl apply -k .` launches `auth-migrate`, `ai-migrate`, `auth-service`, `ai-service`, and `worker` in parallel.
- **Evidence:** `kustomization.yaml` flat resource list; `infra/kubernetes/ai-service/migrate-job.yaml` header notes.
- **Risk Impact:** `ai-migrate` creates `patients` table with a foreign key to `hospitals(id)`. If `auth-migrate` has not finished creating `hospitals`, `ai-migrate` crashes immediately.
- **Remediation Phase:** Phase 13.2.1 / 13.3
- **Status:** Open (Audited)

---

### MIG-06: Triple Concurrent Flyway Execution on K8s Startup
- **Severity:** **HIGH**
- **Scope Classification:** **CONFIGURATION**
- **Component:** `auth-service`
- **Description:** `auth-service/deployment.yaml` specifies `replicas: 2`. `application-production.yml` sets `spring.flyway.enabled: true`. Meanwhile, `job/auth-migrate` also runs Flyway migrate.
- **Evidence:** `auth-service/deployment.yaml` line 17 (`replicas: 2`); `application-production.yml` line 23 (`flyway.enabled: true`); `migrate-job.yaml` lines 28-36.
- **Risk Impact:** Three concurrent processes attempt Flyway migration simultaneously on deployment, creating lock contention.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-07: Cross-Service Table DDL Mutation in Untracked Alembic Revision
- **Severity:** **HIGH**
- **Scope Classification:** **LOCAL_WORKING_TREE**
- **Component:** `ai-service` (Alembic)
- **Description:** Untracked Alembic revision `01efd2b23442_schema_validation.py` executes DDL against `audit_logs` and `hospitals` (tables owned by `auth-service`).
- **Evidence:** Lines 24-34 of `01efd2b23442_schema_validation.py`.
- **Risk Impact:** Violates microservice boundary isolation in local working-tree migration graph.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-08: Shared `public` Schema & Cross-Service FK Coupling
- **Severity:** **HIGH**
- **Scope Classification:** **ARCHITECTURE**
- **Component:** PostgreSQL Architecture
- **Description:** Both services write to the `public` schema in database `medmatch`. Models in `ai-service` declare physical foreign keys to `auth-service` tables (`patients.hospital_id -> hospitals.id`, `trials.hospital_id -> hospitals.id`).
- **Evidence:** Database connection URLs and SQLAlchemy model foreign key declarations.
- **Risk Impact:** Prevents independent deployment, schema evolution, and failure domain isolation.
- **Remediation Phase:** Phase 13.2.1 (Interim Schema Partitioning) / Phase 14 (Separate DBs)
- **Status:** Open (Audited)

---

### MIG-09: Destructive Table Wipe in Untracked Migration `V10`
- **Severity:** **MEDIUM**
- **Scope Classification:** **LOCAL_WORKING_TREE**
- **Component:** `auth-service` (Flyway Lineage A)
- **Description:** Untracked file `V10__fix_role_seed_data.sql` executes `DELETE FROM roles;` followed by re-seeding. Not present in Git repository or clean clone.
- **Evidence:** Lines 1-3 of `V10__fix_role_seed_data.sql`.
- **Risk Impact:** If mounted in local Docker Compose, triggers a foreign key violation aborting the migration if user rows exist.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-10: Destructive Column Drops in Untracked Migrations `V15` and `V16`
- **Severity:** **MEDIUM**
- **Scope Classification:** **LOCAL_WORKING_TREE**
- **Component:** `auth-service` (Flyway Lineage A)
- **Description:** Untracked file `V15` drops `user_id`, and `V16` drops `resource`. Not present in Git repository or clean clone.
- **Evidence:** `V15` and `V16` SQL file contents.
- **Risk Impact:** Irreversible data loss of historical audit log metadata if executed locally.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-11: Zero Integration Test Coverage for DB Migrations
- **Severity:** **MEDIUM**
- **Scope Classification:** **TRACKED_REPOSITORY**
- **Component:** Test Infrastructure
- **Description:** Existing tests perform only static regex/file checks on migration filenames. No tests execute `flyway migrate` or `alembic upgrade head` in a real test container.
- **Evidence:** `tests/production_engineering/test_production_engineering_baseline.py` inspects files statically without running migrations.
- **Risk Impact:** Migration syntax errors, constraint collisions, and circular dependencies remain undetected until deployment.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-12: Local Git Exclude Masking Untracked Migration Files
- **Severity:** **LOW**
- **Scope Classification:** **LOCAL_WORKING_TREE**
- **Component:** Repository Hygiene
- **Description:** `.git/info/exclude` excludes `services/auth-service/src/main/resources/db/migration/` and `services/ai-service/alembic/versions/`.
- **Evidence:** Lines 12-13 of `.git/info/exclude`.
- **Risk Impact:** Obscures real filesystem state from Git in local developer clones.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-13: Orphan Alembic Directory at Repository Root
- **Severity:** **LOW**
- **Scope Classification:** **LOCAL_WORKING_TREE**
- **Component:** Repository Hygiene
- **Description:** Untracked directory `alembic/versions/` exists at the repo root containing 3 disconnected files without an `alembic.ini`.
- **Evidence:** Directory listing and diff against `services/ai-service/alembic/versions/`.
- **Risk Impact:** Developer confusion; risk of running alembic CLI commands from repo root.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-14: Untracked Alembic Backup Directory in AI Service
- **Severity:** **LOW**
- **Scope Classification:** **LOCAL_WORKING_TREE**
- **Component:** Repository Hygiene
- **Description:** `services/ai-service/alembic/versions_backup_before_fix/` contains 10 stale migration files.
- **Evidence:** Directory listing of `versions_backup_before_fix/`.
- **Risk Impact:** Repository clutter; risk of accidental inclusion in build artifacts.
- **Remediation Phase:** Phase 13.2.1
- **Status:** Open (Audited)

---

### MIG-15: Empty Operational Migration Script `migrate.sh` (0 Bytes)
- **Severity:** **INFORMATIONAL**
- **Scope Classification:** **TRACKED_REPOSITORY**
- **Component:** Operational Tooling
- **Description:** Tracked script `infra/scripts/migrate.sh` exists but has 0 bytes.
- **Evidence:** File size inspection (0 bytes).
- **Risk Impact:** Operators attempting to execute `migrate.sh` encounter a silent no-op.
- **Remediation Phase:** Phase 13.3 (Operational Scripting)
- **Status:** Open (Audited)
