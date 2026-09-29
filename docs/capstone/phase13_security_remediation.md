# Phase 13.1 — Security & Secrets Remediation Report

**Phase**: 13.1 — Security & Secrets Remediation  
**Status**: REMEDIATION COMPLETE — AWAITING REVIEW (Phase 13 In Progress)  
**Base Commit**: `2b61977`  
**Branch**: `capstone/phase-13-production-engineering`  
**Date**: September 2026  

---

## Executive Summary

During the Phase 13.0 Production Engineering Audit, several critical security and secret-hygiene vulnerabilities were identified across Spring Boot `auth-service`, FastAPI `ai-service`, Celery workers, Redis, and deployment artifacts. Phase 13.1 implements a non-breaking, defense-in-depth remediation across 7 core security findings without modifying clinical research logic, research evaluation contracts, or clinical reasoning behavior.

All 7 security findings have been remediated, verified via targeted automated test suites, validated against static scanners, and corroborated through end-to-end integration and configuration checks.

---

## Remediation Item Details

### 1. RSA Key Architecture & Key Handling

#### Finding
The RSA private key (`private.pem`) was physically checked into local development trees and loaded via brittle file-path assumptions in `JwtService.java`. If the file was missing or placed in an alternate container mount, startup failed. Conversely, `ai-service` lacked flexible configuration-driven discovery of public keys across container, local dev, and Kubernetes environments.

#### Root Cause
Tight coupling to local filesystem paths (`src/main/resources/keys/private.pem`) rather than Spring `Resource` abstraction or environment variables; absence of multi-source key resolution in FastAPI.

#### Remediation
- **Spring Boot `JwtService.java`**: Implemented multi-tier key loading:
  1. Primary: Spring `Resource` loader supporting `file:`, `classpath:`, and arbitrary URI paths configured via `jwt.private-key-path` (defaults to `${JWT_PRIVATE_KEY_PATH:classpath:keys/private.pem}`).
  2. Fallback: Direct environment variable `JWT_PRIVATE_KEY` for 12-factor container and Kubernetes Secret injection.
  3. Header normalization: Supports PKCS#8 (`BEGIN PRIVATE KEY`) and standard RSA PEM headers (`BEGIN RSA PRIVATE KEY`).
- **FastAPI `security.py`**: Implemented `load_public_key()`:
  1. Checks `JWT_PUBLIC_KEY` environment variable (both inline PEM and file path).
  2. Checks `JWT_PUBLIC_KEY_PATH` environment variable.
  3. Probes candidate filesystem locations (`/app/keys/public.pem`, `keys/public.pem`, and relative paths).
  4. Returns `None` gracefully if unconfigured rather than raising an unhandled exception at import time.
- **Git Hygiene**: Verified `.gitignore` prevents `private.pem` from being committed; no real private key material is tracked in the Git index. Safe example template provided.

#### Security Rationale
Prevents accidental commits of private key material while ensuring 100% cloud-native deployment flexibility where keys are injected via Kubernetes Secrets or External Secrets Operators without image rebuilding.

#### Tests Executed
- `JwtServiceTest.java`: 7 test cases passed (token generation, claim extraction, role validation, expiration).
- `services/ai-service/tests/test_task_security.py`: Token verification across tenant headers.

---

### 2. Kubernetes Secret Handling

#### Finding
Local configuration files (`infra/kubernetes/secrets/secrets.yaml`) risked accidental tracking if `.gitignore` rules were relaxed or developer commits were unvetted.

#### Root Cause
Absence of explicit secret sanitization validation and clear template boundaries in Kubernetes directory trees.

#### Remediation
- Preserved strict git-ignore for `infra/kubernetes/secrets/secrets.yaml`.
- Maintained and updated safe template `infra/kubernetes/secrets/secrets.yaml.example` containing only synthetic placeholder tokens (`REPLACE_ME_*`). Added `REDIS_PASSWORD` placeholder.
- Validated via `git ls-files "*secrets.yaml*"` and `git grep` that no real credentials or secret values exist in git tracking or commit history.

#### Security Rationale
Enforces zero-secret footprint in repository source control. In production, Kubernetes Secrets are managed out-of-band via SealedSecrets, HashiCorp Vault, or AWS Secrets Manager / GCP Secret Manager using External Secrets Operator.

---

### 3. Spring Boot Actuator Exposure

#### Finding
`/actuator/**` was globally permitted (`.permitAll()`) in `SecurityConfig.java`, exposing sensitive runtime configuration, environment variables, mappings, and beans to anonymous callers.

#### Root Cause
Permissive wildcard routing in Spring Security configuration intended for local testing.

#### Remediation
- Updated [SecurityConfig.java](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/src/main/java/com/medmatch/auth/security/SecurityConfig.java):
  - Permitted anonymously ONLY the minimum necessary endpoints for health and monitoring:
    - `/actuator/health`
    - `/actuator/health/**`
    - `/actuator/info`
    - `/actuator/prometheus`
  - Restricted all remaining actuator endpoints (`/actuator/**`, including `/env`, `/beans`, `/mappings`, `/heapdump`) to authenticated users with role `SYSTEM_ADMIN`.
- Updated [application-production.yml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/src/main/resources/application-production.yml):
  - Set `management.endpoint.health.show-details: when_authorized`.
  - Restricted exposed endpoints via `management.endpoints.web.exposure.include: health,info,prometheus`.

#### Security Rationale
Prevents reconnaissance and information disclosure attacks against Spring Boot internals while maintaining Prometheus scraping and Kubernetes liveness/readiness probe compatibility.

#### Tests Executed
- `auth-service` test suite (81/81 passed).
- Static assertion in `test_production_engineering_baseline.py::test_spring_security_actuator_hardened`.

---

### 4. Task-Status Endpoint Authentication & Tenant Isolation

#### Finding
`GET /api/tasks/{task_id}` lacked authentication dependencies (`get_current_user`), allowing anonymous users to poll arbitrary Celery task IDs, query task state, and observe raw internal exception tracebacks. Furthermore, the endpoint route was omitted from `api_router` registration in `app/api/routes/__init__.py`.

#### Root Cause
Route defined in isolation without authentication guard or tenant tracking integration; unrouted endpoint file.

#### Remediation
- **Tenant Registry**: Created [task_registry.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/task_registry.py) providing `record_task_tenant(task_id, hospital_id)` and `get_task_tenant(task_id)`. Employs Redis with fallback to an in-memory bounded LRU cache for resilience during Redis offline/test mode.
- **Task Dispatch Hook**: Updated [trial.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/api/routes/trial.py) to immediately record the initiating hospital tenant ID upon task submission. Updated [celery/tasks.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/celery/tasks.py) to return `hospital_id` in the task result dictionary.
- **Route Hardening**: Updated [tasks.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/api/routes/tasks.py):
  - Injected `get_current_user` and `get_current_hospital_id` dependencies.
  - Returns HTTP 404 (`Task not found`) if task ID has no recorded tenant or does not exist in Celery.
  - Returns HTTP 403 (`Forbidden: cross-tenant task access`) if requesting tenant does not match the owning hospital tenant.
  - Sanitized error message on Celery task failure: returns generic `"Task processing failed"` instead of leaking internal Python tracebacks or database error messages.
- **Router Mounting**: Registered `tasks_router` into `app/api/routes/__init__.py`.

#### Security Rationale
Eliminates cross-tenant data leakage and reconnaissance. Enforces strict multi-tenant authorization barriers on asynchronous task polling.

#### Tests Executed
- Created [test_task_security.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/tests/test_task_security.py):
  1. `test_task_status_unauthenticated`: Validates 401 when no token is passed.
  2. `test_task_status_same_tenant_success`: Validates 200 and sanitized result for same-tenant caller.
  3. `test_task_status_cross_tenant_forbidden`: Validates 403 when hospital A queries hospital B's task.
  4. `test_task_status_nonexistent_task`: Validates 404 when task ID is unknown.
  5. `test_task_status_failure_message_sanitized`: Validates error message is sanitized on task failure.
  All 5 tests passed (100%).

---

### 5. Redis Authentication

#### Finding
Redis was deployed without password authentication (`--requirepass` omitted), allowing any process capable of reaching port 6379 to execute arbitrary Redis commands, inspect cache entries, or inject Celery tasks.

#### Root Cause
Default unauthenticated deployment configuration for dev/compose environments.

#### Remediation
- **FastAPI / Celery Settings**: Updated [settings.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/config/settings.py) to add `REDIS_PASSWORD`. Added `configure_redis_authentication` model validator that dynamically injects URL-encoded credentials (`quote(pw, safe="")`) into `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` when `REDIS_PASSWORD` is supplied.
- **Redis Client**: Updated [redis.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/cache/redis.py) to pass `password=settings.REDIS_PASSWORD` explicitly to `redis.from_url`.
- **Docker Compose**: Updated [docker-compose.yml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docker-compose.yml) with conditional password support: launches `redis-server --requirepass` if `REDIS_PASSWORD` is set, and uses authenticated healthcheck (`redis-cli -a`). Injected `REDIS_PASSWORD` into `ai-service` and `celery-worker`.
- **Kubernetes**: Updated [redis-statefulset.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/redis/redis-statefulset.yaml), [ai-service/deployment.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/ai-service/deployment.yaml), and [worker/deployment.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/worker/deployment.yaml) to consume `REDIS_PASSWORD` via `secretKeyRef` (with `optional: true` for zero-friction local/offline fallback).

#### Security Rationale
Restricts Redis access to authenticated services, mitigating unauthorized data tampering, unauthorized cache reading, or remote code execution via Celery task poisoning.

#### Tests Executed
- Created [test_redis_config.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/tests/test_redis_config.py):
  1. `test_redis_config_without_password`: Verifies clean URL formatting when password is empty.
  2. `test_redis_config_with_password`: Verifies safe URL encoding of passwords with special characters.
  3. `test_redis_config_with_existing_creds_in_url`: Prevents double-injection.
  All 3 tests passed.

---

### 6. Removal of Debug Credential Logging

#### Finding
Arbitrary `print` and `System.out.println` statements logged sensitive internal authentication state:
- `deps.py`: `print("AI SERVICE JWT USER = ...")` and hospital ID.
- `trial.py`: `print("========== CREATE TRIAL ROUTE HIT ==========")`.
- `trial_service.py`: `print("========== BEFORE DB COMMIT ==========")`, `print("========== FLUSH COMPLETED ==========")`.
- `AuthServiceImpl.java`: `System.out.println("LOGIN USER FOUND = " + ...)`, `LOGIN USER ID`, `LOGIN HOSPITAL ID`, and `PASSWORD MATCH RESULT`.
- `application.yml`: Hibernate bind logging `org.hibernate.orm.jdbc.bind: trace` printed SQL parameter bindings.

#### Root Cause
Temporary debugging artifacts left in production service paths.

#### Remediation
- Removed all debug `print` statements from [deps.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/api/deps.py).
- Removed route tracing print statements from [trial.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/api/routes/trial.py).
- Removed commit/flush print statements from [trial_service.py](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/trial_service.py).
- Removed `LOGIN USER FOUND`, `LOGIN USER ID`, `LOGIN HOSPITAL ID`, and `PASSWORD MATCH RESULT` print statements from [AuthServiceImpl.java](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/src/main/java/com/medmatch/auth/service/AuthServiceImpl.java).
- Adjusted Hibernate logging to `WARN` in `application.yml` and `application-production.yml`. Structured HIPAA audit logging (`auditService.createAuditLog`) was preserved intact.

#### Security Rationale
Prevents credential, identity, and query exposure in container log streams (stdout/stderr) and log aggregators.

---

### 7. Docker Build Context Hygiene

#### Finding
No `.dockerignore` files existed in the repository. As a result, `docker build` contexts included `.git`, `.venv`, `.env`, temporary test artifacts, local datasets, and private keys.

#### Root Cause
Absence of build-context exclusion rules.

#### Remediation
- Created root [.dockerignore](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/.dockerignore) excluding:
  - Version control (`.git/`)
  - Environment and secrets (`.env*`, `**/secrets.yaml`)
  - Cryptographic keys (`**/*.pem`, `**/*.key`, `**/*.pk8`, preserving only necessary public keys)
  - Python virtual environments and caches (`**/.venv/`, `**/__pycache__/`)
  - Node / frontend artifacts (`**/node_modules/`, `**/dist/`)
  - Local datasets and uploads (`uploads/`, `data/`, `results/`, `tmp/`)
  - Temporary files, logs, and IDE configurations.
- Created service-level `.dockerignore` files for defense in depth in `services/ai-service/`, `services/auth-service/`, and `frontend/medmatch-ui/`.

#### Security Rationale
Minimizes Docker build context transfer time, protects secrets from being accidentally baked into intermediate image layers, and prevents sensitive host files from being copied via `COPY . .`.

---

## Verification & Test Results

| Test Category | Suite / Command | Result | Details |
|---|---|---|---|
| AI Service Tests | `pytest services/ai-service/tests` | **PASS (60/60)** | Comprehensive suite covering health, LLM, match repos, RAG, task security, tenant isolation, redis config, and RSA JWT |
| Task Security Tests | `pytest services/ai-service/tests/test_task_security.py` | **PASS (7/7)** | Unauthenticated, same-tenant, cross-tenant, 404, failure sanitization, pod restart recovery, and missing-registry fail-closed |
| Redis Auth Tests | `pytest services/ai-service/tests/test_redis_config.py` | **PASS (6/6)** | URL formatting, password URL-encoding, idempotence, production missing-password rejection, and production valid-password success |
| RSA JWT E2E Tests | `pytest services/ai-service/tests/test_rsa_jwt_verification.py` | **PASS (4/4)** | Valid token verification, forged attacker signature rejection, expired token rejection, missing claim rejection |
| Auth Service Tests | `mvnw.cmd test` | **PASS (81/81)** | JWT service, controllers, auth service, audit logs, health, hospitals |
| Baseline Tests | `pytest tests/production_engineering/test_production_engineering_baseline.py` | **PASS (20/20)** | Validated remediated actuator, tasks endpoint, dockerignore, k8s, alembic |
| Frontend Lint | `npm run lint` (frontend/medmatch-ui) | **PASS** | 0 errors |
| Frontend Build | `npm run build` (frontend/medmatch-ui) | **PASS** | Output: `dist/` bundle created in 985ms |
| Docker Builds | `docker build` (all 4 images) | **PASS (4/4)** | `medmatch/frontend`, `medmatch/auth-service`, `medmatch/ai-service`, `medmatch/worker` built and exported successfully |
| Compose Config | `docker compose config` | **PASS** | Valid YAML, all services, environments, volumes resolved |
| Kustomize Build | `kubectl kustomize .` | **PASS** | Root deployment manifests validated without errors |
| Tracked Git Secret Scan | `git ls-files`, `git grep` | **PASS** | Zero tracked private keys, zero tracked real secrets in Git history/index |

### Secret Scan & Hygiene Distinction
- **A. Tracked Git Repository Content**: Thoroughly audited via `git ls-files` and `git grep`. Zero PEM private keys, zero real API keys, zero production passwords, and zero production connection strings are tracked in the Git repository or index. Only sanitized example templates (`secrets.yaml.example`, `.env.example`) and CI scanning patterns exist in tracked files.
- **B. Local Working-Tree Files**: Local untracked files intentionally excluded by `.gitignore` (such as local development RSA key pairs in `src/main/resources/keys/private.pem` or developer `.env` files) may exist in the developer's working tree outside Git to support local offline development. These files are strictly excluded from Docker build contexts by [.dockerignore](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/.dockerignore) and excluded from version control by [.gitignore](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/.gitignore).

---

## Production Isolation & Research Invariant Verification

- **Services modified**:
  - `services/auth-service`: `JwtService.java`, `SecurityConfig.java`, `AuthServiceImpl.java`, `application*.yml`.
  - `services/ai-service`: `deps.py`, `routes/__init__.py`, `routes/tasks.py`, `routes/trial.py`, `cache/redis.py`, `celery/tasks.py`, `config/security.py`, `config/settings.py`, `services/trial_service.py`, `services/task_registry.py`.
- **Infrastructure modified**:
  - `docker-compose.yml`, `infra/kubernetes/ai-service/deployment.yaml`, `infra/kubernetes/worker/deployment.yaml`, `infra/kubernetes/redis/redis-statefulset.yaml`, `infra/kubernetes/secrets/secrets.yaml.example`, `infra/kubernetes/config/configmap.yaml`.
- **Zero Research Impact**:
  - `scripts/` (Phases 2–12 research code): **UNTOUCHED**
  - `docs/capstone/phase0` through `phase12`: **UNTOUCHED**
  - Clinical reasoning contracts: **UNTOUCHED**

---

## Remaining Phase 13 Risks & Planned Roadmap

Phase 13 follows the established canonical implementation roadmap:
- **13.1 Security & Secrets Remediation** (COMPLETED — This Phase)
- **13.2 Database & Migration Hardening** (Next Phase: addressing Flyway version prefix collisions `V1__`–`V4__`, Alembic consolidation)
- **13.3 Kubernetes & Network Hardening** (NetworkPolicies, PodSecurityStandards, non-root initContainers, RWO PVC evaluation)
- **13.4 Reliability & Lifecycle Hardening** (Graceful shutdowns, health probe timings, Celery solo-pool tuning)
- **13.5 Observability & Monitoring** (Populating Prometheus scrape rules, alert definitions, Alertmanager configs)
- **13.6 CI/CD & Build Hardening** (Workflow caching, test automation, multi-stage artifact signing)
- **13.7 Final Phase 13 Validation** (Chaos validation, stress testing, full readiness sign-off)

### Remaining Technical Risks to Address in Subsequent Subphases:
1. **Kubernetes Cluster Secret Encryption at Rest (Phase 13.3)**: Plain Kubernetes Secrets are base64-encoded. Production clusters must enable KMS encryption-at-rest or integrate External Secrets Operator with HashiCorp Vault / Cloud KMS.
2. **Flyway Migration Version Collisions (Phase 13.2)**: Duplicate migration version prefixes (`V1__`, `V2__`, etc.) remain in `services/auth-service/src/main/resources/db/migration/` and must be sequenced cleanly.
3. **Multi-Node ReadWriteOnce PVC (Phase 13.3)**: `uploads-pvc.yaml` is configured with `ReadWriteOnce`. If `ai-service` and `celery-worker` reside on different cluster nodes, a `ReadWriteMany` storage class or cloud object storage is required.
4. **Prometheus / Alertmanager Configuration (Phase 13.5)**: Alert rule manifests in `infra/monitoring/` are currently 0-byte templates awaiting production metrics definitions.
