# Phase 13.5 — Observability & Runtime Reliability Audit Report

**Checkpoint**: `92f615c — feat: complete phase 13.4 storage remediation`
**Branch**: `capstone/phase-13-production-engineering`
**Audit Scope**: Observability, Logging, Metrics, Health Probes, Async Task Reliability, AI/API Timeout Resilience, Operational Failure Detection, and Alerting Readiness.

---

## 1. Executive Summary

Following the successful completion of Phase 13.1 (Security & Secrets), Phase 13.2 (Database & Migrations), Phase 13.3 (Docker & Containers), and Phase 13.4 (Storage & Volume Permissions), this Phase 13.5 audit evaluates the runtime reliability and observability posture of the MedMatch V2 platform.

The audit was conducted strictly against the repository source code, Kubernetes manifests, configuration files, and dependencies at checkpoint `92f615c`. It reveals that while baseline network security, multi-stage images, database migration controls, and local-path volume permissions are hardened, significant runtime observability and reliability gaps remain:
1. **Unbounded External AI Invocation**: Google Gemini API calls in `LLMService` have **no request, read, or connection timeout**. Although `LLM_TIMEOUT_SECONDS = 60` is declared in `settings.py`, it is completely unreferenced in the invocation pipeline. A hung API call blocks the Celery worker thread indefinitely.
2. **Worker Probe Deadlock (`CONT-10`)**: The Celery worker runs with `--pool=solo --concurrency=1` while its Kubernetes liveness probe executes `celery inspect ping` every 60s with a 30s timeout. During heavy embedding or inference operations (30–60s+), the single worker thread is blocked, causing Kubernetes liveness checks to fail 5 consecutive times and restart healthy workers mid-processing.
3. **Observability Vacuum**: `infra/monitoring/prometheus/prometheus.yaml`, `infra/monitoring/prometheus/alerts.yaml`, and `infra/monitoring/alertmanager/alertmanager.yaml` are **0-byte empty files**. No Prometheus server, Alertmanager, or Grafana workloads are configured in `docker-compose.yml` or Kubernetes deployment manifests.
4. **Broken Spring Actuator Prometheus Endpoint**: In `services/auth-service/pom.xml`, `spring-boot-starter-actuator` is present, but `io.micrometer:micrometer-registry-prometheus` is absent. Consequently, `/actuator/prometheus` returns HTTP 404, rendering the `auth-service-monitor` `ServiceMonitor` inoperable.
5. **Cascading Health Probe Restarts**: In `auth-service`, both `livenessProbe` and `readinessProbe` target the composite `/actuator/health` endpoint. If PostgreSQL experiences a transient network blip, Actuator reports `DOWN`, causing Kubernetes to trigger a destructive pod restart rather than simply taking the pod out of the routing endpoints.
6. **Continuous Storage Churn**: `ai-service`'s readiness probe physically writes and unlinks `.readiness_check.tmp` on the shared persistent volume every 10 seconds, causing perpetual disk I/O churn.
7. **Unstructured & Disconnected Logging**: Application logs use human-readable pipe-delimited text without JSON structure. Request correlation IDs (`X-Request-ID`) are generated in middleware but never propagated across internal service calls, repository methods, or Celery asynchronous tasks.

---

## 2. Previous Phase 13 Findings Reconciliation

| Finding ID | Description | Original Phase | Status as of Phase 13.5 | Evidence / Resolution Details |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Actuator `/actuator/*` unrestricted access | 13.1 | **REMEDIATED** | `SecurityConfig.java` restricts Actuator; only `/actuator/health` and `/actuator/info` are public. |
| **SEC-02** | Unauthenticated task status polling | 13.1 | **REMEDIATED** | `/api/tasks/{task_id}` requires JWT auth and hospital tenant isolation (`task_registry.py`). |
| **SEC-03** | Hibernate SQL trace parameter logging | 13.1 | **REMEDIATED** | `application-production.yml` sets `org.hibernate.SQL: WARN` and `org.hibernate.orm.jdbc.bind: WARN`. |
| **DB-01** | Split Alembic migration heads & orphan files | 13.2.1 | **REMEDIATED** | Alembic chain unified to single head `6f0604b23df6`; root migrations removed. |
| **DB-02** | Conflicting migration execution during container startup | 13.2.2 | **REMEDIATED** | Startup migrations decoupled into dedicated K8s Jobs (`ai-migrate`, `auth-migrate`) and initContainers. |
| **CONT-01** | Compose external Postgres volume deadlock | 13.3 | **REMEDIATED** | `external: true` removed from `docker-compose.yml`. |
| **CONT-02** | Redis unauthenticated access in Compose | 13.3 | **REMEDIATED** | Redis password authentication enforced across Compose and Kubernetes. |
| **CONT-05** | Redundant worker Dockerfile drift | 13.3 | **REMEDIATED** | `worker.Dockerfile` removed; worker consolidated to `ai-service.Dockerfile`. |
| **CONT-06** | Mutable image tags (`:latest`, `:phase13-test`) | 13.3 | **DEFERRED** | Deferred to release engineering and CI/CD image promotion pipeline. |
| **CONT-07** | Dev dependencies (`pytest`) in production image | 13.3 | **REMEDIATED** | `pytest` separated into `requirements-dev.txt`; production image contains only runtime dependencies. |
| **CONT-08** | Worker root initContainer with `chmod 777` | 13.4 | **REMEDIATED** | `init-uploads` removed; native `fsGroup: 1000` with `OnRootMismatch` implemented. |
| **CONT-10** | Celery worker liveness probe timeout under solo pool | 13.3 | **OPEN (AUDITED)** | Confirmed open; audited in detail in Section 4 and 6 of this report. |
| **ARCH-08** | RWO upload volume multi-attach constraint | 13.4 | **REMEDIATED (BOUNDED)** | Worker `podAffinity` co-locates worker replicas on the `ai-service` node under RWO local-path storage. |

---

## 3. Logging Audit

### 3.1 Codebase Search Results

- **`print()` statements**:
  - `services/ai-service`: Zero `print()` statements in production code (`app/`). Found only in standalone benchmark script `services/ai-service/app/benchmarks/retrieval_benchmark.py`.
  - `services/auth-service`: Found only in utility CLI `PasswordGenerator.java`. Production Spring code uses SLF4J / Logback.
- **Secrets in logs**:
  - No database passwords, JWT private keys, or API tokens are printed in logging statements.
  - Previous Phase 13.1 remediation confirmed that Hibernate SQL bind logging is disabled (`WARN`).
- **Patient Identifiers & PHI**:
  - In `patient_service.py` (lines 85–87), `f"Patient '{patient.first_name} {patient.last_name}' created."` is constructed and sent to `audit_service.log()`. `audit_service` writes to the PostgreSQL `audit_logs` table and logs only `"Failed to create audit log."` on error without printing names.
  - Uploaded trial PDF files are generated using random UUID4 (`uuid4().pdf` in `pdf_service.py`), avoiding original filename or clinical identity leakage in file paths.

### 3.2 Logging Framework & Format Analysis

- **AI Service**:
  - **Framework**: Standard Python `logging`.
  - **Format**: Configured in `app/main.py`:
    ```python
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | [%(name)s] | %(message)s",
    )
    ```
  - **Defects**:
    1. **Not machine-parseable**: Pipe-delimited plaintext format rather than structured JSON. Log aggregators (ELK, Loki, CloudWatch) require regex parsing instead of native JSON ingestion.
    2. **Missing Correlation IDs**: `RequestIDMiddleware` generates an `X-Request-ID` and sets `request.state.request_id`. `RequestLoggingMiddleware` prints `[%s]` for inbound/outbound HTTP requests. However, this ID is **never stored in a Python `contextvars.ContextVar`** and is **never configured in the log formatter**. Consequently, all logs emitted by `matching_service.py`, `embedding_service.py`, `llm_service.py`, and database repositories lack request correlation.
    3. **Missing Asynchronous Traceability**: Celery tasks in `tasks.py` log `Task ID: %s`, but cannot correlate the asynchronous task back to the originating HTTP `request_id` or hospital tenant in a unified log stream.

- **Auth Service**:
  - **Framework**: Logback via Spring Boot starter.
  - **Format**: Standard Spring plaintext console output. No JSON encoder (such as `logstash-logback-encoder`) is present in `pom.xml`.

---

## 4. Metrics Audit

### 4.1 FastAPI & Custom Business Metrics (`services/ai-service`)

- **HTTP Metrics**: `Instrumentator().instrument(app).expose(app)` in `main.py` provides standard Prometheus HTTP metrics on `/metrics` (e.g., `http_requests_total`, `http_request_duration_seconds`).
- **Declared Metrics in `app/metrics/metrics.py`**:
  - `MATCH_REQUESTS`, `MATCH_SUCCESS`, `MATCH_FAILURE`, `MATCH_DURATION`
  - `UPLOAD_REQUESTS`, `UPLOAD_SUCCESS`, `UPLOAD_FAILURE`
  - `EMBEDDING_REQUESTS`, `LLM_REQUESTS`
  - `EMBEDDING_CACHE_HITS`, `EMBEDDING_CACHE_MISSES`
  - `RETRIEVAL_CACHE_HITS`, `RETRIEVAL_CACHE_MISSES`
  - `LLM_CACHE_HITS`, `LLM_CACHE_MISSES`
- **Instrumentation Gaps (Evidence)**:
  1. `app.metrics` is imported **only** in `matching_service.py` and `embedding_service.py`.
  2. `UPLOAD_REQUESTS`, `UPLOAD_SUCCESS`, and `UPLOAD_FAILURE` are **never imported or incremented anywhere** in `trial.py`, `pdf_service.py`, or `tasks.py`.
  3. **Zero Celery Metrics**: There are no metrics tracking task queue depth, task execution duration histograms, retry counts, or worker processing status.
  4. **Zero LLM Latency & Error Classification Metrics**: `LLM_REQUESTS` is incremented, but there is no latency histogram for Gemini API roundtrips, no counter classified by error code (e.g., 429 rate limit vs. 503 unavailable vs. timeout), and no circuit-breaker state gauge.

### 4.2 Spring Boot Actuator Metrics (`services/auth-service`)

- **Declared Configuration**: `application-production.yml` specifies `management.endpoints.web.exposure.include: [health, prometheus]`.
- **CRITICAL DEFECT**: `services/auth-service/pom.xml` contains `spring-boot-starter-actuator`, but **does NOT declare `io.micrometer:micrometer-registry-prometheus`**.
- **Impact**: Without this dependency, Spring Boot does not configure the Prometheus meter registry. Requests to `/actuator/prometheus` return HTTP 404 Not Found. The Kubernetes `ServiceMonitor` `auth-service-monitor` targeting `/actuator/prometheus` fails to scrape any metrics.

### 4.3 Monitoring Infrastructure (`infra/monitoring`)

- `infra/monitoring/prometheus/prometheus.yaml`: **0 bytes (empty)**.
- `infra/monitoring/prometheus/alerts.yaml`: **0 bytes (empty)**.
- `infra/monitoring/alertmanager/alertmanager.yaml`: **0 bytes (empty)**.
- `docker-compose.yml`: Contains 0 monitoring services (no Prometheus, Grafana, or Alertmanager).
- `infra/kubernetes`: Contains 2 `ServiceMonitor` CRDs, but 0 manifests for deploying Prometheus, Alertmanager, or Grafana workloads.

---

## 5. Health Probe Audit

### 5.1 Workload Probing Matrix

| Workload | Probe Type | Current Target | Current Timings | Operational Verification & Defect Analysis |
| :--- | :--- | :--- | :--- | :--- |
| **`ai-service`** | `startupProbe` | `/api/health/live` (HTTP 8000) | init: 10s, period: 5s, thresh: 30 (160s window) | **Defect**: Passes as soon as FastAPI binds to 8000. Does **not** verify SentenceTransformer model loading. |
| **`ai-service`** | `livenessProbe` | `/api/health/live` (HTTP 8000) | init: 30s, period: 15s, timeout: 5s, thresh: 3 | **Correct**: Answers "is the process alive?" without external dependency side effects. |
| **`ai-service`** | `readinessProbe` | `/api/health/ready` (HTTP 8000) | init: 15s, period: 10s, timeout: 5s, thresh: 3 | **Defect**: Verifies DB, Redis, Alembic head, and pgvector correctly, but **performs physical write/unlink of `.readiness_check.tmp` on PVC every 10s**, causing constant disk churn. |
| **`worker`** | `livenessProbe` | `celery inspect ping` (exec) | init: 120s, period: 60s, timeout: 30s, thresh: 5 | **CRITICAL DEFECT (`CONT-10`)**: Spawns heavy Python CLI. Fails when `--pool=solo` worker is processing long tasks (>30s), causing Kubernetes to kill healthy workers. |
| **`worker`** | `readinessProbe` | `celery inspect ping` (exec) | init: 60s, period: 60s, timeout: 30s, thresh: 5 | **Anti-Pattern**: Celery worker is not a Kubernetes Service backend; readiness probe has no routing effect but consumes CPU/memory and triggers timeouts. |
| **`auth-service`** | `startupProbe` | *None* | *None* | JVM cold-start under resource pressure risks early liveness failure. |
| **`auth-service`** | `livenessProbe` | `/actuator/health` (HTTP 8081) | init: 45s, period: 15s, timeout: 5s, thresh: 3 | **CRITICAL DEFECT**: Targets composite health endpoint which checks PostgreSQL. If DB blips, JVM is killed and enters `CrashLoopBackOff`. Must target `/actuator/health/liveness`. |
| **`auth-service`** | `readinessProbe` | `/actuator/health` (HTTP 8081) | init: 20s, period: 10s, timeout: 5s, thresh: 3 | Acceptable for DB dependency, but should target `/actuator/health/readiness` (Spring Boot availability group). |
| **`postgres`** | `livenessProbe` | `pg_isready` (exec) | init: 30s, period: 15s, timeout: 5s, thresh: 5 | Correct standard PostgreSQL health check. |
| **`postgres`** | `readinessProbe` | `pg_isready` (exec) | init: 10s, period: 10s, timeout: 5s, thresh: 3 | Correct standard PostgreSQL readiness check. |
| **`redis`** | `livenessProbe` | `redis-cli ping` (exec) | init: 15s, period: 15s, timeout: 5s, thresh: 5 | Correct standard Redis health check. |
| **`redis`** | `readinessProbe` | `redis-cli ping` (exec) | init: 5s, period: 10s, timeout: 5s, thresh: 3 | Correct standard Redis readiness check. |
| **`frontend`** | `livenessProbe` | `/` (HTTP 5173) | init: 15s, period: 15s, timeout: 5s, thresh: 3 | Correct static Nginx check. |
| **`frontend`** | `readinessProbe` | `/` (HTTP 5173) | init: 5s, period: 10s, timeout: 5s, thresh: 3 | Correct static Nginx check. |

---

## 6. External AI / API Resilience Audit (Gemini)

Inspection of `services/ai-service/app/services/llm_service.py` and `services/ai-service/app/config/llm.py` revealed:

1. **Missing Timeout**:
   - `get_llm()` creates `genai.Client(api_key=settings.GOOGLE_API_KEY)`.
   - `_generate_raw_json()` invokes `self.client.models.generate_content(...)` without passing any timeout or HTTP options.
   - `LLM_TIMEOUT_SECONDS: int = 60` is defined in `settings.py`, but is **completely unreferenced** in `llm_service.py` or `llm.py`.
   - **Impact**: If a network socket hangs or the Gemini backend stalls, the call waits indefinitely.
2. **Worker Blocking Risk**:
   - In `process_trial` (Celery task), the worker runs with `--pool=solo`. A hung Gemini call blocks the single thread indefinitely.
   - Because the thread is blocked, `celery inspect ping` probe fails, leading to pod termination after 5 minutes.
3. **Multiplicative Retries**:
   - `_generate_raw_json` has a `@retry` decorator configured with `stop=stop_after_attempt(3)`.
   - `process_trial` catches `LLMCommunicationError` and calls `self.retry(max_retries=3)`.
   - **Compounding Retries**: A single failing task attempts the LLM up to $3 \times 3 = 9$ times before failing terminally.
4. **Absence of Circuit Breaker & Fallback**:
   - There is no circuit-breaker mechanism (e.g., tracking consecutive failures to trip open).
   - If the external API suffers an outage, every inbound matching request and Celery task repeatedly attempts requests until timing out or exhausting retries.

---

## 7. Celery / Async Task Reliability Audit

1. **State Representation**:
   - Task states are restricted to standard Celery states: `PENDING`, `STARTED`, `SUCCESS`, `FAILURE`, `RETRY`.
   - There are no intermediate stage events (e.g., `EXTRACTING_PDF`, `GENERATING_EMBEDDINGS`, `MATCHING_CRITERIA`).
2. **Failure Observability**:
   - Task failures are logged via `logger.exception("Failed processing trial PDF...")`.
   - `/api/tasks/{task_id}` sanitizes errors to `"Task processing failed"`, preventing internal trace leakage.
   - However, because there are no Prometheus counters for failed tasks, an operator cannot detect a spike in Celery failures without manually searching container logs.
3. **Queue Depth & Backlog**:
   - Celery tasks are stored in the Redis list `celery`.
   - Neither `ai-service` nor a Celery exporter monitors the Redis queue length. Queue depth is unmeasurable from metrics.
4. **Time Limits**:
   - `CELERY_TASK_TIME_LIMIT = 300` (5 minutes) is configured in `celery_app.conf`.
   - However, **no `task_soft_time_limit`** is configured. When 300s elapses, Celery issues a hard `SIGKILL`, preventing the task from executing `_delete_uploaded_file` in its `finally` block or saving a clean failure status.

---

## 8. Database & Redis Runtime Observability Audit

1. **PostgreSQL Outage Detection**:
   - Detected at runtime by `ai-service` `/api/health/ready` (checks `SELECT 1` + `alembic_version`).
   - Detected by `auth-service` `/actuator/health`.
   - **Gap**: Connection pool exhaustion is not monitored. SQLAlchemy `QueuePool` size is 10 (overflow 20, timeout 30s), but pool checked-out connection count is not exposed as a metric.
2. **Redis Outage Detection**:
   - Detected at runtime by `ai-service` `/api/health/ready` via `RedisClient.ping()`.
   - **Gap**: Redis memory consumption, hit/miss ratios, and connection spikes are not monitored by an exporter.

---

## 9. Kubernetes Operational Observability Audit

| Failure Scenario | Detected by Kubernetes? | Actionable Project Metric / Alert Exists? | Diagnostic Experience |
| :--- | :--- | :--- | :--- |
| **Pod CrashLoopBackOff** | Yes (`kubectl get pods`) | **No** (0-byte `alerts.yaml`) | Requires manual CLI discovery or external APM. |
| **Worker OOMKilled (1Gi limit)** | Yes (Exit code 137) | **No** | Worker disappears silently during heavy embedding batch. |
| **Celery Worker Deadlock (`CONT-10`)**| Yes (Liveness probe fails) | **No** | Kubernetes restarts worker; active PDF task is aborted and retried. |
| **PostgreSQL Outage** | Yes (Readiness probe 503) | **No** | Pods marked unready; Auth pods restart into CrashLoop. |
| **Redis Outage** | Yes (Readiness probe 503) | **No** | AI service unready; Celery task dispatch fails with 503. |
| **Gemini API Outage / Rate Limit** | No (Pods remain healthy) | **No** | Users experience hanging requests; Celery tasks accumulate in queue. |
| **Storage PVC Exhaustion** | No (Until write fails) | **No** | Readiness probe fails on write; upload endpoints return 500/503. |

---

## 10. Finding Prioritization by Engineering Impact

### CRITICAL
1. **Unbounded External AI Timeout**: Lack of explicit socket/read timeout on `genai.Client` and `generate_content()` allows external network hangs to stall Celery workers and HTTP threads indefinitely.
2. **Celery Worker Probe Deadlock (`CONT-10`)**: Spawning `celery inspect ping` against a `--pool=solo` worker executing synchronous CPU/embedding jobs triggers false liveness timeouts and kills healthy workers.
3. **Auth-Service Cascading Liveness Probe Failure**: Targeting composite `/actuator/health` causes transient database interruptions to trigger pod restarts rather than standard traffic shedding.

### HIGH
4. **Observability Vacuum (0-byte Monitoring Files)**: `prometheus.yaml`, `alerts.yaml`, and `alertmanager.yaml` are empty placeholders; no active Prometheus/Alertmanager/Grafana stack exists.
5. **Broken Auth-Service Prometheus Endpoint**: Missing `micrometer-registry-prometheus` in `pom.xml` leaves `/actuator/prometheus` returning 404, breaking ServiceMonitor scraping.
6. **Unstructured Logs & Missing Context Propagation**: Logs are human-readable plaintext without JSON format, and request correlation IDs are not propagated into service/worker execution contexts.
7. **Uninstrumented Celery & Upload Metrics**: Celery queue depth, task duration, and task failures have zero metric instrumentation.

### MEDIUM
8. **Embedding Model Startup Warm-up Gap**: SentenceTransformer (~73s load time) is loaded lazily on the first request rather than pre-warmed during lifespan, causing initial client timeouts.
9. **Readiness Probe Disk Churn**: `/api/health/ready` executes physical disk writes/unlinks on the shared PVC every 10s.
10. **Missing Soft Time Limit in Celery**: Lack of `task_soft_time_limit` leads to ungraceful `SIGKILL` termination without resource cleanup.

### LOW / INFORMATIONAL
11. **Frontend InitContainer Root Chown**: `nginx-temp-init` uses root `chown` on `emptyDir` mounts (low risk as it does not affect persistent storage).
12. **Redundant Celery Readiness Probe**: Readiness probe on worker provides no routing benefit.
13. **PostgreSQL Backup Cron & HA**: Documented architectural constraint for cloud deployment.
14. **Mutable Image Tags (`CONT-06`)**: Retained for release engineering milestone.

---

## 11. Phase 13.5 Implementation Boundary

To ensure stability and adhere to Phase 13 scope guidelines, the proposed Phase 13.5 implementation is bounded strictly to operational reliability and observability fixes that require **no redesign of core application business logic or cloud infrastructure**:

### Proposed Implementation Items

| Item | Target Files | Nature of Change | Risk | Validation Method |
| :--- | :--- | :--- | :--- | :--- |
| **1. Explicit Gemini API Timeout** | `services/ai-service/app/services/llm_service.py`, `services/ai-service/app/config/llm.py` | Pass `settings.LLM_TIMEOUT_SECONDS` (60s) to GenAI client / call options. | Low | Unit test verifying timeout configuration and simulated timeout handling. |
| **2. Remediate Celery Worker Probe (`CONT-10`)** | `infra/kubernetes/worker/deployment.yaml`, `services/ai-service/app/celery/` | Replace blocking `celery inspect ping` with lightweight process/heartbeat check; remove redundant readiness probe. | Low | K8s manifest validation; verify probe passes while task is executing. |
| **3. Fix Auth-Service Liveness Probe** | `infra/kubernetes/auth-service/deployment.yaml` | Point liveness probe to `/actuator/health/liveness` and readiness to `/actuator/health/readiness`. | Low | `kubectl apply --dry-run=client` and Actuator endpoint verification. |
| **4. Fix Auth-Service Prometheus Endpoint** | `services/auth-service/pom.xml` | Add `io.micrometer:micrometer-registry-prometheus` dependency. | Low | Spring Boot test verifying `/actuator/prometheus` returns HTTP 200 with metrics. |
| **5. Populate Core Prometheus & Alertmanager Configs** | `infra/monitoring/prometheus/prometheus.yaml`, `alerts.yaml`, `alertmanager.yaml` | Replace 0-byte placeholders with production scrape jobs and alert rules (ServiceDown, High5xx, QueueBacklog). | Low | Promtool / YAML lint syntax validation. |
| **6. Eliminate AI Readiness Disk Churn** | `services/ai-service/app/api/routes/health.py` | Replace write/unlink of `.readiness_check.tmp` with non-destructive directory permissions check (`os.access(upload_dir, os.W_OK)`). | Low | Health test suite verifying ready response without filesystem mutation. |
| **7. Contextual Request ID Propagation** | `services/ai-service/app/middleware/`, `services/ai-service/app/main.py` | Use `contextvars` to inject `request_id` into all log records emitted during request processing. | Medium | Test verifying presence of `request_id` across service-level logs. |

---

## 12. Deferred Work

The following items are deliberately deferred to future post-Phase 13 milestones:
1. **Full Grafana Dashboard Deployments**: Grafana server manifests and JSON dashboards are deferred to a dedicated release/visualization phase.
2. **PostgreSQL Clustering & HA Replication**: Multi-node Patroni / Cloud SQL managed failover remains a cloud infrastructure consideration.
3. **Automated Remote Backup Scheduling**: Object-storage backup cron jobs require dedicated S3/GCS credentials and infrastructure.
4. **LLM Circuit Breaker with Automated Keyword Fallback**: Implementing automated degraded clinical reasoning requires validation against Phase 12 clinical safety invariants.
5. **Container Image Tag Immutability (`CONT-06`)**: SHA-256 digest pinning deferred to the CI/CD release pipeline.

---

## 13. Validation Plan

1. **Manifest Validation**:
   - `kubectl kustomize .` must render cleanly.
   - `kubectl apply --dry-run=client -k .` must validate without syntax errors.
2. **Java / Auth Service Validation**:
   - `mvn test` in `services/auth-service` to confirm build integrity with Micrometer Prometheus registry.
3. **Python / AI Service Validation**:
   - Targeted unit tests for health endpoints, timeout handling, and request-id propagation.
4. **Git Hygiene**:
   - `git diff --check` to ensure zero whitespace/formatting defects.
   - Exact scope control verifying no unauthorized changes outside targeted manifests and configuration files.

---

## 14. Explicit Out-of-Scope Items

- DO NOT modify database schemas, Alembic migrations, or Flyway SQL.
- DO NOT alter PVC access modes (`ReadWriteOnce`) or StorageClass.
- DO NOT rewrite Celery architecture from Redis to RabbitMQ.
- DO NOT modify the core clinical matching algorithms or prompts.
- DO NOT introduce external cloud services (AWS S3, GCP Cloud SQL, Azure Monitor).
- DO NOT deploy unapproved monitoring operators to the Kubernetes cluster during audit.

---

**FINAL STATUS**:
Phase 13.5 Observability & Runtime Reliability Audit Complete — Implementation Pending
