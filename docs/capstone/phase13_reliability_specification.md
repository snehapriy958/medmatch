# Phase 13 — Production Reliability Specification

## 1. Scope & Objective

This specification defines the engineering standards and implementation contracts required to transition MedMatch from a functional prototype to a highly reliable, fault-tolerant clinical trial matching system.

---

## 2. Core Reliability Architecture

```
                  +-----------------------------------+
                  |           Ingress / TLS           |
                  +-----------------+-----------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+-----------------------+                           +--------------------+
|  Frontend (React SPA) |                           | Auth Service (JVM) |
|      Nginx Proxy      |                           | Spring Boot 3.5.x  |
+-----------+-----------+                           +----------+---------+
            |                                                  |
            +-----------------------+--------------------------+
                                    |
                                    v
                        +-----------------------+
                        |   FastAPI AI Service  |
                        | (Pre-warmed Embedding)|
                        +---+---------------+---+
                            |               |
                 +----------+               +----------+
                 v                                     v
       +-------------------+                 +-------------------+
       | PostgreSQL 17     |                 | Redis 8 Broker    |
       | + pgvector        |                 | + AOF Persistence |
       +-------------------+                 +---------+---------+
                                                       |
                                                       v
                                             +-------------------+
                                             | Celery Worker     |
                                             | (Prefork Pool)    |
                                             +-------------------+
```

---

## 3. Application Lifecycle & Startup Pre-warming

### 3.1 Embedding Model Warm-up Contract
- **Problem**: `SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')` takes ~73 seconds to load from disk and warm up on CPU. If deferred to the first request, clients experience gateway timeouts.
- **Contract**:
  1. The embedding model MUST be initialized synchronously inside FastAPI's `@asynccontextmanager lifespan()` hook.
  2. A warm-up forward pass with a dummy string (`"MedMatch startup warm-up"`) MUST complete before the application enters the `yield` state.
  3. If model loading fails, FastAPI MUST throw an exception and abort startup immediately (fail-fast principle).

```python
# Specification for app/main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting MedMatch AI Service initialization...")
    
    # 1. Database pool verification
    logger.info("Verifying database connectivity...")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    
    # 2. Synchronous model pre-warming
    logger.info("Pre-warming SentenceTransformer embedding model...")
    embedding_model = EmbeddingModel()
    dummy_vector = embedding_model.encode("MedMatch startup warm-up")
    assert len(dummy_vector) == 384, "Embedding dimension mismatch"
    logger.info("Embedding model pre-warmed successfully (dimension=%d).", len(dummy_vector))
    
    # 3. Cache verification
    logger.info("Verifying Redis cache connectivity...")
    RedisClient.ping()
    
    logger.info("MedMatch AI Service fully initialized and ready.")
    yield
    
    # Graceful shutdown
    logger.info("Shutting down MedMatch AI Service...")
    engine.dispose()
    logger.info("Database connection pools closed.")
```

---

## 4. Kubernetes Probing Architecture

To eliminate race conditions between 75-second model loading and orchestrator health checks, Kubernetes deployments MUST separate **Startup Probes**, **Readiness Probes**, and **Liveness Probes**.

### 4.1 Probe Specifications

| Probe | Target Endpoint | Interval | Timeout | Failure Threshold | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Startup Probe** | `/api/health/live` | 10s | 5s | 12 (120s max) | Protects the pod from premature termination during the ~75s model warm-up. |
| **Readiness Probe** | `/api/health/ready` | 10s | 5s | 3 | Verifies DB, Redis, and vector extension availability. If DOWN, takes pod out of endpoints without killing it. |
| **Liveness Probe** | `/api/health/live` | 15s | 5s | 3 | Simple process health check. Does NOT query DB or Redis. If deadlocked, restarts pod. |

### 4.2 Eliminating Disk Churn in Readiness Checks
- **Current Defect**: Current `health.py` creates and unlinks `.readiness_check.tmp` on every single scrape (every 10 seconds), causing continuous I/O churn on shared storage.
- **Specification**: Readiness probe MUST check `os.access(upload_dir, os.W_OK)` rather than physically writing and deleting temporary files on disk.

---

## 5. Circuit Breaking & Fallback Policies

### 5.1 External LLM Resilience Contract
- **Circuit Breaker Configuration**:
  - **Failure Threshold**: 5 consecutive failures within 60 seconds.
  - **Recovery Time (Half-Open)**: 30 seconds.
  - **Excluded Exceptions**: Client validation errors (HTTP 400).
  - **Included Exceptions**: Timeouts, HTTP 429, HTTP 500, HTTP 503.
- **Degraded Fallback Mode**:
  - When the circuit breaker is OPEN, the matching engine MUST NOT crash.
  - The engine MUST fallback to deterministic keyword/regex criterion matching against patient conditions and age/gender fields, setting:
    - `eligibility: "UNKNOWN"` or `"PROVISIONAL"`
    - `confidence: 0.50`
    - `explanation: "Automated reasoning degraded: Gemini API temporarily unavailable. Provisional keyword match provided."`

---

## 6. Celery Concurrency & Task Safety

### 6.1 Worker Concurrency Tuning
- **Problem**: Current Kubernetes deployment uses `--pool=solo --concurrency=1`. Solo pool blocks the worker event loop during heavy PyTorch / SentenceTransformer inference, causing Celery control commands and probes to time out.
- **Specification**:
  - Worker pool MUST be set to `prefork` with `--concurrency=2` (or matched to assigned CPU limits).
  - Worker liveness probe MUST NOT spawn heavy new Python processes via `celery inspect ping`.
  - Instead, worker MUST write a timestamped heartbeat file (`/tmp/celery_heartbeat`) via Celery's `heartbeat_tick` signal, and the liveness probe MUST check the file age using a lightweight shell test:
    ```yaml
    livenessProbe:
      exec:
        command:
          - sh
          - -c
          - test $(($(date +%s) - $(stat -c %Y /tmp/celery_heartbeat))) -lt 60
      initialDelaySeconds: 30
      periodSeconds: 15
    ```

### 6.2 Task Idempotency Guarantee
- Every task submitted to `process_trial(file_path, hospital_id)` MUST follow the idempotency pattern:
  1. Verify hospital tenancy.
  2. Compute content hash or query existing trial by `(hospital_id, title, condition, phase)`.
  3. If already present, return existing `trial_id` and exit cleanly.
  4. Perform DB inserts inside a single transaction.
  5. Delete temporary upload file in a `finally` block or upon permanent failure.

---

## 7. Graceful Shutdown & Signal Handling

1. **AI Service (Uvicorn / FastAPI)**:
   - Must handle `SIGTERM` and `SIGINT` gracefully.
   - Set `--timeout-graceful-shutdown 30` in Uvicorn startup.
   - Kubernetes `terminationGracePeriodSeconds` set to `45`.
2. **Celery Worker**:
   - Celery handles `SIGTERM` by finishing in-flight tasks (warm shutdown).
   - Kubernetes `terminationGracePeriodSeconds` set to `90` to allow running trial embedding tasks to complete before forceful SIGKILL.
3. **Spring Boot**:
   - Enable `server.shutdown: graceful` in `application.yml`.
   - Set `spring.lifecycle.timeout-per-shutdown-phase: 30s`.
