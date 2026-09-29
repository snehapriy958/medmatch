# Phase 15 Evaluation & Performance Dashboard Report

**Project:** MedMatch V2 Clinical Trial Matching System
**Milestone:** Phase 15 — Evaluation & Performance Dashboard
**Status:** Completed & Validated
**Git Checkpoint:** Branch `capstone/phase-13-production-engineering`
**Security & RBAC Boundary:** `SYSTEM_ADMIN`, `HOSPITAL_ADMIN`, `RESEARCH_COORDINATOR`

---

## 1. Executive Summary

Phase 15 delivers an empirical, read-only research observability and performance dashboard for MedMatch V2. The dashboard surfaces historical evaluation artifacts across Phases 5 through 14 without modifying the underlying clinical matching algorithms, retrieval logic, prompt engineering, database schemas, or safety gate implementations.

Every displayed metric is anchored directly to immutable source artifacts stored in `results/` and `data/fixtures/` and is strictly qualified using the repository's standardized evidence classification taxonomy.

---

## 2. Evidence Classification Framework

To preserve scientific and clinical integrity, every quantitative and qualitative assertion in the dashboard carries an explicit evidence classification:

| Evidence Classification | Definition & Scope | Example in MedMatch V2 |
| :--- | :--- | :--- |
| **`MEASURED`** | Empirically quantified under a reproducible benchmark harness on local runtime infrastructure. | Phase 14.2 criteria loading latency reduction (121.55 ms → 25.34 ms; 79.15%). |
| **`OFFLINE EXPERIMENT`** | Precomputed deterministic research script execution over frozen cohorts. | Phase 5 dense vs hybrid retrieval comparisons; Phase 7 RAG vs non-RAG. |
| **`SYNTHETIC / DEVELOPMENT FIXTURE`** | Verified against deterministic test fixtures ($n=6$ patients, 14 adversarial error injections). Strictly prohibited from supporting clinical efficacy claims. | Phase 11 component ablations (A1–A5); Phase 12 adversarial error injections (14/14). |
| **`CONFIGURATION RISK ONLY`** | Derived from architectural configurations rather than empirical load testing. | Celery single-concurrency serialization (`--pool=solo --concurrency=1`). |
| **`NOT MEASURED`** | Deliberately omitted from offline benchmark harnesses to prevent fabricated numbers or unauthenticated network failures. | Live Gemini LLM inference latency; external network HTTP socket latency. |

---

## 3. Phase 14 Performance Methodology & Distinction

The dashboard strictly enforces the separation between historical references and same-run controlled experiments:

### 3.1 Frozen Phase 14.1 Historical Reference
- **Baseline Commit:** `03cd93a`
- **Workload:** 5 candidate trials, 77 criteria
- **Criteria Loading Mean:** $128.32\text{ ms}$
- **Total Local Pipeline Mean:** $181.60\text{ ms}$
- **Sequential SQL Queries:** 5 queries
- **Status:** Frozen historical reference. Not used as the denominator for cross-run percentage calculations to avoid inter-run system scheduler and CPU governor variance.

### 3.2 Phase 14.2 Same-Run Controlled Experiment
- **Headline Query Reduction:** $5\text{ queries} \to 1\text{ query}$ ($80.0\%$ reduction, 4 queries eliminated)
- **Criteria Loading Latency:** $121.55\text{ ms} \to 25.34\text{ ms}$ ($79.15\%$ improvement, $96.21\text{ ms}$ absolute reduction)
- **Total Local Pipeline Latency:** $163.63\text{ ms} \to 67.57\text{ ms}$ ($58.71\%$ improvement, $96.06\text{ ms}$ absolute reduction)
- **Direct PostgreSQL Latency:** $118.51\text{ ms} \to 2.79\text{ ms}$ ($97.65\%$ improvement, $115.72\text{ ms}$ absolute reduction)
- **Secondary ORM Selectin Observation:** Under unconfigured ORM relationship loading, cascading selectin loads emitted 55 queries. Applying `noload` options collapsed this cascade to 1 query.
- **Unmeasured Components:** Gemini LLM generation latency and real external HTTP network socket latency are prominently flagged as `NOT MEASURED`.

---

## 4. Architecture & Data Flow

```
[ Frontend: React 19 + Tailwind v4 + Recharts ]
                      │
                      │ JWT (Bearer Token)
                      ▼
[ FastAPI AI-Service: /api/evaluation/* ]
                      │
                      ├─► Depends(require_admin_or_researcher())  [401 / 403 enforcement]
                      ├─► Rate Limiter: 60/min
                      │
                      ▼
[ EvaluationService (Singleton, In-Memory Cached) ]
                      │
                      ├─► results/phase14/*.json, *.csv
                      ├─► results/phase12/*.json
                      ├─► results/phase11/*.json
                      └─► data/fixtures/phase9/*.json
```

1. **Client Request:** The authenticated client navigates to `/evaluation`.
2. **Security Gate:** FastAPI executes `require_admin_or_researcher()`, validating the RSA-signed JWT. Roles `SYSTEM_ADMIN`, `HOSPITAL_ADMIN`, and `RESEARCH_COORDINATOR` proceed; `PATIENT` and `PHYSICIAN` receive HTTP 403 Forbidden; unauthenticated requests receive HTTP 401 Unauthorized.
3. **Service Layer:** `EvaluationService` resolves artifact directories across local dev and container roots (`/app` vs repo root), validates payload schemas against Pydantic v2 models, and serves cached responses.
4. **Presentation:** The frontend renders six tabbed views with Recharts visualizations, evidence badges, and disclaimer alerts.

---

## 5. Backend Endpoints & API Specifications

All endpoints are read-only (`GET`), require admin/researcher authorization, and enforce a 60 requests/minute rate limit.

### 5.1 `GET /api/evaluation/overview`
- **Response Model:** `EvaluationOverviewResponse`
- **Contents:**
  - Executive highlights (Safety 100%, Query reduction 80%, Criteria loading 79.15%, Review recall 100%, Gemini unmeasured).
  - Milestone coverage matrix covering Phases 5 through 14.2.
  - Strict evidence classification dictionary.
  - Scientific integrity disclaimers.

### 5.2 `GET /api/evaluation/performance`
- **Response Model:** `EvaluationPerformanceResponse`
- **Contents:**
  - `frozen_phase14_1_reference`: 128.32 ms criteria loading, 181.60 ms pipeline, 5 queries.
  - `controlled_same_run_experiment`: 121.55 ms → 25.34 ms criteria loading (79.15%), 163.63 ms → 67.57 ms pipeline (58.71%), 5 → 1 SQL queries (80.0%).
  - `real_postgresql_measurement`: 118.51 ms → 2.79 ms (97.65%).
  - `vector_retrieval_scaling`: Unindexed <=> distance scan from 100 rows (0.589 ms) to 50,000 rows (19.831 ms).
  - `completeness_matrix`: Complete 14-dimension status matrix.
  - `unmeasured_components`: Explicit callouts for Gemini API and HTTP socket transmission.

### 5.3 `GET /api/evaluation/safety`
- **Response Model:** `EvaluationSafetyResponse`
- **Evidence Classification:** `SYNTHETIC / DEVELOPMENT FIXTURE`
- **Contents:**
  - Phase 12 adversarial error injection summary: 14/14 detected and intercepted (100% interception rate, 0 missed).
  - Safety pipeline comparison: S-E0 unmitigated unsafe rate 58.33% → S-E4 safety pipeline 0.00%.
  - Gate pass rate: 92.77% on eligible cohorts.
  - Human review routing recall: 100.0%.
  - Safety ablations A-S1 through A-S7.
  - Detailed catalog of 14 adversarial error scenarios.
  - Phase 9 uncertainty taxonomy and priority triage.

### 5.4 `GET /api/evaluation/ablations`
- **Response Model:** `EvaluationAblationsResponse`
- **Evidence Classification:** `SYNTHETIC / DEVELOPMENT FIXTURE`
- **Contents:**
  - Sample size: $n=6$ development fixture patients.
  - Architectural experiments E0 (Baseline), E1 (Structured Profile), E2 (Dense RAG), E3 (Hybrid RAG), and E4 (Reranked RAG).
  - Component ablations A1 (Dense vs Hybrid), A2 (Hybrid vs Reranked), A3 (Raw Note vs Structured Profile), A4 (Non-RAG vs Dense RAG), and A5 (Non-Retrieved vs Grounded Reasoning).
  - Guardrail disclaimer prohibiting clinical generalization.

---

## 6. Frontend Information Architecture

The dashboard is mounted at `/evaluation` within `DashboardLayout`:

1. **Tab 1 — Executive Overview:** High-level summary stat cards, project phase milestone table, evidence classification dictionary, and prominent disclaimer banner.
2. **Tab 2 — Phase 14 Performance:** Side-by-side historical reference vs. controlled same-run cards, Recharts BarChart comparing baseline vs. optimized latency, vector scaling LineChart, and benchmark completeness table.
3. **Tab 3 — Clinical Safety & Error Injection:** Error injection detection statistics, S-E0 vs S-E4 safety comparison, 7 safety gate ablations table, and 14 adversarial scenario breakdown.
4. **Tab 4 — Component Ablations (A1–A5):** Component impact BarChart, detailed ablation specification table, and $n=6$ development fixture qualification notices.
5. **Tab 5 — Retrieval & RAG Comparison (E0–E4):** Recharts multi-metric BarChart (Recall@5, Precision@5, MRR, Grounding Score), and experiment configuration matrix.
6. **Tab 6 — Uncertainty & Human Review:** Phase 9 uncertainty categorization, mandatory clinician escalation policies, and human review routing recall.

---

## 7. Container Packaging & Dockerfile Changes

In production builds, `.dockerignore` previously excluded all files under `results/` and `data/`. To package only the evaluation artifacts without leaking unrelated datasets or scratch scripts, the following minimal changes were applied:

1. **`.dockerignore` Whitelist:**
   ```
   !data/fixtures/phase8/*.json
   !data/fixtures/phase9/*.json
   !data/fixtures/phase10/*.json
   !results/phase11/*.json
   !results/phase12/*.json
   !results/phase14/*.json
   !results/phase14/*.csv
   ```
2. **`infra/docker/ai-service.Dockerfile` Copy Directives:**
   ```dockerfile
   # Read-only evaluation artifacts for Phase 15 Evaluation & Performance Dashboard
   COPY --chown=fastapi:fastapi results/phase11 ./results/phase11
   COPY --chown=fastapi:fastapi results/phase12 ./results/phase12
   COPY --chown=fastapi:fastapi results/phase14 ./results/phase14
   COPY --chown=fastapi:fastapi data/fixtures/phase8 ./data/fixtures/phase8
   COPY --chown=fastapi:fastapi data/fixtures/phase9 ./data/fixtures/phase9
   COPY --chown=fastapi:fastapi data/fixtures/phase10 ./data/fixtures/phase10
   ```

---

## 8. Verification & Test Results

### 8.1 Backend Tests (`services/ai-service`)
- **Suite:** `tests/test_evaluation_api.py` (28 tests)
- **Security & RBAC:**
  - Unauthenticated requests rejected with 401 across all 4 endpoints (4 passed).
  - `PATIENT` role rejected with 403 Forbidden across all 4 endpoints (4 passed).
  - `PHYSICIAN` role rejected with 403 Forbidden across all 4 endpoints (4 passed).
  - `SYSTEM_ADMIN`, `HOSPITAL_ADMIN`, and `RESEARCH_COORDINATOR` accepted with 200 across all 4 endpoints (12 passed).
- **Data Parity & Integrity:**
  - Performance endpoint parity with Phase 14 artifacts verified (passed).
  - Safety endpoint parity with Phase 12 artifacts verified (passed).
  - Ablations endpoint parity with Phase 11 artifacts verified (passed).
  - Overview endpoint coverage and highlights verified (passed).
- **Existing Regression Tests:** `test_task_security.py` (7 tests passed).

### 8.2 Frontend Validation (`frontend/medmatch-ui`)
- **Build (`npm run build`):** Exit code 0 (`tsc -b && vite build` completed in 0.988s, 2547 modules transformed).
- **Lint (`npm run lint`):** Exit code 0 (ESLint passed with 0 errors and 0 warnings).

---

## 9. Limitations & Research Boundaries

1. **Synthetic Cohort Scope:** Phase 11 and 12 experiments reflect deterministic fixture evaluation ($n=6$ patients, 14 synthetic corruptions). These results demonstrate algorithmic correctness, gate enforcement, and error interception, but do not prove clinical generalizability across real patient populations.
2. **Gemini Latency:** Live Gemini 2.5 Flash API calls were not measured in local benchmarks to ensure reproducibility without external network dependencies.
3. **HTTP Socket Overhead:** Network socket latency, Uvicorn connection queues, and TLS handshake overhead were not measured; benchmarks reflect in-process ASGI service execution.
