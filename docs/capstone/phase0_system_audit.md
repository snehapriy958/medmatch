# MedMatch Technical Audit — Phase 0: System Audit

**Audit Date:** September 2026  
**Auditor:** AI Systems & Applied ML Engineering Team  
**Scope:** Complete repository technical audit (`MEDMATCH_V2`)  
**Objective:** Establish technical, architectural, and ML baselines before beginning Capstone transformation.

---

## 1. Executive Summary

MedMatch is a dual-microservice clinical trial matching platform composed of:
1. **`auth-service`**: Java 21 / Spring Boot 4.1.0 (Spring Security 6, Nimbus JOSE JWT, Hibernate/Flyway, PostgreSQL).
2. **`ai-service`**: Python 3.13 / FastAPI (SQLAlchemy 2.0, Alembic, Celery, Redis, PyMuPDF, SentenceTransformers, Google Gemini 2.5 Flash).
3. **`frontend/medmatch-ui`**: React 19 / Vite 8 / TypeScript / Tailwind CSS v4 / Axios / React Hook Form / Zod / Recharts.

The platform has established solid foundations for:
- Asymmetric RS256 JWT authentication between Spring Boot (signing) and FastAPI (verification).
- Tenant isolation by `hospital_id` across databases, API routes, and vector queries.
- Clean PDF upload validation, text extraction (PyMuPDF), and async queuing (Celery/Redis).
- Deterministic RAG prompting and Pydantic validation for clinical trial eligibility reasoning.
- 126 automated unit and mock integration tests passing (81 in auth-service, 45 in ai-service).
- Production-ready frontend TypeScript build (`tsc -b && vite build` in 1.57s) with zero lint errors.

However, the audit revealed **critical architectural disconnects and missing research infrastructure**:
1. **Matches are not persisted:** The `matches` table was created in Alembic migration `0008` and `MatchRepository` exists, but neither `MatchingService` nor any API route writes to it. Evaluated matches are returned only in-memory and logged in audit trails.
2. **Patient profiles are disconnected from matching:** The matching API takes a raw `patient_note` string. It does not accept `patient_id`, cannot reason over structured patient records (age, diagnosis, cancer stage, gender), and does not link matching outcomes to the patient in the database.
3. **No clinical NLP / entity extraction:** The system does not extract clinical concepts, stages, laboratory values, or biomarkers from patient notes, nor does it normalize them against clinical ontologies (UMLS, SNOMED, ICD-10, MedDRA).
4. **Pure vector retrieval with unindexed embeddings:** Semantic search uses brute-force sequential cosine distance scans (`<=>` in pgvector). There are no HNSW or IVFFlat vector indexes on the embedding tables. No keyword retrieval (BM25) or hybrid retrieval exists.
5. **Zero ML research infrastructure:** There is no benchmark dataset, no ground truth annotations, no train/val/test splits, no evaluation metrics (P@k, Recall@k, nDCG, MRR, RAG faithfulness), no ablation scripts, and no baseline comparison models. The existing benchmark script (`retrieval_benchmark.py`) is broken due to an outdated method signature.
6. **Flyway migration collision:** Conflicting duplicate migration files exist in `services/auth-service/src/main/resources/db/migration` (`V1__create_hospitals.sql` vs `V1__create_roles_table.sql`, etc.), which blocks fresh deployments from initializing.

---

## 2. High-Level Repository Map

```text
MEDMATCH_V2/
├── .env                                  # Root environment variables (DATABASE_PASSWORD, GOOGLE_API_KEY)
├── .gitignore                            # Git exclusion rules
├── Makefile                              # Make target definitions (currently empty)
├── README.md                             # Repository readme (currently empty)
├── docker-compose.yml                    # Multi-container orchestration (Postgres, Redis, Auth, AI, Worker, Frontend)
├── kustomization.yaml                    # Kubernetes Kustomize root
├── backfill_isolation.py                 # Utility script to backfill criteria embeddings for specific hospital
├── ai-openapi.json                       # AI service OpenAPI specification snapshot
├── services/
│   ├── auth-service/                     # Java Spring Boot Authentication & Tenant Microservice
│   │   ├── pom.xml                       # Maven build configuration (Java 21, Spring Boot 4.1.0)
│   │   ├── src/main/java/com/medmatch/auth/
│   │   │   ├── controller/               # Auth, User, Hospital, Audit, Dashboard REST controllers
│   │   │   ├── dto/                      # Requests, responses, and dashboard projection records
│   │   │   ├── entity/                   # JPA entities: User, Role, Hospital, AuditLog
│   │   │   ├── repository/               # Spring Data JPA repositories
│   │   │   ├── security/                 # Nimbus JWT service (RS256), Spring Security configuration
│   │   │   └── service/                  # Business logic implementations
│   │   ├── src/main/resources/
│   │   │   ├── application.yml           # Base application configuration
│   │   │   ├── application-dev.yml       # Development profile configuration
│   │   │   ├── application-production.yml# Production profile configuration
│   │   │   ├── db/migration/             # Flyway SQL migrations (V1 to V16)
│   │   │   └── keys/                     # RSA key pairs (public.pem, private.pem - gitignored)
│   │   └── src/test/java/com/medmatch/auth/ # 81 automated JUnit/Mockito tests
│   └── ai-service/                       # Python FastAPI AI / RAG / Ingestion Microservice
│       ├── requirements.txt              # Python dependencies (Torch CPU, sentence-transformers, fastapi, google-genai)
│       ├── alembic.ini                   # Alembic migration configuration
│       ├── alembic/versions/             # Database migrations (0001 to 0008, head merges)
│       ├── keys/                         # Public RSA key for JWT verification (gitignored)
│       ├── models/all-MiniLM-L6-v2/      # Local SentenceTransformer embedding model weights (384-d)
│       ├── uploads/                      # Temporary storage directory for uploaded PDFs
│       ├── tests/                        # 45 automated pytest tests (health, matching, rag, llm, security)
│       └── app/
│           ├── main.py                   # FastAPI initialization, middleware, routes, Prometheus
│           ├── api/                      # API routing and dependency injection (deps.py)
│           │   └── routes/               # health.py, matching.py, patients.py, trial.py, tasks.py
│           ├── benchmarks/               # retrieval_benchmark.py (evaluation script - currently broken)
│           ├── cache/                    # Redis caching service and key management
│           ├── celery/                   # Celery application configuration and task definitions
│           ├── config/                   # Settings, logging, rate limiting, LLM client, security
│           ├── db/                       # SQLAlchemy session and initialization
│           ├── embeddings/               # SentenceTransformer model wrapper (thread-safe singleton)
│           ├── exceptions/               # Custom exception classes and global handlers
│           ├── logging/                  # Structured logging configuration
│           ├── metrics/                  # Prometheus custom metric definitions
│           ├── middleware/               # Request ID tracking and structured access logging
│           ├── models/                   # SQLAlchemy ORM models: Patient, Trial, TrialCriteria, Match, etc.
│           ├── prompts/                  # Prompt templates: trial extraction and eligibility reasoning
│           ├── rag/                      # Context aggregation and prompt builder
│           ├── repositories/             # Data access layer (Postgres / pgvector)
│           ├── schemas/                  # Pydantic v2 schemas for API contracts
│           ├── services/                 # Business logic: MatchingService, TrialService, PatientService, etc.
│           └── tasks/                    # Empty placeholder files (ingestion_tasks.py, embedding_tasks.py)
├── frontend/
│   └── medmatch-ui/                      # React SPA
│       ├── package.json                  # Dependencies: React 19, Vite 8, Tailwind v4, Axios, Lucide
│       ├── vite.config.ts                # Vite build configuration
│       ├── src/
│       │   ├── api/                      # Axios API clients (authApi, patientApi, trialApi, matchingApi)
│       │   ├── auth/                     # AuthProvider, ProtectedRoute, role definitions
│       │   ├── components/               # Layout (Navbar, Sidebar), common modals and cards
│       │   ├── context/                  # React AuthContext
│       │   ├── pages/                    # Dashboard, Patients, ClinicalTrials, Matching, AuditLogs, Reports
│       │   ├── types/                    # TypeScript interfaces for all domain models
│       │   └── utils/                    # Form and validation utilities
├── infra/
│   ├── docker/                           # Dockerfiles for AI service, Auth service, Worker, Frontend, Nginx
│   ├── kubernetes/                       # Kubernetes manifests (Deployments, Services, Ingress, Secrets, HPA)
│   ├── monitoring/                       # Prometheus and Alertmanager configuration
│   └── scripts/                          # Shell automation (backup, deploy, health-check, migrate, validate)
└── docs/                                 # Extensive technical documentation (ADRs, architecture, standards)
```

---

## 3. Subsystem Implementation Status Summary

| Subsystem | Verified Status | Evidence | Summary Notes |
| :--- | :--- | :--- | :--- |
| **Authentication Service** | **IMPLEMENTED** | `JwtService.java`, `SecurityConfig.java`, 81 passing tests | RS256 signing, user management, and hospital assignment verified. |
| **RBAC** | **IMPLEMENTED** | Spring Security `@PreAuthorize`, FastAPI `require_roles()` | Role enforcement active on all endpoints. Minor role naming discrepancy. |
| **Multi-Tenancy** | **IMPLEMENTED** | Application-level scoping on all DB repositories | Tenant isolation enforced in code; no Postgres RLS configured. |
| **Inter-Service Auth** | **IMPLEMENTED** | Shared RSA key pair (Nimbus signing, PyJWT verification) | FastAPI decodes claims signed by Spring Boot. |
| **Trial PDF Upload & Storage** | **IMPLEMENTED** | `pdf_service.py`, `POST /api/trials/upload` | Size validation, MIME header checks, UUID filename storage verified. |
| **PDF Text Extraction** | **IMPLEMENTED** | `PDFService.extract_text()` via `pymupdf` | Sequential page extraction and raw text aggregation verified. |
| **Trial Info Extraction** | **IMPLEMENTED** | `LLMService.extract_trial_information()` | Gemini 2.5 Flash extracts JSON validated against `TrialExtraction`. |
| **Criteria Segmentation** | **IMPLEMENTED** | `TrialCriteria` model, `trial_service.py` | Inclusion and exclusion criteria stored individually in database. |
| **Trial Ingestion Queue** | **IMPLEMENTED** | `app/celery/tasks.py` (`process_trial`) | Celery worker task runs full extraction, embedding, and storage. |
| **Ingestion Task Status API** | **PARTIALLY IMPLEMENTED** | `GET /api/trials/upload/status/{task_id}` exists | Backend endpoint works, but frontend does not poll it and `tasks.py` route is unmounted. |
| **Patient Profile Management** | **IMPLEMENTED** | `POST/GET/PUT/DELETE /api/patients` | Complete CRUD on patient demographic and diagnostic records. |
| **Patient Clinical Notes** | **IMPLEMENTED** | `POST/GET /api/patients/{id}/notes` | Saves raw notes and creates 384-d vector embeddings in database. |
| **Patient Clinical NLP** | **MISSING** | Code search across `services/ai-service` | No entity extraction, no lab parsing, no negation handling, no ontology mapping. |
| **Patient-to-Match Linkage** | **MISSING** | `MatchingRequest` schema only takes `patient_note` | Matching operates statelessly on text; does not link to `patient_id`. |
| **Embedding Generation** | **IMPLEMENTED** | `EmbeddingModel` (`all-MiniLM-L6-v2`) | Local execution verified (load: 325.8ms, encode: 153.4ms). |
| **Vector Database Storage** | **IMPLEMENTED** | `pgvector.sqlalchemy.Vector(384)` | Schema columns in `criteria_embeddings`, `trial_embeddings`, `patient_note_embeddings`. |
| **Vector Indexing (HNSW/IVFFlat)**| **MISSING** | Alembic migrations 0005, 0006, 0007 | No index on `embedding` columns. Brute-force sequential scan used. |
| **Semantic Retrieval Strategy** | **IMPLEMENTED** | `MatchingRepository.find_similar_criteria()` | Two-stage cosine distance query with hospital tenant isolation. |
| **Keyword / Hybrid Retrieval** | **MISSING** | Code search across `MatchingRepository` | No BM25, no Elasticsearch, no Reciprocal Rank Fusion. Pure vector only. |
| **RAG Prompt Engineering** | **IMPLEMENTED** | `PromptBuilder`, `TRIAL_MATCHING_PROMPT` | 966-line prompt with strict evidence, boundary, and legacy rules. |
| **LLM Reasoning & Validation** | **IMPLEMENTED** | `LLMService.evaluate_eligibility()` | Validated JSON array parsing into `EligibilityResponse`. |
| **Hallucination Defense** | **IMPLEMENTED** | `MatchingService._validate_llm_trial_results` | Enforces 1-to-1 match with retrieved trial IDs; abstains on failure. |
| **Match Result Persistence** | **PARTIALLY IMPLEMENTED** | `Match` model and `MatchRepository` exist | Model and repository exist with tests, but no service writes to them. |
| **Frontend UI Integration** | **IMPLEMENTED** | `frontend/medmatch-ui`, Vite build | Clean dashboard, patients table, trials table, and AI matching page. |
| **Frontend Automated Testing** | **MISSING** | `package.json` in `medmatch-ui` | No test framework installed; 0 test files in `frontend/src`. |
| **Flyway Migrations** | **BROKEN** | `src/main/resources/db/migration` | Conflicting duplicate version numbers (`V1__`, `V2__`, `V3__`, `V4__`). |
| **Retrieval Benchmark Script** | **BROKEN** | `app/benchmarks/retrieval_benchmark.py` | Calls `find_similar_criteria()` without mandatory `hospital_id`. |
| **Evaluation Dataset & Ground Truth**| **MISSING** | Workspace search | No gold-standard patient-trial match dataset or test splits. |
| **Evaluation Metrics Framework** | **MISSING** | Workspace search | No calculation of P@k, Recall@k, nDCG, F1, or RAG groundedness metrics. |

---

## 4. Verification Methodology

Every finding in this audit has been verified through direct code inspection and local tool execution:
- Automated test suites executed:
  - `services/ai-service`: **45 passed** in 79.03s.
  - `services/auth-service`: **81 passed** in 21.36s.
  - Total automated tests verified: **126 passing**.
- Frontend build verified:
  - `npm run build` executed: transformed 1,970 modules, generated distribution bundle in 1.57s with zero errors.
  - `npm run lint` executed: zero ESLint errors across all TypeScript/React components.
- Local performance measured:
  - SentenceTransformer model initialization: **325.8 ms**.
  - Single clinical text encoding (384 dimensions): **153.4 ms**.
- Secret scanning:
  - `.env` files inspected for format and keys; confirmed `.pem` keys are gitignored and not tracked by git.
  - Secrets are not hardcoded in application logic.
