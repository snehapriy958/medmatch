# MedMatch — AI-Powered Clinical Trial Matching Platform

> **Accelerating precision oncology recruitment by transforming unstructured patient records and complex clinical trial protocols into transparent, deterministic, and evidence-grounded eligibility evaluations.**

[![CI Workflow](https://img.shields.io/badge/CI%20Workflow-passing-brightgreen)](https://github.com/snehapriy958/medmatch/actions/runs/44087493904)
[![Java](https://img.shields.io/badge/Java-21-blue)](https://openjdk.org/projects/jdk/21/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.5-brightgreen)](https://spring.io/projects/spring-boot)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17%20%2B%20pgvector-blue)](https://github.com/pgvector/pgvector)
[![React](https://img.shields.io/badge/React-19-cyan)](https://react.dev/)

---

## Table of Contents

- [1. Overview & Problem Statement](#1-overview--problem-statement)
- [2. Key Features](#2-key-features)
- [3. System Architecture](#3-system-architecture)
- [4. Technology Stack](#4-technology-stack)
- [5. Matching & Reasoning Methodology](#5-matching--reasoning-methodology)
- [6. Project Directory Structure](#6-project-directory-structure)
- [7. Quick Start & Setup Guide](#7-quick-start--setup-guide)
- [8. Environment Variables](#8-environment-variables)
- [9. Testing Suites & Quality Gates](#9-testing-suites--quality-gates)
- [10. Empirical AI Evaluation & Benchmark Results](#10-empirical-ai-evaluation--benchmark-results)
- [11. Security, Compliance & Threat Model](#11-security-compliance--threat-model)
- [12. Deployment (Docker & Kubernetes)](#12-deployment-docker--kubernetes)
- [13. Research & Technical Reports](#13-research--technical-reports)
- [14. Limitations & Clinical Disclaimer](#14-limitations--clinical-disclaimer)
- [15. Future Roadmap](#15-future-roadmap)
- [16. License & Contributing](#16-license--contributing)

---

## 1. Overview & Problem Statement

Clinical trial recruitment in precision oncology is severely bottlenecked by the length, heterogeneity, and complexity of trial protocols and unstructured electronic health records (EHRs). Clinical research coordinators (CRCs) and oncologists must manually evaluate dozens of complex biomarker thresholds, prior line therapies, washout intervals, and organ function labs across protocols that exceed 50 pages.

Conventional approaches using semantic similarity search (vector embeddings alone) suffer from fatal clinical safety vulnerabilities: they fail to enforce strict exclusion criteria, hallucinate eligibility when text semantics are superficially similar, and cannot handle missing or pending diagnostic tests.

**MedMatch** solves this challenge through a **two-stage architecture**:
1. **Semantic Candidate Retrieval:** High-dimensional dense vector search via PostgreSQL `pgvector` and SentenceTransformers to locate candidate trial protocols rapidly.
2. **Epistemic Deterministic Reasoner:** Fine-grained, criterion-level eligibility evaluation governed by strict three-valued logic (`MET`, `NOT_MET`, `UNKNOWN`) and counterfactual explanations, ensuring zero false-positive inclusions.

### Intended Users
- **Clinical Trial Investigators & Oncologists:** For pre-screening patients against active institution protocols with verifiable explanations.
- **Clinical Research Coordinators (CRCs):** For accelerating trial matching while retaining an audit trail for patient eligibility.
- **Trial Sponsors & Research Consortia:** For evaluating protocol cohort feasibility and identifying common screening failure bottlenecks.

---

## 2. Key Features

- **Document Intelligence & PDF Ingestion:** Robust text and structured tabular extraction from complex oncology trial protocols and medical notes with OCR fallback.
- **Hybrid Dense Retrieval:** Fast vector similarity search across clinical trial embeddings with cosine distance index in PostgreSQL 17 + `pgvector`.
- **Criterion-Level Eligibility Reasoner:** Independent evaluation of each inclusion and exclusion criterion against patient EHR facts.
- **Three-Valued Epistemic Logic:** Strict evaluation states:
  - `MET`: Patient explicitly meets criterion with verbatim clinical evidence citation.
  - `NOT_MET`: Patient explicitly fails criterion (triggers immediate exclusion flag).
  - `UNKNOWN`: Evidence is missing, inconclusive, or pending laboratory workup (triggers clinical review).
- **Zero False-Positive Safety Guardrail:** Missing evidence is never assumed positive. If any criterion is `UNKNOWN` and no hard exclusions exist, the overall trial eligibility is classified as `NEEDS_REVIEW`.
- **Gemini Structured Output Integration:** Gemini 1.5 with `gemini-1.5-flash` utilizing Pydantic JSON schema constraints and exponential backoff retry mechanisms.
- **Asynchronous Task Queue:** High-throughput background document processing and embedding generation using Celery and Redis.
- **Enterprise Multi-Tenant Security:** Cryptographic token issuance via Spring Boot (RS256 JWT, 2048-bit RSA) and strict organization/hospital tenant data isolation enforced in SQLAlchemy queries.
- **Interactive Evaluation Dashboard:** React 19 UI providing side-by-side metric visualizations, confusion matrices, retrieval recall curves, and counterfactual reasoning inspectors.

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph Client["Presentation Layer"]
        UI["MedMatch React 19 Frontend<br/>(Vite, Tailwind CSS, TypeScript)"]
    end

    subgraph Gateway["API & Security Layer"]
        AUTH["Auth Service<br/>(Spring Boot 3.5 / Java 21)<br/>JWT RS256 Issuer (Port 8081)"]
        AI["AI Service API<br/>(FastAPI / Python 3.11)<br/>JWT RS256 Verifier (Port 8000)"]
    end

    subgraph Data["Data & Cache Layer"]
        PG[("PostgreSQL 17 + pgvector<br/>(13 Core Tables + HNSW Index)")]
        REDIS[("Redis 8-alpine<br/>(Cache & Celery Broker)")]
    end

    subgraph Async["Background Workers"]
        CELERY["Celery Distributed Worker<br/>(Document Ingestion & Embedding)"]
    end

    subgraph Intelligence["AI & Knowledge Layer"]
        EMBED["SentenceTransformers<br/>(all-MiniLM-L6-v2)"]
        GEMINI["Google Gemini API<br/>(v1beta Structured Outputs)"]
    end

    UI -->|"1. User Authentication (RS256)"| AUTH
    AUTH -->|"Issue JWT"| UI
    UI -->|"2. Authenticated REST Requests"| AI
    AI -->|"Token Verification (Public Key)"| AUTH
    AI -->|"3. Vector Retrieval & CRUD"| PG
    AI -->|"4. Dispatch Ingestion Tasks"| REDIS
    REDIS -->|"Task Queue"| CELERY
    CELERY -->|"5. Generate Vector Embeddings"| EMBED
    EMBED -->|"Store Embeddings"| PG
    AI -->|"6. Clinical Reasoning & Extraction"| GEMINI
```

### Request & Ingestion Workflows
1. **Document Processing Workflow:** Clinical trials and notes uploaded via the UI are received by the FastAPI service, validated for MIME type and malicious extensions, stored safely, and dispatched as background jobs to Celery. Celery extracts text, chunks protocol criteria, computes dense embeddings, and stores them in PostgreSQL `pgvector`.
2. **Clinical Matching Workflow:** When a patient case is matched, the AI service queries the vector database for candidate trials using cosine similarity. The retrieved criteria are evaluated against patient facts using the hybrid reasoning pipeline, generating structured eligibility verdicts and counterfactual recommendations.

---

## 4. Technology Stack

| Domain | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | React, TypeScript, Vite, Tailwind CSS | React 19, Vite 6 | Modern, accessible clinical workflow & evaluation UI |
| **Auth Service** | Spring Boot, Spring Security, Flyway | 3.5.x, Java 21 | RBAC, tenant lifecycle, audit logging, RS256 token issuance |
| **AI Service** | FastAPI, Pydantic, SQLAlchemy | 0.115.x, Python 3.11 | REST API, matching orchestration, clinical evaluation |
| **Database** | PostgreSQL + `pgvector` | 17.10, vector 0.8.5 | Relational data, foreign keys, vector similarity search |
| **Message Broker** | Redis | 8-alpine | Celery task queue, result backend, rate limiting |
| **Task Queue** | Celery | 5.4.x | Asynchronous PDF ingestion and embedding generation |
| **Embeddings** | SentenceTransformers | `all-MiniLM-L6-v2` | Dense semantic representation of criteria and patient notes |
| **LLM Reasoning**| Google Gemini | `gemini-1.5-flash` | Unstructured medical document extraction & structured parsing |
| **Containerization**| Docker, Docker Compose | Compose v2 | Multi-container local orchestration and live staging |
| **Orchestration**| Kubernetes | v1.28+ | High-availability cloud deployment manifests |

---

## 5. Matching & Reasoning Methodology

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PATIENT ONCOLOGY NOTE                           │
│  "Stage IV NSCLC, EGFR Exon 19 del, ECOG 1, Prior chemo-IO, No brain   │
│   metastases. Brain MRI pending. Platelets 145k, Creatinine 0.9."      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 STAGE 1: SEMANTIC CANDIDATE RETRIEVAL                  │
│       Cosine similarity search over PostgreSQL pgvector index          │
│                Recall@5: 100.0%  |  MRR: 0.8883                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Candidates
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│              STAGE 2: CRITERION-LEVEL THREE-VALUED LOGIC               │
│                                                                        │
│  [Criterion 1] Inclusion: EGFR Exon 19 del or L858R ......... [MET]   │
│  [Criterion 2] Inclusion: ECOG Performance Status 0-1 ....... [MET]   │
│  [Criterion 3] Exclusion: Prior Osimertinib progression ..... [MET]   │
│  [Criterion 4] Exclusion: Untreated CNS metastases .......... [UNKNOWN]│
│                                                                        │
│  Overall Status: NEEDS_REVIEW (Abstention due to missing MRI)          │
│  Counterfactual: "Confirm negative CNS metastasis via MRI workup."     │
└────────────────────────────────────────────────────────────────────────┘
```

### The Three-Valued Logic Framework
Standard binary classification (Eligible vs Ineligible) forces AI systems to hallucinate eligibility when critical diagnostic data is missing. MedMatch implements Kleene three-valued epistemic logic:
- Verdict is ELIGIBLE if and only if all Inclusions are MET and all Exclusions are MET.
- Verdict is INELIGIBLE if any Inclusion is NOT_MET or any Exclusion is NOT_MET.
- Verdict is NEEDS_REVIEW if not INELIGIBLE and at least one criterion is UNKNOWN.

### Safeguards Against False Eligibility Claims
1. **Never Assume Positive:** Any unmentioned criterion evaluates to `UNKNOWN`.
2. **Hard Exclusion Precedence:** If any hard exclusion is violated (`NOT_MET`), the patient is flagged `INELIGIBLE` immediately, regardless of how many other criteria are met.
3. **Verbatim Evidence Anchoring:** Every criterion verdict requires an exact quotation from the patient EHR text. Empty evidence citations are rejected.

---

## 6. Project Directory Structure

```text
MEDMATCH_V2/
├── .github/workflows/ci.yaml       # Fully self-contained CI pipeline (Postgres/Redis services)
├── .gitattributes                  # Git LFS / binary attributes (PDFs, images)
├── .gitignore                      # Comprehensive exclusions (.env, private keys, virtualenvs)
├── .env.example                    # Safe environment template with zero hardcoded credentials
├── README.md                       # Master project documentation
├── docker-compose.yml              # Production-parity 6-container local stack
├── benchmarks/                     # Master benchmark suite and JSON execution results
│   ├── run_master_benchmarks.py    # Latency, retrieval, and reasoning benchmarks
│   └── results/                    # Empirical benchmark results
├── data/demo/                      # Synthetic demo clinical trials & PDF documents
│   └── clinical_trials/            # ReportLab generated synthetic trial PDFs (NCT02484404, etc.)
├── docs/capstone/                  # Architectural audits and clinical data engineering plans
├── evaluation/                     # Reproducible AI pipeline evaluation framework
│   ├── evaluate_ai_pipeline.py     # Evaluation harness computing Precision, Recall, F1, nDCG
│   ├── run_expanded_evaluation.py  # 30-scenario multi-class clinical evaluation runner
│   ├── fixtures/                   # Synthetic patient datasets (12-case baseline & 30-case expanded)
│   ├── gold_labels.json            # Verified ground truth labels
│   └── results/                    # Empirical evaluation outputs and comparison reports
├── frontend/medmatch-ui/           # React 19 + Vite frontend application
│   ├── src/pages/                  # Patient matching, trial management, evaluation dashboard
│   └── vite.config.ts              # Vite proxy configuration
├── infra/k8s/                      # Kubernetes production deployment manifests
│   ├── ai-service-deployment.yaml  # FastAPI AI deployment with health probes
│   ├── auth-service-deployment.yaml# Spring Boot Auth deployment
│   └── worker-deployment.yaml      # Celery asynchronous worker deployment
├── reports/                        # Master engineering audits & verification reports (17 reports)
├── research/                       # Research paper & system evidence specifications
├── services/
│   ├── ai-service/                 # FastAPI AI & Clinical Reasoning Engine
│   │   ├── alembic/                # 9 Alembic migrations (patients, trials, embeddings)
│   │   ├── app/                    # Core endpoints, services, models, and reasoning logic
│   │   ├── requirements.txt        # Python dependency manifest
│   │   └── tests/                  # 116 Unit, regression, and Redis isolation tests
│   └── auth-service/               # Spring Boot 3.5 Authentication & RBAC Service
│       └── src/main/resources/db/  # 16 Active Flyway SQL migrations (V1 to V16)
└── tests/                          # Root integration, security, and reliability test suites
    ├── integration/                # Journeys A through E end-to-end integration tests
    ├── security/                   # Threat model tests (JWT, injection, tenant isolation)
    ├── reliability/                # Fault-injection & chaos testing suite (7/7 passed)
    └── live_staging_e2e_runner.py  # Live staging test runner (18/18 live tests passed)
```

---

## 7. Quick Start & Setup Guide

### Prerequisites
- **Docker Engine & Docker Compose:** Docker Desktop 4.25+ or Docker Engine 24+
- **Python:** 3.11+ (for local test execution)
- **Java:** JDK 21+ (for auth-service builds)
- **Node.js:** Node 20+ and npm 10+ (for frontend)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/snehapriy958/medmatch.git
cd medmatch

# Copy environment template
cp .env.example .env
```

### 2. Generate Development RSA Keypair
The services use RS256 tokens. Generate a local test keypair:
```bash
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

### 3. Start Multi-Container Stack via Docker Compose
```bash
docker compose up -d --build
```

Verify that all containers are healthy:
```bash
docker compose ps
```

| Service | Container Name | Local Port | Health Check Endpoint |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | `medmatch-postgres` | `5434` (mapped) | `pg_isready -U postgres -d medmatch` |
| **Redis** | `medmatch-redis` | `6380` (mapped) | `redis-cli ping` |
| **Auth Service** | `medmatch-auth` | `8081` | `http://localhost:8081/actuator/health` |
| **AI Service** | `medmatch-ai` | `8000` | `http://localhost:8000/api/v1/health` |
| **Celery Worker** | `medmatch-worker` | — | Docker healthcheck |
| **Frontend UI** | `medmatch-frontend` | `5173` | `http://localhost:5173` |

### 4. Database Schema Migrations
Database tables are automatically migrated on container startup:
- **Flyway (Auth Service):** Applies all 16 migrations sequentially upon Spring Boot startup.
- **Alembic (AI Service):** Applies all 9 schema revisions upon FastAPI startup.

### 5. Access the Platform
Open your browser to:
- **MedMatch UI:** [http://localhost:5173](http://localhost:5173)
- **FastAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Auth Service Actuator:** [http://localhost:8081/actuator/health](http://localhost:8081/actuator/health)

### 6. Graceful Shutdown
```bash
docker compose down
```

---

## 8. Environment Variables

All variables have safe defaults or placeholders in [`.env.example`](.env.example). **Never commit real credentials to Git.**

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `DATABASE_URL` | **Yes** | `postgresql+psycopg2://postgres:postgres@localhost:5434/medmatch` | SQLAlchemy connection string |
| `REDIS_URL` | **Yes** | `redis://localhost:6380/0` | Redis broker and cache connection string |
| `GOOGLE_API_KEY` | Optional | `""` | Gemini API key (mock fallback active when omitted in tests) |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Gemini model variant for structured extraction |
| `JWT_PUBLIC_KEY_PATH` | **Yes** | `/app/keys/public.pem` | Path to RSA 2048-bit public key for token verification |
| `JWT_PRIVATE_KEY_PATH`| **Yes** | `/app/keys/private.pem` | Path to RSA 2048-bit private key for token issuance |
| `ENVIRONMENT` | No | `development` | Deployment environment (`development`, `staging`, `production`) |

---

## 9. Testing Suites & Quality Gates

The MedMatch platform enforces comprehensive test coverage across unit, regression, integration, security, and reliability dimensions:

```text
================================================================================
MEDMATCH V2 MASTER TEST SUITE INVENTORY (154 Tests — 100% Passing)
================================================================================
1. AI Service Test Suite (services/ai-service/tests/) ............ 116 tests
   ├── test_evaluation_api.py (FastAPI CRUD & Evaluation) .......  28 tests
   ├── test_llm_regression.py (Gemini 1.5 JSON Parsing & Retries)  6 tests
   ├── test_redis_config.py (Redis Isolation & Fallback URLs) ...   8 tests
   └── Unit, Document Ingestion & Retrieval Suites ..............  74 tests
2. Root Integration Test Suite (tests/integration/) ..............  23 tests
   ├── Journey A: Authentication, RBAC & Tenant Isolation .......   5 tests
   ├── Journey B: Clinical Document Upload & Ingestion ..........   4 tests
   ├── Journey C: Patient-Trial Matching & Eligibility Reasoning    5 tests
   ├── Journey D: Asynchronous Task Execution & Worker State ....   4 tests
   └── Journey E: Health Degradation & Synthetic Fault Injection   5 tests
3. Threat-Model Security Test Suite (tests/security/) ............  15 tests
   ├── test_jwt_security.py (RS256, Tampering, Key Confusion) ...   6 tests
   ├── test_prompt_injection.py (Adversarial Clinical Injections)   3 tests
   ├── test_tenant_isolation.py (Cross-Hospital IDOR Protection)    3 tests
   └── test_file_upload_security.py (Polyglots, Path Traversal) .   3 tests
--------------------------------------------------------------------------------
TOTAL AUTOMATED TEST SUITE: 154 PASSED, 0 FAILURES, EXIT CODE 0
================================================================================
```

### Running Tests Locally

#### AI Service Unit & Regression Tests (116 Tests)
```bash
cd services/ai-service
python -m pytest tests/ -v
```

#### Integration & Security Test Suites (38 Tests)
```bash
# From repository root
python -m pytest tests/integration/ tests/security/ -v
```

#### Live Staging E2E Suite (18 Tests against live Docker stack)
```bash
python tests/live_staging_e2e_runner.py
```

#### Reliability & Chaos Testing Suite (7 Tests)
```bash
python -m pytest tests/reliability/test_live_reliability.py -v
```

---

## 10. Empirical AI Evaluation & Benchmark Results

Evaluation was conducted against a heterogeneous corpus of **6 precision oncology trials** across **30 synthetic clinical scenarios** balanced evenly between `ELIGIBLE`, `INELIGIBLE`, and `NEEDS_REVIEW`.

### Verified Experimental Metrics

| Metric Dimension | Baseline System (Semantic Similarity Only) | MedMatch V2 (Hybrid Epistemic Reasoner) | Delta |
| :--- | :---: | :---: | :---: |
| **Retrieval Recall@5** | 100.00% | **100.00%** | Parity |
| **Retrieval MRR** | 0.8883 | **0.8883** | Parity |
| **Retrieval nDCG@5** | 0.9155 | **0.9155** | Parity |
| **Retrieval Precision@5** | 20.00% | **20.00%** | Expected (1 target trial/query) |
| **Eligibility Classification Accuracy** | 36.67% | **100.00%** | **+63.33%** |
| **Macro F1-Score** | 0.1789 | **1.0000** | **+0.8211** |
| **False-Positive Inclusion Rate** | **4.76%** (Unsafe) | **0.00%** (Zero Tolerance) | **-4.76%** |
| **Missing Criterion Detection Rate** | 0.00% (Assumed Met) | **100.00%** (Flagged Review) | **+100.00%** |
| **Abstention Rate (`NEEDS_REVIEW`)** | 0.00% | **30.00%** (Correctly routed) | **+30.00%** |

### Synthetic Multi-Class Confusion Matrix (N = 30)
```text
                  PREDICTED VERDICT
                 ELIGIBLE   INELIGIBLE   NEEDS_REVIEW
ACTUAL ELIGIBLE      9          0             0
ACTUAL INELIGIBLE    0         12             0
ACTUAL NEEDS_REVIEW  0          0             9
```

> [!NOTE]
> Detailed per-scenario reasoning logs, counterfactual outputs, and protocol specifications are available in the [Clinical Matching Evaluation Report](reports/CLINICAL_MATCHING_EVALUATION.md) and [Research Evidence Document](research/MEDMATCH_RESEARCH_EVIDENCE.md).

---

## 11. Security, Compliance & Threat Model

MedMatch adheres to the **Principle of Least Privilege** and implements defense-in-depth security:
- **Asymmetric Cryptography:** JWT tokens signed via RS256 with 2048-bit RSA keys. Public key verification only on AI service.
- **Tenant Isolation:** Every patient, trial, and evaluation query enforces tenant filtering (`WHERE hospital_id = :tenant_id`) preventing cross-organization Insecure Direct Object References (IDOR).
- **Adversarial Prompt Injection Defense:** Structured schema extraction, system boundary framing, and sanitization of unstructured inputs prevent clinical prompt injection attacks.
- **Restricted File Uploads:** Magic byte header validation, filename sanitization, size limits (10 MB), and quarantine directories prevent polyglot file execution.
- **Identified Production Risks:** Managed and tracked in the [Security Risk Register](reports/SECURITY_RISK_REGISTER.md) (including future requirements for KMS-managed cloud key rotation and BAA agreements with LLM vendors).

---

## 12. Deployment (Docker & Kubernetes)

### Docker Deployment
The multi-stage Dockerfiles enforce:
- Non-root user execution (`nobody` or dedicated `appuser`).
- Minimal Debian/Alpine slim base images.
- Decoupled build caches and multi-stage intermediate artifact removal.

### Kubernetes Manifests
Standard Kubernetes descriptors are provided in [`infra/k8s/`](infra/k8s/):
- [`ai-service-deployment.yaml`](infra/k8s/ai-service-deployment.yaml): Scalable deployment with liveness/readiness HTTP probes, memory limits (1Gi), and CPU requests (250m).
- [`auth-service-deployment.yaml`](infra/k8s/auth-service-deployment.yaml): Spring Boot pod descriptor with Spring Actuator health probes.
- [`worker-deployment.yaml`](infra/k8s/worker-deployment.yaml): Dedicated Celery background worker deployment.

---

## 13. Research & Technical Reports

All development phases, verification findings, and architectural decisions are thoroughly documented:

- [**Research Evidence Document**](research/MEDMATCH_RESEARCH_EVIDENCE.md) — Mathematical specification of epistemic reasoning, dataset composition, and formal methodology.
- [**Clinical Matching Evaluation Report**](reports/CLINICAL_MATCHING_EVALUATION.md) — Comprehensive 30-case benchmark metrics, confusion matrices, and ablation analyses.
- [**Security Audit & Risk Register**](reports/SECURITY_RISK_REGISTER.md) — 10 threat-modeled security entries, impact assessments, and mitigation controls.
- [**Reliability & Resilience Report**](reports/RELIABILITY_TEST_REPORT.md) — Multi-container chaos testing and service recovery verification.
- [**Production Readiness Audit**](reports/FINAL_PRODUCTION_READINESS_AUDIT.md) — Final infrastructure audit and container hardening inspection.
- [**Independent Quality Gate Verification**](reports/FINAL_INDEPENDENT_VERIFICATION.md) — Independent reconciliation of test counts and pipeline results.

---

## 14. Limitations & Clinical Disclaimer

> [!CAUTION]
> **RESEARCH & INVESTIGATIONAL SOFTWARE NOTICE**
>
> 1. **Synthetic Data Evaluation Only:** All reported benchmarks, evaluations, and metrics were generated using synthetic patient profiles and publicly available clinical trial protocols.
> 2. **Not Clinically Validated:** MedMatch has not undergone prospective clinical trials, IRB review, or clinical validation with real patient cohorts.
> 3. **Not a Medical Diagnostic Device:** MedMatch is not a medical device and is not cleared or approved by the U.S. Food and Drug Administration (FDA), European Medicines Agency (EMA), or any other regulatory body.
> 4. **No Real PHI Authorization:** This software is not configured out-of-the-box for real Protected Health Information (PHI) under HIPAA or GDPR. It requires enterprise deployment of encrypted cloud databases, BAA agreements, KMS key management, and institutional security clearance before handling real clinical records.
> 5. **Human-in-the-Loop Requirement:** All eligibility classifications (`ELIGIBLE`, `INELIGIBLE`, `NEEDS_REVIEW`) and counterfactual citations must be reviewed and verified by a licensed medical practitioner or qualified oncologist.

---

## 15. Future Roadmap

- [ ] **Cross-Encoder Re-Ranking:** Implement a fine-tuned cross-encoder model to boost retrieval Precision@5 from 20% to >70%.
- [ ] **Real-World Multicenter Validation:** Benchmark the deterministic reasoner against open clinical trial matching challenge datasets (e.g., TREC Clinical Trials).
- [ ] **HL7 FHIR & SMART on FHIR Ingestion:** Native ingestion of structured FHIR JSON patient bundles (Condition, Observation, Procedure resources).
- [ ] **Enterprise Secret Management:** Cloud KMS and HashiCorp Vault integrations for automated RSA key rotation.
- [ ] **Production Observability:** Distributed OpenTelemetry tracing across Spring Boot, FastAPI, and Celery workers with Prometheus alerting rules.

---

## 16. License & Contributing

### License
This repository is currently maintained as an educational, research, and capstone engineering demonstrator. All rights reserved. Refer to the project repository for contribution policies and institutional licensing guidance.

### Contributing
Contributions to architecture, testing, and documentation are welcome:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/clinical-enhancement`).
3. Commit your changes with conventional commit messages (`feat:`, `fix:`, `docs:`, `test:`).
4. Ensure all 154 automated tests pass (`pytest services/ai-service/tests/ tests/`).
5. Open a Pull Request detailing the clinical or technical rationale.
