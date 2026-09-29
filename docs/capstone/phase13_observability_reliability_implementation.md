# Phase 13.5 — Observability & Runtime Reliability Implementation

## 1. Executive Summary

Phase 13.5 establishes the runtime reliability, observability, and health monitoring baseline for the MedMatch platform following the completion of the Phase 13.4 storage remediation. In accordance with the accepted Phase 13.5 audit (`docs/capstone/phase13_observability_reliability_audit.md`), this implementation strictly adheres to the approved boundary:
- Enforces an explicit 60-second request timeout on Google Gemini GenAI client requests.
- Replaces the blocking Celery worker liveness probe with a lightweight process-level probe and removes the redundant readiness probe.
- Separates Spring Boot Actuator liveness and readiness probes for `auth-service`.
- Integrates the Micrometer Prometheus registry for Spring Boot Actuator.
- Provides production Prometheus scraping and Alertmanager routing configurations matching actual exposed metric endpoints.
- Replaces temporary-file disk write/unlink churn in AI service readiness with non-destructive permissions checking (`os.access`).
- Implements asynchronous `contextvars`-based request ID propagation and logging correlation filter for `ai-service`.

All database migrations, clinical matching rules, eligibility reasoning, retrieval mechanisms, RAG pipelines, model choices, and Phase 13.4 storage architectures remain 100% untouched.

---

## 2. Files Modified and Created

### Source & Configuration Files Modified
- [`services/ai-service/app/config/llm.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/config/llm.py): Configures client-level `HttpOptions(timeout=settings.LLM_TIMEOUT_SECONDS * 1000)` on the Google GenAI client.
- [`services/ai-service/app/services/llm_service.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/llm_service.py): Applies request-level `HttpOptions(timeout=settings.LLM_TIMEOUT_SECONDS * 1000)` to `GenerateContentConfig` in `_generate_raw_json`.
- [`services/ai-service/app/api/routes/health.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/api/routes/health.py): Replaces `.readiness_check.tmp` file write/unlink with `os.access(upload_dir, os.W_OK)`.
- [`services/ai-service/app/middleware/request_id.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/middleware/request_id.py): Implements `contextvars`-backed request ID storage, preservation of valid incoming `X-Request-ID` headers, automatic reset in `finally:`, and `RequestIDLogFilter`.
- [`services/ai-service/app/middleware/request_logging.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/middleware/request_logging.py): References `get_current_request_id()`.
- [`services/ai-service/app/main.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/main.py): Configures root logging handler with `RequestIDLogFilter` and `[%(request_id)s]` log format.
- [`services/auth-service/pom.xml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/pom.xml): Adds `io.micrometer:micrometer-registry-prometheus` dependency.
- [`services/auth-service/src/main/resources/application.yml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/src/main/resources/application.yml): Enables Spring Boot Actuator probe endpoints (`management.endpoint.health.probes.enabled: true`).
- [`services/auth-service/src/main/resources/application-production.yml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/src/main/resources/application-production.yml): Enables Spring Boot Actuator probe endpoints in production profile.
- [`infra/kubernetes/auth-service/deployment.yaml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/auth-service/deployment.yaml): Configures `livenessProbe` to `/actuator/health/liveness` and `readinessProbe` to `/actuator/health/readiness`.
- [`infra/kubernetes/worker/deployment.yaml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/worker/deployment.yaml): Replaces `celery inspect ping` with `/bin/sh -c "kill -0 1"` liveness probe and removes redundant readiness probe.
- [`infra/monitoring/prometheus/prometheus.yaml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/monitoring/prometheus/prometheus.yaml): Configures scraping for `ai-service` (`/metrics`) and `auth-service` (`/actuator/prometheus`).
- [`infra/monitoring/prometheus/alerts.yaml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/monitoring/prometheus/alerts.yaml): Defines alert rules for `ServiceDown`, `HighHttp5xxRate`, and `HighMatchFailureRate`.
- [`infra/monitoring/alertmanager/alertmanager.yaml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/monitoring/alertmanager/alertmanager.yaml): Defines routing and default notification receiver configuration.

### Tests Created
- [`services/ai-service/tests/test_llm_timeout.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/tests/test_llm_timeout.py): 3 unit tests verifying timeout propagation to client and request config, configuration respect, and retry integration.
- [`services/ai-service/tests/test_health_readiness.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/tests/test_health_readiness.py): 2 unit tests verifying that readiness succeeds without creating temporary files on the upload filesystem.
- [`services/ai-service/tests/test_request_id_propagation.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/tests/test_request_id_propagation.py): 7 unit tests verifying incoming ID preservation, UUID generation, context cleanup, unhandled exception reset, log enrichment, and concurrent isolation.
- [`services/auth-service/src/test/java/com/medmatch/auth/controller/ActuatorEndpointsTest.java`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/src/test/java/com/medmatch/auth/controller/ActuatorEndpointsTest.java): 4 unit tests verifying `/actuator/prometheus`, `/actuator/health/liveness`, `/actuator/health/readiness`, and protection of sensitive actuator endpoints.

---

## 3. Detailed Component Implementations

### 3.1. Gemini Timeout Enforcement
- **Inspection Finding**: `google-genai` SDK v2.25.0 uses `google.genai.types.HttpOptions(timeout=...)` measured in milliseconds. Previously, `LLM_TIMEOUT_SECONDS = 60` was defined in `settings.py` but never passed to the Gemini SDK.
- **Implementation**:
  - `app/config/llm.py`: Instantiates `genai.Client(api_key=..., http_options=types.HttpOptions(timeout=settings.LLM_TIMEOUT_SECONDS * 1000))`.
  - `app/services/llm_service.py`: Passes `http_options=HttpOptions(timeout=settings.LLM_TIMEOUT_SECONDS * 1000)` inside `GenerateContentConfig` for `_generate_raw_json`.
- **Failure Path**: If a request exceeds 60 seconds, `httpx.TimeoutException` or `google.genai.errors.APIError` is raised, intercepted by Tenacity retry decorators, and logged without exposing keys or clinical contents.

### 3.2. Celery Worker Liveness Probe Remediation
- **Problem**: The worker operates under `--pool=solo --concurrency=1`. When running a long embedding or extraction task, `celery inspect ping` blocks waiting for worker thread execution, triggering spurious Kubernetes probe timeouts (30s) and container restarts.
- **Implementation**:
  - Replaced probe command with `/bin/sh -c "kill -0 1"`.
  - Tuned probe parameters: `initialDelaySeconds: 15`, `periodSeconds: 15`, `timeoutSeconds: 5`, `failureThreshold: 3`.
  - Removed redundant `readinessProbe` because the Celery worker is a consumer queue worker, not a Kubernetes Service routing target.
  - Verified no Redis/Celery inspect control command is executed.

### 3.3. Auth-Service Probe Separation
- **Problem**: Composite `/actuator/health` probe caused pod restarts if PostgreSQL experienced temporary network jitter or restarts.
- **Implementation**:
  - `infra/kubernetes/auth-service/deployment.yaml`:
    - `livenessProbe`: `/actuator/health/liveness` (checks JVM state without restarting on database blips).
    - `readinessProbe`: `/actuator/health/readiness` (checks PostgreSQL dependency to pull pod from traffic when unready).
  - `application.yml` & `application-production.yml`: Added `management.endpoint.health.probes.enabled: true`.

### 3.4. Spring Prometheus Registry
- **Implementation**: Added `io.micrometer:micrometer-registry-prometheus` to `services/auth-service/pom.xml`.
- **Exposure**: Actuator configuration already exposes `prometheus` under `management.endpoints.web.exposure.include: health,info,prometheus`.
- **Validation**: Added Spring MockMvc test confirming `/actuator/prometheus` returns HTTP 200 with Prometheus formatted metric lines, while sensitive endpoints like `/actuator/env` return HTTP 403 Forbidden.

### 3.5. Prometheus + Alertmanager Configuration
- **Metrics Scraping**:
  - `ai-service`: Scraped at `/metrics` on port 8000 via `prometheus-fastapi-instrumentator`.
  - `auth-service`: Scraped at `/actuator/prometheus` on port 8081 via `micrometer-registry-prometheus`.
- **Alert Rules**:
  - `ServiceDown`: Triggers if any service instance is down for > 1m (critical).
  - `HighHttp5xxRate`: Triggers if 5xx rate exceeds 5% of total requests over 5m (warning).
  - `HighMatchFailureRate`: Triggers if clinical matching failure rate exceeds 10% over 5m (warning).
- **Limitation Acknowledged**: Celery queue depth metrics (`CeleryQueueBacklog`) cannot be measured without deploying a Celery Prometheus exporter (e.g., `celery-prometheus-exporter`) or Redis queue length exporter. In accordance with audit instructions, no fake metric alerts were invented.
- **Alertmanager**: Configured with valid default grouping and local fallback receiver.

### 3.6. AI Readiness — Removed PVC Disk Churn
- **Problem**: Readiness probe previously wrote and deleted `/app/uploads/.readiness_check.tmp` on every probe invocation (every 10s per replica), creating continuous inode churn and I/O noise on the shared volume.
- **Implementation**: Replaced write/unlink with `if not os.access(upload_dir, os.W_OK): raise PermissionError(...)`.
- **Verification**: Verified zero file creation or deletion during readiness checks. Preserved all other readiness gates: database connectivity, Alembic head migration status, Redis connectivity, and pgvector extension availability.

### 3.7. Request-ID Context Propagation
- **Implementation**:
  - Used Python `contextvars.ContextVar[str | None]` (`_REQUEST_ID_CTX`) in `services/ai-service/app/middleware/request_id.py`.
  - Incoming `X-Request-ID` validated against `^[a-zA-Z0-9_\-]{1,64}$`. Valid IDs are preserved; invalid or missing IDs are replaced with generated `uuid4`.
  - Set context token at request start and reset via `reset_current_request_id(token)` in `finally:`.
  - Implemented `RequestIDLogFilter(logging.Filter)` injecting `record.request_id = get_current_request_id() or "-"`.
  - Configured root logger format in `app/main.py`: `%(asctime)s | %(levelname)s | [%(name)s] | [%(request_id)s] | %(message)s`.
  - Celery tasks and background scripts do not run through the HTTP middleware and receive `"-"` (never fabricated request IDs).
  - Celery task correlation across process boundaries is deferred to avoid altering task argument contracts.

---

## 4. Test & Verification Results

### 4.1. AI-Service Test Suite
- Executed: `services\ai-service\.venv\Scripts\python.exe -m pytest -q services/ai-service/tests -o pythonpath=services/ai-service`
- **Result: 78 passed, 0 failed, 1 warning in 68.62s** (up from 66 tests in Phase 13.4).
- Tests included:
  - 3 new tests in `test_llm_timeout.py` (timeout options passed, config respected, error handling).
  - 2 new tests in `test_health_readiness.py` (writable directory verified, zero temporary files created).
  - 7 new tests in `test_request_id_propagation.py` (incoming header preserved, generated UUID, context availability, cleanup on success/error, logging enrichment, concurrent async thread isolation).

### 4.2. Auth-Service Test Suite
- Executed: `cd services\auth-service && mvnw.cmd test`
- **Result: 85 tests run, 0 failures, 0 errors, 0 skipped. BUILD SUCCESS in 24.77s** (up from 81 tests in Phase 13.4).
- Tests included:
  - 4 new tests in `ActuatorEndpointsTest.java` (`/actuator/prometheus` 200 OK, `/actuator/health/liveness` 200 UP, `/actuator/health/readiness` 200 UP, `/actuator/env` 403 Forbidden).

### 4.3. Frontend Validation
- Executed: `npm run lint` and `npm run build` in `frontend/medmatch-ui`.
- **Result: 0 lint errors; production build completed successfully in 1.22s**.

### 4.4. Infrastructure Manifest Validation
- `docker compose config`: Exited 0 with fully validated service configurations and volumes.
- `kubectl kustomize .`: Exited 0; all resources rendered cleanly.
- `kubectl apply --dry-run=client -k .`: Exited 0 for all standard Kubernetes resources (`deployment.apps/auth-service`, `deployment.apps/worker`, `storageclass`, `persistentvolumeclaim`, etc.).
- Monitoring YAML syntax: `python -c "import yaml; ..."` validated `prometheus.yaml`, `alerts.yaml`, and `alertmanager.yaml` as valid YAML.
- `git diff --check`: Exited 0 with no whitespace errors.

---

## 5. Remaining Limitations & Deferred Work

1. **Celery Task Correlation**:
   - HTTP request IDs are preserved in ASGI contextvars during request processing, but are not forwarded across Redis into Celery task signatures or headers. Propagating request IDs into background Celery workers requires modifying task invocation signatures or implementing custom Celery task publish/receive signals. This is documented and deferred to a dedicated task architecture enhancement.
2. **Celery Queue Depth Instrumentation**:
   - Celery does not expose native Prometheus metrics without a dedicated metrics sidecar/exporter (such as `celery-prometheus-exporter`). Celery queue depth alerts (`CeleryQueueBacklog`) are deferred until exporter infrastructure is introduced.
3. **Grafana Deployment**:
   - Grafana visualization dashboards were explicitly excluded from Phase 13.5 and remain deferred.
4. **PostgreSQL HA / Patroni**:
   - Clustered database HA was excluded from Phase 13.5 and remains deferred.

---

## 6. Explicitly Unchanged Clinical Behavior

- **No Schema Changes**: Database models and migrations are unchanged.
- **No Matching Logic Changes**: `app/services/matching_service.py` and rule-based matching algorithms remain untouched.
- **No Prompt Changes**: Clinical prompt templates and system instructions are unaltered.
- **No Retrieval/RAG Changes**: Hybrid retrieval, chunking, and embedding workflows are untouched.
- **No Storage Architecture Changes**: Phase 13.4 permissions, RWO PVC, podAffinity, and `fsGroup: 1000` settings remain active.
