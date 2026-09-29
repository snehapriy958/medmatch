# Phase 14.0 — Performance Engineering Audit & Design

## 1. Executive Summary

Phase 14.0 establishes an evidence-grounded performance baseline and bottleneck architecture model for MedMatch V2 at checkpoint `9e8662a` (`feat: complete phase 13.5 observability reliability`).

In accordance with performance engineering principles, **no performance claim is assumed or optimized without evidence**. Every finding, latency component, and architectural constraint in this audit is strictly categorized using a five-tier evidence classification:
1. **MEASURED**: Directly measured and verified by reproducible benchmarks or test suites within this repository.
2. **OBSERVED FROM EXISTING DOCUMENTED MEASUREMENT**: Recorded in prior project capstone artifacts (Phase 5, Phase 12, Phase 13).
3. **DERIVED FROM CONFIGURATION**: Deterministically identified from inspecting schemas, deployment manifests, Dockerfiles, or settings.
4. **ESTIMATED**: Engineering estimations based on external API characteristics or standard component behavior, pending local measurement.
5. **NOT MEASURED**: Critical performance dimensions currently lacking instrumentation or reproducible benchmarks.

### Core Architecture Findings:
- **Gemini Dominance (ESTIMATED)**: External Gemini API roundtrips are estimated to dominate end-to-end matching latency on cache misses (~90–98%) and trial PDF ingestion (~65–85%), but repository-specific latency distribution histograms are currently **NOT MEASURED**.
- **Unindexed Sequential Vector Scans (DERIVED FROM CONFIGURATION)**: Neither `trial_embeddings` nor `criteria_embeddings` has an HNSW or IVFFlat index in production migrations (`0005`, `0007`). In PostgreSQL with pgvector, missing index operator classes force an unindexed sequential scan (`Seq Scan`). Runtime `EXPLAIN` verification is **NOT MEASURED**.
- **Worker Ingestion Serialization (DERIVED FROM CONFIGURATION)**: The Celery worker is configured with `--pool=solo --concurrency=1`, which strictly serializes background ingestion tasks to one task at a time.
- **RWO Storage Constrains Multi-Node Scaling (DERIVED FROM CONFIGURATION)**: The uploads volume (`medmatch-uploads-pvc`) is `ReadWriteOnce` (`RWO`) local-path storage. Worker replicas are pinned by `podAffinity` to the single node running `ai-service`.
- **Code-Path Verified N+1 Query Patterns (DERIVED FROM CONFIGURATION / CODE-PATH VERIFIED)**: Candidate criteria retrieval in `MatchingService._get_complete_trial_criteria` exhibits an $N+1$ query loop, and trial ingestion executes sequential single-row inserts and `flush()` round-trips for each criterion. Runtime latency impact is **NOT MEASURED**.
- **Connection Capacity vs. Pool Risk (DERIVED FROM CONFIGURATION)**: Total configured client connection capacity ($30 + 20 + 30 = 80$ at baseline replicas, scaling up to $140$ under worker HPA) exceeds PostgreSQL's default `max_connections` (100). No runtime connection exhaustion has been observed; this is a **configuration-based risk**.

---

## 2. Performance Evidence Baseline

The following baseline compiles all known performance measurements and estimates across MedMatch V2:

| Metric / Dimension | Value | Evidence Classification | Source / Verification Method |
| :--- | :--- | :--- | :--- |
| **Frontend Production Build** | 1.22s – 2.50s | **MEASURED** | Vite v8.2.1 build in `medmatch-ui` (`npm run build`) |
| **AI Service Test Suite Execution** | 68.62s (78 tests) | **MEASURED** | `pytest -q` on Python 3.13 venv (Phase 13.5) |
| **Auth Service Test Suite Execution** | 24.77s (85 tests) | **MEASURED** | `mvnw test` on Java 21 (Phase 13.5) |
| **Small Cohort Exact Scan Retrieval** | < 15ms (< 1,000 trials) | **OBSERVED** | Documented in `phase5_retrieval_report.md` (L128) |
| **Clinical Safety Regression Suite** | 1.49s (48 tests) | **OBSERVED** | Documented in `phase12_clinical_safety_report.md` (L229) |
| **Full Research Regression Suite** | 5.30s (334 tests) | **OBSERVED** | Documented in `phase12_clinical_safety_report.md` (L230) |
| **SentenceTransformer Initialization** | ~73s on CPU container | **OBSERVED** | Documented in `phase13_production_readiness_matrix.md` (L32) |
| **Single SentenceTransformer Inference**| 50ms – 150ms / text | **ESTIMATED** | Standard CPU benchmark for `all-MiniLM-L6-v2`; unmeasured in repo |
| **Gemini 2.5 Flash Evaluation Latency** | 1,500ms – 6,000ms | **ESTIMATED** | Typical Google GenAI SaaS roundtrip; unmeasured in repo |
| **Gemini Trial Extraction Latency** | 3,000ms – 12,000ms | **ESTIMATED** | Typical multi-page extraction roundtrip; unmeasured in repo |
| **PDF Text Extraction (PyPDF)** | 100ms – 500ms / file | **ESTIMATED** | Standard 5–15 page protocol PDF; unmeasured in repo |
| **Trial PDF Ingestion Task Duration** | 5s – 20s / trial | **ESTIMATED** | Cumulative estimate under solo worker; unmeasured in repo |
| **API Endpoint P50/P95/P99 Latency** | *Unknown* | **NOT MEASURED** | No load test harness or latency histogram exists |
| **Pgvector Query Latency at 10k+ Trials**| *Unknown* | **NOT MEASURED** | Corpus evaluated only at small synthetic scale (<300) |
| **Runtime EXPLAIN on Vector Queries** | *Unknown* | **NOT MEASURED** | Query plans not captured on production-sized tables |
| **Redis Throughput Under Load** | *Unknown* | **NOT MEASURED** | No sustained Redis benchmark executed |
| **Worker Queue Wait Time Under Load** | *Unknown* | **NOT MEASURED** | Queue latency not instrumented |
| **Container Startup to Kubelet Ready** | *Unknown* | **NOT MEASURED** | Real cluster rollout timing not recorded |

---

## 3. Request Latency Audit & Decomposition

### 3.1. Major API Paths

```
[Client Request]
       │
       ▼
 ┌───────────────┐
 │ Ingress NGINX │ (Estimated: ~1-2ms)
 └───────┬───────┘
         │
         ├────────────────────────────────────────┬────────────────────────────────────────┐
         │                                        │                                        │
         ▼                                        ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐                    ┌──────────────────┐
│   Auth Service   │                    │    AI Service    │                    │  Celery Worker   │
│  (Spring Boot)   │                    │    (FastAPI)     │                    │  (Async Queue)   │
└────────┬─────────┘                    └────────┬─────────┘                    └────────┬─────────┘
         │                                        │                                        │
         ▼                                        ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐                    ┌──────────────────┐
│ PostgreSQL Auth  │                    │ PostgreSQL / Vec │                    │ Shared Local PVC │
│ (HikariCP / JPA) │                    │ (SQLAlchemy)     │                    │ (/app/uploads)   │
└──────────────────┘                    └────────┬─────────┘                    └────────┬─────────┘
                                                 │                                       │
                                                 ▼                                       ▼
                                        ┌──────────────────┐                    ┌──────────────────┐
                                        │   Redis Cache    │                    │  Google Gemini   │
                                        │  (DB 0 / DB 1)   │                    │  (REST / HTTPS)  │
                                        └────────┬─────────┘                    └──────────────────┘
                                                 │
                                                 ▼
                                        ┌──────────────────┐
                                        │  Google Gemini   │
                                        │ (60s Max Timeout)│
                                        └──────────────────┘
```

### 3.2. Latency Component Breakdown by Evidence Tier

1. **Authentication (`POST /api/auth/login`)**:
   - BCrypt password verification: **ESTIMATED** ~80–120ms (standard BCrypt work factor 10).
   - RSA JWT signing: **ESTIMATED** ~2–5ms (in-memory crypto).
   - Database query: **ESTIMATED** ~2–5ms (`SELECT * FROM users WHERE email = ...`).
   - Total HTTP latency: **ESTIMATED** ~85–130ms. Runtime P50/P95/P99 is **NOT MEASURED**.

2. **Trial Upload (`POST /api/trials/upload`)**:
   - Multipart file upload & filesystem write to `/app/uploads`: **ESTIMATED** ~10–30ms for 5MB PDF.
   - Redis Celery task enqueue (`process_trial.delay`): **ESTIMATED** ~2–5ms.
   - Total HTTP latency: **ESTIMATED** ~15–40ms. Runtime P50/P95/P99 is **NOT MEASURED**.

3. **Trial Matching / Eligibility Evaluation (`POST /api/matching/evaluate`)**:
   - JWT RS256 signature verification: **ESTIMATED** ~1ms.
   - Redis retrieval cache check: **ESTIMATED** ~1–3ms.
   - *On Retrieval Cache Miss*:
     - Redis embedding cache check: **ESTIMATED** ~1–3ms.
     - SentenceTransformer CPU inference (`model.encode`): **ESTIMATED** ~50–150ms.
     - Vector similarity query (`find_similar_criteria`): **ESTIMATED** ~10–30ms at current corpus size.
     - Criteria loading ($N+1$ query loop for $N$ trials): **ESTIMATED** ~5–15ms.
     - Redis retrieval cache write: **ESTIMATED** ~1–3ms.
   - Prompt construction: **ESTIMATED** <1ms.
   - Redis LLM cache check: **ESTIMATED** ~1–3ms.
   - *On LLM Cache Miss*:
     - Google Gemini API call (`gemini-2.5-flash`): **ESTIMATED** ~1,500–6,000ms.
     - Redis LLM cache write: **ESTIMATED** ~1–3ms.
   - Response validation & audit log persistence: **ESTIMATED** ~5–10ms.
   - **Theoretical Total Latency (Full Cache Miss)**: **ESTIMATED** ~1,600–6,300ms.
   - **Theoretical Total Latency (Full Cache Hit)**: **ESTIMATED** ~15–35ms.
   - **Note on Percentages**: Gemini is estimated to represent ~90% to 98% of total response latency on cache misses based on typical external network roundtrip times, but exact end-to-end percentiles are **NOT MEASURED**.

4. **Health / Readiness (`GET /api/health/ready`)**:
   - Database checks (`SELECT 1`, Alembic version, pgvector extension): **ESTIMATED** ~3–8ms.
   - Redis ping: **ESTIMATED** ~1–3ms.
   - Non-destructive filesystem check (`os.access`): **ESTIMATED** <0.1ms.
   - Total HTTP latency: **ESTIMATED** ~5–12ms. Runtime P50/P95/P99 is **NOT MEASURED**.

---

## 4. AI Inference Performance

### 4.1. SentenceTransformer (`all-MiniLM-L6-v2`)
- **Initialization Lifecycle**:
  - Implemented as a singleton in [`services/ai-service/app/embeddings/model.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/embeddings/model.py) using thread-safe double-checked locking (`_lock = Lock()`).
  - **Lifecycle Breakdown**:
    1. *Container Startup*: Fast (~1–3s to launch Python interpreter and dependencies).
    2. *FastAPI Lifespan*: Runs `init_db()` in [`app/main.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/main.py). The embedding model is **not** loaded during lifespan.
    3. *FastAPI Readiness*: Responds HTTP 200 on `/api/health/ready` before the model is loaded.
    4. *Model Initialization / First Request*: Triggered lazily on the first client call to `/api/matching/search` or `/api/matching/evaluate`.
  - **Cold-Start Latency**: A ~73-second warm-up delay on low-resource CPU containers was **OBSERVED** in the Phase 13.0 production readiness matrix (`phase13_production_readiness_matrix.md` L32). Because the model is not pre-warmed during startup, the initial client request absorbing model initialization suffers this cold-start delay.
- **Inference Mode & Concurrency**:
  - Hardcoded to `device="cpu"` (`SentenceTransformer(str(cls.MODEL_PATH), device="cpu")`).
  - Strictly single-text: `encode(self, text: str) -> list[float]`. No batching API (`encode_batch`) exists (**DERIVED FROM CONFIGURATION**).
  - Synchronous CPU work: Under FastAPI `def` endpoints, calls execute in Starlette thread pools. Multiple concurrent embedding requests will compete for the single CPU core assigned to `ai-service` in Kubernetes (`limits.cpu: "1"`).
- **Memory Footprint**:
  - PyTorch runtime + model weights consume **ESTIMATED** ~400–500MB resident memory per process.
  - Memory is duplicated across processes: `ai-service` and `celery-worker` maintain separate in-memory model instances (**DERIVED FROM CONFIGURATION**).

### 4.2. Google Gemini (`gemini-2.5-flash`)
- **Integration**: Synchronous HTTPS calls via `google-genai` SDK v2.20.0 in [`services/ai-service/app/services/llm_service.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/llm_service.py).
- **Timeout Enforcement**: Explicit 60-second client-level timeout (`HttpOptions(timeout=60000)`) verified in Phase 13.5 (**DERIVED FROM CONFIGURATION**).
- **Retry Policy**: Tenacity retries up to 3 attempts with exponential backoff (`min=2s, max=10s`). Maximum theoretical retry duration under consecutive timeouts is $\approx 180$ seconds (**DERIVED FROM CONFIGURATION**).
- **Latency Distribution**: Empirical P50/P95/P99 latency histograms for Gemini calls in this repository are **NOT MEASURED**.

---

## 5. Retrieval Performance Audit

### 5.1. Production Query Architecture
Production retrieval is implemented in [`MatchingRepository.find_similar_criteria`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/repositories/matching_repository.py):
```sql
WITH ranked_trials AS (
    SELECT
        t.id AS trial_id, t.title, t.condition, t.phase, t.status, t.brief_summary,
        te.embedding <=> CAST(:embedding AS vector) AS distance
    FROM trials t
    JOIN trial_embeddings te ON te.trial_id = t.id
    WHERE t.hospital_id = :hospital_id
      AND EXISTS (SELECT 1 FROM trial_criteria tc WHERE tc.trial_id = t.id)
    ORDER BY te.embedding <=> CAST(:embedding AS vector) ASC, t.id ASC
    LIMIT :trial_limit
),
ranked_criteria AS (
    SELECT
        rt.trial_id, rt.title, rt.condition, rt.phase, rt.status, rt.brief_summary,
        tc.id, tc.criteria_type, tc.description, rt.distance,
        ROW_NUMBER() OVER (
            PARTITION BY rt.trial_id
            ORDER BY ce.embedding <=> CAST(:embedding AS vector) ASC, tc.id ASC
        ) AS criterion_rank
    FROM ranked_trials rt
    JOIN trial_criteria tc ON tc.trial_id = rt.trial_id
    JOIN criteria_embeddings ce ON ce.criteria_id = tc.id
)
SELECT id, trial_id, title, condition, phase, status, brief_summary, criteria_type, description, distance
FROM ranked_criteria
WHERE criterion_rank = 1
ORDER BY distance ASC, trial_id ASC, id ASC;
```

### 5.2. Sequential Vector Scan Verification
- **Schema Evidence**: Alembic migrations `0005_create_criteria_embeddings_table.py` and `0007_create_trial_embeddings_table.py` create b-tree indexes on `criteria_id` and `trial_id`, but **no index on the `embedding` column** (**DERIVED FROM CONFIGURATION**).
- **Query Planner Implication**: In PostgreSQL pgvector, distance operators (`<=>`) without a supporting index operator class (`vector_cosine_ops`) require an unindexed sequential table scan (`Seq Scan`).
- **Runtime Measurement Status**: Runtime `EXPLAIN (ANALYZE, BUFFERS)` execution against production-scale data is **NOT MEASURED**.
- **Reason for HNSW Absence**: HNSW was evaluated in research phase E4 (`reproducibility_specification.md` L53; `phase5_retrieval_report.md` L125–131) to benchmark recall trade-offs, but was never packaged into an active production migration (**OBSERVED**).

### 5.3. Role of `top_k=5`
- In `MatchingRepository.find_similar_criteria`, `LIMIT :trial_limit` (default 5) does **not** prune the initial vector scan over tenant trials: every trial embedding in the hospital partition is scanned to compute cosine distance (**DERIVED FROM CONFIGURATION**).
- However, `top_k=5` strictly constrains downstream execution:
  - Prunes `ranked_criteria` joins to criteria of candidate trials only.
  - Limits N+1 queries in `MatchingService._get_complete_trial_criteria` to at most 5 database calls.
  - Constrains prompt token volume and Gemini reasoning duration.

---

## 6. Database Performance Audit

### 6.1. Connection Capacity vs. Pool Risk
- **Configured Pools**:
  - `ai-service`: `pool_size = 10, max_overflow = 20` (SQLAlchemy, max 30 per pod). Configured replicas: **1** (`strategy: Recreate`) (**DERIVED FROM CONFIGURATION**).
  - `auth-service`: HikariCP default `maximum-pool-size = 10`. Configured replicas: **2** (**DERIVED FROM CONFIGURATION**).
  - `celery-worker`: Uses `SessionLocal()` inheriting `pool_size = 10, max_overflow = 20`. Configured replicas: **1** (scales to 3 under HPA) (**DERIVED FROM CONFIGURATION**).
- **Capacity Analysis**:
  - At baseline replicas: 1 AI pod (30) + 2 Auth pods (20) + 1 Worker pod (30) = **80 theoretical maximum connections**.
  - At peak HPA scaling (3 worker pods): 1 AI pod (30) + 2 Auth pods (20) + 3 Worker pods (90) = **140 theoretical maximum connections**.
  - Default PostgreSQL `max_connections` is **100** (**DERIVED FROM CONFIGURATION**).
  - **Finding Status**: No connection exhaustion has been observed in runtime logs. PERF-04 is classified as a **CONFIGURATION-BASED RISK**, not an observed exhaustion.

### 6.2. Code-Path Verified Query Patterns

| Location | Pattern | Evidence / Code Path | Status |
| :--- | :--- | :--- | :--- |
| `MatchingService._get_complete_trial_criteria` | N+1 criteria queries | Loops over `trial_ids` executing `list_by_trial(UUID(trial_id))` ([`matching_service.py:L268-275`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/matching_service.py#L268-L275)) | **CODE-PATH VERIFIED** |
| `TrialService.process_pdf` | Repeated single-row inserts & flushes | Iterates over criteria calling `create_trial_embedding` with explicit `flush()` per item ([`trial_service.py:L431-436`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/trial_service.py#L431-L436)) | **CODE-PATH VERIFIED** |
| `AuditLogRepository.findTop50...` | Unindexed sort on `created_at` | `ORDER BY created_at DESC LIMIT 50`; `audit_logs` has no index on `created_at` ([`V4__create_audit_logs_table.sql`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/src/main/resources/db/migration/V4__create_audit_logs_table.sql)) | **CODE-PATH VERIFIED** |
| `AuditLogRepository.countByAction` | Unindexed filter on `action` | `WHERE action = ...`; `audit_logs` has no index on `action` ([`V4__create_audit_logs_table.sql`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/services/auth-service/src/main/resources/db/migration/V4__create_audit_logs_table.sql)) | **CODE-PATH VERIFIED** |

---

## 7. Redis Performance Audit

- **Shared Database (DB 0)**:
  - `REDIS_URL` defaults to `redis://redis:6379/0` (app cache).
  - `CELERY_BROKER_URL` defaults to `redis://redis:6379/0` (task broker) (**DERIVED FROM CONFIGURATION**).
  - `CELERY_RESULT_BACKEND` defaults to `redis://redis:6379/1` (task backend).
  - App cache and Celery broker co-exist in DB 0. If Redis reaches memory limits and an eviction policy like `allkeys-lru` is applied, Celery task queue structures risk eviction (**CONFIGURATION-BASED RISK**).
- **TTL Enforcement**:
  - `CacheService.set` explicitly enforces positive TTLs (`EMBEDDING_CACHE_TTL = 7 days`, `RETRIEVAL_CACHE_TTL = 1 hour`, `LLM_CACHE_TTL = 30 minutes`). Unbounded key growth is prevented under normal operation (**DERIVED FROM CONFIGURATION**).
- **Throughput & Saturation**: Redis operation latency and memory growth curves are **NOT MEASURED**.

---

## 8. Celery Throughput & Worker Scaling Audit

- **Solo Pool Serialization**:
  - Worker runs with `--pool=solo --concurrency=1` ([`infra/kubernetes/worker/deployment.yaml`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/worker/deployment.yaml)).
  - Single process and single thread: tasks execute strictly sequentially (**DERIVED FROM CONFIGURATION**).
  - During I/O-bound Gemini extraction (estimated 3–12s), the worker thread blocks, preventing concurrent task execution.
- **RWO Storage Lock on Scaling**:
  - `medmatch-uploads-pvc` is `ReadWriteOnce` on `local-path` storage (**DERIVED FROM CONFIGURATION**).
  - Worker pods specify `podAffinity` requiring co-location with `ai-service` on the same physical node (**DERIVED FROM CONFIGURATION**).
  - Horizontal scaling across multiple cluster nodes is architecturally prohibited without shared network storage or object storage.
- **Throughput Metrics**: Effective task throughput under concurrent uploads is **NOT MEASURED**.

---

## 9. Performance Evidence Table

The following table catalogs every performance finding, its evidence classification, source, confidence, and engineering impact:

| ID | Finding Title | Evidence Classification | Measured? | Source / File Reference | Confidence | Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PERF-01** | SentenceTransformer Lazy Loading Cold-Start | **OBSERVED** | Partially (~73s documented) | `app/embeddings/model.py`, `phase13_production_readiness_matrix.md` | **HIGH** | **HIGH** |
| **PERF-02** | Unindexed Sequential Vector Scans | **DERIVED** | No | `alembic/versions/0005`, `0007` | **HIGH** | **HIGH** |
| **PERF-03** | Celery Solo Worker Strict Task Serialization | **DERIVED** | No | `infra/kubernetes/worker/deployment.yaml` | **HIGH** | **HIGH** |
| **PERF-04** | Connection Capacity Exceeds Postgres Default | **DERIVED** | No | `database.py`, `application.yml` | **HIGH** | **MEDIUM** |
| **PERF-05** | N+1 Criteria Query Pattern in Matching | **DERIVED / CODE-PATH** | No | `matching_service.py:L268-275` | **HIGH** | **MEDIUM** |
| **PERF-06** | Unbatched Criteria Embedding & DB Flush Loops | **DERIVED / CODE-PATH** | No | `trial_service.py:L431-436` | **HIGH** | **MEDIUM** |
| **PERF-07** | RWO Upload PVC Constrains Multi-Node Worker Scale | **DERIVED** | No | `worker/deployment.yaml`, `uploads-pvc.yaml` | **HIGH** | **MEDIUM** |
| **PERF-08** | Missing Indexes on `audit_logs(created_at, action)`| **DERIVED / CODE-PATH** | No | `V4__create_audit_logs_table.sql` | **HIGH** | **LOW** |
| **PERF-09** | Celery Broker and Cache Share Redis DB 0 | **DERIVED** | No | `settings.py:L208, L236` | **HIGH** | **LOW** |
| **PERF-10** | Gemini Latency Dominates Matching Response | **ESTIMATED** | No | `llm_service.py` | **MEDIUM** | **INFORMATIONAL** |

---

## 10. Benchmark Gap & Measurement Plan (Phase 14.1 Requirement)

Before implementing any code optimizations, the following performance dimensions must be empirically measured in Phase 14.1:

1. **Embedding Model Inference Latency**:
   - Measure P50, P95, and P99 latency for single-text encoding on CPU.
   - Benchmark batch sizes (1, 4, 8, 16, 32) to measure potential throughput gains.
2. **Retrieval Latency vs. Corpus Scale**:
   - Measure P50, P95, P99 query latency for cosine distance search across synthetic corpora of 100, 1,000, 10,000, and 50,000 trials.
   - Capture execution plans using `EXPLAIN (ANALYZE, BUFFERS)` to record buffer hits, disk reads, and scan types.
3. **Gemini API Roundtrip Latency**:
   - Collect empirical P50, P95, P99 latency histograms for `extract_trial_information` and `evaluate_eligibility_raw`.
4. **End-to-End Matching Latency Distribution**:
   - Benchmark `/api/matching/evaluate` under cold-cache and warm-cache conditions at concurrency levels: **1, 5, 10, and 25 concurrent requests**.
   - Measure P50, P95, P99, error rate (5xx), and throughput (requests/sec).
5. **Trial Ingestion Pipeline Duration**:
   - Profile the exact execution duration of each stage in `process_pdf` (PyPDF, Gemini, embedding loop, DB commit) on standardized test PDFs.
6. **Celery Worker Queue Saturation**:
   - Measure queue wait time, task execution time, and task throughput under 5 and 10 concurrent PDF uploads.
7. **Resource Utilization Under Load**:
   - Track CPU utilization and Linux CFS throttling percentages against Kubernetes cgroup limits (`1 core` in AI, `0.5 core` in worker).
   - Profile peak RSS memory usage to assess OOM risk against 1Gi limits.
8. **Database Connection Pool Utilization**:
   - Monitor active vs. idle connections in SQLAlchemy and HikariCP connection pools during concurrent load testing.

---

## 11. Phase 14 Implementation Boundary & Optimization Hypotheses

The following candidate optimizations represent **hypotheses to validate with benchmarks before optimization**. No code change will be claimed to improve performance until proven by Phase 14.1 measurements:

1. **Hypothesis 1 — Startup Pre-Warming (`PERF-01`)**:
   - *Target*: `services/ai-service/app/main.py` (`lifespan`).
   - *Hypothesis*: Initializing `EmbeddingModel()` during application lifespan will eliminate the cold-start latency spike on the first client request, shifting initialization time to container startup.
2. **Hypothesis 2 — Criteria Batch Querying (`PERF-05`)**:
   - *Target*: `services/ai-service/app/repositories/trial_criteria_repository.py` and `matching_service.py`.
   - *Hypothesis*: Replacing the N+1 loop in `_get_complete_trial_criteria` with `WHERE trial_id IN (...)` will reduce database network round-trips from $N$ to 1 during matching evaluation.
3. **Hypothesis 3 — Bulk Persistence for Ingested Criteria (`PERF-06`)**:
   - *Target*: `services/ai-service/app/services/trial_service.py`.
   - *Hypothesis*: Grouping criteria embedding records into a single bulk insert and atomic flush will reduce database round-trips during PDF ingestion from $M$ to 1.
4. **Hypothesis 4 — Audit Log Indexing (`PERF-08`)**:
   - *Target*: `services/auth-service/src/main/resources/db/migration/`.
   - *Hypothesis*: Adding b-tree indexes on `audit_logs(created_at DESC)` and `audit_logs(action)` will prevent sequential table scans as audit records accumulate.
5. **Hypothesis 5 — Connection Pool Configuration (`PERF-04`)**:
   - *Target*: `services/ai-service/app/config/settings.py`.
   - *Hypothesis*: Setting `DB_POOL_SIZE = 5, DB_MAX_OVERFLOW = 5` will bound peak connections per AI pod to 10, keeping total cluster connection demand safely below PostgreSQL's default limit.

### Explicitly Deferred Items:
- **HNSW Vector Index Migration**: Deferred until clinical recall benchmarks prove that approximate nearest neighbor search maintains 100% recall.
- **Celery Multi-Process Concurrency**: Deferred until multi-process PyTorch memory consumption is profiled.
- **Object Storage Migration**: Deferred to a future cloud storage phase.
- **Redis Database Splitting**: Deferred to infrastructure hardening.

---

## 12. Validation Plan

Validation for this audit phase is strictly read-only:
- `git status`
- `git diff --check`
- `git diff --stat`
- `git diff --name-only`
- Manifest validation: `kubectl kustomize .`
- No source code changes. No migrations applied. No container configs modified.

---

## 13. Explicit Out-of-Scope Items
- Modifying application source code.
- Modifying database schemas or applying migrations.
- Modifying Kubernetes manifests, Dockerfiles, or Docker Compose.
- Changing clinical reasoning, eligibility rules, prompts, or model selection.
