# MedMatch Evaluation & Research Readiness Baseline

**Document ID:** EVAL-BASE-001  
**Phase:** Phase 0 Baseline  
**Scope:** Automated Testing, Performance Benchmarks, Research Readiness, and Paper Mapping

---

## 1. Automated Testing Audit

MedMatch has high test coverage across core business logic in both Java and Python microservices, with **126 automated tests passing**.

```text
Unit Tests: IMPLEMENTED (126 passing)
Integration / Mock Service Tests: IMPLEMENTED
API Router Tests: IMPLEMENTED (FastAPI TestClient & Spring MockMvc)
Database / Repository Scoping Tests: IMPLEMENTED
AI / RAG Pipeline Unit Tests: IMPLEMENTED
End-to-End Functional Tests: MISSING
Frontend UI Tests: MISSING (0 test files in medmatch-ui)
Security Penetration Tests: MISSING
```

### 1.1. Service Test Breakdown

| Test Suite | Framework | Total Tests | Passing | Failing | Skipped | Execution Time | Coverage Scope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`services/auth-service`** | JUnit 5 + Mockito + MockMvc | **81** | **81** | 0 | 0 | 21.36 s | AuthController (14), HospitalController (11), UserController (10), AuditController (2), DashboardController (3), JwtService (7), SecurityUtils (3), AuthServiceImpl (9), HospitalServiceImpl (12), UserServiceImpl (6), AuditServiceImpl (6), DashboardServiceImpl (5). |
| **`services/ai-service`** | Pytest 9.1 + pytest-mock + FastAPI TestClient | **45** | **45** | 0 | 0 | 79.03 s | `test_health.py` (2), `test_llm_service.py` (6), `test_match_repository.py` (11), `test_match_repository_filters.py` (5), `test_matching.py` (6), `test_rag_pipeline.py` (5), `test_tenant_isolation.py` (5), `test_trial_embedding_repository.py` (5). |
| **`frontend/medmatch-ui`** | None | **0** | 0 | 0 | 0 | N/A | No test runner configured in `package.json` (no Vitest, Jest, or Cypress). |
| **Total Platform Tests** | — | **126** | **126** | **0** | **0** | — | — |

> [!NOTE]
> All 45 AI service tests run with mocks for LLM and database sessions, allowing deterministic CI/CD verification without external API charges or database dependencies.

---

## 2. Empirical Performance Baseline

Measurements were captured locally on the target hardware under controlled conditions:

| Measurement Metric | Measured Value | Measurement Context / Details | Status |
| :--- | :--- | :--- | :--- |
| **Embedding Model Cold Load** | **`325.8 ms`** | SentenceTransformer (`all-MiniLM-L6-v2`) initialized from local weights on CPU | Measured |
| **Single Text Encode Latency** | **`153.4 ms`** | Encodes a 54-year-old oncology patient query into 384-d normalized vector | Measured |
| **Frontend Bundle Build Time** | **`1.57 s`** | Vite 8 + React 19 production build (`tsc -b && vite build`) transforming 1,970 modules | Measured |
| **Auth Test Suite Execution** | **`21.36 s`** | Full Maven test lifecycle compiling and executing 81 tests | Measured |
| **AI Test Suite Execution** | **`79.03 s`** | Pytest execution for 45 tests (includes PyTorch CPU engine loading) | Measured |
| **PDF Text Extraction Latency** | *Unmeasured (No PDFs)* | `pymupdf` page parsing on representative clinical trial documents | Missing Dataset |
| **Vector Retrieval Latency** | *Unmeasured (No Live DB)* | Brute-force pgvector sequential scan query time | Missing Live DB |
| **Gemini 2.5 Flash API Latency**| *Unmeasured (No Live DB)* | Network roundtrip for 966-line prompt + generation | Missing Live Run |
| **End-to-End Match Latency** | *Unmeasured (No Live DB)* | Total time from note submission to eligibility response | Missing Live Run |

---

## 3. AI/ML Research Readiness Assessment

As this project transitions from an engineering prototype to a **research-grade AIML capstone**, it was evaluated against standard research reproducibility and experimental criteria:

```text
Evaluation dataset: MISSING
Ground truth annotations: MISSING
Train/validation/test split: MISSING
Baseline comparison models: MISSING
Standard evaluation metrics: MISSING
Information retrieval metrics: MISSING
RAG groundedness / faithfulness metrics: MISSING
Error analysis framework: MISSING
Ablation study scripts: MISSING
Reproducibility benchmark runner: BROKEN
```

### 3.1. Detailed Research Readiness Breakdown

| Research Dimension | Status | Current Repository State | What Is Required for Capstone |
| :--- | :--- | :--- | :--- |
| **Evaluation Dataset** | **MISSING** | No evaluation cohort or patient records exist in the repository. | Standardized benchmark dataset (e.g., TREC Clinical Trials 2021/2022 or TrialGPT cohort). |
| **Ground Truth** | **MISSING** | No expert-annotated labels for eligibility decisions (Eligible / Ineligible / Excluded). | Gold-standard trial eligibility labels across a minimum test cohort (50-200 patients). |
| **Data Splits** | **MISSING** | No dataset partition exists. | Deterministic Train / Validation / Test splits stratified by medical condition. |
| **Baseline Models** | **MISSING** | Only the single production RAG pipeline exists. | Lexical baseline (BM25), Generic dense baseline (MiniLM), Zero-shot LLM baseline without RAG. |
| **Retrieval Metrics** | **MISSING** | No retrieval performance calculation. | Implementation of Recall@k, Precision@k, Mean Reciprocal Rank (MRR), and nDCG@k. |
| **Classification Metrics**| **MISSING** | Decisions are emitted as un-evaluated strings. | Multi-class Macro-F1, Precision, Recall, and Confusion Matrices for eligibility decisions. |
| **RAG Grounding Metrics**| **MISSING** | Validation only verifies trial ID set equality. | LLM-as-a-judge / Ragas metrics: Context Relevance, Groundedness (Faithfulness), and Answer Relevance. |
| **Error Analysis** | **MISSING** | No taxonomy of model failure modes. | Categorization of false positives/negatives into extraction error, retrieval omission, or reasoning failure. |
| **Ablation Studies** | **MISSING** | No feature toggle or pipeline ablation support. | Systematic experiments ablating: (1) vector vs hybrid, (2) criteria hydration, (3) prompt constraints. |
| **Benchmark Scripts** | **BROKEN** | `app/benchmarks/retrieval_benchmark.py` exists but fails with `TypeError: missing hospital_id`. | Automated benchmark runner executing evaluation queries and logging statistical results. |

---

## 4. Research Paper Mapping

To ground future capstone phases in peer-reviewed clinical NLP and biomedical AI literature, the table below maps relevant scientific literature to current MedMatch capabilities:

| Research Area | Relevant Literature | What MedMatch Currently Has | Identified Research Gap | Potential Capstone Experiment |
| :--- | :--- | :--- | :--- | :--- |
| **Clinical Trial Matching** | **TrialGPT** (Wang et al., *Nature Communications* 2024 / arXiv:2404.03741) | Prompt-based reasoning with tri-state criteria evaluation | No criterion-level formal scoring, aggregation, or patient profile parsing | Implement two-stage TrialGPT-style criterion-level scoring vs monolithic prompt reasoning. |
| **Eligibility Criteria Parsing**| **Criteria2Query** (Yuan et al., *JAMIA* 2019) | LLM extraction of inclusion/exclusion text lists | Criteria stored as raw strings; no semantic attribute parsing | Extract structured criterion entities (attribute, operator, value, unit) and compare against raw text matching. |
| **Biomedical Embeddings** | **PubMedBERT** (Gu et al., *ACM TOIS* 2021) / **BioLinkBERT** (Yasunaga et al., 2022) | Generic general-domain embedding model (`all-MiniLM-L6-v2`, 384-d) | Out-of-vocabulary medical concepts and acronyms poorly separated in vector space | Benchmark domain-specific clinical embedding models (PubMedBERT, BGE-en-clinical) against MiniLM. |
| **Clinical Retrieval Benchmarks**| **TREC Clinical Trials Track** (Soboroff et al., 2021-2022) | 5 hardcoded toy queries in a broken script | No standardized queries, no standardized relevance assessments (qrels) | Ingest TREC 2021/2022 topics and qrels; evaluate retrieval using standard trec_eval metrics (nDCG@10, P@10). |
| **Hybrid Retrieval** | **BM25 + Dense Fusion** (Robertson et al. / Cormack et al., *SIGIR* 2009) | Pure vector retrieval (`<=>` cosine distance) | Fails on exact gene mutations (*EGFR T790M*), drug names, and numerical ranges | Implement Reciprocal Rank Fusion (RRF) combining BM25 keyword search with dense vectors. |
| **RAG Hallucination & Grounding**| **Ragas / TruLens RAG Triad** (Es et al., 2023) | Set-equality check on `trial_ids_evaluated` | No verification that matched criteria text matches retrieved documents | Implement automated Faithfulness and Citation Attribution scoring to detect ungrounded medical claims. |
| **Clinical Decision Support & Abstention**| **Med-PaLM 2** (Singhal et al., *Nature* 2023) | Safe abstention fallback on unexpected trial IDs | Confidence scores are qualitative LLM self-reports without calibration | Calibrate confidence scores using conformal prediction or uncertainty quantification over criteria evidence. |
