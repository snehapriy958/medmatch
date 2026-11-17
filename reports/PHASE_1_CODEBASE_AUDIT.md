# PHASE 1: COMPLETE CODEBASE AUDIT & ARCHITECTURE MAPPING

**Repository:** `https://github.com/snehapriy958/medmatch`
**Audit Date:** 2026-11-17
**Branch:** `production-readiness/medmatch-hardening`
**Auditor Roles:** Principal Software Architect, Senior Backend Engineer, Senior AI/ML Engineer, Senior Frontend Engineer, DevSecOps Engineer, QA & Healthcare AI Reliability Reviewer

---

## 1. Executive Summary

A comprehensive, code-level inspection of the entire MedMatch codebase was performed. No assumptions from README files, existing capstone reports, or comments were accepted without verification.

### System Vital Statistics
- **Backend (Auth Service):** Java 21, Spring Boot 4.1.0, Spring Security, Spring Data JPA, Flyway 10, PostgreSQL driver 42.7.13, JUnit 5, Mockito. (85 tests passing).
- **Backend (AI Service):** Python 3.13, FastAPI 0.141.1, Starlette 1.6.0, SQLAlchemy 2.0, pgvector-python, SentenceTransformers (all-MiniLM-L6-v2), Google GenAI SDK (Gemini), Celery 5.6.3, Redis 7, Alembic. (108 tests passing).
- **Frontend:** React 19.2.8, TypeScript 6.0.2, Vite 8.2.1, Tailwind CSS 4.3.3, Lucide React, Axios 1.19.0, React Hook Form 7.85.0, Zod 4.4.3. (0 lint errors, production build succeeds in 2.04s).
- **Infrastructure:** Docker Compose v5, Kubernetes manifests (Kustomize), PostgreSQL 16 + pgvector 0.5.1, Redis 7 Alpine, Prometheus, Alertmanager, Grafana.

---

## 2. Actual System Architecture & Communication Topology

```mermaid
graph TD
    User["End User (Browser)"]
    Nginx["Nginx Reverse Proxy / Ingress (Port 5173 / 80)"]
    AuthService["Auth Service (Spring Boot - Port 8081)"]
    AIService["AI Service (FastAPI - Port 8000)"]
    Postgres[("PostgreSQL 16 + pgvector (Port 5434/5432)")]
    Redis[("Redis 7 Cache & Broker (Port 6380/6379)")]
    CeleryWorker["Celery Worker (Python)"]
    GeminiAPI["Google Gemini LLM API (External HTTPS)"]

    User -->|HTTP / SPA| Nginx
    Nginx -->|/api/auth/*, /api/auth/users/*, /api/auth/dashboard/*| AuthService
    Nginx -->|/api/patients/*, /api/trials/*, /api/ai/*| AIService

    AuthService -->|JDBC (Hibernate/Flyway)| Postgres
    AuthService -->|Signs JWT RS256| User

    AIService -->|SQLAlchemy / pgvector| Postgres
    AIService -->|Cache Get/Set| Redis
    AIService -->|Verify RS256 with Public Key| AuthService
    AIService -->|Async Task Dispatch| Redis

    CeleryWorker -->|Pulls Tasks| Redis
    CeleryWorker -->|Extracts Text & Saves Vectors| Postgres
    CeleryWorker -->|Calls LLM Extraction| GeminiAPI

    AIService -->|Live Eligibility Inference| GeminiAPI
```

---

## 3. Subsystem Breakdown

### 3.1 Authentication & Authorization Service (`services/auth-service`)
- **Port:** `8081` (Container: `8081`, Host in Docker Compose: `8081`)
- **Security Mechanism:** RSA asymmetric keypair (RS256). Private key signs tokens in Auth Service (`src/main/resources/keys/private.pem`), public key verifies in both Auth Service and AI Service (`src/main/resources/keys/public.pem`).
- **Token Claims:** `sub` (UUID string), `email`, `role`, `hospital_id` (UUID string), `iat`, `exp` (1 hour default).
- **Controllers & Endpoints:**
  - `AuthController` (`/auth`):
    - `POST /auth/login` (Public): Validates email/password via BCrypt, issues RS256 JWT + user info.
    - `POST /auth/register` (Requires `SYSTEM_ADMIN` or `HOSPITAL_ADMIN`): Onboards staff; hospital-admin can only register users for their own hospital.
  - `UserController` (`/users`):
    - `GET /users/me`: Current user details.
    - `GET /users`: Hospital-scoped user list.
    - `GET /users/{id}`: Hospital-scoped user lookup.
    - `PUT /users/{id}/status`: Enable/disable user.
  - `HospitalController` (`/hospitals`):
    - `GET /hospitals`: List hospitals (admin scoped).
    - `GET /hospitals/{id}`: Hospital detail.
  - `AuditController` (`/audit-logs`):
    - `GET /audit-logs/user/{userId}`: Scoped audit logs.
  - `DashboardController` (`/dashboard`):
    - `GET /dashboard/system`: System admin stats.
    - `GET /dashboard/hospital`: Hospital admin metrics.
    - `GET /dashboard/physician`: Physician patient counts.
    - `GET /dashboard/coordinator`: Research coordinator trial counts.
- **Database Migrations:** Flyway managed. Migrations `V1__create_hospitals.sql` through `V16__remove_audit_resource_column.sql`. Note: Java entity `AuditLog.java` maps 8 columns, while the underlying physical table contains 12 columns shared with Python AI Service.

### 3.2 AI & Clinical Intelligence Service (`services/ai-service`)
- **Port:** `8000` (Host in Docker Compose: `8000`)
- **Framework:** FastAPI with async lifespan, Pydantic v2 schemas, SQLAlchemy 2.0 ORM.
- **Security & RBAC:**
  - `app.config.security.verify_token`: Loads RS256 public key from `keys/public.pem`, validates signature, expiration, and extracts claims into `JWTClaims`.
  - `app.api.deps.require_roles`: Enforces role-based permissions (`SYSTEM_ADMIN`, `HOSPITAL_ADMIN`, `PHYSICIAN`, `RESEARCH_COORDINATOR`, `PATIENT`).
  - `app.api.deps.get_current_hospital_id`: Enforces hospital tenant ID presence.
- **Controllers & Routing:**
  - `/api/health`: Liveness and readiness probes (verifies DB connection, Alembic migration head `6f0604b23df6`, Redis ping, writable uploads volume).
  - `/api/patients`: Full CRUD for patients (`patients` table) and clinical progress notes (`patient_notes` table) with strict hospital isolation.
  - `/api/trials`: Clinical trial metadata and criteria CRUD, plus PDF upload (`POST /api/trials/upload`).
  - `/api/matching`:
    - `POST /api/matching/search`: Fast semantic vector search over criteria embeddings using pgvector cosine distance `<=>`.
    - `POST /api/matching/evaluate`: End-to-end condition-aware retrieval + Gemini LLM eligibility assessment.
  - `/api/tasks`: Async task polling (`GET /api/tasks/{task_id}`) backed by Redis task registry with cross-tenant isolation checks.
  - `/api/evaluation`: Executive metrics and benchmark reporting across Phases 5–14.
- **AI/ML Pipeline Implementation:**
  - **PDF Text Ingestion:** `PDFService` parses PDF buffers using PyMuPDF (`fitz`), checks magic bytes `%PDF-`, enforces 10 MB size limits and 100-page limit.
  - **Text Preprocessing:** `TextCleaner` removes form-feed characters, page headers/footers, and normalizes unicode whitespace.
  - **Embedding Model:** Local SentenceTransformer `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) loaded as thread-safe singleton from `models/all-MiniLM-L6-v2`. CPU inference with float32 normalization.
  - **Vector Retrieval:** pgvector cosine distance operator `<=>` against `criteria_embeddings` table with hospital scoping filter. Threshold defaults to `0.75` (max distance).
  - **RAG Prompt Construction:** `PromptBuilder.build_matching_prompt` groups criteria by `trial_id` and formats structured sections.
  - **LLM Engine:** Google Gemini (`gemini-2.5-flash`), temperature `0.0`, `response_mime_type="application/json"`, retry with exponential backoff on transient errors (`LLMCommunicationError`).
  - **Hallucination & Scope Control:** `_validate_llm_trial_results` enforces that Gemini returns exactly one result per retrieved `trial_id`, rejecting responses containing unexpected or duplicate trial IDs.

### 3.3 Database & Migrations
- **PostgreSQL 16 + pgvector 0.5.1:**
  - Split ownership:
    - Flyway owns: `roles`, `hospitals`, `users`, `audit_logs`.
    - Alembic owns: `patients`, `trials`, `patient_notes`, `trial_criteria`, `criteria_embeddings`, `patient_note_embeddings`, `trial_embeddings`, `matches`.
  - Vector indexing: HNSW cosine index `ix_criteria_embeddings_embedding` on `criteria_embeddings(embedding vector_cosine_ops)`.

---

## 4. Connection & Integration Contract Matrix

| Producer (Caller) | Consumer (Callee) | Protocol / Endpoint | Request Schema | Response Schema | Auth Method | Status Codes | Verified Alignment |
|---|---|---|---|---|---|---|---|
| Frontend | Auth Service | `POST /api/auth/login` | `LoginRequest` (email, password) | `AuthResponse` (token, user) | None (Public) | 200, 401, 422 | PASS |
| Frontend | Auth Service | `GET /api/auth/users/me` | Empty | `UserResponse` | Bearer RS256 | 200, 401, 403 | PASS |
| Frontend | Auth Service | `GET /api/auth/dashboard/*` | Empty | `DashboardResponse` | Bearer RS256 | 200, 401, 403 | PASS |
| Frontend | AI Service | `GET /api/patients` | Query params (skip, limit) | `PatientListResponse` | Bearer RS256 | 200, 401, 403 | PASS |
| Frontend | AI Service | `POST /api/patients` | `PatientCreate` | `PatientResponse` | Bearer RS256 | 201, 401, 403, 422 | PASS |
| Frontend | AI Service | `GET /api/trials` | Query params (skip, limit) | `list[TrialResponse]` | Bearer RS256 | 200, 401, 403 | PASS |
| Frontend | AI Service | `POST /api/trials/upload` | `multipart/form-data` (file) | `TrialUploadResponse` (task_id) | Bearer RS256 | 202, 400, 401, 403, 413 | PASS |
| Frontend | AI Service | `GET /api/tasks/{task_id}` | Empty | `TaskStatusResponse` | Bearer RS256 | 200, 401, 403, 404 | PASS |
| Frontend | AI Service | `POST /api/ai/api/matching/search` | `MatchingRequest` | `MatchingResponse` | Bearer RS256 | 200, 401, 403, 422 | PASS |
| Frontend | AI Service | `POST /api/ai/api/matching/evaluate`| `MatchingRequest` | `EligibilityEvaluationResponse` | Bearer RS256 | 200, 401, 403, 422 | PASS |
| Frontend | AI Service | `GET /api/ai/api/evaluation/*` | Empty | `Evaluation*Response` | Bearer RS256 | 200, 401, 403 | PASS |
| AI Service | PostgreSQL | JDBC/TCP :5432 | SQL Statements | Tabular result sets | DB Password | Success/Error | PASS |
| AI Service | Redis | TCP :6379 | RESP protocol | Serialized JSON / Bytes | Redis Password | Success/Error | PASS |
| AI Service | Celery Worker | Redis Queue `celery` | Serialized JSON task | Task result JSON | Redis Password | ACK/RETRY/NACK | PASS |
| AI Service | Gemini API | HTTPS / REST | JSON Prompt | JSON Response array | API Key (`GEMINI_API_KEY`) | 200, 429, 503 | PASS |

---

## 5. Architectural Findings: Gaps, Dead Code & Incomplete Integrations

### Finding 1.1: Dead Code / Orphan Directory in AI Service (`app/tasks/`)
- **Location:** `services/ai-service/app/tasks/`
- **Files:** `embedding_tasks.py` (0 bytes), `ingestion_tasks.py` (0 bytes), `matching_tasks.py` (0 bytes).
- **Root Cause:** In earlier iterations, tasks were planned in `app/tasks/`, but the actual production Celery implementation was centralized in `services/ai-service/app/celery/tasks.py`. The empty files were left untracked or unused.
- **Remediation:** Remove the dead directory `app/tasks/` to avoid developer confusion.

### Finding 1.2: Frontend Development Proxy Disconnect
- **Location:** `frontend/medmatch-ui/vite.config.ts`
- **Observation:** `vite.config.ts` lacks a `server.proxy` block. While Nginx in Docker Compose correctly routes `/api/auth/` to port 8081 and `/api/` to port 8000, running `npm run dev` directly without environment overrides results in 404s for API calls.
- **Remediation:** Configure `server.proxy` in `vite.config.ts` mapping `/api/auth` to `http://localhost:8081` and `/api` to `http://localhost:8000`.

### Finding 1.3: Isolation Test Pattern Collision in Evaluation Schemas
- **Location:** `services/ai-service/app/schemas/evaluation.py` lines 247-249 and `tests/explainability/test_phase10_isolation.py`.
- **Observation:** Baseline isolation tests in `tests/` scanned `services/` using raw word regexes (`\bexplainability_metrics\b`, `\buncertainty_metrics\b`, `\bgrounding_metrics\b`). In Phase 15, response schema fields were named with these exact words, causing 3 isolation tests to fail despite no production import of research scripts existing.
- **Remediation:** Adjust field naming or test boundary to ensure pure research script isolation while maintaining the dashboard API schema contract.

### Finding 1.4: Outdated Negative Baseline Tests in Production Engineering
- **Location:** `tests/production_engineering/test_production_engineering_baseline.py`
- **Observation:** Tests `test_docker_compose_ai_service_healthcheck_gap` asserted that `healthcheck` was missing from `ai-service` in `docker-compose.yml`. When the healthcheck was properly added in Phase 13.3, this baseline test failed.
- **Remediation:** Update test suite to assert the presence and validity of the remediated healthcheck.

### Finding 1.5: Auth Service Duplicate Migration Tracking
- **Location:** `services/auth-service/src/main/resources/db/migration/`
- **Observation:** Files `V1__create_roles_table.sql` through `V4__create_audit_logs_table.sql` were committed previously alongside existing `V1__create_hospitals.sql` through `V4__create_audit_logs.sql`. This caused duplicate Flyway version numbers.
- **Remediation:** Clean up duplicate migration files and ensure exact alignment with Flyway version history.
