# Phase 13 — Production Engineering Error Taxonomy

## 1. Overview & Classification Schema

The MedMatch Production Engineering Error Taxonomy (`PE-01` through `PE-20`) provides an exhaustive, evidence-backed classification of infrastructure, deployment, runtime, and security failures identified in the repository audit.

---

## 2. Canonical Error Categories

### PE-01: Configuration Failure
- **Definition**: Missing, invalid, or mismatched configuration parameters preventing service operation.
- **Repository Evidence**: Missing `.env.example`; `docker-compose.yml` mounting whole migration directory; `SPRING_PROFILES_ACTIVE: dev` in Compose.
- **Impact**: Container failure on startup or unintended development features enabled in production.
- **Severity**: HIGH

### PE-02: Secret Exposure
- **Definition**: Unencrypted sensitive credentials, private keys, or API tokens committed in code or manifests.
- **Repository Evidence**: `private.pem` committed in `services/auth-service/.../keys/`; real Google API key in `.env` and `secrets.yaml`.
- **Impact**: Full compromise of authentication signing authority and cloud provider billing abuse.
- **Severity**: CRITICAL

### PE-03: Container Privilege Escalation Failure
- **Definition**: Containers executing as root (UID 0) or requesting unnecessary host privileges.
- **Repository Evidence**: `init-uploads` initContainer in `infra/kubernetes/worker/deployment.yaml` running as `runAsUser: 0` with `chmod 777`.
- **Impact**: Increased container breakout attack surface.
- **Severity**: HIGH

### PE-04: Startup Race Condition
- **Definition**: Dependent service starting before its upstream dependencies are fully initialized and healthy.
- **Repository Evidence**: `docker-compose.yml` frontend depending on `ai-service` via `condition: service_started` instead of `service_healthy`.
- **Impact**: Transient HTTP 502 errors when users connect to frontend while backend is still warming up.
- **Severity**: HIGH

### PE-05: Health-Check False Negative / Positive
- **Definition**: Orchestrator probes failing on healthy workloads or reporting healthy when degraded.
- **Repository Evidence**: AI service probes with 15s/30s delays terminating pods during the 73s embedding model warm-up; worker `celery inspect ping` hanging during task execution under `--pool=solo`.
- **Impact**: Continuous CrashLoopBackOff of healthy workloads.
- **Severity**: HIGH

### PE-06: Database Migration Conflict / Failure
- **Definition**: Colliding migration versions, multiple heads, or non-idempotent DDL scripts.
- **Repository Evidence**: Duplicate Flyway version prefixes (`V1` through `V4`) in `services/auth-service/.../db/migration`; orphaned partial `alembic/versions` at root.
- **Impact**: Migration job crash halting entire deployment.
- **Severity**: CRITICAL

### PE-07: Database Connection Pool Exhaustion
- **Definition**: High request volume saturating connection pool limits without queuing or timeout protection.
- **Repository Evidence**: Lack of PgBouncer or connection pool proxy; unmetered concurrent search queries.
- **Impact**: Database connection rejections and cascading HTTP 500 errors.
- **Severity**: HIGH

### PE-08: Redis Broker / Cache Failure
- **Definition**: Broker unavailability, unauthenticated access, or connection timeouts.
- **Repository Evidence**: Redis running without password authentication in Compose and k8s; unhandled connection loss during task queueing.
- **Impact**: Inability to queue PDF processing jobs; cache lookups failing.
- **Severity**: HIGH

### PE-09: Celery Task Loss
- **Definition**: Background tasks lost or permanently stalled due to worker crash or volume unmount.
- **Repository Evidence**: Tasks submitted with local file paths on ephemeral volumes; if worker dies and node changes, file is lost.
- **Impact**: Incomplete trial ingestion requiring manual user re-upload.
- **Severity**: MEDIUM

### PE-10: Duplicate Processing Hazard
- **Definition**: Re-processing of previously ingested or in-flight data causing resource waste or constraint violations.
- **Repository Evidence**: Missing upload file content hashing; reliance on late database duplicate checks.
- **Impact**: Unnecessary LLM token expenditure on identical documents.
- **Severity**: LOW

### PE-11: External Model Timeout
- **Definition**: External AI API (Google Gemini) taking excessive time or hanging without timeout bounds.
- **Repository Evidence**: No explicit per-request timeout passed to `client.models.generate_content` in `LLMService`.
- **Impact**: Client connection timeouts after prolonged hangs.
- **Severity**: MEDIUM

### PE-12: Model API Failure / Rate Limiting
- **Definition**: Downstream AI provider returning HTTP 429, 500, or 503 errors.
- **Repository Evidence**: Tenacity retries up to 3 times, but lacks a circuit breaker or degraded fallback response.
- **Impact**: Complete failure of clinical trial matching when LLM provider experiences downtime.
- **Severity**: HIGH

### PE-13: Missing Observability
- **Definition**: Inability to monitor system metrics, logs, or traces due to missing monitoring infrastructure.
- **Repository Evidence**: 0-byte Prometheus and Alertmanager files in `infra/monitoring`; missing Grafana manifests; missing latency histograms.
- **Impact**: Blindness to production incidents, capacity exhaustion, and SLA breaches.
- **Severity**: HIGH

### PE-14: Information Leakage in Logs
- **Definition**: Sensitive tokens, session pointers, or personal data written to system logs.
- **Repository Evidence**: `deps.py` printing raw JWT claims (`AI SERVICE JWT USER`); `trial_service.py` printing session pointers; Hibernate tracing SQL bind values.
- **Impact**: Compliance violation (HIPAA/GDPR) and potential token leakage to log collectors.
- **Severity**: HIGH

### PE-15: Tenant Isolation Failure
- **Definition**: Accessing or leaking data across hospital tenant boundaries.
- **Repository Evidence**: `GET /api/tasks/{task_id}` has no authentication or hospital tenant checks; any user can poll any task.
- **Impact**: Cross-tenant visibility into trial ingestion metadata and system errors.
- **Severity**: HIGH

### PE-16: Deployment Rollback Failure
- **Definition**: Deploying new releases without automated verification, preventing clean rollbacks.
- **Repository Evidence**: `deploy.sh` applies Deployments before migrations finish; `ai-service` uses `Recreate` strategy; no automated rollback on failure.
- **Impact**: Service downtime during failed deployments requiring emergency manual triage.
- **Severity**: HIGH

### PE-17: Resource Exhaustion (OOM / CPU Throttling)
- **Definition**: Container exceeding memory or CPU limits under peak load.
- **Repository Evidence**: AI service constrained to 1Gi memory in k8s deployment despite running PyTorch, SentenceTransformer, and FastAPI.
- **Impact**: Pod OOMKilled by kernel.
- **Severity**: HIGH

### PE-18: Storage Failure / Volume Attachment Collision
- **Definition**: PVC attachment errors or disk exhaustion preventing file operations.
- **Repository Evidence**: `uploads-pvc.yaml` configured as `ReadWriteOnce` mounted across independent deployments (`ai-service` and `worker`).
- **Impact**: Multi-Attach error causing pods to remain stuck in `ContainerCreating` on multi-node clusters.
- **Severity**: CRITICAL

### PE-19: CI Regression / Test Gate Omission
- **Definition**: Failure of CI pipelines to detect regressions or validate production code prior to merge.
- **Repository Evidence**: `ci.yaml` runs `compileall` on `ai-service` rather than `pytest`; secret scanner produces false positive on `JwtService.java`.
- **Impact**: Broken code merged into main without detection.
- **Severity**: HIGH

### PE-20: Configuration Drift
- **Definition**: Desynchronization between Docker Compose, Kubernetes, and local development configurations.
- **Repository Evidence**: Ingress routes `/api` to `auth-service`, while Compose Nginx routes `/api/ai` to `ai-service`; different environment variable names (`LLM_API_KEY` vs `GOOGLE_API_KEY`).
- **Impact**: Features functioning locally in Compose fail upon deployment to Kubernetes.
- **Severity**: HIGH
