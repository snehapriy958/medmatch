# Phase 13 — Production Resilience & Failure Matrix

## 1. Overview & Objective

This document analyzes the current behavior of MedMatch under 18 failure scenarios, identifying gaps between current handling and production engineering requirements.

---

## 2. Failure Matrix

### Scenario 1: PostgreSQL Unavailable
- **Failure**: Database container/pod crashes, stops responding, or network connection fails.
- **Detection**: Readiness probe `/api/health/ready` returns 503; SQLAlchemy throws `OperationalError` / `psycopg2.OperationalError`.
- **Current Behavior**: Requests block until socket timeout, then fail with 500 Internal Server Error via generic/database exception handlers.
- **Recovery**: Container restarts via Kubernetes/Compose restart policy. No automated failover exists (single replica).
- **User-Visible Behavior**: HTTP 500/503 errors on all endpoints requiring database access (matching, trial listing, user login).
- **Data-Loss Risk**: None for committed transactions; in-flight requests abort.
- **Retry Behavior**: None at API level. SlowAPI and client retries may cause request amplification.
- **Missing Control**: Connection pool health-check pre-validation (`pool_pre_ping=True`), exponential backoff on transient reconnect, read-only degraded mode for cached items.
- **Proposed Control**: Configure `pool_pre_ping=True` in SQLAlchemy engine; return structured 503 with `Retry-After`; serve read-only queries from Redis cache where feasible.

---

### Scenario 2: Redis Unavailable
- **Failure**: Redis pod/container crashes or network becomes partitioned.
- **Detection**: Celery broker connection error logged; `/api/health/ready` redis ping throws exception.
- **Current Behavior**: AI service healthcheck fails (returns 503); trial upload endpoint `/api/trials/upload` attempts `process_trial.delay()` and throws `redis.exceptions.ConnectionError`, catching it and raising HTTP 503. Cache lookups fail silently or log errors.
- **Recovery**: Automatic container restart; AOF replay on recovery.
- **User-Visible Behavior**: PDF uploads fail with 503; semantic match requests continue with slower uncached retrieval.
- **Data-Loss Risk**: Unwritten queue messages in memory prior to AOF fsync could be lost.
- **Retry Behavior**: Redis client does not retry failed submissions; client must re-upload PDF.
- **Missing Control**: Circuit breaker on cache reads/writes to prevent thread pool exhaustion when Redis hangs.
- **Proposed Control**: Implement circuit breaker on CacheService; configure Redis Sentinel or clustered deployment for HA.

---

### Scenario 3: Celery Worker Unavailable
- **Failure**: Celery worker pods crash or are killed by orchestrator (e.g. OOMKilled or probe timeout).
- **Detection**: Queue depth grows in Redis; `GET /api/tasks/{task_id}` stays in `PENDING` state indefinitely.
- **Current Behavior**: Tasks accumulate in Redis broker list; no worker consumes them; client UI displays infinite loading spinner.
- **Recovery**: Pod restart via Deployment controller.
- **User-Visible Behavior**: Uploaded trials never transition to `SUCCESS` or `FAILURE`.
- **Data-Loss Risk**: Low (messages persist in Redis if AOF enabled).
- **Retry Behavior**: Tasks remain in queue until a worker comes back online.
- **Missing Control**: Dead-letter queue / timeout expiration alerting; task age monitoring; automated worker scaling based on queue depth.
- **Proposed Control**: Add Prometheus Celery queue depth exporter; configure KEDA HPA to scale workers based on Redis queue length; alert when task age exceeds 15 minutes.

---

### Scenario 4: Gemini API Unavailable
- **Failure**: Google Gemini API returns HTTP 500, 503, 429 rate limit, or network timeouts.
- **Detection**: `LLMCommunicationError`, `LLMServiceUnavailableError`, or `LLMRateLimitError` raised in `LLMService`.
- **Current Behavior**: Tenacity retries up to 3 times with exponential backoff (min 1s, max 8s). If all 3 fail, exception propagates to `matching_service.py` or `celery/tasks.py`. Match endpoint returns 500/503.
- **Recovery**: Recovers when Google API service restores.
- **User-Visible Behavior**: Match evaluation fails with error message; trial PDF processing task in Celery marks task as FAILED after 3 task retries.
- **Data-Loss Risk**: None.
- **Retry Behavior**: 3 internal retries in LLMService + 3 Celery task retries with exponential backoff.
- **Missing Control**: Circuit breaker to prevent cascading thread pool starvation; offline rule-based eligibility fallback; explicit per-call timeout.
- **Proposed Control**: Implement circuit breaker (`pybreaker`); configure explicit 30s timeout on Gemini client calls; fallback to deterministic criteria keyword matching when LLM is unavailable.

---

### Scenario 5: Embedding Model Unavailable / Corrupted
- **Failure**: Local model files in `models/all-MiniLM-L6-v2` missing or corrupted.
- **Detection**: `EmbeddingModel._load_model()` throws `RuntimeError`.
- **Current Behavior**: The first request attempting to embed text throws `RuntimeError("Failed to initialize embedding model")`. Handled by generic exception handler as HTTP 500.
- **Recovery**: Requires image rebuild or volume mount fix.
- **User-Visible Behavior**: All search, matching, and trial ingestion operations permanently fail with 500.
- **Data-Loss Risk**: None.
- **Retry Behavior**: None (permanent error).
- **Missing Control**: Startup verification in `lifespan()` to halt pod launch immediately if model files are missing or unreadable.
- **Proposed Control**: Pre-warm model in FastAPI lifespan startup hook; if loading fails, fail fast before declaring pod ready.

---

### Scenario 6: Malformed PDF Upload
- **Failure**: Uploaded file has `.pdf` extension but contains random garbage bytes or corrupted headers.
- **Detection**: `PDFService.save_pdf` verifies magic bytes (`%PDF-`) and PyMuPDF `fitz.open()` readability.
- **Current Behavior**: Raises `ValueError("Uploaded file is not a valid PDF")`. Caught in route handler and returned as HTTP 400 Bad Request. Upload file is closed and cleaned up.
- **Recovery**: Immediate (clean error response).
- **User-Visible Behavior**: Clear error message: "Uploaded file is not a valid PDF."
- **Data-Loss Risk**: None.
- **Retry Behavior**: None (client error).
- **Missing Control**: None (handled cleanly by current validation logic).
- **Proposed Control**: Retain current validation; add audit log entry for malformed upload attempts.

---

### Scenario 7: Corrupted Trial Document (Extraction Failure)
- **Failure**: Valid PDF file, but text extraction yields empty content (scanned image PDF with no OCR text) or LLM returns malformed JSON.
- **Detection**: `PDFService.extract_text` raises `ValueError("No extractable text found")` or `LLMService` raises `InvalidLLMResponseError`.
- **Current Behavior**: If text is empty, Celery task logs error and deletes PDF; if LLM returns bad JSON, Tenacity retries 3 times then fails task.
- **Recovery**: Task ends in `FAILURE` state; PDF deleted.
- **User-Visible Behavior**: `GET /api/tasks/{task_id}` reports status `FAILURE` with error message.
- **Data-Loss Risk**: None.
- **Retry Behavior**: Retried 3 times if LLM response is unparseable; not retried if PDF has no text.
- **Missing Control**: Optical Character Recognition (OCR) fallback for scanned PDFs; structured error recording in a persistent `trial_processing_failures` table.
- **Proposed Control**: Add OCR preprocessing option for image-only PDFs; persist failed trial processing errors to database with administrative review flag.

---

### Scenario 8: Oversized Upload
- **Failure**: User attempts to upload PDF exceeding `settings.MAX_UPLOAD_SIZE_MB` (default 25 MB).
- **Detection**: `PDFService.save_pdf` streams file in 1MB chunks and tracks accumulated bytes.
- **Current Behavior**: If accumulated size > max allowed, raises `ValueError`. Route handler converts to HTTP 413 Payload Too Large.
- **Recovery**: Immediate.
- **User-Visible Behavior**: HTTP 413: "File exceeds the maximum allowed size of 25 MB."
- **Data-Loss Risk**: None.
- **Retry Behavior**: None (client error).
- **Missing Control**: Ingress-level and Nginx-level enforcement before payload hits application layer.
- **Proposed Control**: Ensure Ingress `nginx.ingress.kubernetes.io/proxy-body-size: "25m"` matches application setting.

---

### Scenario 9: Duplicate Upload
- **Failure**: User uploads the same trial PDF multiple times.
- **Detection**: `TrialService.process_pdf` checks `find_existing_trial(hospital_id, title, condition, phase)` prior to insertion.
- **Current Behavior**: If match is found, creation is skipped, log recorded, temporary PDF deleted, and task returns: `{"message": "Trial already exists. Duplicate import skipped."}`.
- **Recovery**: Clean termination without duplicate rows.
- **User-Visible Behavior**: Task succeeds with message indicating trial already exists.
- **Data-Loss Risk**: None.
- **Retry Behavior**: None.
- **Missing Control**: Hash-based deduplication at upload time (e.g. SHA-256 of PDF file) before queuing Celery task.
- **Proposed Control**: Compute SHA-256 hash of uploaded file and check against previously ingested document hashes to avoid unnecessary Celery queueing and LLM token usage.

---

### Scenario 10: Celery Worker Crash Mid-Processing
- **Failure**: OOM kill, SIGKILL, or hardware node failure during PDF processing.
- **Detection**: Redis detects lost TCP socket; `task_reject_on_worker_lost=True` triggers requeue in Celery.
- **Current Behavior**: Task is returned to Redis queue and reassigned to another worker. If the database transaction was in-flight, it rolled back on connection drop.
- **Recovery**: New worker attempts to re-process the file.
- **User-Visible Behavior**: Processing takes longer but succeeds if shared storage retains the PDF.
- **Data-Loss Risk**: High if ephemeral storage is used and the file was lost when the previous node crashed.
- **Retry Behavior**: Task re-executed automatically.
- **Missing Control**: Shared durable object store for uploads instead of local node filesystem.
- **Proposed Control**: Store uploaded PDFs in S3/MinIO/GCS with signed URLs instead of relying on POSIX shared disk mounts.

---

### Scenario 11: Database Connection Pool Exhaustion
- **Failure**: High concurrent request volume exhausts SQLAlchemy or HikariCP connection pools.
- **Detection**: `sqlalchemy.exc.TimeoutError: QueuePool limit of size X overflow Y reached`.
- **Current Behavior**: Application threads block waiting for available connections until pool timeout (default 30s), then throw 500 Internal Server Error.
- **Recovery**: Connections freed as in-flight queries complete.
- **User-Visible Behavior**: Slow response times followed by HTTP 500 errors.
- **Data-Loss Risk**: None.
- **Retry Behavior**: None.
- **Missing Control**: Connection pool size tuning; PgBouncer connection pooler in front of PostgreSQL; pool saturation metrics export.
- **Proposed Control**: Deploy PgBouncer as a database sidecar or intermediate service; expose connection pool saturation metrics in Prometheus.

---

### Scenario 12: Frontend/Backend Unavailable
- **Failure**: Reverse proxy cannot connect to backend service (e.g. `ai-service` or `auth-service` down).
- **Detection**: Nginx logs `connect() failed (111: Connection refused) while connecting to upstream`.
- **Current Behavior**: Nginx returns HTTP 502 Bad Gateway to the browser.
- **Recovery**: Container restart by orchestrator.
- **User-Visible Behavior**: Browser displays generic 502 Bad Gateway or Axios network error toast.
- **Data-Loss Risk**: None.
- **Retry Behavior**: React Query retries failed queries according to client policy (default 3 times).
- **Missing Control**: Branded friendly maintenance/outage page; automated health routing.
- **Proposed Control**: Configure custom Nginx `error_page 502 503 /error.html` with informative retry instructions.

---

### Scenario 13: Authentication Service Unavailable
- **Failure**: `auth-service` is down or unreachable.
- **Detection**: HTTP calls to `/api/auth/*` fail with 502/503.
- **Current Behavior**: Users cannot log in or refresh tokens. However, `ai-service` validates JWTs locally using public key cryptography (`RS256`), so existing valid tokens continue to work for AI endpoints until expiration.
- **Recovery**: Orchestrator restarts `auth-service`.
- **User-Visible Behavior**: Login fails; active logged-in sessions continue to work until token expiration (1 hour).
- **Data-Loss Risk**: None.
- **Retry Behavior**: Frontend auth state redirects to login.
- **Missing Control**: Token refresh grace periods; multi-replica HA for auth-service.
- **Proposed Control**: Ensure minimum 2 replicas for auth-service with PodDisruptionBudget; decouple audit log writes if auth-service is down.

---

### Scenario 14: Partial Kubernetes Rollout
- **Failure**: New image has a bug causing CrashLoopBackOff on new pods during rolling update.
- **Detection**: `kubectl rollout status` hangs or times out; readiness probes fail.
- **Current Behavior**: If `type: RollingUpdate`, old pods remain active while new pods fail. If `type: Recreate` (as currently configured for `ai-service`), old pods are terminated first, causing complete service outage!
- **Recovery**: Manual `kubectl rollout undo` required; no automated rollback script exists.
- **User-Visible Behavior**: Complete downtime if using `Recreate`; partial degradation if using `RollingUpdate`.
- **Data-Loss Risk**: None.
- **Retry Behavior**: None.
- **Missing Control**: RollingUpdate strategy with `maxUnavailable: 0`; automated rollback on deployment failure in CI/CD.
- **Proposed Control**: Change `ai-service` and `worker` to `RollingUpdate`; add automated rollback step in deployment pipeline.

---

### Scenario 15: Sudden Pod Restart (SIGKILL / OOM)
- **Failure**: Kernel sends SIGKILL to pod due to memory limit breach.
- **Detection**: Pod termination reason `OOMKilled`; exit code 137.
- **Current Behavior**: Process terminates immediately without executing cleanup or graceful shutdown hooks. In-flight database transactions are aborted by PostgreSQL.
- **Recovery**: Kubernetes restarts pod.
- **User-Visible Behavior**: Immediate dropped connection (TCP reset) or 502 error.
- **Data-Loss Risk**: Low (Postgres WAL ensures ACID consistency).
- **Retry Behavior**: None at server; client sees connection error.
- **Missing Control**: Realistic memory limits (current AI service limit is 1Gi, which is tight for PyTorch + Transformers); OOM alerts in Alertmanager.
- **Proposed Control**: Increase memory request/limit to 2Gi/4Gi for AI workloads; add Alertmanager alert for `KubePodCrashLooping` and `OOMKilled`.

---

### Scenario 16: Persistent Disk Exhaustion
- **Failure**: `/app/uploads` PVC fills up to 100% capacity.
- **Detection**: `PDFService.save_pdf` throws `OSError: [Errno 28] No space left on device`.
- **Current Behavior**: Upload endpoint raises HTTP 500; temporary files cannot be created.
- **Recovery**: Manual intervention required (volume expansion or manual file deletion).
- **User-Visible Behavior**: All trial uploads fail with internal server error.
- **Data-Loss Risk**: Cannot accept new uploads.
- **Retry Behavior**: None.
- **Missing Control**: Disk usage exporter; automated volume expansion (`allowVolumeExpansion: true`); proactive TTL cleanup of old upload files.
- **Proposed Control**: Enable `allowVolumeExpansion: true` in storage class; configure Prometheus alert at 85% PVC capacity; implement background cron to purge orphaned temporary files older than 24 hours.

---

### Scenario 17: Invalid Environment Configuration
- **Failure**: Missing required environment variable (e.g. `GOOGLE_API_KEY` missing or `DATABASE_URL` malformed).
- **Detection**: Pydantic `BaseSettings` validation error in `app.config.settings.Settings`.
- **Current Behavior**: Application raises `pydantic.ValidationError` during import/startup and exits with non-zero status code.
- **Recovery**: CrashLoopBackOff until configuration is corrected.
- **User-Visible Behavior**: Service unavailable (502 / 503).
- **Data-Loss Risk**: None.
- **Retry Behavior**: Crash loop until fixed.
- **Missing Control**: Pre-deployment configuration validation in CI before pushing manifests to cluster.
- **Proposed Control**: Add automated `python -c "from app.config.settings import settings"` validation step in CI and deployment scripts.

---

### Scenario 18: Failed Database Migration
- **Failure**: Alembic or Flyway migration fails due to SQL syntax error, constraint violation, or lock timeout.
- **Detection**: Migration Job exits with non-zero status code; `deploy.sh` wait command times out.
- **Current Behavior**: Database is left in partially migrated state. `deploy.sh` aborts, but application Deployments were already applied in Step 1 of `deploy.sh`!
- **Recovery**: Manual database inspection and rollback required.
- **User-Visible Behavior**: Application pods crash-loop or fail queries if schema does not match code expectations.
- **Data-Loss Risk**: Moderate if destructive DDL (e.g. `ALTER TABLE DROP COLUMN`) failed halfway.
- **Retry Behavior**: Migration job retries up to `backoffLimit: 3`.
- **Missing Control**: Two-phase deployment: migration must run and succeed BEFORE Deployments are applied; transactional DDL enforcement; migration rollback scripts.
- **Proposed Control**: Decouple migration Job from application manifests; apply application Deployments ONLY after migration Job reports `condition=complete`; write and test down-revisions for all migrations.
