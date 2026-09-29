# Phase 13.3: Pre-Implementation Targeted Verification

**Checkpoint:** `bfb17e1` — *feat: harden database migration execution*
**Branch:** `capstone/phase-13-production-engineering`
**Status:** TARGETED VERIFICATION COMPLETE — IMPLEMENTATION PENDING

---

## 1. Executive Summary

This targeted verification pass evaluates the two potentially risky remediation assumptions identified during the Phase 13.3 Docker/container engineering audit:

1. **Target 1 (CONT-05):** Worker Image Consolidation (merging/replacing `infra/docker/worker.Dockerfile` with `infra/docker/ai-service.Dockerfile`).
2. **Target 2 (CONT-07):** Test Dependencies Separation (moving `pytest` and `pytest-mock` from production `requirements.txt` to `requirements-dev.txt`).

Every question posed in the verification mandate was examined against the actual repository files, Python code symbols, Dockerfiles, GitHub Actions workflows, Compose configurations, and Kubernetes manifests.

---

## 2. Target 1 — Worker Image Consolidation (CONT-05)

### Detailed Question-by-Question Analysis

#### 1. Whether every Python dependency required by Celery exists in the AI image
- **Direct Evidence:**
  - `services/ai-service/requirements.txt` declares `redis` (line 13) and `celery` (line 14).
  - `services/ai-service/app/celery/celery_app.py` imports `from celery import Celery` and `from app.config.settings import settings`.
  - `services/ai-service/app/celery/tasks.py` imports repositories (`TrialRepository`, `CriteriaEmbeddingRepository`, etc.) and services (`EmbeddingService`, `LLMService`, `PDFService`, etc.).
  - All application packages and third-party dependencies (`torch`, `sentence-transformers`, `pymupdf`, `fastapi`, `sqlalchemy`, `psycopg2-binary`, `pgvector`, `google-genai`) are installed by `ai-service.Dockerfile` into `/opt/venv`.
- **Finding:** **YES.** The AI image already installs 100% of the Python dependencies required by Celery and all background tasks.

#### 2. Whether the worker requires any file that the AI Dockerfile does not copy
- **Direct Evidence:**
  - Assets copied by `worker.Dockerfile`:
    - `/opt/venv`
    - `/opt/huggingface`
    - `services/ai-service/app` -> `./app`
    - `services/ai-service/models` -> `./models`
  - Assets copied by `ai-service.Dockerfile`:
    - `/opt/venv`
    - `/opt/huggingface`
    - `services/ai-service/app` -> `./app`
    - `services/ai-service/models` -> `./models`
    - `services/ai-service/alembic.ini` -> `./alembic.ini`
    - `services/ai-service/alembic` -> `./alembic`
- **Finding:** **NO.** `ai-service.Dockerfile` copies a strict superset of what `worker.Dockerfile` copies. There are zero files copied by `worker.Dockerfile` that are omitted in `ai-service.Dockerfile`.

#### 3. Whether the worker requires Alembic files/configuration
- **Direct Evidence:**
  - The Celery worker daemon process (`tasks.py`) uses SQLAlchemy sessions (`SessionLocal()`) for database CRUD operations; it does not execute `alembic upgrade`.
  - However, in `infra/kubernetes/worker/deployment.yaml`, the `wait-for-ai-migrations` initContainer executes a Python script with `psycopg2` checking `alembic_version`.
  - Having `alembic.ini` and `alembic/` inside the container is strictly beneficial: it allows operational inspection commands (e.g. `alembic current`) inside worker pods if needed.
- **Finding:** The worker does not strictly require Alembic to process tasks, but having Alembic files present is completely harmless and operationally beneficial.

#### 4. Whether the worker requires model files
- **Direct Evidence:**
  - In `services/ai-service/app/celery/tasks.py`, `process_trial` instantiates `EmbeddingService`, which instantiates `EmbeddingModel`.
  - `EmbeddingModel` loads `services/ai-service/models/all-MiniLM-L6-v2`.
- **Finding:** **YES.** The worker requires model files. `ai-service.Dockerfile` copies `services/ai-service/models ./models` identically to `worker.Dockerfile`.

#### 5. Whether the worker requires a different USER or filesystem permission setup
- **Direct Evidence:**
  - `ai-service.Dockerfile` sets:
    ```dockerfile
    RUN groupadd --system --gid 1000 fastapi \
        && useradd --system --uid 1000 --gid fastapi --no-create-home fastapi
    USER fastapi
    ```
  - `worker.Dockerfile` sets:
    ```dockerfile
    RUN groupadd --system --gid 1000 celery \
        && useradd --system --uid 1000 --gid celery --no-create-home celery
    USER celery
    ```
  - Both users have identical numeric identifiers: **UID 1000 and GID 1000**.
  - Linux kernel and POSIX filesystem permission checks evaluate UID/GID numbers (1000:1000), not username strings.
  - Celery checks that the user is non-root (`UID != 0`). Both `fastapi` and `celery` satisfy this check identically.
- **Finding:** **NO.** The worker does not require a different user or filesystem permission setup.

#### 6. Whether the worker image is currently used by any Kubernetes initContainer
- **Direct Evidence:**
  - In `infra/kubernetes/worker/deployment.yaml`:
    - Line 60: `initContainer` `wait-for-ai-migrations` specifies `image: ghcr.io/snehapriy958/medmatch-worker:latest`.
    - Line 142: main container specifies `image: ghcr.io/snehapriy958/medmatch-worker:latest`.
  - Both containers run within the same pod specification.
- **Finding:** **YES.** The worker image is used by the `wait-for-ai-migrations` initContainer in `worker/deployment.yaml`. If the pod image is updated to `medmatch-ai-service`, both references must be updated simultaneously.

#### 7. Whether replacing worker.Dockerfile would change the effective runtime filesystem
- **Direct Evidence:**
  - The runtime filesystem of `ai-service.Dockerfile` is identical to `worker.Dockerfile` except for the presence of `/app/alembic.ini` and `/app/alembic/`.
  - Celery does not conflict with Alembic files.
- **Finding:** **NO.** The effective runtime filesystem is 100% compatible.

#### 8. Whether replacing it would affect the existing migration gate
- **Direct Evidence:**
  - The migration gate in `worker/deployment.yaml` (`wait-for-ai-migrations`) runs `python - << 'EOF'` with `import psycopg2` to check `alembic_version == '6f0604b23df6'`.
  - Both images contain Python 3.12 and `psycopg2-binary` in `/opt/venv`.
- **Finding:** **NO.** The migration gate behavior is completely unaffected.

#### 9. Whether the two Dockerfiles are actually functionally equivalent apart from CMD/ENTRYPOINT
- **Direct Evidence:**
  - Both build from `python:3.12-slim`.
  - Both install `build-essential` in build stage.
  - Both install `requirements.txt` into `/opt/venv`.
  - Both bake the local model into `/app/models`.
  - Both run as non-root UID 1000.
  - In `ai-service.Dockerfile`, the default instruction is `CMD ["uvicorn", ...]`, which is trivially overridden in Compose or Kubernetes by passing `command: ["celery", ...]`.
- **Finding:** **YES.** The two Dockerfiles are functionally equivalent.

#### 10. Whether consolidation is safe without changing application code
- **Direct Evidence:**
  - Application code (`celery_app.py`, `tasks.py`, `embedding_service.py`) remains 100% unchanged.
  - In Compose, `celery-worker` specifies `command: ["celery", "-A", "app.celery.celery_app", "worker", ...]`.
  - In Kubernetes, `worker/deployment.yaml` already specifies `command: ["celery", "-A", "app.celery.celery_app", "worker", ...]`.
- **Finding:** **YES.** Consolidation requires zero application code modifications.

---

### CI/CD Workflow Consideration
Inspection of `.github/workflows/docker-build.yaml` lines 20–29 revealed:
```yaml
      matrix:
        include:
          - name: auth-service
            file: infra/docker/auth-service.Dockerfile
          - name: ai-service
            file: infra/docker/ai-service.Dockerfile
          - name: worker
            file: infra/docker/worker.Dockerfile
          - name: frontend
            file: infra/docker/frontend.Dockerfile
```
If `infra/docker/worker.Dockerfile` were deleted outright, GitHub Actions `docker-build.yaml` would fail when attempting to find `infra/docker/worker.Dockerfile`.
**Safe Strategy:** Rather than deleting `worker.Dockerfile`, keep `worker.Dockerfile` as a minimal alias pointing to `ai-service.Dockerfile`, OR update `docker-compose.yml` while maintaining backward compatibility for CI workflows.

### Target 1 Verdict:
**SAFE TO CONSOLIDATE**

---

## 3. Target 2 — Test Dependencies Separation (CONT-07)

### Detailed Question-by-Question Analysis

#### 1. Why pytest is currently in requirements.txt
- **Direct Evidence:**
  - `services/ai-service/requirements.txt` lines 35–37:
    ```text
    # Testing
    pytest
    pytest-mock
    ```
  - It was included in the primary requirements file for early developer convenience, enabling a single `pip install -r requirements.txt` to install both runtime packages and test runners.

#### 2. Whether production Docker runtime actually needs pytest
- **Direct Evidence:**
  - A comprehensive search across `services/ai-service/app/` for `pytest` returned **0 matches**.
  - `pytest` is imported exclusively inside `services/ai-service/tests/`.
  - Neither FastAPI, Uvicorn, SQLAlchemy, Celery, PyMuPDF, nor Google GenAI requires `pytest` at runtime.
- **Finding:** **NO.** The production Docker runtime has zero dependencies on `pytest`.

#### 3. Whether Docker build installs requirements.txt into the final runtime image
- **Direct Evidence:**
  - `ai-service.Dockerfile` Stage 1 executes:
    ```dockerfile
    RUN pip install --upgrade pip \
        && pip install --retries 10 --timeout 120 -r requirements.txt
    ```
  - Stage 2 copies `/opt/venv` from Stage 1 into the runtime container:
    ```dockerfile
    COPY --from=build /opt/venv /opt/venv
    ```
- **Finding:** **YES.** Docker build installs all packages in `requirements.txt` (including `pytest` and `pytest-mock`) into the final production runtime image.

#### 4. Whether CI/tests install requirements.txt directly
- **Direct Evidence:**
  - In `.github/workflows/ci.yaml` lines 69–78:
    ```yaml
      - name: Install dependencies
        working-directory: services/ai-service
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Compile Python sources
        working-directory: services/ai-service
        run: python -m compileall app
    ```
  - `ci.yaml` runs `compileall app` (not `pytest`).
  - Because `app/` does not import `pytest`, `compileall app` will continue to pass without `pytest`.

#### 5. Whether requirements-dev.txt already exists
- **Direct Evidence:**
  - Filesystem inspection confirmed: `Test-Path services/ai-service/requirements-dev.txt` returned **False**.
- **Finding:** **NO.** `requirements-dev.txt` does not exist yet.

#### 6. Whether moving pytest/pytest-mock would break any current workflow
- **Direct Evidence:**
  - In `ci.yaml`: `compileall app` does not import `pytest`.
  - In Docker builds: images build and run without `pytest`.
  - Local developers running tests need `pytest`. If `requirements-dev.txt` contains `-r requirements.txt` followed by `pytest` and `pytest-mock`, running `pip install -r requirements-dev.txt` installs the complete environment.
- **Finding:** **NO.** Moving `pytest`/`pytest-mock` will not break any automated workflow.

#### 7. Exactly which files would need modification
1. `services/ai-service/requirements.txt`: Remove lines 35–37 (`# Testing`, `pytest`, `pytest-mock`).
2. `services/ai-service/requirements-dev.txt` (New File):
   ```text
   -r requirements.txt
   pytest
   pytest-mock
   ```
3. Documentation references (e.g. `docs/runbooks/local-development.md` for developer onboarding).

### Target 2 Verdict:
**SAFE TO MOVE**

---

## 4. Verification Summary Table

| Target | Proposed Remediation | Verdict | Core Finding | Actionable Next Step |
| :--- | :--- | :--- | :--- | :--- |
| **Target 1 (CONT-05)** | Consolidate Celery worker to AI Service image | **SAFE TO CONSOLIDATE** | Worker and AI service share 100% of dependencies, UID 1000, and model files. AI image is a strict superset. | Unify `docker-compose.yml` to build from `ai-service.Dockerfile`. Retain `worker.Dockerfile` as a compatible alias for CI/CD matrix. |
| **Target 2 (CONT-07)** | Move `pytest` and `pytest-mock` to `requirements-dev.txt` | **SAFE TO MOVE** | App never imports `pytest`; CI runs `compileall app` which does not require `pytest`. | Create `requirements-dev.txt` and remove testing block from `requirements.txt`. |

---

## 5. Non-Changes Preserved
In accordance with pre-implementation verification rules:
- No Dockerfiles were modified.
- No requirements files were modified.
- No Kubernetes manifests were modified.
- No application code was modified.
- No images were built or pushed.
