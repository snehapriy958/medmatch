# MedMatch Capstone Gap Analysis & Roadmap

**Document ID:** GAP-BASE-001  
**Phase:** Phase 0 Baseline  
**Objective:** Gap analysis and prioritized roadmap for converting MedMatch into a research-grade AIML Capstone.

---

## 1. Prioritized Limitations

### Critical Limitations
*Prevents reliable evaluation or capstone completion.*

1. **Complete Absence of Evaluation Dataset & Ground Truth:**
   - *Current State:* The repository contains 0 benchmark patient profiles, 0 annotated trial matches, and 0 ground truth eligibility labels.
   - *Consequence:* It is mathematically impossible to compute precision, recall, or accuracy, or validate whether RAG improvements produce statistically meaningful gains.
2. **Disconnected Matching Engine & Missing Match Persistence:**
   - *Current State:* The `matches` table exists in Alembic migration 0008, but `MatchingService` never writes to it. Evaluated matches exist only in ephemeral HTTP responses. The matching API takes a raw string and does not accept `patient_id`.
   - *Consequence:* The platform cannot track patient eligibility over time, link trial matches to patient records, or store model decisions for historical evaluation.
3. **Broken Retrieval Benchmark Script:**
   - *Current State:* `services/ai-service/app/benchmarks/retrieval_benchmark.py` calls `repository.find_similar_criteria(embedding, limit)` without the mandatory `hospital_id` parameter, causing an immediate `TypeError`.
   - *Consequence:* No automated benchmarking script currently functions in the repository.
4. **Flyway Migration Version Collisions:**
   - *Current State:* Duplicate migration prefixes (`V1__create_hospitals.sql` and `V1__create_roles_table.sql`, through `V4__`) exist in `services/auth-service/src/main/resources/db/migration`.
   - *Consequence:* A clean deployment or fresh container initialization will fail on database migration.

---

### High Limitations
*Significantly improves research and engineering quality.*

5. **Pure Vector Retrieval without Lexical / Keyword Matching (No BM25):**
   - *Current State:* Retrieval relies exclusively on dense vector cosine distance (`<=>` in pgvector).
   - *Consequence:* Dense bi-encoders frequently fail to match exact medical terms, gene mutations (*EGFR T790M*, *KRAS G12C*), drug names, and numerical clinical thresholds.
6. **No Vector Indexing (Missing HNSW / IVFFlat):**
   - *Current State:* Database tables (`trial_embeddings`, `criteria_embeddings`) have no vector indexes.
   - *Consequence:* Every query performs an unindexed brute-force sequential scan, which will not scale to research cohorts.
7. **Absence of Clinical NLP & Entity Extraction for Patients:**
   - *Current State:* Narrative clinical notes are stored as raw text without extracting medical entities (diagnoses, stage, labs, prior treatments) or detecting negation.
   - *Consequence:* RAG prompt context includes noisy narrative text rather than normalized clinical facts.
8. **Lack of RAG Groundedness & Faithfulness Metrics:**
   - *Current State:* Guardrails only verify trial ID set equality. The system does not verify whether individual matched criteria claims are actually supported by the source document.
   - *Consequence:* Susceptible to subtle LLM hallucinations where a criterion is asserted to match without supporting evidence in the patient note.

---

### Medium Limitations
*Useful improvements for platform usability and evaluation depth.*

9. **Zero Frontend Automated Testing:**
   - *Current State:* `frontend/medmatch-ui` has no test framework installed and 0 unit/E2E test files.
   - *Consequence:* Regression risks during UI enhancement.
10. **Frontend Asynchronous Task Polling Gap:**
    - *Current State:* `TrialUploadModal.tsx` contains static text stating that no status-check endpoint exists, even though the backend implements `GET /api/trials/upload/status/{task_id}`.
    - *Consequence:* Users must manually refresh the page after uploading trial PDFs.
11. **Unmounted Tasks Router:**
    - *Current State:* `app/api/routes/tasks.py` contains dead code unmounted from `FastAPI`.

---

### Low Limitations
*Cosmetic, polish, and future capabilities.*

12. **Role Naming Divergence:**
    - *Current State:* Seeded SQL migration roles (`ADMIN`, `DOCTOR`) diverge from Java enum values (`SYSTEM_ADMIN`, `PHYSICIAN`).
13. **Local Dev Proxy Configuration:**
    - *Current State:* `vite.config.ts` lacks `server.proxy` entries, requiring Nginx to proxy API calls in local development.

---

## 2. Current MedMatch Capstone Readiness

| Category | Status | Evidence | Required Work |
| :--- | :--- | :--- | :--- |
| **Problem definition** | **PARTIALLY IMPLEMENTED** | Documented in product roadmap and prompt guidelines; lacks mathematical problem formulation. | Formalize the clinical trial matching task as a two-stage retrieval + multi-label eligibility classification problem. |
| **Dataset** | **MISSING** | 0 trial PDFs or patient records in repository; uploads directory is empty. | Acquire/curate a standardized benchmark dataset (e.g., TREC Clinical Trials cohort or synthetic mimic cohort). |
| **Ground truth** | **MISSING** | No gold-standard labels (Eligible / Not Eligible / Possibly Eligible) exist. | Assemble an annotated ground truth test set with criteria-level and trial-level eligibility labels. |
| **Trial extraction** | **IMPLEMENTED** | `PDFService` + `LLMService.extract_trial_information` with Pydantic validation. | Enhance extraction evaluation; add structured attribute parsing (attribute, operator, value, unit). |
| **Patient NLP** | **MISSING** | Patient profiles contain basic string fields; notes are raw text without NER or negation. | Implement clinical entity extraction (biomarkers, conditions, stage, labs) and medical ontology normalization. |
| **Retrieval** | **PARTIALLY IMPLEMENTED**| pgvector cosine distance retrieval works, but uses unindexed sequential scans and pure vector search. | Add HNSW vector indexes; implement BM25 lexical search; build hybrid retrieval with Reciprocal Rank Fusion (RRF). |
| **RAG** | **IMPLEMENTED** | `PromptBuilder` hydrator + Gemini 2.5 Flash with structured Pydantic schema validation. | Refactor RAG context to supply extracted patient entities; implement two-stage criterion-level evaluation. |
| **Eligibility reasoning** | **IMPLEMENTED** | 966-line deterministic system prompt with tri-state exclusion logic. | Move from monolithic prompt evaluation to modular criterion scoring with formal decision aggregation. |
| **Explainability** | **PARTIALLY IMPLEMENTED**| Returns plain-text reasoning, recommendation, and categorized criteria lists. | Add structured evidence citations linking exact patient sentences to specific trial criteria. |
| **Grounding** | **PARTIALLY IMPLEMENTED**| Defensive validation rejects hallucinated trial IDs; abstains on failure. | Implement automated groundedness scoring (Ragas / TruLens Faithfulness) to detect clinical hallucination. |
| **Evaluation** | **MISSING** | No metrics computed (0 IR metrics, 0 classification metrics). | Implement evaluation harness computing Recall@k, MRR, nDCG@k, Precision, Recall, Macro-F1, and Confusion Matrix. |
| **Ablation studies** | **MISSING** | No experiment framework or ablation flags exist. | Build ablation framework evaluating: Vector vs Hybrid, PubMedBERT vs MiniLM, Full Context vs Entity-only. |
| **Security** | **IMPLEMENTED** | Asymmetric RS256 JWT, tenant isolation guards, PDF signature checks, parameterized queries. | Consolidate Flyway migrations; add PostgreSQL Row Level Security (RLS) policies. |
| **Deployment** | **PARTIALLY IMPLEMENTED**| Full Docker Compose and Kubernetes manifests exist, but Flyway collision blocks clean deployment. | Fix duplicate Flyway migration versions; verify automated end-to-end container startup. |
| **Reproducibility** | **MISSING** | `retrieval_benchmark.py` is broken; no deterministic evaluation scripts exist. | Fix benchmark script; create end-to-end reproducibility CLI runner with fixed seeds. |
| **Documentation** | **IMPLEMENTED** | Comprehensive architecture documents, ADRs, coding standards, and Phase 0 baselines. | Maintain capstone phase documentation tracking experimental progress and evaluation results. |

---

## 3. Top 10 Capstone Gaps

1. **Benchmark Evaluation Cohort & Ground Truth:** Construct a reproducible evaluation set of clinical trial protocols paired with patient notes and verified eligibility ground truth.
2. **Quantitative Metrics Harness:** Build a dedicated evaluation harness computing IR metrics (Recall@k, MRR, nDCG@k) and classification metrics (Accuracy, Macro-F1, Precision, Recall).
3. **Persist Matches to Database:** Wire `MatchingService` to `MatchRepository` so that eligibility results, confidence scores, and criteria breakdowns are permanently recorded in the `matches` table.
4. **Connect Patient Profiles to Matching:** Update `/api/matching/evaluate` to accept `patient_id`, retrieving structured attributes (age, sex, stage, diagnosis) and linking results back to the patient.
5. **Hybrid Retrieval (Dense + Sparse Fusion):** Implement BM25 lexical retrieval alongside SentenceTransformers dense retrieval, combining them via Reciprocal Rank Fusion (RRF).
6. **Domain-Specific Clinical Embeddings:** Evaluate specialized biomedical encoders (e.g., PubMedBERT, BGE-clinical) against the generic `all-MiniLM-L6-v2` baseline.
7. **PostgreSQL HNSW Vector Indexing:** Add migration creating HNSW cosine distance indexes on `trial_embeddings` and `criteria_embeddings` to eliminate sequential table scans.
8. **Structured Criterion-Level Scoring:** Transition from monolithic prompt reasoning to modular criterion-level evaluation (TrialGPT style) with transparent rule-based aggregation.
9. **Automated RAG Grounding & Hallucination Assessment:** Integrate Ragas / TruLens evaluation to measure context recall, context precision, and faithfulness across prompt variations.
10. **Fix Flyway Migration Collision & Benchmark Script:** Clean up duplicate Flyway files (`V1` to `V4`) in `auth-service` and update `retrieval_benchmark.py` with required tenant arguments.

---

## 4. Recommended Next Phase

### Phase 1: Research Problem & Evaluation Design
The immediate next priority is **Phase 1**, focusing on:
1. Formalizing the research problem, hypotheses, and clinical trial matching task definition.
2. Sourcing and formatting an annotated clinical evaluation dataset (e.g., TREC Clinical Trials / synthetic cohort).
3. Establishing the ground truth schema and stratified train/val/test splits.
4. Building the automated evaluation harness to compute baseline retrieval and reasoning metrics.
