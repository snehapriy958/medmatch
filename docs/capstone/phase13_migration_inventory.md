# Phase 13.2 — Complete Migration File Inventory

**Document Status:** Complete (Corrected Audit Baseline)  
**Execution Phase:** Phase 13.2  
**Implementation Status:** Not Started (Audit Gate Active)  
**Checkpoint:** `0d64976`  
**Branch:** `capstone/phase-13-production-engineering`  

---

## 1. Flyway Migration Inventory — Auth Service

Directory inspected:  
`services/auth-service/src/main/resources/db/migration/` (20 files physically present on disk)

### 1.1 Complete Flyway Inventory Table

| Version | Filename | Purpose | Git Status | Clean Clone? | K8s Packaged? | Lineage | Scope & Operational Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **V1** | `V1__create_hospitals.sql` | Initial 5-column `hospitals` table | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Causes duplicate V1 collision locally |
| **V1** | `V1__create_roles_table.sql` | Creates `roles` + seeds 6 roles | **TRACKED** | **YES** | **YES** | **B** (Consolidated) | TRACKED_REPOSITORY: Official production V1 |
| **V2** | `V2__create_roles.sql` | Initial 4 roles seed table | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Causes duplicate V2 collision locally |
| **V2** | `V2__create_hospitals_table.sql` | Creates `hospitals` table with `active`, `updated_at` | **TRACKED** | **YES** | **YES** | **B** (Consolidated) | TRACKED_REPOSITORY: Official production V2 |
| **V3** | `V3__create_users.sql` | Initial `users` table | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Causes duplicate V3 collision locally |
| **V3** | `V3__create_users_table.sql` | Creates `users` table with status, updated_at | **TRACKED** | **YES** | **YES** | **B** (Consolidated) | TRACKED_REPOSITORY: Official production V3 |
| **V4** | `V4__create_audit_logs.sql` | Initial 6-column `audit_logs` table | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Causes duplicate V4 collision locally |
| **V4** | `V4__create_audit_logs_table.sql` | Creates 12-column `audit_logs` shared table | **TRACKED** | **YES** | **YES** | **B** (Consolidated) | TRACKED_REPOSITORY: Official production V4 |
| **V5** | `V5__add_ip_address_to_audit_logs.sql` | Adds `ip_address` to `audit_logs` | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V6** | `V6__add_active_to_hospitals.sql` | Adds `active` to `hospitals` | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V7** | `V7__add_updated_at_to_hospitals.sql` | Adds `updated_at` to `hospitals` | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V8** | `V8__add_created_at_to_roles.sql` | Adds `created_at` to `roles` | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V9** | `V9__add_updated_at_to_users.sql` | Adds `updated_at` to `users` | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V10** | `V10__fix_role_seed_data.sql` | `DELETE FROM roles;` + re-seed | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Destructive local wipe |
| **V11** | `V11__add_user_status.sql` | Adds `status` to `users` | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V12** | `V12__add_audit_actor_columns.sql` | Adds actor columns to audit log | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V13** | `V13__fix_audit_actor_columns.sql` | Modifies actor column length | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V14** | `V14__add_audit_resource_columns.sql`| Adds resource columns to audit | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Legacy patch file |
| **V15** | `V15__fix_audit_user_id.sql` | Drops column `user_id` | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Destructive local drop |
| **V16** | `V16__remove_audit_resource_column.sql`| Drops column `resource` | **UNTRACKED** | NO | NO | **A** (Iterative) | LOCAL_WORKING_TREE: Destructive local drop |

---

### 1.2 Summary of Flyway Inventory

- **Total Files Physically Present in Working Tree:** 20
- **Total Files Tracked by Git (at checkpoint `0d64976`):** **4** (`V1__create_roles_table.sql`, `V2__create_hospitals_table.sql`, `V3__create_users_table.sql`, `V4__create_audit_logs_table.sql`)
- **Total Local Untracked Files:** **16** (Lineage A files, hidden by `.git/info/exclude`)
- **Duplicate Versions in Git Repository:** **0** (The Git repository contains NO duplicate version prefixes)
- **Duplicate Versions in Current Working Tree:** **4** (`V1`, `V2`, `V3`, `V4`)
- **Destructive Migrations (`V10`, `V15`, `V16`) Status:** **UNTRACKED / LOCAL ONLY.** They are not included in Git, not packaged in Kubernetes, and do not exist in a clean clone.

---

## 2. Alembic Migration Inventory — AI Service

Directory inspected:  
`services/ai-service/alembic/versions/` (12 files physically present on disk)

### 2.1 Complete Alembic Inventory Table

| Revision ID | Down Revision | Filename | Git Status | Clean Clone? | Branch | Purpose & Scope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0001** | `None` | `0001_create_patients_table.py` | **TRACKED** | **YES** | Trunk | TRACKED_REPOSITORY: Creates `patients` (FK to `hospitals`) |
| **0002** | `0001` | `0002_create_trials_table.py` | **TRACKED** | **YES** | Trunk | TRACKED_REPOSITORY: Creates `trials` & unique constraint |
| **0003** | `0002` | `0003_create_patient_notes_table.py` | **TRACKED** | **YES** | Trunk | TRACKED_REPOSITORY: Creates `patient_notes` |
| **0004** | `0003` | `0004_create_trial_criteria_table.py` | **TRACKED** | **YES** | Trunk | TRACKED_REPOSITORY: Creates `trial_criteria` |
| **0005** | `0004` | `0005_create_criteria_embeddings_table.py` | **TRACKED** | **YES** | Trunk | TRACKED_REPOSITORY: Creates `criteria_embeddings` |
| **0006** | `0005` | `0006_create_patient_note_embeddings_table.py`| **TRACKED** | **YES** | Trunk | TRACKED_REPOSITORY: Creates `patient_note_embeddings` |
| **0007** | `0006` | `0007_create_trial_embeddings_table.py` | **TRACKED** | **YES** | Branchpoint | TRACKED_REPOSITORY: Creates `trial_embeddings` |
| **0008** | `0007` | `0008_create_matches_table.py` | **TRACKED** | **YES** | Branch A | TRACKED_REPOSITORY: Creates `matches` |
| **2248598b8f7e**| `0007` | `2248598b8f7e_initial_schema.py` | **UNTRACKED**| NO | Branch B | LOCAL_WORKING_TREE: Duplicate constraint collision locally |
| **01efd2b23442**| `2248598b8f7e`| `01efd2b23442_schema_validation.py` | **UNTRACKED**| NO | Branch B | LOCAL_WORKING_TREE: Cross-service DDL on auth tables |
| **3f3884863f27**| `01efd2b23442`| `3f3884863f27_add_trial_embeddings.py` | **UNTRACKED**| NO | Branch B | LOCAL_WORKING_TREE: Duplicate table collision locally |
| **6f0604b23df6**| `('0008', '3f3884863f27')` | `6f0604b23df6_merge_schema_heads.py` | **TRACKED** | **YES** | Merge Head | TRACKED_REPOSITORY: Merge head referencing missing revision |

---

### 2.2 Summary of Alembic Inventory

- **Total Files Physically Present in Working Tree:** 12
- **Total Files Tracked by Git (at checkpoint `0d64976`):** **9** (`0001` through `0008`, and `6f0604b23df6`)
- **Total Local Untracked Files:** **3** (`2248598b8f7e`, `01efd2b23442`, `3f3884863f27`, hidden by `.git/info/exclude`)
- **Clean-Clone Defect:** `6f0604b23df6` references untracked `3f3884863f27`. A clean clone fails graph resolution with `Can't locate revision identified by '3f3884863f27'`.
- **Working-Tree Defect:** The local working tree can build the graph, but `alembic upgrade head` fails on a blank database because Branch B duplicates constraints and tables created in `0002` and `0007`.

---

## 3. Orphan & Auxiliary Directories

### 3.1 Repository Root `alembic/versions/` (Orphan Directory)
- **Location:** `alembic/versions/`
- **Files Present:** 3 files (`01efd2b23442_schema_validation.py`, `2248598b8f7e_initial_schema.py`, `3f3884863f27_add_trial_embeddings.py`)
- **Git Status:** **UNTRACKED** (Ignored by `.git/info/exclude`)
- **Operational Status:** Disconnected orphan directory. No `alembic.ini` exists at the root.

### 3.2 AI Service `versions_backup_before_fix/` (Stale Backup Directory)
- **Location:** `services/ai-service/alembic/versions_backup_before_fix/`
- **Files Present:** 10 files (revisions `0001`–`0007`, `2248598b8f7e`, `01efd2b23442`, `3f3884863f27`)
- **Git Status:** **UNTRACKED** (Ignored by `.git/info/exclude`)
- **Operational Status:** Stale pre-merge snapshot directory left in working tree.
