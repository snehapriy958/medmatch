# Phase 13.3: Docker Remediation Implementation Report

**Checkpoint:** `bfb17e1` — *feat: harden database migration execution*
**Branch:** `capstone/phase-13-production-engineering`
**Status:** IMPLEMENTATION COMPLETE — PENDING REVIEW

---

## 1. Executive Summary

This report documents the physical implementation of the Phase 13.3 Docker and container remediations for MedMatch V2. Building upon the Phase 13.3 Docker Audit (`docs/capstone/phase13_docker_container_audit.md`), Remediation Design Review (`docs/capstone/phase13_docker_remediation_design.md`), and Pre-Implementation Targeted Verification (`docs/capstone/phase13_docker_targeted_verification.md`), five confirmed remediation items (covering six issue identifiers: CONT-01, CONT-02, CONT-03, CONT-04, CONT-07, and CONT-05) have been implemented and verified.

All changes were strictly constrained to container configurations, Dockerfiles, Kubernetes deployment probes, CI build matrices, and Python dependency definitions. Zero changes were made to application business logic, Flyway or Alembic migrations, database schemas, or authentication logic.

---

## 2. Implemented Remediations

### CONT-01 — Docker Compose PostgreSQL Volume Declaration
- **Original Finding:** `docker-compose.yml` declared the `postgres_data` volume with `external: true` alongside `name: medmatch_postgres_data`. On a fresh clone or any workstation lacking a pre-existing volume named `medmatch_postgres_data`, executing `docker compose up` crashed with a missing volume error.
- **Implementation:** Removed `external: true` from the `postgres_data` volume block in [docker-compose.yml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docker-compose.yml) while retaining `name: medmatch_postgres_data`.
- **Files Changed:**
  - `docker-compose.yml`
- **Validation:**
  - Executed `docker compose config`. The configuration resolved and validated successfully with `name: medmatch_postgres_data` without requiring manual pre-creation of external Docker volumes.
- **Residual Risk:** Low. Existing developer machines with `medmatch_postgres_data` continue to attach to the volume without data loss; new checkouts automatically initialize the volume.
- **Status:** **RESOLVED**

---

### CONT-02 — Docker Compose Healthchecks for AI Service
- **Original Finding:** In `docker-compose.yml`, `ai-service` lacked a healthcheck definition, while `frontend` depended on `ai-service` via `condition: service_started`. Because Uvicorn and model initialization take 5–15 seconds, Nginx reverse-proxy routed incoming requests prematurely, leading to 502 Bad Gateway responses.
- **Implementation:**
  1. Added a container healthcheck to `ai-service` in [docker-compose.yml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docker-compose.yml) testing `/api/health/ready` using Python standard library `urllib.request` (avoiding external `curl`/`wget` dependencies inside `python:3.12-slim`):
     ```yaml
     healthcheck:
       test:
         [
           "CMD",
           "python",
           "-c",
           "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/ready')"
         ]
       interval: 10s
       timeout: 5s
       retries: 5
       start_period: 40s
     ```
  2. Updated `frontend.depends_on.ai-service` condition from `service_started` to `service_healthy`.
  3. No healthcheck was added to `celery-worker` in Compose, as it is a consumer with no dependent HTTP callers.
- **Files Changed:**
  - `docker-compose.yml`
- **Validation:**
  - `docker compose config` parsed and validated the healthcheck configuration and dependency condition cleanly.
- **Residual Risk:** Low. `start_period: 40s` provides sufficient grace time for slow initial model loads on low-spec development machines before healthcheck retries increment failure counts.
- **Status:** **RESOLVED**

---

### CONT-03 — Redundant Hugging Face Model Download in Docker Build
- **Original Finding:** `infra/docker/ai-service.Dockerfile` executed `RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"` in Stage 1 and copied `/opt/huggingface` into Stage 2. However, application code in `EmbeddingModel` exclusively loads the local git-tracked model from `/app/models/all-MiniLM-L6-v2`. The remote download bloated images by ~100MB+ with unreferenced files and added network failure risk to Docker builds.
- **Implementation:**
  1. Removed the Stage 1 remote model download from [infra/docker/ai-service.Dockerfile](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/docker/ai-service.Dockerfile).
  2. Removed `COPY --from=build /opt/huggingface /opt/huggingface` from Stage 2.
  3. Aligned `HF_HOME` and `TRANSFORMERS_CACHE` environment variables in `ai-service.Dockerfile` to `/tmp/huggingface` (matching Kubernetes and Compose configurations and ensuring writeability for non-root UID 1000).
  4. Added `--no-cache-dir` to `pip install` commands in the build stage.
- **Files Changed:**
  - `infra/docker/ai-service.Dockerfile`
- **Validation:**
  - Zero references to `/opt/huggingface` remain in `infra/docker/`. Model directory `services/ai-service/models/all-MiniLM-L6-v2` is preserved and baked into `/app/models`.
- **Residual Risk:** Very Low. Application embedding loader was verified to load from `/app/models/all-MiniLM-L6-v2` exclusively.
- **Status:** **RESOLVED**

---

### CONT-04 — Kubernetes AI Service StartupProbe
- **Original Finding:** In `infra/kubernetes/ai-service/deployment.yaml`, only `livenessProbe` (`initialDelaySeconds: 30`, `failureThreshold: 3`) and `readinessProbe` were defined. On throttled nodes or under cold startup, PyTorch and SentenceTransformer initialization could exceed 30–75 seconds, triggering premature container termination by kubelet before the app reached a healthy state.
- **Implementation:** Added a dedicated `startupProbe` to [infra/kubernetes/ai-service/deployment.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/ai-service/deployment.yaml) targeting `/api/health/live`:
  ```yaml
  startupProbe:
    httpGet:
      path: /api/health/live
      port: 8000
    initialDelaySeconds: 10
    periodSeconds: 5
    timeoutSeconds: 5
    failureThreshold: 30
  ```
  This allows up to `10s + (5s * 30) = 160s` for cold startup without loosening the steady-state liveness (`15s` period, `3` failure threshold) or readiness probes.
- **Files Changed:**
  - `infra/kubernetes/ai-service/deployment.yaml`
- **Validation:**
  - `kubectl kustomize .` produced valid Kubernetes YAML manifests containing the `startupProbe`.
  - `kubectl apply --dry-run=client -k .` confirmed syntactic correctness across all deployment resources.
- **Residual Risk:** Very Low. Protects cold start without altering application behavior or steady-state recovery semantics.
- **Status:** **RESOLVED**

---

### CONT-07 — Test Dependencies Separation
- **Original Finding:** `services/ai-service/requirements.txt` included `pytest` and `pytest-mock`. As a result, test frameworks and test dependencies were installed into production container images, enlarging image size and expanding the attack surface.
- **Implementation:**
  1. Removed `pytest` and `pytest-mock` from [services/ai-service/requirements.txt](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/requirements.txt).
  2. Created [services/ai-service/requirements-dev.txt](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/requirements-dev.txt):
     ```text
     -r requirements.txt
     pytest
     pytest-mock
     ```
  3. Inspected `.github/workflows/ci.yaml`: CI runs `pip install -r requirements.txt` followed by `python -m compileall app`. Because production application code has zero imports of `pytest`, CI continues to compile and pass without installing test dependencies.
- **Files Changed:**
  - `services/ai-service/requirements.txt`
  - `services/ai-service/requirements-dev.txt`
- **Validation:**
  - Grep search confirmed zero occurrences of `pytest` in `services/ai-service/requirements.txt`.
  - Development requirements file confirmed present and referencing `-r requirements.txt`.
  - Local AI tests continue to execute via the existing test runner.
- **Residual Risk:** Very Low. Clean separation follows Python best practices.
- **Status:** **RESOLVED**

---

### CONT-05 — Consolidate Celery Worker Container Image
- **Original Finding:** `infra/docker/worker.Dockerfile` was an 80% redundant clone of `infra/docker/ai-service.Dockerfile`. Maintaining two separate Dockerfiles led to drift (e.g. `worker.Dockerfile` omitted Alembic files and initContainer dependencies), doubled CI build times, and increased storage overhead.
- **Implementation:**
  1. Deleted duplicate `infra/docker/worker.Dockerfile`.
  2. Updated [.github/workflows/docker-build.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/.github/workflows/docker-build.yaml) matrix entry for `worker` to build from `file: infra/docker/ai-service.Dockerfile`. This ensures GHCR continues to publish the expected image `ghcr.io/snehapriy958/medmatch-worker:latest` without breaking downstream consumers.
  3. Updated [docker-compose.yml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docker-compose.yml) `celery-worker` service to build from `infra/docker/ai-service.Dockerfile` with explicit command override:
     ```yaml
     command:
       - celery
       - -A
       - app.celery.celery_app
       - worker
       - --loglevel=info
       - --concurrency=1
       - --pool=solo
     ```
  4. Verified `infra/kubernetes/worker/deployment.yaml`: Both the `wait-for-ai-migrations` initContainer and the `medmatch-worker` main container use `image: ghcr.io/snehapriy958/medmatch-worker:latest`, which now builds from the consolidated AI image containing Python, Celery, psycopg2, and the local models.
- **Files Changed:**
  - `infra/docker/worker.Dockerfile` (deleted)
  - `.github/workflows/docker-build.yaml`
  - `docker-compose.yml`
- **Validation:**
  - `docker compose config` validated successfully.
  - `kubectl kustomize .` and `kubectl apply --dry-run=client -k .` confirmed both worker and AI service deployments are valid.
  - Zero active references to `worker.Dockerfile` remain in CI/CD workflows or Compose definitions.
- **Residual Risk:** Low. Worker runtime command is explicitly declared in both Compose and Kubernetes manifests, overriding Uvicorn default CMD. UID 1000 and non-root execution are preserved.
- **Status:** **RESOLVED**

---

## 3. Explicitly Deferred Findings

As directed in the remediation design and implementation specification, the following findings are explicitly deferred and were **not** modified during Phase 13.3:

1. **CONT-06 — Mutable Image Tags in Kubernetes Manifests (`:latest`, `:phase2-migrations`)**
   - *Reason for Deferral:* Tag immutability (replacing `:latest` with git commit SHAs like `:bfb17e1`) is part of CI/CD release pipeline hardening and should be automated via Kustomize image transformers during deployment workflow execution, rather than hardcoded during container configuration cleanup.
   - *Target Phase:* Release Engineering / Deployment Pipeline Hardening.

2. **CONT-08 — Worker InitContainer Root Permissions (`init-uploads`)**
   - *Reason for Deferral:* Changing the `init-uploads` initContainer security context (`runAsUser: 0`, `chmod 777`) requires coordination with PVC volume ownership, `fsGroup`, and storage class permissions.
   - *Target Phase:* Phase 13.4 Storage & Volume Permissions Hardening.

3. **CONT-10 — Celery Solo Pool Probe Behavior**
   - *Reason for Deferral:* Modifying or replacing the `celery inspect ping` exec probe requires task-load concurrency testing to measure whether probes timeout under heavy Celery task execution.
   - *Target Phase:* Phase 13.4 after load/concurrency benchmarking.

---

## 4. Verification Suite Results

| Step | Check | Target | Result | Notes |
|:---|:---|:---|:---|:---|
| 1 | `git diff --check` | Repository root | **PASS** | Clean diff with zero whitespace/formatting errors |
| 2 | `docker compose config` | Repository root | **PASS** | Validated `medmatch_postgres_data` volume, AI healthcheck, worker image consolidation |
| 3 | `kubectl kustomize .` | Repository root | **PASS** | Cleanly synthesized all Kubernetes resources including `startupProbe` |
| 3b | `kubectl apply --dry-run=client -k .` | Repository root | **PASS** | Syntactically valid across deployments, jobs, network policies, and statefulsets |
| 4 | AI Service Pytest | `services/ai-service` | **66 PASS, 0 FAIL** | 66 tests passed, 0 failures, 0 errors, 0 skipped (`PYTHONPATH=services/ai-service python -m pytest services/ai-service/tests -q`) |
| 5 | Auth Service Maven | `services/auth-service` | **PASS** | 81 tests run, 0 failures, 0 errors, BUILD SUCCESS |
| 6a | Frontend Lint | `frontend/medmatch-ui` | **PASS** | ESLint passed with 0 errors |
| 6b | Frontend Build | `frontend/medmatch-ui` | **PASS** | Vite production build generated in `dist/` |
| 7 | CI Workflow Inspection | `.github/workflows/docker-build.yaml` | **PASS** | Worker matrix references `infra/docker/ai-service.Dockerfile` |
| 8 | Codebase Target Search | Repository-wide | **PASS** | Zero dangling `worker.Dockerfile` references in build configs; zero `/opt/huggingface` in Dockerfiles; `pytest` removed from prod `requirements.txt` |
| 9 | Scope Guard | Working tree | **PASS** | Only the 6 targeted files modified/deleted + 1 dev requirements file created |

---

## 5. Scope Guard Compliance

- **Modified Files:**
  - `.github/workflows/docker-build.yaml`
  - `docker-compose.yml`
  - `infra/docker/ai-service.Dockerfile`
  - `infra/docker/worker.Dockerfile` (deleted)
  - `infra/kubernetes/ai-service/deployment.yaml`
  - `services/ai-service/requirements.txt`
- **Untracked Files:**
  - `services/ai-service/requirements-dev.txt`
  - `docs/capstone/phase13_docker_remediation_implementation.md`
  - `results/phase13/docker_remediation_implementation_summary.json`
- **Strictly Preserved (Zero modifications):**
  - Application business logic
  - Database migrations (Flyway / Alembic)
  - Database schemas
  - Authentication logic
  - Redis architecture
  - Celery tasks

---

## 6. Phase 13.3 Final Docker Validation Results

An end-to-end physical Docker validation was executed against the modified codebase to confirm runtime behavior, image construction, and container gating:

### 1. Docker Build Result
- **Command:** `docker compose build ai-service celery-worker`
- **Results:**
  - `medmatch_v2-ai-service:latest`: Built successfully from `infra/docker/ai-service.Dockerfile` (cached multi-stage build, 0 errors).
  - `medmatch_v2-celery-worker:latest`: Built successfully from `infra/docker/ai-service.Dockerfile` (cached multi-stage build, 0 errors).
  - Consolidated worker image confirmed to build directly from `infra/docker/ai-service.Dockerfile`.
  - Non-root user verified in resulting image: `uid=1000(fastapi) gid=1000(fastapi)`.
  - Local model files verified present: `/app/models/all-MiniLM-L6-v2` contains `model.safetensors` (90.8MB), `config.json`, `tokenizer.json`, and vocabularies.
  - Zero missing `COPY` sources; zero dependency installation failures.

### 2. AI Actual Startup-to-Healthy Time
- **Validation Stack:** `docker compose up -d postgres redis ai-service`
- **Execution Log:**
  - Container Start: `2026-09-29T10:24:30.347318055Z`
  - Healthcheck Probe 1 (`10:24:35Z`): Connection refused (Uvicorn / model initialization in progress).
  - Healthcheck Probe 2 (`10:24:41Z`): Exit Code 0 (`/api/health/ready` responded HTTP 200 with all subsystem checks `UP`).
  - Container Status Transition: `starting` -> `healthy` at `2026-09-29T10:24:41.442938885Z`.
  - **Actual Startup-to-Healthy Duration:** **11.0 seconds**.
  - **Verdict:** The configured `start_period: 40s` provides a robust ~3.6x safety buffer for production while avoiding premature healthcheck retry exhaustion.
  - Ephemeral test containers cleanly stopped and removed post-validation.

### 3. Worker Effective Command
- **Resolved Compose Configuration:**
  - `ai-service`: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (default CMD from `ai-service.Dockerfile`).
  - `celery-worker`: `["celery", "-A", "app.celery.celery_app", "worker", "--loglevel=info", "--concurrency=1", "--pool=solo"]` (explicit command override in `docker-compose.yml`).
  - **Verdict:** Verified that `celery-worker` does NOT inherit Uvicorn and explicitly launches Celery worker.

### 4. Worker Image & Manifest Verification
- **Kubernetes Manifest (`infra/kubernetes/worker/deployment.yaml`):**
  - Main container `medmatch-worker`: `image: ghcr.io/snehapriy958/medmatch-worker:latest`.
  - InitContainer `wait-for-ai-migrations`: `image: ghcr.io/snehapriy958/medmatch-worker:latest`.
- **CI Workflow (`.github/workflows/docker-build.yaml`):**
  - Worker matrix entry: `{ name: worker, file: infra/docker/ai-service.Dockerfile }`.
  - Image published: `ghcr.io/${{ github.repository_owner }}/medmatch-worker:latest`.
  - **Verdict:** Worker images across Kubernetes and CI are fully aligned and built from `infra/docker/ai-service.Dockerfile`.

### 5. Frontend Dependency Verification
- **Resolved Compose Configuration:**
  ```yaml
  frontend:
    depends_on:
      ai-service:
        condition: service_healthy
        required: true
      auth-service:
        condition: service_healthy
        required: true
  ```
  - **Verdict:** Frontend container waits for AI service to reach `healthy` before accepting web traffic.

### 6. Test Dependency Separation
- `services/ai-service/requirements.txt`: Confirmed zero occurrences of `pytest` or `pytest-mock`.
- `services/ai-service/requirements-dev.txt`: Confirmed `-r requirements.txt`, `pytest`, `pytest-mock`.
- Production image verified clean of test framework packages.

### 7. Cleanliness and Hygiene Checks
- `git diff --check`: 0 errors.
- `git diff --stat`: 6 files changed (42 insertions, 81 deletions).
- `git grep -n "worker.Dockerfile"`: 0 matches across `.github`, `infra/docker`, `infra/kubernetes`, and `docker-compose.yml`.
- `Select-String -Path "infra/docker/*" -Pattern "/opt/huggingface"`: 0 matches.
