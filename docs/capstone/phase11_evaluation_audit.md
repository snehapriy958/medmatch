# Phase 11 Audit: Evaluation Foundations & Benchmark Availability

**Document ID:** EVAL-AUDIT-P11  
**Phase:** Phase 11 — Evaluation & Ablation  
**Scope:** Historical Audit (Phases 2–10), Physical Benchmark Verification, Dataset Layer Classification, and Empirical Guardrails

---

## 1. Executive Summary

Phase 11 converts the research and evaluation infrastructure established across Phases 2 through 10 into an automated, scientifically reproducible evaluation and ablation pipeline.

Before executing or interpreting any experimental pipeline, scientific rigor requires an uncompromising audit of:
1. What upstream software contracts and capabilities exist from Phases 2–10.
2. What datasets physically exist in the local repository versus what datasets were merely identified in literature or design documents.
3. Whether the local dataset can support generalized empirical claims, statistical significance, or clinical validation.

---

## 2. Upstream Capability Audit (Phases 2–10)

| Phase | Core Capability | Established Canonical Contract | Phase 11 Reuse Strategy |
|:---|:---|:---|:---|
| **Phase 2** | Dataset & Ground Truth | `CanonicalTrial`, `CanonicalPatient`, `CriterionGroundTruth`, `TrialGroundTruth`, `compute_trial_eligibility` | Reused directly in [`scripts/dataset_validator_extended.py`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/dataset_validator_extended.py). |
| **Phase 3** | Document Intelligence | `TrialDocument`, `TrialCriterion`, `CriterionProvenance` | Referenced for criterion boundaries and verbatim text spans. |
| **Phase 4** | Patient Clinical Extraction | `PatientClinicalProfile`, `ClinicalFact`, `FactProvenance` | Powers Condition E1–E4 structured patient representations. |
| **Phase 5** | Retrieval Engine | `DenseRetriever`, `LexicalBM25Retriever`, `HybridRRFRetriever`, `RerankingRetriever` | Invoked directly by [`scripts/experiment_runner.py`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/experiment_runner.py) for retrieval conditions. |
| **Phase 6** | Eligibility Reasoning | `RuleBasedEligibilityReasoner`, `EligibilityAggregator`, `EligibilityValidator` | Evaluates criteria across all conditions (PASS/FAIL/UNKNOWN) and aggregates decisions. |
| **Phase 7** | RAG vs. Non-RAG | `NonRAGExperimentRunner`, `RAGExperimentRunner` | Provides the anti-leakage isolation boundary and RAG context grounding mechanism. |
| **Phase 8** | Grounding Evaluation | `GroundingEvaluation`, `GroundingClaim`, `ClaimSupportStatus` | Used to compute claim support rates, unsupported claim rates, and citation validity. |
| **Phase 9** | Uncertainty & Review | `UncertaintyRecord`, `HumanReviewRecord`, `ReviewAuditTrail` | Reused to evaluate uncertainty routing, conservative escalation, and reviewer immutability. |
| **Phase 10** | Explainability & Graph | `EvidenceGraph`, `StructuredExplanation`, G1–G12 invariants, X1–X14 errors | Supplies traceability metrics, graph integrity rates, and contradiction disclosure checks. |

---

## 3. Physical Benchmark Availability Audit

An exhaustive inspection of the local filesystem (`data/`, `data/fixtures/`, `data/splits/`, `data/raw/`) was performed at the start of Phase 11.

```text
+-----------------------------------------------------------------------------------------------------------------------------+
|                                             PHYSICAL DATASET AVAILABILITY AUDIT                                             |
+------------------------------------+--------------------------+-----------------------+-------------------+-----------------+
| Benchmark Candidate                | Physical File Path       | Ingestion Status      | Record Count      | Empirical Claim |
+------------------------------------+--------------------------+-----------------------+-------------------+-----------------+
| MedMatch Development Fixture       | data/fixtures/           | LOCAL FIXTURE         | 1 trial, 6 pats,  | PROHIBITED      |
|                                    |                          | IMPLEMENTED           | 48 crit labels    | (Test fixture)  |
| ClinicalTrials.gov REST API v2     | None (Curated template)  | IDENTIFIED —          | 0 bulk protocols  | PROHIBITED      |
|                                    |                          | NOT YET INGESTED      |                   | (No qrels)      |
| TrialGPT Benchmark Cohort          | None                     | IDENTIFIED —          | 0 narratives      | PROHIBITED      |
| (Qiao Jin et al., Nat Comm 2024)   |                          | NOT YET INGESTED      |                   | (Not ingested)  |
| TREC Clinical Trials 2021 Track    | None                     | IDENTIFIED —          | 0 topics/qrels    | PROHIBITED      |
| (NIST / OHSU)                      |                          | NOT YET INGESTED      |                   | (Not ingested)  |
| TREC Clinical Trials 2022 Track    | None                     | IDENTIFIED —          | 0 topics/qrels    | PROHIBITED      |
| (NIST / OHSU)                      |                          | NOT YET INGESTED      |                   | (Not ingested)  |
| MIMIC-IV Clinical Database         | None                     | REJECTED —            | 0 records         | PROHIBITED      |
| (PhysioNet)                        |                          | NOT SUITABLE          |                   | (DUA, no labels)|
+------------------------------------+--------------------------+-----------------------+-------------------+-----------------+
```

### Detailed Findings by Source:

1. **ClinicalTrials.gov REST API v2:**
   - Identified in Phase 2 documentation.
   - Status: `IDENTIFIED — NOT YET INGESTED`.
   - Protocol NCT02484404 was manually extracted as a structural template for Phase 3/4 testing. Bulk studies have not been ingested. Contains zero patient cases and zero eligibility labels.

2. **TrialGPT Benchmark Cohort:**
   - Identified in Phase 2 documentation.
   - Status: `IDENTIFIED — NOT YET INGESTED`.
   - The 184 synthetic EHR narratives and ~1,200 clinician-annotated patient-trial pairs from Jin et al. have not been downloaded or formatted into local repository tables.

3. **TREC Clinical Trials 2021 & 2022:**
   - Identified in Phase 2 documentation.
   - Status: `IDENTIFIED — NOT YET INGESTED`.
   - The 75 (2021) and 50 (2022) topics and associated NIST relevance qrels have not been ingested locally.

4. **MedMatch Development Test Fixture (`data/fixtures/`):**
   - Status: `LOCAL FIXTURE IMPLEMENTED`.
   - Composition: Exactly 1 trial protocol (`NCT02484404`), 8 criteria (5 inclusion, 3 exclusion), 6 synthetic patient records (`SYN_P001` to `SYN_P006`), 48 criterion-level labels, 6 trial-level labels.

---

## 4. Development Fixture Classification & Guardrails

> [!CRITICAL]
> **MANDATORY RESEARCH GUARDRAIL:**  
> The 6-patient dataset currently residing in `data/fixtures/` is **strictly classified as a DEVELOPMENT/TEST FIXTURE ONLY**.  
> Under no circumstances may it be described or treated as a generalizable research evaluation benchmark.

### Rationale:
1. **Sample Size ($n=6$):** A sample size of six synthetic patients across one clinical protocol provides zero statistical power. Reporting statistical significance ($p < 0.05$) or calculating 95% confidence intervals on $n=6$ constitutes pseudo-scientific fabrication.
2. **Rule-Derived Synthesis:** The six patients were generated by [`scripts/data_generation/generate_synthetic_patients.py`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/data_generation/generate_synthetic_patients.py) specifically to exercise unit tests, schema invariants, boundary conditions, and CI/CD pipelines.
3. **No External Validation:** The labels were established as deterministic unit test fixtures, not derived from multi-institutional blinded clinician consensus on real hospital cohorts.

---

## 5. Scope Boundary of Phase 11

Phase 11 implements the complete, defensible evaluation harness, pipelines, and ablations.
- If a valid external benchmark is not present locally, the pipeline executes against the local development fixture to **validate the evaluation code itself**.
- All resulting metrics are marked: `is_development_fixture_observation_only = True` and `empirical_claim_permitted = False`.
- Claims of "RAG accuracy improvement" or "retrieval superiority" are explicitly withheld until Phase 12 or subsequent benchmark ingestion phases.

---

## 6. Baseline Reproduction & E0 Scope Specification

E0 faithfully reproduces the production baseline's input representation, dense retrieval architecture, prompt structure, and reasoning boundary, using a deterministic offline research surrogate rather than invoking Gemini 2.5 Flash.

- **Production baseline uses Gemini 2.5 Flash:** In the deployed AI service (`services/ai-service/app/services/matching_service.py`), candidate trial criteria and raw patient notes are assembled into a monolithic prompt via `PromptBuilder.build_matching_prompt()` and submitted to Gemini 2.5 Flash (`temperature=0.0`).
- **Phase 11 E0 does NOT make live Gemini API calls:** To maintain 100% deterministic, offline, and hermetic execution in CI/CD environments without network dependencies, external API keys, or provider quota constraints, live LLM calls are intentionally withheld.
- **E0 is a deterministic research surrogate designed to preserve the baseline architecture/input contract for reproducible offline evaluation:** It enforces the raw narrative representation, dense retrieval candidate pool, and monolithic prompt tri-state criteria evaluation boundary without structured fact extraction or citation links.
- **Therefore E0 results must not be interpreted as measurements of Gemini model behavior itself:** Rather, they measure the mathematical and architectural properties of unstructured raw-note prompt matching under identical test inputs.
