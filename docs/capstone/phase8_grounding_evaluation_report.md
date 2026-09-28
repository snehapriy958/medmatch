# Phase 8 Final Report: Evidence Grounding & Hallucination Evaluation

## 1. Objective

Phase 8 of the MedMatch research roadmap establishes a reproducible, deterministic evaluation layer for measuring hallucination, evidence grounding, unsupported claims, citation/provenance correctness, and answer faithfulness in MedMatch eligibility reasoning.

The goal is **not** to tune or improve the model prematurely. The objective is to define and implement a mathematically sound and code-verified research evaluation layer that determines whether generated eligibility reasoning is actually supported by available patient facts and retrieved protocol evidence, without conflating ungrounded assertions with clinical validity.

---

## 2. Audit Findings

The audit documented in [`docs/capstone/phase8_grounding_audit.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_grounding_audit.md) identified the information boundaries, entry points, and structural constraints across Phase 6 reasoning and Phase 7 RAG evaluation:

1. **Patient Fact Ingestion**: Patient facts enter criterion reasoning via the normalized `PatientClinicalProfile` (`ClinicalFact` objects) and free-text notes. In production/Phase 6, patient assertions are bound to fact IDs.
2. **Trial Evidence Ingestion**: Protocol criteria enter via structured `TrialCriterion` objects. In RAG configurations (E6–E8), retrieved evidence chunks enter with provenance (`chunk_id`, `criterion_id`, `rank`, `score`, `method`). In NON-RAG (E5), retrieved chunks are strictly prohibited.
3. **Reasoning Generation & Status**: Reasoning text is generated per criterion alongside a deterministic three-valued status (`PASS`, `FAIL`, `UNKNOWN`).
4. **Information Gap**: Standard Phase 6 outputs provide evidence IDs and cited spans, but did not formally extract atomic propositions from free-form justification text to evaluate whether individual statements within a `PASS` or `FAIL` verdict were supported, contradicted, or fabricated.
5. **Taxonomic Separation**: The audit established seven distinct evaluation dimensions:
   - **A. Factual Support**: Direct entailment from verified evidence.
   - **B. Evidence Provenance**: Verifiable pointer to source document, section, and text span.
   - **C. Unsupported Inference**: Clinical leaps not justified by recorded data.
   - **D. Contradiction**: Direct conflict with patient record or protocol text.
   - **E. Missing Evidence**: Legitimate clinical absence ($UNKNOWN \neq FAIL$).
   - **F. Citation / Provenance Mismatch**: Citing nonexistent chunks, corrupted offsets, or wrong entity IDs.
   - **G. Hallucinated Clinical Facts**: Fabricating conditions, lab values, or temporal dates out of thin air.

---

## 3. Canonical Grounding Schema

The canonical schema is implemented in [`scripts/grounding_schema.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_schema.py) using strongly typed Pydantic models:

- **Enums**:
  - `SupportStatus`: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`. (Never collapsed into `PASS`/`FAIL`/`UNKNOWN`).
  - `ClaimType`: `PATIENT_FACT`, `TRIAL_CRITERION`, `TEMPORAL_FACT`, `NUMERICAL_VALUE`, `ELIGIBILITY_CONCLUSION`, `INFERRED_CLAIM`.
  - `EvidenceSourceType`: `PATIENT_FACT`, `PATIENT_NOTE`, `PATIENT_DEMOGRAPHIC`, `TRIAL_CRITERION`, `RETRIEVED_PASSAGE`, `EXTERNAL_KNOWLEDGE`, `UNKNOWN`.
  - `ContradictionStatus`: `NONE`, `NUMERICAL_CONTRADICTION`, `POLARITY_CONTRADICTION`, `TEMPORAL_CONTRADICTION`, `FACTUAL_CONTRADICTION`.
  - `HallucinationCategory`: `H1` (fabricated patient fact) through `H10` (unsupported certainty).
- **Core Models**:
  - `GroundingEvidence`: Canonical evidence representation with source typing, text, span/offsets, retrieval metadata (`method`, `rank`, `score`), and SHA-256 text fingerprint.
  - `GroundingClaim`: Atomic proposition representation with claim text, type, support status, citations, contradiction status, and mapped hallucination category.
  - `CitationValidationRecord`: Audit record assessing citation validity, existence of evidence span, offset accuracy, entity matching, and provenance consistency.
  - `GroundingEvaluation`: Aggregated evaluation container capturing claim counts, validity rates, grounding score, hallucination rate, and engine version.

---

## 4. Claim Extraction Contract

The claim extraction contract is specified in [`docs/capstone/phase8_claim_extraction_specification.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_claim_extraction_specification.md) and implemented in [`scripts/claim_extractor.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/claim_extractor.py).

- **Deterministic Rule-Based Architecture**: Eliminates circular LLM evaluation dependency. Claims are extracted using rule-based proposition boundary segmentation, syntactic clauses, and typed pattern detectors.
- **Atomic Disaggregation**: Splits compound conjunctions ("The patient has hypertension and type 2 diabetes") into atomic claims:
  1. *Patient has hypertension* (`PATIENT_FACT`)
  2. *Patient has type 2 diabetes* (`PATIENT_FACT`)
- **Claim Categorization Rules**:
  1. `NUMERICAL_VALUE`: Detects quantities with units (e.g., `7.2%`, `140 mmHg`, `50 mg/dL`, `> 18`).
  2. `TEMPORAL_FACT`: Detects temporal boundaries, durations, and dates (e.g., `last 6 months`, `within 30 days`, `prior to enrollment`).
  3. `ELIGIBILITY_CONCLUSION`: Detects eligibility verdicts and criteria fulfillment statements (e.g., `patient meets criterion`, `criterion is satisfied`, `verdict is PASS`).
  4. `TRIAL_CRITERION`: Detects protocol requirement restatements (e.g., `trial requires`, `protocol specifies`, `must be diagnosed with`).
  5. `PATIENT_FACT`: Detects clinical assertions regarding the patient's state, diagnoses, medications, or historical findings.
  6. `INFERRED_CLAIM`: Detects ungrounded speculative reasoning markers (`likely`, `suggests`, `assumed`).

---

## 5. Evidence Support Policy

Documented in [`docs/capstone/phase8_grounding_policy.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_grounding_policy.md) and enforced by [`scripts/grounding_validator.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_validator.py):

- **`SUPPORTED`**: Direct entailment where the claimed clinical entity, relation, and value are verified in patient facts, clinical notes, or protocol evidence.
- **`PARTIALLY_SUPPORTED`**: Multi-token or compound proposition where some clinical entities are verified, but secondary constraints remain unevidenced.
- **`UNSUPPORTED`**: The claimed fact does not exist in any available patient record, note, or protocol chunk.
- **`CONTRADICTED`**: Available evidence asserts an incompatible fact (value mismatch, e.g., claiming HbA1c is 7.2% when recorded as 8.4%; or polarity mismatch, e.g., claiming condition is present when record states "denies history of").
- **`INSUFFICIENT_EVIDENCE`**: Explicit uncertainty or missing evidence where the claim acknowledges that facts are insufficient to verify fulfillment.
- **Preservation of Phase 6 Semantics**:
  - *Silence $\neq$ Absence*: Lack of mention in patient notes produces `INSUFFICIENT_EVIDENCE` (or $H9$ if omitted), never negative evidence.
  - *Negation Preservation*: Explicit negation (e.g., "denies tobacco use") is treated as negative assertion, not missing data.
  - *No Fabricated Dates*: Relative expressions cannot be converted to absolute synthetic dates without evidence.

---

## 6. Provenance & Citation Validation

The research validator in [`scripts/grounding_validator.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_validator.py) audits every citation link without assuming correctness:

1. **Source Existence**: Confirms whether cited `source_id` exists in available patient facts or protocol evidence pool.
2. **Span Fidelity**:
   - For string spans without character offsets: performs normalized substring verification.
   - For character offsets `[start, end]`: strictly validates that `source_text[start:end] == span_text`. Catching off-by-one errors as `NONEXISTENT_EVIDENCE_SPAN`.
3. **Reference Consistency**: Flags mismatches between trial IDs, criterion IDs, and patient fact IDs (`WRONG_TRIAL_REFERENCE`, `WRONG_CRITERION_REFERENCE`, `WRONG_PATIENT_FACT_REFERENCE`).
4. **Retrieval Provenance**: Verifies that cited retrieved passages match the expected retrieval method (`DENSE`, `BM25`, `HYBRID_RRF`, `RERANK`) and rank metadata.
5. **No Invented Offsets**: Where character offsets are unavailable, the system uses `-1, -1` per project convention rather than synthesizing locations.

---

## 7. Hallucination Error Taxonomy

The complete taxonomy is specified in [`docs/capstone/phase8_hallucination_error_taxonomy.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_hallucination_error_taxonomy.md), defining operational criteria, detection mechanisms, and research interpretations for ten categories:

| ID | Name | Operational Definition | Severity / Research Impact |
|:---|:---|:---|:---|
| **H1** | Fabricated Patient Fact | Patient diagnosis, medication, or lab asserted without patient record support | Critical (Patient Safety Risk) |
| **H2** | Fabricated Trial Criterion | Nonexistent eligibility threshold or condition attributed to the protocol | High (Protocol Invalidity) |
| **H3** | Fabricated Numerical Value | Synthesized laboratory value, dosage, or cutoff differing from source data | Critical (Quantitative Distortion) |
| **H4** | Fabricated Temporal Fact | Absolute date or timeframe asserted without timestamp evidence | High (Window Violation) |
| **H5** | Unsupported Clinical Inference | Speculative clinical conclusion without documented intermediate steps | Moderate (Over-interpretation) |
| **H6** | Contradiction of Source Evidence | Claim directly inverting or conflicting with documented patient/trial evidence | Critical (Direct Contradiction) |
| **H7** | Provenance / Citation Mismatch | Citation pointing to wrong chunk, corrupted offset, or invalid identifier | High (Provenance Audit Failure) |
| **H8** | Unsupported Eligibility Conclusion | Concluding satisfaction/exclusion when underlying premises are unsupported | Critical (Erroneous Matching) |
| **H9** | Evidence Omission | Generating a conclusive verdict while ignoring recorded conflicting facts | High (Selective Reasoning) |
| **H10** | Unsupported Certainty | High-confidence assertion when recorded evidence is explicitly ambiguous | Moderate (Overconfidence) |

---

## 8. Grounding Metrics Specification

The metrics engine is specified in [`docs/capstone/phase8_metrics_specification.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_metrics_specification.md) and implemented in [`scripts/grounding_metrics.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_metrics.py):

$$\text{Claim Support Rate (CSR)} = \frac{N_{\text{supported}}}{N_{\text{evaluable}}}$$

$$\text{Unsupported Claim Rate (UCR)} = \frac{N_{\text{unsupported}}}{N_{\text{evaluable}}}$$

$$\text{Contradiction Rate (CR)} = \frac{N_{\text{contradicted}}}{N_{\text{evaluable}}}$$

$$\text{Citation Validity Rate (CVR)} = \frac{N_{\text{valid citations}}}{N_{\text{citations}}}$$

$$\text{Evidence Coverage (EC)} = \frac{N_{\text{supported}}}{N_{\text{requiring evidence}}}$$

$$\text{Grounding Score (GS)} = \frac{N_{\text{supported}} + 0.5 \cdot N_{\text{partially supported}}}{N_{\text{evaluable}}}$$

$$\text{Hallucination Rate (HR)} = \frac{N_{\text{unsupported}} + N_{\text{contradicted}}}{N_{\text{evaluable}}}$$

- **Zero-Denominator Invariants**:
  - When $N_{\text{evaluable}} = 0$: $CSR = 1.0$, $UCR = 0.0$, $CR = 0.0$, $GS = 1.0$, $HR = 0.0$.
  - When $N_{\text{citations}} = 0$: $CVR = 1.0$ (no invalid citations emitted).
- **Conservative Penalties**: Contradictions contribute directly to the hallucination numerator.

---

## 9. Experiment Matrix (G1–G4 Grounding Evaluation)

Documented in [`docs/capstone/phase8_experiment_matrix.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_experiment_matrix.md) and implemented in [`scripts/grounding_experiment.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_experiment.py):

- **G1 (NON-RAG Grounding)**:
  - Input: Patient clinical profile + criterion text only.
  - Retrieval: Strictly prohibited (`retrieved_evidence = []`).
  - Evaluates baseline hallucination tendencies when protocol context must come from internal parametric knowledge.
- **G2 (Dense-RAG Grounding)**:
  - Input: Patient clinical profile + criterion text + Phase 5 Dense Retriever top-k passages.
  - Evaluates grounding fidelity under semantic vector search.
- **G3 (Hybrid-RAG Grounding)**:
  - Input: Patient clinical profile + criterion text + Phase 5 Hybrid RRF Retriever top-k passages.
  - Evaluates grounding fidelity under combined lexical and dense retrieval.
- **G4 (RAG + Reranking Grounding)**:
  - Input: Patient clinical profile + criterion text + Phase 5 Cross-Encoder Reranking Retriever passages.
  - Evaluates citation accuracy and grounding precision when passages are reranked for criterion relevance.
- **Controlled Invariants**: Identical patient records, identical criterion specifications, identical claim extraction rules, identical validator policies. The only independent variable is the retrieval channel.

---

## 10. Synthetic Development Fixtures

Located in [`data/fixtures/phase8/grounding_fixtures.json`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase8/grounding_fixtures.json), with documentation in [`data/fixtures/phase8/README.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase8/README.md).

Contains **16 canonical test cases** explicitly covering:
1. `case-01-fully-supported`: Fully supported reasoning with valid citation span.
2. `case-02-partially-supported`: Multi-clause claim with partial evidence support.
3. `case-03-unsupported-claim`: Fabricated patient clinical condition ($H1$).
4. `case-04-contradicted-claim`: Claimed value directly contradicting lab record ($H6$).
5. `case-05-missing-evidence`: Explicit unknown/insufficient evidence handling ($UNKNOWN$).
6. `case-06-invalid-citation`: Citation referencing nonexistent evidence ID ($H7$).
7. `case-07-wrong-criterion-citation`: Valid passage citing mismatched criterion ID ($H7$).
8. `case-08-fabricated-numerical`: Invented lab measurement value ($H3$).
9. `case-09-fabricated-temporal`: Invented absolute temporal milestone ($H4$).
10. `case-10-unsupported-certainty`: Definite verdict asserted on speculative evidence ($H10$).
11. `case-11-negated-fact-handled`: Correct identification of negative status (denies disease).
12. `case-12-not-mentioned-handled`: Not-mentioned status treated as unknown, not negative.
13. `case-13-compound-mixed-support`: Multi-sentence reasoning containing both supported and unsupported claims.
14. `case-14-multiple-evidence-sources`: Supported claims drawing from multiple disparate evidence items.
15. `case-15-valid-retrieval-provenance`: Full RAG provenance with matching method and rank.
16. `case-16-invalid-retrieval-provenance`: Provenance claiming reranking when retrieval method was BM25 ($H7$).

**Notice**: Explicitly labeled as development test fixtures only, not clinical ground truth.

---

## 11. Test Results & Verification

All test suites were executed cleanly and deterministically:

### Research Grounding Evaluation Suite (`tests/grounding_evaluation/`)
- Total Tests: **36**
- Passed: **36** (100%)
- Execution time: ~0.44s
- Covered areas:
  - Canonical schema validation & serialization
  - Regex and rule-based claim extraction & categorization
  - Span verification and offset fidelity
  - Entity ID and retrieval method provenance checks
  - Support policy assignment (SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED)
  - Hallucination error taxonomy mapping (H1–H10)
  - Grounding metric computation & zero-denominator handling
  - Full execution of all 16 development fixtures
  - RAG vs. NON-RAG retrieval isolation and guardrail enforcement

### Regression Test Suite Across All Phases
- `tests/grounding_evaluation`: **36 passed**
- `tests/rag_evaluation`: **29 passed**
- `tests/document_intelligence`: **45 passed**
- `tests/patient_information`: **31 passed**
- `tests/eligibility`: **31 passed**
- `tests/retrieval`: **21 passed**
- `tests/dataset`: **17 passed**
- **Total Root Research Tests**: **210 passed** (0 failures, 0 warnings).

### Production AI Service Test Suite
- `services/ai-service/tests`: **45 passed**, 1 warning (Starlette deprecation), 0 failures.

---

## 12. Production Isolation Verification

Strict production isolation was maintained throughout Phase 8:

1. **`git diff --stat services/`**: Completely clean. Zero modified files.
2. **`git diff --name-only services/`**: Completely clean. Zero modified files.
3. **No Production Imports**: Neither `services/ai-service/` nor `services/auth-service/` imports any Phase 8 modules (`grounding_schema`, `claim_extractor`, `grounding_validator`, `grounding_metrics`, `grounding_experiment`).
4. **No Production Mutation**:
   - Production Gemini prompts: Untouched.
   - Production matcher algorithms: Untouched.
   - Production database schema and migrations: Untouched.
   - Production REST endpoints: Untouched.

---

## 13. Empirical Benchmark Guardrails

In adherence to scientific integrity principles:

- The external benchmark candidates identified in Phase 1 and Phase 2 have **not yet been ingested** as a validated research ground-truth benchmark.
- **Empirical Guardrail Enforcement**:
  - `grounding_experiment.py` enforces `has_validated_benchmark() == False`.
  - The experiment runner explicitly prohibits claiming empirical clinical performance metrics (hallucination percentages, grounding improvements, clinical safety).
  - All metrics reported in this phase are explicitly denoted as:
    > *"Development validation only; no empirical benchmark result."*

---

## 14. Reproducibility

Documented in [`docs/capstone/phase8_reproducibility.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_reproducibility.md):

- Evaluator version: `1.0.0-phase8-research`
- Schema version: `1.0.0`
- Fixture version: `phase8-dev-v1.0`
- Random seed: Deterministic `42` where applicable.
- Order invariants: Sorted claim IDs and evidence IDs ensure identical serialization across operating systems and runs.
- Missing offset policy: Represented as `(-1, -1)` without synthesizing fake offsets.

---

## 15. Limitations

1. **Rule-Based Claim Extraction**: The deterministic regex/rule extractor avoids LLM circularity, but complex grammatical syntax (e.g., deeply nested relative clauses) may produce coarse proposition boundaries.
2. **Lexical Token Overlap in Entailment**: While sufficient for deterministic validation of structured clinical facts, full semantic entailment of complex clinical reasoning requires curated benchmark annotations.
3. **Development Fixture Scope**: The 16 synthetic test cases validate implementation correctness and edge cases; they do not represent clinical population distributions.

---

## 16. Phase 9 Boundary

The following systems are **strictly excluded** from Phase 8 and reserved for Phase 9:
- Clinical decision support robustness and safety harnesses
- Human-in-the-loop review and physician override workflows
- Interactive evidence graph UI
- Production explainability interfaces
- Live clinical safety alerting or risk scoring in production services
- External clinical trial benchmark ingestion

Phase 8 terminates at the **reproducible hallucination and evidence-grounding evaluation layer**.

---

## Final Verification Checklist

| Item | Description | Status | Evidence |
|:---|:---|:---|:---|
| **A** | **Grounding Schema** | **PASS** | [`scripts/grounding_schema.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_schema.py) implements `GroundingClaim`, `GroundingEvidence`, `CitationValidationRecord`, `GroundingEvaluation`, and enums without string collapse. |
| **B** | **Claim Extraction** | **PASS** | [`scripts/claim_extractor.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/claim_extractor.py) and [`docs/capstone/phase8_claim_extraction_specification.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_claim_extraction_specification.md) provide deterministic proposition extraction across all 6 claim types without LLM circularity. |
| **C** | **Evidence Support Policy** | **PASS** | [`docs/capstone/phase8_grounding_policy.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_grounding_policy.md) operationalizes `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE` while preserving Phase 6 semantics. |
| **D** | **Provenance Validation** | **PASS** | [`scripts/grounding_validator.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_validator.py) audits source existence, exact character offsets, entity references, and retrieval method metadata. Tested in `test_provenance_validation.py`. |
| **E** | **Hallucination Taxonomy** | **PASS** | [`docs/capstone/phase8_hallucination_error_taxonomy.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_hallucination_error_taxonomy.md) specifies H1–H10 with operational criteria, detection rules, examples, and non-examples. |
| **F** | **Metrics** | **PASS** | [`scripts/grounding_metrics.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_metrics.py) and [`docs/capstone/phase8_metrics_specification.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_metrics_specification.md) define CSR, UCR, CR, CVR, EC, GS, and HR with zero-denominator safety. |
| **G** | **RAG/NON-RAG Methodology** | **PASS** | [`docs/capstone/phase8_experiment_matrix.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_experiment_matrix.md) and [`scripts/grounding_experiment.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_experiment.py) isolate G1–G4 under identical controls with strict anti-leakage guards. |
| **H** | **Development Fixtures** | **PASS** | Exactly 16 test cases in [`data/fixtures/phase8/grounding_fixtures.json`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase8/grounding_fixtures.json) covering all required error modes; documented in [`data/fixtures/phase8/README.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase8/README.md). |
| **I** | **Tests** | **PASS** | 36 Phase 8 tests passing (`tests/grounding_evaluation/`), 210 total research tests passing across all phases, 45 production AI service tests passing. |
| **J** | **Production Isolation** | **PASS** | `git diff --stat services/` is completely empty. No production services import Phase 8 code. |
| **K** | **Benchmark Guardrail** | **PASS** | Grounding harness refuses to report empirical claims without an ingested benchmark (`has_validated_benchmark() == False`). |
| **L** | **Phase 9 Boundary** | **PASS** | No Phase 9 safety harnesses, UI components, or clinical review workflows implemented. Work stopped cleanly at evaluation layer. |
