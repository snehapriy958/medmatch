# Phase 12 Clinical Safety Audit: Vulnerability & Failure Mode Analysis

**Document ID:** SAFETY-AUDIT-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Comprehensive Clinical Safety Audit Across Historical Research Modules (Phases 2–11) and Production Services (`services/`)  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Epistemic Scope

Phase 12 formalizes, specifies, implements, and tests the clinical-safety mechanisms for the MedMatch clinical trial eligibility matching system.

> [!CRITICAL]
> **RESEARCH CAPSTONE BOUNDARY & EPISTEMIC DISCLAIMER:**  
> MedMatch is an academic capstone and research software architecture. It is **NOT** a certified medical device, SaMD (Software as a Medical Device), or clinically validated diagnostic aid.  
> In accordance with scientific integrity standards, this audit strictly distinguishes between four levels of safety assurance:
> 1. **Formally Specified Safety Mechanisms:** Written rules, policies, and gate contracts defining safe clinical reasoning behaviors.
> 2. **Implemented and Tested Safety Mechanisms:** Deterministic Python algorithms, Pydantic validators, invariant checks, and unit/regression test suites.
> 3. **Synthetic Fixture Demonstrations:** Empirical observations executed strictly on synthetic, hand-authored patient profiles (`data/fixtures/`).
> 4. **Clinical Validation:** Prospective or retrospective multi-center clinical trials evaluated by blinded clinicians on real-world patient cohorts. **MedMatch has NOT undergone clinical validation. Zero claims of medical efficacy, real-world clinical safety, or regulatory compliance (FDA/MDR) are asserted.**

### Core Safety Principle
The fundamental tenet of MedMatch clinical safety is **conservative failure under uncertainty**:
> *The system must be designed so that uncertainty, missing information, conflicting evidence, temporal ambiguity, numerical boundary conditions, and unsupported clinical inferences are handled conservatively. The system must NEVER silently convert uncertainty or missing evidence into patient trial eligibility.*

---

## 2. Upstream Architecture & Contract Audit (Phases 2–11)

An audit of the software contracts established across Phases 2 through 11 reveals existing foundational safety guardrails and critical remaining gaps:

| Phase | Capability | Established Contract | Existing Safety Guardrail | Remaining Safety Gap |
|:---|:---|:---|:---|:---|
| **Phase 2** | Dataset & Ground Truth | `CanonicalPatient`, `CanonicalTrial`, `CriterionGroundTruth` | Explicit `UNKNOWN` ground truth state; strict split isolation preventing leakage. | Synthetic sample size ($n=6$) cannot represent clinical edge cases. |
| **Phase 3** | Document Intelligence | `TrialDocument`, `TrialCriterion`, `CriterionProvenance` | Character-level verbatim criterion span provenance; criteria type normalization. | Free-text unstructured criteria lack formal computable logical operators (e.g., nested AND/OR). |
| **Phase 4** | Patient Information | `PatientClinicalProfile`, `ClinicalFact`, `AssertionType` | Tri-state assertion (`PRESENT`, `ABSENT`, `UNKNOWN`); structured temporal span and confidence. | Clinical notes with implicit negations or conflicting historical records require deterministic resolution. |
| **Phase 5** | Retrieval Engine | `CandidateTrialRecord`, `DenseRetriever`, `HybridRRFRetriever` | Explicit tenant filtering (`hospital_id`); top-$k$ bounding; candidate deduplication. | Semantic bi-encoder can retrieve irrelevant protocols based on lexical surface similarity without detecting condition mismatches. |
| **Phase 6** | Eligibility Reasoning | `CriterionEvaluationRecord`, `EligibilityAggregator` | Deterministic aggregation: 1 FAIL $\rightarrow$ INELIGIBLE; 1 UNKNOWN (0 FAIL) $\rightarrow$ NEEDS_REVIEW. | Offline rule reasoner relies on hardcoded concept regexes rather than a full clinical ontology. |
| **Phase 7** | RAG vs. Non-RAG | `NonRAGExperimentRunner`, `RAGExperimentRunner` | `assert_no_retrieval_leakage()` strictly isolates non-retrieval reasoning from protocol hints. | RAG context injection does not guarantee that the reasoner only cites retrieved text. |
| **Phase 8** | Grounding Evaluation | `GroundingEvaluation`, `ClaimSupportStatus`, `GroundingValidator` | Hallucination taxonomy (H1–H5); claim support status verification; character span citation checks. | Grounding validation is post-hoc; does not actively intercept or abort an ungrounded inference mid-generation. |
| **Phase 9** | Uncertainty & Review | `UncertaintyRecord`, `HumanReviewRecord`, `HumanReviewPolicy` | 5 uncertainty dimensions; deterministic review routing; immutable audit trail of overrides. | Reviewer override lacks automated verification against external hospital medical records. |
| **Phase 10** | Explainability & Graph | `EvidenceGraph`, `StructuredExplanation`, G1–G12 invariants | Graph integrity enforcement; circular dependency prevention; contradiction disclosure. | Graph generation occurs after evaluation; an ungrounded reasoning step can propagate before graph rejection. |
| **Phase 11** | Evaluation & Ablation | `ExperimentConfig`, `Phase11ExperimentRunner`, `EvaluationMetrics` | Hermetic offline evaluation; statistical significance safeguards ($n < 30 \implies p = \text{None}$). | Evaluation pipeline measures accuracy on fixtures, not live system safety under adversarial inputs. |

---

## 3. Production Service Architecture Audit (`services/`)

Inspection of the current production AI service ([`services/ai-service/app/services/matching_service.py`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/matching_service.py), [`services/ai-service/app/services/prompt_builder.py`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/prompt_builder.py), and [`services/ai-service/app/services/llm_service.py`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/services/ai-service/app/services/llm_service.py)) identified several concrete clinical safety risks in the production implementation:

```text
+----------------------------------------------------------------------------------------------------+
|                              PRODUCTION MATCHER ARCHITECTURE & RISKS                               |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  1. Incoming Request: patient_note + hospital_id + authenticated current_user                       |
|     - Mitigation: _validate_user_hospital() checks hospital_id matches user JWT. [SAFE]            |
|                                                                                                    |
|  2. Semantic Retrieval: _retrieve_matching_criteria() via PostgreSQL pgvector CTE                  |
|     - Risk R-RET-01: Low-similarity queries filter all criteria.                                   |
|     - Verified Production Code: In MatchingService.evaluate_eligibility (lines 541–597):          |
|         if not filtered_criteria:                                                                  |
|             return EligibilityEvaluationResponse(results=[EligibilityResponse(                     |
|                 eligibility=EligibilityStatus.POSSIBLY_ELIGIBLE, confidence=0.0,                    |
|                 trial_ids_evaluated=[],                                                            |
|                 summary="No matching clinical trial criteria were retrieved. Eligibility cannot...",|
|                 missing_information=["No matching clinical trial criteria available."],             |
|                 reasoning="No trial criteria were retrieved for this patient..."                    |
|             )])                                                                                    |
|     - Reachability: Fully reachable when no criteria exceed similarity threshold.                  |
|     - Downstream Handling: Directly returned to API client via app/api/routes/matching.py (HTTP 200).|
|     - User Visibility: Fully user-visible in API responses and frontend UI.                         |
|     - Downstream Review Routing: Phase 9 review policy is currently an offline research harness     |
|       and is NOT invoked inline in production route; thus POSSIBLY_ELIGIBLE is emitted directly.    |
|     - CRITICAL SAFETY GAP: Using the enum value POSSIBLY_ELIGIBLE rather than a fail-closed status |
|       (e.g. INSUFFICIENT_RETRIEVAL_DATA or NEEDS_REVIEW) risks downstream client systems filtering  |
|       for positive candidates and treating zero-retrieval matches as potentially eligible.          |
|                                                                                                    |
|  3. Prompt Assembly: PromptBuilder.build_matching_prompt()                                         |
|     - Combines raw clinical note + complete criteria text.                                         |
|     - Risk R-PRM-01: Monolithic prompt passes unparsed patient narrative directly to LLM.          |
|       Numerical parsing, temporal washouts, and assertion states depend 100% on LLM inference.     |
|                                                                                                    |
|  4. LLM Execution: Gemini 2.5 Flash (temperature=0.0)                                              |
|     - Risk R-LLM-01: Non-deterministic edge cases, prompt injection via clinical note text,       |
|       or hallucinated criterion evaluations.                                                       |
|                                                                                                    |
|  5. Result Validation: _validate_llm_trial_results()                                               |
|     - Mitigation: Ensures returned trial IDs match expected retrieved set. [SAFE]                  |
|     - Production Gap: Validates trial IDs only! Does NOT validate that criteria citations exist,   |
|       that numerical boundaries were respected, or that missing patient info was flagged.          |
|                                                                                                    |
|  6. Audit Logging: _log_matching_audit()                                                           |
|     - Mitigation: Logs action, user, hospital, and counts to audit table. Patient note excluded.   |
|     - Production Gap: Individual criterion-level decisions and reasoning chains are not logged    |
|       to the persistent audit trail.                                                               |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Comprehensive Safety Risk Audit (Categories A–T)

Every stage of the clinical matching workflow is analyzed below across 20 distinct safety categories:

### A. Patient Information Extraction
- **Risk ID:** `RISK-PIE-01`
- **Failure Mode:** False positive extraction of a condition or biomarker not present in patient note (Hallucinated Patient Fact).
- **Trigger Condition:** LLM or NLP extractor misinterprets family history (e.g., "Mother had breast cancer") as patient diagnosis.
- **Potential Consequence:** Patient erroneously matched to targeted therapy trial, risking toxic exposure to ineffective drug.
- **Existing Mitigation:** Phase 4 assertion modeling (`AssertionType.ABSENT` / `FAMILY_HISTORY`); regex concept extraction.
- **Existing Test Coverage:** `tests/patient_information/test_patient_extractor.py` (family history separation).
- **Remaining Gap:** Production pipeline passes raw note directly to prompt without structured extraction filtering.
- **Proposed Safety Control:** `GATE-01` (Patient Fact Provenance Gate: No patient assertion permitted without exact character span match).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (Scenario `SCEN-01`, `SCEN-03`).
- **Clinical Validation Required:** Yes, for unconstrained clinical narrative vocabulary.

### B. Trial Criterion Extraction
- **Risk ID:** `RISK-TCE-01`
- **Failure Mode:** Misclassification of an exclusion criterion as an inclusion criterion.
- **Trigger Condition:** Protocol document uses non-standard headings or ambiguous phrasing (e.g., "Contraindications and Ineligibility").
- **Potential Consequence:** An exclusion (e.g., "Active hepatitis B") is treated as a required inclusion, inverting eligibility logic.
- **Existing Mitigation:** Phase 3 `section_normalizer.py` and `CriterionType` enum validation.
- **Existing Test Coverage:** `tests/document_intelligence/test_document_intelligence.py`.
- **Remaining Gap:** Multi-part criteria containing both inclusion and exclusion clauses in a single sentence.
- **Proposed Safety Control:** `GATE-02` (Criterion Schema Integrity Gate: Explicit criteria typing with mandatory contradiction checks).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-14`, `SCEN-15`).
- **Clinical Validation Required:** Yes, across diverse institutional protocol authoring formats.

### C. Retrieval
- **Risk ID:** `RISK-RET-01`
- **Failure Mode:** Semantic retrieval omission of an available, clinically indicated trial due to lexical divergence.
- **Trigger Condition:** Patient note describes "squamous cell carcinoma of the lung" while trial indexes only "NSCLC".
- **Potential Consequence:** Patient misses enrollment window for life-prolonging clinical trial.
- **Existing Mitigation:** Phase 5 Hybrid RRF (`HybridRRFRetriever`) combining BM25 keyword matching with dense embeddings.
- **Existing Test Coverage:** `tests/retrieval/test_retrieval_engine.py`.
- **Remaining Gap:** Vocabulary mismatch on rare disease synonyms or acronyms; production matcher uses dense-only retrieval.
- **Proposed Safety Control:** `GATE-03` (Retrieval Sufficiency Gate: Mandatory hybrid retrieval with query expansion and coverage monitoring).
- **Control Type:** Model-dependent / Deterministic fallback.
- **Evaluable on Fixtures:** Yes (`SCEN-17`).
- **Clinical Validation Required:** Yes, on large multi-trial cohorts ($N > 1,000$).

### D. Evidence Selection
- **Risk ID:** `RISK-EVS-01`
- **Failure Mode:** Selecting outdated or superseded evidence passages from patient medical record.
- **Trigger Condition:** Encounter history contains lab results from 2 years prior alongside current labs.
- **Potential Consequence:** Eligibility determined based on historical remissions or obsolete biomarkers.
- **Existing Mitigation:** Phase 4 temporal anchoring (`TemporalSpan`); recency ordering in `EvidenceGraphBuilder`.
- **Existing Test Coverage:** `tests/patient_information/test_temporal_representation.py`.
- **Remaining Gap:** Notes lacking ISO timestamps or explicit relative time anchors ("previously", "initially").
- **Proposed Safety Control:** `GATE-04` (Temporal Evidence Validity Gate: Require explicit temporal validity window $\le 90$ days for dynamic clinical facts).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-06`, `SCEN-07`).
- **Clinical Validation Required:** Yes, on real EHR longitudinal encounters.

### E. Criterion-Level Reasoning
- **Risk ID:** `RISK-CLR-01`
- **Failure Mode:** Converting an `UNKNOWN` criterion status into `PASS` without supporting evidence.
- **Trigger Condition:** Patient record lacks mention of brain MRI; trial excludes CNS metastases. Model assumes absence of mention implies absence of metastases.
- **Potential Consequence:** Patient with undetected brain metastases enrolled in trial with neurotoxic investigational agent.
- **Existing Mitigation:** Phase 6 tri-state logic (`RuleBasedEligibilityReasoner`); Phase 9 `UncertaintyDimension.MISSING_INFORMATION`.
- **Existing Test Coverage:** `tests/eligibility/test_eligibility_reasoner.py`.
- **Remaining Gap:** Production Gemini prompt can hallucinate negative findings when absence of evidence is ambiguous.
- **Proposed Safety Control:** `GATE-05` (Strict Tri-State Evidence Gate: Criterion cannot evaluate to PASS/FAIL without explicit positive/negative evidence).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-01`, `SCEN-04`).
- **Clinical Validation Required:** No (logical invariant).

### F. Numerical Comparisons
- **Risk ID:** `RISK-NUM-01`
- **Failure Mode:** Floating-point boundary or operator inversion in laboratory thresholds (e.g., $<$ vs $\le$).
- **Trigger Condition:** Patient platelet count $= 99 \times 10^9/\text{L}$; criterion requires $\ge 100 \times 10^9/\text{L}$.
- **Potential Consequence:** Cytopenic patient enrolled in trial causing severe bone marrow suppression.
- **Existing Mitigation:** Phase 6 regex numerical comparator in `eligibility_reasoner.py`.
- **Existing Test Coverage:** `tests/eligibility/test_eligibility_reasoner.py` (boundary tests).
- **Remaining Gap:** Unit mismatches (e.g., $\text{g/dL}$ vs $\text{g/L}$, $\mu\text{mol/L}$ vs $\text{mg/dL}$); LLM numerical reasoning hallucinations.
- **Proposed Safety Control:** `GATE-06` (Deterministic Numerical Boundary Gate: Automated unit normalization and strict mathematical evaluation).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-08`, `SCEN-09`, `SCEN-10`, `SCEN-11`).
- **Clinical Validation Required:** No (mathematical verification).

### G. Temporal Reasoning
- **Risk ID:** `RISK-TMP-01`
- **Failure Mode:** Premature enrollment during mandatory drug washout window.
- **Trigger Condition:** Chemotherapy completed 27 days prior; protocol requires $\ge 28$ day washout.
- **Potential Consequence:** Adverse drug-drug interaction between prior chemotherapy and experimental trial agent.
- **Existing Mitigation:** Phase 4 `TemporalSpan` duration calculation; Phase 6 `_check_temporal_washout()`.
- **Existing Test Coverage:** `tests/eligibility/test_eligibility_reasoner.py`.
- **Remaining Gap:** Relative date expressions ("completed 3 weeks ago", "last month") without explicit reference dates.
- **Proposed Safety Control:** `GATE-07` (Conservative Temporal Washout Gate: Relative temporal ambiguity defaults to `UNKNOWN` $\rightarrow$ `NEEDS_REVIEW`).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-07`).
- **Clinical Validation Required:** Yes, for fuzzy clinical time expressions.

### H. Negation / Assertion
- **Risk ID:** `RISK-NEG-01`
- **Failure Mode:** Negation scope misinterpretation (treating "No history of myocardial infarction, but patient reports hypertension" as negating hypertension).
- **Trigger Condition:** Complex clinical narrative sentence with multiple clauses and coordinating conjunctions.
- **Potential Consequence:** Patient's active cardiovascular comorbidity missed; patient enrolled in high-risk cardiotoxic trial.
- **Existing Mitigation:** Phase 4 assertion normalization; NegEx-based pattern matching.
- **Existing Test Coverage:** `tests/patient_information/test_patient_extractor.py`.
- **Remaining Gap:** Double negations ("cannot rule out", "not inconsistent with") and linguistic hedging.
- **Proposed Safety Control:** `GATE-08` (Negation Integrity Gate: Hedged or ambiguous assertions must be tagged as `UNCERTAIN` and routed to human review).
- **Control Type:** Deterministic / Rule-based.
- **Evaluable on Fixtures:** Yes (`SCEN-03`, `SCEN-04`).
- **Clinical Validation Required:** Yes, on annotated clinical linguistics benchmarks.

### I. Conflicting Patient Information
- **Risk ID:** `RISK-CPI-01`
- **Failure Mode:** Silent resolution of discordant patient clinical facts without clinician notification.
- **Trigger Condition:** Tissue biopsy reports "EGFR exon 19 deletion", while subsequent cfDNA liquid biopsy reports "EGFR wild-type".
- **Potential Consequence:** Inappropriate therapy selection based on arbitrary tie-breaking.
- **Existing Mitigation:** Phase 9 `UncertaintyDimension.CONFLICTING_EVIDENCE`; `EvidenceGraph` contradiction nodes.
- **Existing Test Coverage:** `tests/human_review/test_conflict_resolution.py`.
- **Remaining Gap:** Production service has no multi-source conflict reconciliation engine.
- **Proposed Safety Control:** `GATE-09` (Contradiction Escalation Gate: Any fact conflict automatically forces criterion status `UNKNOWN` and routes to review).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-05`, `SCEN-13`).
- **Clinical Validation Required:** No (conservative policy enforcement).

### J. Conflicting Trial Evidence
- **Risk ID:** `RISK-CTE-01`
- **Failure Mode:** Conflicting eligibility requirements within the protocol itself (e.g., protocol body specifies ECOG 0–1 while schema table lists ECOG 0–2).
- **Trigger Condition:** Protocol amendments or inconsistencies across trial registry entries.
- **Potential Consequence:** Patient enrolled based on superseded or inconsistent protocol section.
- **Existing Mitigation:** Phase 3 document section normalization and provenance tracking.
- **Existing Test Coverage:** `tests/document_intelligence/test_section_normalizer.py`.
- **Remaining Gap:** Registry vs PDF protocol discrepancies.
- **Proposed Safety Control:** `GATE-10` (Protocol Discrepancy Gate: Flag conflicting criteria between protocol text and registry schema).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-18`).
- **Clinical Validation Required:** Yes, on real-world sponsor amendment packages.

### K. Missing Information
- **Risk ID:** `RISK-MSI-01`
- **Failure Mode:** Treating missing information as negative evidence (Closed-World Assumption violation).
- **Trigger Condition:** Patient narrative makes no mention of hepatitis infection; model assumes patient does not have hepatitis.
- **Potential Consequence:** Patient with undiagnosed or unrecorded chronic infection enrolled in immunosuppressive trial.
- **Existing Mitigation:** Phase 4 Open-World Assumption principle; Phase 6 `CriterionEvaluationStatus.UNKNOWN`.
- **Existing Test Coverage:** `tests/patient_information/test_uncertainty_semantics.py`.
- **Remaining Gap:** LLM zero-shot prompts frequently exhibit default closed-world reasoning bias.
- **Proposed Safety Control:** `GATE-11` (Open-World Completeness Gate: Absence of mention strictly produces `UNKNOWN`, never `FAIL` or `PASS`).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-01`, `SCEN-12`).
- **Clinical Validation Required:** No (core architectural invariant).

### L. Unsupported Inference
- **Risk ID:** `RISK-USI-01`
- **Failure Mode:** Clinical inference not supported by documented patient facts (e.g., inferring patient has brain metastases from "headache").
- **Trigger Condition:** LLM uses speculative reasoning without grounding in imaging or pathology reports.
- **Potential Consequence:** Patient inappropriately excluded from clinical trial based on unconfirmed conjecture.
- **Existing Mitigation:** Phase 8 `ClaimSupportStatus.UNSUPPORTED`; Phase 10 `EvidenceGraphValidator`.
- **Existing Test Coverage:** `tests/grounding_evaluation/test_grounding_validator.py`.
- **Remaining Gap:** Production matcher does not validate LLM reasoning sentences against structured evidence nodes.
- **Proposed Safety Control:** `GATE-12` (Claim Grounding Verification Gate: Every claim must resolve to an explicit source fact or protocol citation).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-16`, `SCEN-19`).
- **Clinical Validation Required:** Yes, for evaluating clinician consensus on plausible inferences.

### M. Hallucination
- **Risk ID:** `RISK-HAL-01`
- **Failure Mode:** Fabrication of non-existent lab values, staging, or trial criteria in generated rationale.
- **Trigger Condition:** Generative model produces fluent, convincing clinical prose detached from input context.
- **Potential Consequence:** Clinician accepts false rationale, compromising trial enrollment integrity and patient safety.
- **Existing Mitigation:** Phase 8 Hallucination Taxonomy (H1–H5); Phase 10 provenance verification.
- **Existing Test Coverage:** `tests/grounding_evaluation/test_hallucination_taxonomy.py`.
- **Remaining Gap:** Generative reasoning occurs before verification; post-hoc detection does not prevent model generation.
- **Proposed Safety Control:** `GATE-13` (Hallucination Suppression Gate: Strip ungrounded claims and force `UNSUPPORTED_CLAIM_ERROR` if unverified text appears).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-19`, `SCEN-20`).
- **Clinical Validation Required:** Yes, for adversarial clinical note benchmarks.

### N. Eligibility Aggregator Logic
- **Risk ID:** `RISK-AGG-01`
- **Failure Mode:** Aggregator marks patient `ELIGIBLE` when one or more criteria remain `UNKNOWN`.
- **Trigger Condition:** Implementation treats `UNKNOWN` as non-blocking or computes eligibility by simple majority voting.
- **Potential Consequence:** Patient enrolled without verifying critical safety exclusion criteria.
- **Existing Mitigation:** Phase 6 `EligibilityAggregator`: strictly requires `failed_count == 0` AND `unknown_count == 0` for `ELIGIBLE`.
- **Existing Test Coverage:** `tests/eligibility/test_eligibility_aggregator.py`.
- **Remaining Gap:** Production service relies on Gemini's self-reported `eligibility` string without deterministic re-aggregation.
- **Proposed Safety Control:** `GATE-14` (Deterministic Aggregation Gate: Final trial decision computed strictly by code, overriding any LLM summary status).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-01`, `SCEN-14`).
- **Clinical Validation Required:** No (mathematical verification).

### O. Human-Review Routing
- **Risk ID:** `RISK-HRR-01`
- **Failure Mode:** System fails to route an uncertain, borderline, or conflicting case to clinician review.
- **Trigger Condition:** Threshold logic silently rounds up or uncertainty score fails to cross escalation trigger.
- **Potential Consequence:** Ambiguous case finalized autonomously without clinical oversight.
- **Existing Mitigation:** Phase 9 `HumanReviewPolicy` and `ReviewPriority` calculation (`P1_CRITICAL` to `P4_INFORMATIONAL`).
- **Existing Test Coverage:** `tests/human_review/test_review_policy.py`.
- **Remaining Gap:** Production matcher has no concept of a human review queue; outputs directly to web UI.
- **Proposed Safety Control:** `GATE-15` (Mandatory Human Escalation Gate: Any `NEEDS_REVIEW` trial status or `UNKNOWN` criterion automatically triggers queue placement).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-01`, `SCEN-05`).
- **Clinical Validation Required:** Yes, for review queue usability and clinician burden assessment.

### P. Human-Review Override
- **Risk ID:** `RISK-HRO-01`
- **Failure Mode:** Reviewer overrides machine recommendation without providing clinical rationale or audit justification.
- **Trigger Condition:** Clinician rapidly clicks "Approve" without logging supporting external evidence.
- **Potential Consequence:** Untraceable decision override; potential medico-legal liability and trial audit failure.
- **Existing Mitigation:** Phase 9 `ReviewerDecision` Pydantic model requiring `rationale` (min 10 chars) and `reviewer_id`.
- **Existing Test Coverage:** `tests/human_review/test_review_schema.py`.
- **Remaining Gap:** Production service lacks override audit logging schemas.
- **Proposed Safety Control:** `GATE-16` (Auditable Override Gate: Overrides strictly preserve original machine outputs, requiring immutable rationale and credentials).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-21`, `SCEN-22`).
- **Clinical Validation Required:** No (compliance/audit invariant).

### Q. Explanation Generation
- **Risk ID:** `RISK-EXG-01`
- **Failure Mode:** Generated explanation contradicts the structured evidence graph or decision status.
- **Trigger Condition:** Natural language generator produces text describing patient as "eligible" while graph indicates "ineligible".
- **Potential Consequence:** Clinician deceived by natural language summary, ignoring structured red flags.
- **Existing Mitigation:** Phase 10 `ExplanationValidator` (X1–X14 failure modes); contradiction disclosure rules.
- **Existing Test Coverage:** `tests/explainability/test_explanation_validator.py`.
- **Remaining Gap:** Production matcher generates explanations via free-form Gemini text without graph validation.
- **Proposed Safety Control:** `GATE-17` (Explanation Graph Alignment Gate: Reject explanation if claims contradict underlying graph states).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-20`).
- **Clinical Validation Required:** Yes, on physician comprehension studies.

### R. Provenance & Citation Mapping
- **Risk ID:** `RISK-PRV-01`
- **Failure Mode:** Citation text span does not match the referenced document source or contains invalid character offsets.
- **Trigger Condition:** Text offset drift between raw document text and tokenized/cleaned representation.
- **Potential Consequence:** Audit verification fails; clinicians cannot inspect verbatim source text.
- **Existing Mitigation:** Phase 3/4 `FactProvenance` and `CriterionProvenance`; Phase 10 G4 provenance invariant.
- **Existing Test Coverage:** `tests/document_intelligence/test_provenance.py`.
- **Remaining Gap:** Offsets pointing to `-1` when exact character location is unrecorded.
- **Proposed Safety Control:** `GATE-18` (Verbatim Provenance Gate: Offsets must match source substring exactly, or explicitly record `-1` with field name).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-23`).
- **Clinical Validation Required:** No (data integrity check).

### S. Multi-Tenant Data Isolation
- **Risk ID:** `RISK-MTI-01`
- **Failure Mode:** Retrieval or evaluation leaks patient notes or trial data across hospital tenant boundaries.
- **Trigger Condition:** Shared cache key collision or missing `hospital_id` filter in database vector queries.
- **Potential Consequence:** Severe HIPAA/GDPR data breach; unauthorized cross-hospital clinical data access.
- **Existing Mitigation:** Production `_validate_user_hospital()`; tenant-isolated cache keys (`f"{hospital_id}:{prompt}"`).
- **Existing Test Coverage:** `services/ai-service/tests/test_matching_service.py` (tenant isolation tests).
- **Remaining Gap:** Research scripts run locally without database multi-tenancy constraints.
- **Proposed Safety Control:** `GATE-19` (Cryptographic Tenant Boundary Gate: Every retrieval request and reasoning context must enforce strict tenant ID match).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-24`).
- **Clinical Validation Required:** No (security/compliance requirement).

### T. Audit Logging
- **Risk ID:** `RISK-AUD-01`
- **Failure Mode:** Matching or eligibility decision occurs without an immutable, persistent audit log record.
- **Trigger Condition:** Database transaction rollback or asynchronous logging failure during high request volume.
- **Potential Consequence:** Clinical trial decision cannot be reconstructed during regulatory or clinical audit.
- **Existing Mitigation:** Production `AuditService.log()`; Phase 9 `ReviewAuditTrail`.
- **Existing Test Coverage:** `services/ai-service/tests/test_audit_service.py`.
- **Remaining Gap:** Production `_log_matching_audit` swallows exceptions (`except Exception: logger.exception(...)`) without aborting transaction.
- **Proposed Safety Control:** `GATE-20` (Fail-Closed Audit Gate: Critical clinical decisions cannot return to user if audit log write fails).
- **Control Type:** Deterministic.
- **Evaluable on Fixtures:** Yes (`SCEN-21`).
- **Clinical Validation Required:** No (software reliability requirement).

---

## 5. Summary Matrix: Risk Severity & Safety Control Implementation

```text
+-------------------------------------------------------------------------------------------------------------------------------+
|                                             PHASE 12 SAFETY RISK AUDIT SUMMARY                                                |
+----------+---------------------------------+---------------+-----------------------+---------------------+--------------------+
| Risk ID  | Category                        | Severity      | Safety Gate           | Control Nature      | Fixture Evaluable? |
+----------+---------------------------------+---------------+-----------------------+---------------------+--------------------+
| RISK-PIE | Patient Fact Fabrication        | CRITICAL      | GATE-01 (Provenance)  | Deterministic       | YES (SCEN-01)      |
| RISK-TCE | Criterion Inversion             | CRITICAL      | GATE-02 (Schema)      | Deterministic       | YES (SCEN-14)      |
| RISK-RET | Critical Trial Omission         | HIGH          | GATE-03 (Sufficiency) | Hybrid/Fallback     | YES (SCEN-17)      |
| RISK-EVS | Outdated Evidence Used          | HIGH          | GATE-04 (Temporal)    | Deterministic       | YES (SCEN-06)      |
| RISK-CLR | UNKNOWN -> PASS Silent Flip     | CRITICAL      | GATE-05 (Tri-State)   | Deterministic       | YES (SCEN-01)      |
| RISK-NUM | Boundary / Unit Error           | CRITICAL      | GATE-06 (Numerical)   | Deterministic       | YES (SCEN-08)      |
| RISK-TMP | Washout Window Violation        | CRITICAL      | GATE-07 (Washout)     | Deterministic       | YES (SCEN-07)      |
| RISK-NEG | Negation Scope Misread          | HIGH          | GATE-08 (Negation)    | Deterministic/Rules | YES (SCEN-03)      |
| RISK-CPI | Discordant Patient Facts        | HIGH          | GATE-09 (Conflict)    | Deterministic       | YES (SCEN-05)      |
| RISK-CTE | Conflicting Protocol Clauses    | MEDIUM        | GATE-10 (Discrepancy) | Deterministic       | YES (SCEN-18)      |
| RISK-MSI | Missing Info -> Negative Bias   | CRITICAL      | GATE-11 (Open-World)  | Deterministic       | YES (SCEN-01)      |
| RISK-USI | Unsupported Speculation         | HIGH          | GATE-12 (Grounding)   | Deterministic       | YES (SCEN-16)      |
| RISK-HAL | Rationale Hallucination         | HIGH          | GATE-13 (Suppression) | Deterministic       | YES (SCEN-19)      |
| RISK-AGG | Premature ELIGIBLE Status       | CRITICAL      | GATE-14 (Aggregation) | Deterministic       | YES (SCEN-01)      |
| RISK-HRR | Review Omission on Ambiguity    | HIGH          | GATE-15 (Escalation)  | Deterministic       | YES (SCEN-01)      |
| RISK-HRO | Unaudited Human Override        | HIGH          | GATE-16 (Override)    | Deterministic       | YES (SCEN-21)      |
| RISK-EXG | Explanation / Graph Mismatch    | MEDIUM        | GATE-17 (Alignment)   | Deterministic       | YES (SCEN-20)      |
| RISK-PRV | Citation / Offset Drift         | LOW           | GATE-18 (Offset)      | Deterministic       | YES (SCEN-23)      |
| RISK-MTI | Cross-Tenant Leakage            | CRITICAL      | GATE-19 (Tenant)      | Deterministic       | YES (SCEN-24)      |
| RISK-AUD | Silent Audit Log Failure        | HIGH          | GATE-20 (Audit)       | Deterministic       | YES (SCEN-21)      |
+----------+---------------------------------+---------------+-----------------------+---------------------+--------------------+
```

---

## 6. Audit Verdict & Phase 12 Roadmap

The audit confirms that while the research pipeline (Phases 2–11) established rigorous contracts for tri-state reasoning, deterministic aggregation, uncertainty routing, and grounding verification, the system requires a **unified clinical-safety layer** that:
1. Formulates explicit **Safety Gates** that halt execution or force conservative fallback whenever an unsafe state is detected.
2. Codifies **Machine-Checkable Invariants** that can be asserted deterministically.
3. Tests these mechanisms against a comprehensive **24-scenario synthetic safety test fixture** including systematic **error injection**.
4. Provides a bridge between research contracts and production safety specifications without altering production code.
