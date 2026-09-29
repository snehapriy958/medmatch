# Phase 13 — Production Engineering Baseline Audit

## 1. Executive Summary

This document establishes the comprehensive technical audit of the **MedMatch** system across all infrastructure, containerization, orchestration, database migration, asynchronous processing, API resilience, AI operational reliability, observability, logging, and security dimensions.

The system was evaluated directly from the repository baseline at checkpoint `2b61977` on branch `capstone/phase-13-production-engineering`. Findings are grounded strictly in code, manifests, and runtime behavior rather than architectural claims or assumptions.

> [!IMPORTANT]
> **Audit Status**: **Phase 13 Audit Complete — Production Hardening Required**.
> This audit does **not** assert that MedMatch is production-ready. Substantial production engineering hardening is required before the platform can safely serve clinical workloads.

---

## 2. Containerization Audit (Docker)

### 2.1 Inventory & Base Images
| Component | Dockerfile | Base Image Stage 1 (Build) | Base Image Stage 2 (Runtime) | User Execution |
| :--- | :--- | :--- | :--- | :--- |
| **ai-service** | `infra/docker/ai-service.Dockerfile` | `python:3.12-slim` | `python:3.12-slim` | Non-root (`fastapi:1000`) |
| **auth-service** | `infra/docker/auth-service.Dockerfile` | `eclipse-temurin:21-jdk-jammy` | `eclipse-temurin:21-jre-jammy` | Non-root (`spring:1000`) |
| **frontend** | `infra/docker/frontend.Dockerfile` | `node:22-alpine` | `nginx:1.27-alpine` | Non-root (`nginx:101`) |
| **celery-worker** | `infra/docker/worker.Dockerfile` | `python:3.12-slim` | `python:3.12-slim` | Non-root (`celery:1000`) |

### 2.2 Key Container Findings
1. **Absence of `.dockerignore` Across Entire Repository**:
   - Neither the root directory nor subdirectories contain a `.dockerignore` file (verified via filesystem scan).
   - When building images (`docker build -f infra/docker/ai-service.Dockerfile .`), the entire repository context is sent to the Docker daemon, including `.env`, `.git` (hundreds of MB), `.venv`, `tests/`, `running-auth-app.jar` (68MB), and local caches.
   - **Risk**: Slow build cycles, accidental inclusion of local secrets (`.env`) into image layers if `COPY . .` patterns are used, and cache invalidation on any uncommitted file edit.
2. **Missing `HEALTHCHECK` Directives**:
   - None of the 4 Dockerfiles declare an internal `HEALTHCHECK` instruction. Containers rely solely on external runtime orchestrators (Compose / Kubernetes) for liveness/readiness detection.
3. **Embedding Model Loading Path Mismatch**:
   - `ai-service.Dockerfile` and `worker.Dockerfile` download `sentence-transformers/all-MiniLM-L6-v2` during image build into `/opt/huggingface`.
   - However, `services/ai-service/app/embeddings/model.py` (lines 25–29) hardcodes:
     ```python
     MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "all-MiniLM-L6-v2"
     ```
   - If `models/all-MiniLM-L6-v2` is not present in the runtime container image, `EmbeddingModel` throws a `RuntimeError("Embedding model not found")`.
4. **Duplicate Worker Image Definition**:
   - `worker.Dockerfile` is an almost exact clone of `ai-service.Dockerfile` with only the default `CMD` altered. Maintaining two separate Dockerfiles creates maintenance drift.

---

## 3. Docker Compose Topology Audit

### 3.1 Topology & Dependency Ordering
The root `docker-compose.yml` orchestrates 8 services:
1. `postgres` (`pgvector/pgvector:pg17`)
2. `redis` (`redis:8-alpine`)
3. `auth-migrate` (`flyway/flyway:10-alpine`)
4. `ai-migrate` (build `infra/docker/ai-service.Dockerfile`)
5. `auth-service` (build `infra/docker/auth-service.Dockerfile`)
6. `ai-service` (build `infra/docker/ai-service.Dockerfile`)
7. `celery-worker` (build `infra/docker/worker.Dockerfile`)
8. `frontend` (build `infra/docker/frontend.Dockerfile`)

### 3.2 Key Compose Findings
1. **External Volume Requirement Failure Hazard**:
   - `docker-compose.yml` lines 295–298 declare `postgres_data` with `external: true`, `name: medmatch_postgres_data`.
   - Running `docker-compose up` on a clean host immediately halts with: `volume medmatch_postgres_data declared as external, but could not be found`.
2. **Missing Healthcheck on `ai-service`**:
   - `ai-service` does NOT define a `healthcheck` block in `docker-compose.yml`.
   - Consequently, `frontend` depends on `ai-service` via `condition: service_started` (line 273), not `service_healthy`.
   - **Race Condition**: `frontend` starts reverse-proxying immediately upon `ai-service` process creation, while `ai-service` is still establishing database connection pools, executing Alembic verification, or initializing caches, resulting in initial HTTP 502 Bad Gateway responses.
3. **Development Profile Injected in Production Service**:
   - `auth-service` has `SPRING_PROFILES_ACTIVE: dev` explicitly hardcoded in `docker-compose.yml` line 152.
4. **Flyway Migration Directory Mount Active Blocker**:
   - `auth-migrate` mounts `./services/auth-service/src/main/resources/db/migration:/flyway/sql:ro`.
   - That directory contains duplicate version prefixes (`V1` through `V4`). When Flyway scans `/flyway/sql`, it terminates with a version collision error (`Found more than one migration with version 1`). This is an **active deployment blocker** under Compose.
5. **Completely Absent Observability Services**:
   - Prometheus, Grafana, and Alertmanager are not declared in `docker-compose.yml`. There is zero runtime observability under Compose.

---

## 4. Kubernetes Manifest Audit

### 4.1 Topology & Ingress
- Entry Point: Root [kustomization.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/kustomization.yaml).
- Deprecated: [infra/kubernetes/kustomization.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/kustomization.yaml) (retained with explanation).
- Orphan: [infra/k8s/worker-deployment.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/k8s/worker-deployment.yaml) (0-byte empty file).

### 4.2 Critical Findings
1. **NetworkPolicy Outbound & Cross-Pod Blockade (Critical)**:
   - `infra/kubernetes/network/network-policy.yaml`:
     - `default-deny-all` blocks all inbound and outbound traffic.
     - `ai-service-policy`: Ingress is permitted **only** from `auth-service`. Ingress from `ingress-nginx` or `frontend` is **BLOCKED**.
     - `ai-service-policy`: Egress is permitted **only** to `postgres:5432` and `redis:6379`. All outbound HTTPS (port 443) traffic is **BLOCKED**. This completely cuts off Gemini API (`generativelanguage.googleapis.com`) calls!
     - `worker-policy`: Egress to external LLM / HuggingFace endpoints is likewise **BLOCKED**.
     - `frontend-policy`: Egress is permitted **only** to `auth-service:8081`. Reverse proxy traffic to `ai-service:8000` is **BLOCKED**.
2. **Ingress Routing Architecture Discrepancy**:
   - `infra/kubernetes/ingress.yaml` routes:
     - `/api` -> `auth-service:8081`
     - `/` -> `frontend-service:5173`
   - Client calls to `/api/patients`, `/api/trials`, and `/api/matching` hitting Ingress are routed to `auth-service`, which does not recognize these routes, returning HTTP 404!
   - Ingress completely omits `tls:` secret configuration, despite specifying `nginx.ingress.kubernetes.io/ssl-redirect: "true"`.
3. **Multi-Node Volume Mount Failure Risk (`ReadWriteOnce`)**:
   - `infra/kubernetes/storage/uploads-pvc.yaml` specifies `accessModes: [ReadWriteOnce]` backed by `storageClassName: medmatch-storage` (`provisioner: rancher.io/local-path`).
   - Both `ai-service` and `worker` mount `medmatch-uploads-pvc` at `/app/uploads`.
   - Because `rancher.io/local-path` is a single-node hostPath provisioner, multi-node RWX is unsupported. If the scheduler places `ai-service` on Node A and `worker` on Node B, Node B will fail to attach the volume with a `Multi-Attach error`.
   - **Remediation Options to Evaluate in Later Implementation**:
     - *Option A*: RWX shared storage (e.g., NFS, AWS EFS, GCP Filestore).
     - *Option B*: Object storage (e.g., MinIO, S3, GCS with pre-signed URLs, eliminating shared POSIX disk requirements).
     - *Option C*: Scheduling co-location (e.g., Kubernetes `podAffinity` forcing worker and AI service onto the same physical node).
     - *Option D*: Hybrid temporary-storage design (e.g., streaming file bytes directly through the async broker/task payload for files under 10MB).
4. **Privilege Escalation in Worker InitContainer**:
   - `infra/kubernetes/worker/deployment.yaml` lines 44–58 runs `initContainers` named `init-uploads` with `busybox` and `runAsUser: 0` (root) executing `chmod 777 /app/uploads`.
5. **Probe Configuration vs. Model Warm-up**:
   - `ai-service/deployment.yaml`:
     - `readinessProbe`: `initialDelaySeconds: 15`, `periodSeconds: 10`, `failureThreshold: 3` (window: 45 seconds).
     - `livenessProbe`: `initialDelaySeconds: 30`, `periodSeconds: 15`, `failureThreshold: 3` (window: 75 seconds).
     - Startup probe: **MISSING**.
     - As demonstrated in benchmark runs, loading `SentenceTransformer` requires ~72–75 seconds. The liveness probe expires before model initialization completes if loaded during startup, triggering a CrashLoopBackOff.
6. **Autoscaling Inconsistency**:
   - `infra/kubernetes/hpa.yaml` defines `HorizontalPodAutoscaler` only for `worker`.
   - `worker` deployment specifies `strategy: type: Recreate` with `replicas: 1` and `--pool=solo`, which conflicts with horizontal autoscaling dynamics.
   - `ai-service`, `auth-service`, and `frontend` have no HPA definitions.

---

## 5. Database & Migration Ownership & Reliability

### 5.1 Migration Ownership & Inventory
- **Auth Service Migration System**: Flyway (Java / Spring Boot).
  - Source directory: `services/auth-service/src/main/resources/db/migration`
  - Total files in directory: 20 SQL files.
- **AI Service Migration System**: Alembic (Python / SQLAlchemy).
  - Source directory: `services/ai-service/alembic/versions`
  - Total files in directory: 12 migration files.

### 5.2 Consumed vs. Orphaned Migrations
1. **Kubernetes Execution**:
   - `auth-migrate` Job: Consumes **ONLY 4 files** (`V1__create_roles_table.sql`, `V2__create_hospitals_table.sql`, `V3__create_users_table.sql`, `V4__create_audit_logs_table.sql`) generated into a ConfigMap by root `kustomization.yaml`.
   - **Orphaned from Kubernetes**: Versions `V5` through `V16` (12 migration scripts: adding columns to audit logs, hospitals, roles, users) are **completely omitted** from the Kubernetes ConfigMap and never executed.
   - `ai-migrate` Job: Consumes `0001` through `0008`, `2248598b8f7e`, `01efd2b23442`, `3f3884863f27`, and `6f0604b23df6`. Authoritative single head: `6f0604b23df6 (head)`.
2. **Docker Compose Execution**:
   - `auth-migrate` Container: Mounts the entire `services/auth-service/src/main/resources/db/migration` directory directly.
   - **Active Blocker**: The directory contains colliding duplicate version prefixes:
     - `V1__create_hospitals.sql` (226 B) vs `V1__create_roles_table.sql` (771 B)
     - `V2__create_hospitals_table.sql` (889 B) vs `V2__create_roles.sql` (379 B)
     - `V3__create_users.sql` (670 B) vs `V3__create_users_table.sql` (1081 B)
     - `V4__create_audit_logs.sql` (249 B) vs `V4__create_audit_logs_table.sql` (1865 B)
     Flyway fails on startup with `FlywayException: Found more than one migration with version 1`.
   - `ai-migrate` Container: Runs `alembic upgrade head` cleanly against `services/ai-service/alembic`.
3. **Orphaned Root Alembic Directory**:
   - `alembic/versions` at repository root contains 3 partial files (`01efd2b23442`, `2248598b8f7e`, `3f3884863f27`) where `2248598b8f7e` defines `down_revision = None`.
   - No `alembic.ini` exists at root. This entire directory is orphaned and unconsumed.

### 5.3 High Availability & Backup Status
- PostgreSQL is deployed as a single StatefulSet replica with no read replicas, no Patroni / Stolon failover, and no WAL archiving.
- `infra/scripts/backup.sh` is an empty 0-byte placeholder. There is no automated backup or restore mechanism.

---

## 6. Asynchronous / Celery Reliability

### 6.1 Worker Kubernetes Probe Details
In `infra/kubernetes/worker/deployment.yaml`:
```yaml
livenessProbe:
  exec:
    command: ["celery", "-A", "app.celery.celery_app", "inspect", "ping"]
  initialDelaySeconds: 120
  periodSeconds: 60
  timeoutSeconds: 30
  failureThreshold: 5

readinessProbe:
  exec:
    command: ["celery", "-A", "app.celery.celery_app", "inspect", "ping"]
  initialDelaySeconds: 60
  periodSeconds: 60
  timeoutSeconds: 30
  failureThreshold: 5
```
Worker Command:
`["celery", "-A", "app.celery.celery_app", "worker", "--loglevel=info", "--concurrency=1", "--pool=solo"]`

### 6.2 Probe Failure Mechanics Under `--pool=solo`
- The probe command spawns a new Python process that publishes a broadcast ping across the Redis broker.
- Because the worker runs with `--pool=solo`, task execution runs synchronously on the main thread of the worker process without a separate heartbeat or control thread.
- While the worker is actively executing a CPU-intensive embedding task (which can take 60–90 seconds), the Python interpreter is blocked and cannot service the `inspect ping` broadcast message.
- If a task execution or sequence of tasks keeps the worker busy across 5 consecutive probes (window: `5 * 60s = 300s = 5 minutes`), the probe exceeds `failureThreshold: 5` and `timeoutSeconds: 30`.
- **Consequence**: Kubelet restarts the worker container mid-task, aborting the active PDF processing job.

### 6.3 Unauthenticated Task Polling Endpoint
- `GET /api/tasks/{task_id}` in `services/ai-service/app/api/routes/tasks.py` is completely unauthenticated. Anyone with a task UUID can poll task completion status, hospital trial metadata, and internal error traces.

---

## 7. API Reliability Audit

### 7.1 FastAPI (AI Service)
- **Strengths**: Strict Pydantic models for all inputs/outputs, structured exception handlers (`APIException`, `SQLAlchemyError`, `RequestValidationError`, `RateLimitExceeded`), SlowAPI rate limiting on critical routes (`/api/trials`, `/api/matching/search`).
- **Gaps**:
  - `RequestIDMiddleware` generates UUIDs but does not propagate or inherit incoming correlation IDs (`X-Correlation-ID` / `X-Request-ID`).
  - Production logs leak raw debugging data: `trial_service.py` (lines 95–100) and `deps.py` (lines 96–104) contain `print()` statements that dump database session addresses and full user JWT claims to stdout.

### 7.2 Spring Boot (Auth Service)
- **Strengths**: Stateless JWT authentication, MethodSecurity (`@PreAuthorize`), Hibernate validation.
- **Gaps**:
  - `SecurityConfig.java` line 65 marks `/actuator/**` as `.permitAll()`. Unauthenticated users can scrape `/actuator/prometheus`, `/actuator/health`, and `/actuator/info`.
  - In `application.yml`, `org.hibernate.orm.jdbc.bind: TRACE` logs raw SQL bind parameters, leaking sensitive data to logs.

---

## 8. AI Service Operational Reliability

### 8.1 Model Startup & Warm-Up
- The embedding model (`sentence-transformers/all-MiniLM-L6-v2`) is wrapped in a singleton `EmbeddingModel` in `services/ai-service/app/embeddings/model.py`.
- Initialization is **lazy**: `_load_model()` is called only upon first request invocation, NOT during application startup (`lifespan` in `app/main.py`).
- **Measured Latency**: Model loading takes **72.91 seconds** on CPU.
- **Consequence**: The first client making a search or match request experiences a ~75-second hang, triggering gateway timeouts (Nginx proxy timeout is 10s default in standard configs).

### 8.2 External LLM Resilience (Gemini)
- `LLMService` wraps calls in Tenacity with exponential backoff (max 3 retries, max delay 8s).
- **Gaps**:
  - No explicit request timeout passed to `client.models.generate_content`.
  - No circuit breaker pattern implemented.
  - No degraded fallback mode (e.g. deterministic rule-based matching or cached response).
  - Outbound calls fail completely under current Kubernetes `network-policy.yaml`.

---

## 9. Observability & Monitoring Audit

### 9.1 Prometheus, Grafana, Alertmanager
- **Status in Compose**: Completely absent.
- **Status in Kubernetes**:
  - `infra/monitoring/prometheus/prometheus.yaml`: **0-byte empty file**.
  - `infra/monitoring/prometheus/alerts.yaml`: **0-byte empty file**.
  - `infra/monitoring/alertmanager/alertmanager.yaml`: **0-byte empty file**.
  - Grafana manifests / dashboards: **Missing from repository**.
  - ServiceMonitors: Two CRDs exist (`ai-service-monitor`, `auth-service-monitor`), but no Prometheus operator or deployment is present to consume them.

### 9.2 Application Metrics Coverage
| Domain | Metric Name | Type | Status |
| :--- | :--- | :--- | :--- |
| **Matching Requests** | `medmatch_ai_match_requests_total` | Counter | IMPLEMENTED |
| **Matching Latency** | `medmatch_ai_match_duration_seconds` | Histogram | IMPLEMENTED |
| **Embedding Latency** | `medmatch_ai_embedding_duration_seconds` | Histogram | **MISSING** |
| **Retrieval Latency** | `medmatch_ai_retrieval_duration_seconds` | Histogram | **MISSING** |
| **LLM Reasoning Latency** | `medmatch_ai_llm_duration_seconds` | Histogram | **MISSING** |
| **Celery Queue Depth** | `celery_queue_length` | Gauge | **MISSING** |
| **Database Pool Usage** | `sqlalchemy_pool_size` / `hikari_active` | Gauge | **MISSING** |
| **Security Violations** | `auth_token_validation_failures` | Counter | **MISSING** |

---

## 10. Secret & Key Exposure Verification

Every claimed secret and credential was audited across 5 specific dimensions:
A. Exists in working tree
B. Git-tracked (`git ls-files`)
C. Present in Git history (`git log --all -- <file>`)
D. Real credential vs. placeholder
E. Validity / rotation status

| Credential / File | In Working Tree? | Git Tracked? | In Git History? | Type / Value Characteristics | Status & Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `services/auth-service/.../keys/private.pem` | **YES** | **NO** (ignored by `*.pem`) | **NO** | Real 2048-bit RSA Private Key (`MIIEvgIBADAN...`) | Local unencrypted key; rotation/validity unknown. **Credential exposure risk requiring rotation/remediation**. |
| `services/auth-service/.../keys/public.pem` | **YES** | **NO** (ignored by `*.pem`) | **YES** (commits `1686eabc`, `bbcf88fc`) | 2048-bit RSA Public Key | Public key; no secret leakage. |
| `infra/kubernetes/secrets/secrets.yaml` | **YES** | **NO** (ignored by `.gitignore`) | **NO** | Contains RSA private key, Google API key string, and `CHANGE_ME_REDIS_PASSWORD` | Local unencrypted manifest; validity unknown. **Credential exposure risk requiring rotation/remediation**. |
| `infra/kubernetes/secrets/secrets.yaml.example` | **YES** | **YES** | **YES** | Pure placeholder template (`REPLACE_ME_*`) | Sanitized template. No exposure. |
| `.env` (root) | **YES** | **NO** (ignored by `.env`) | **NO** | Contains Google API key string and `DATABASE_PASSWORD=postgres` | Local unencrypted environment file. **Credential exposure risk requiring rotation/remediation**. |
| `services/ai-service/.env` | **YES** | **NO** (ignored by `.env`) | **NO** | Contains local DB connection string (`postgres:postgres`) | Local development environment file. |

> [!NOTE]
> **Correction from Preliminary Audit**: The RSA private key and Kubernetes secrets manifest are **NOT** committed into Git history and are **NOT** tracked in the Git index. They exist exclusively as unencrypted files in the local developer working tree. Therefore, they represent a **credential exposure risk requiring rotation/remediation prior to production**, rather than an established public compromise.

---

## 11. CI/CD Pipeline Audit

1. **GitHub Actions Workflows**:
   - `ci.yaml`: Runs frontend lint/build and auth-service tests. For `ai-service`, it **only runs `python -m compileall app`**—it does NOT run `pytest`!
   - `docker-build.yaml`: Builds and pushes images to GHCR on `main` branch.
   - `deploy.yaml`: Contains only placeholder `echo` commands.
   - `security-scan.yaml`: Runs Trivy fs scan.
2. **Branch Trigger Limitation**:
   - Workflows only trigger on `main` and `phase-0-2-transfer`. Feature and capstone branches (`capstone/*`) bypass CI completely.
3. **Secret Scan Flaw**:
   - `ci.yaml` secret regex step flags `JwtService.java` string replacement as a false positive, causing validation to fail.
