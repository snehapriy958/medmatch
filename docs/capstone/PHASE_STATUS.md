# MedMatch Capstone Phase Status

```text
PHASE 0 — CURRENT SYSTEM AUDIT
STATUS: COMPLETE

PHASE 1 — RESEARCH PROBLEM + EVALUATION DESIGN
STATUS: COMPLETE

PHASE 2 — DATASET + GROUND TRUTH
STATUS: COMPLETE and ACCEPTED

PHASE 3 — CLINICAL TRIAL DOCUMENT INTELLIGENCE
STATUS: COMPLETE and ACCEPTED

PHASE 4 — PATIENT CLINICAL INFORMATION EXTRACTION
STATUS: COMPLETE

PHASE 5 — RETRIEVAL ENGINE
STATUS: COMPLETE

PHASE 6 — ELIGIBILITY REASONING
STATUS: COMPLETE

PHASE 7 — RAG vs. NON-RAG EXPERIMENTAL EVALUATION
STATUS: COMPLETE and ACCEPTED

PHASE 8 — EVIDENCE GROUNDING & HALLUCINATION EVALUATION
STATUS: COMPLETE and ACCEPTED

PHASE 9 — CLINICAL DECISION SUPPORT ROBUSTNESS & SAFETY HARNESS (UNCERTAINTY & HUMAN REVIEW)
STATUS: IMPLEMENTATION COMPLETE — AWAITING USER ACCEPTANCE

Next phase:
PHASE 10 — EXPLAINABILITY & EVIDENCE GRAPH FOUNDATION (NOT STARTED)
```

---

## Artifact Index for Phase 9 (Uncertainty & Human Review Foundation)

- [Phase 9 Uncertainty Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_uncertainty_audit.md)
- [Canonical Uncertainty Schema](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/uncertainty_schema.py)
- [Canonical Review Schema](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_schema.py)
- [Uncertainty Model Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_uncertainty_model.md)
- [Human Review Workflow Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_review_workflow.md)
- [Deterministic Review Routing Policy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_policy.py)
- [Review Policy Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_review_policy.md)
- [Deterministic Review Prioritizer](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_priority.py)
- [Review Resolution & Audit Manager](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_audit.py)
- [Conflict Resolution & Recency Policy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_conflict_resolution.md)
- [Error Taxonomy & Guardrails (U1–U12)](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_error_taxonomy.md)
- [Uncertainty Metrics Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_metrics_specification.md)
- [Uncertainty Metrics Engine](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/uncertainty_metrics.py)
- [Phase 9 Experiment Harness](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/human_review_experiment.py)
- [Phase 9 Development Fixtures](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase9/human_review_fixtures.json)
- [Phase 9 Development Fixtures README](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase9/README.md)
- [Phase 9 Human Review Test Suite](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/tests/human_review/)
- [Phase 9 Reproducibility Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_reproducibility.md)
- [Phase 9 Final Report](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_human_review_report.md)

---

## Artifact Index for Phase 8 (Evidence Grounding & Hallucination Evaluation)

- [Phase 8 Grounding Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_grounding_audit.md)
- [Canonical Grounding Schema](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_schema.py)
- [Claim Extraction Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_claim_extraction_specification.md)
- [Deterministic Claim Extractor](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/claim_extractor.py)
- [Evidence Support Policy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_grounding_policy.md)
- [Grounding & Provenance Validator](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_validator.py)
- [Hallucination Error Taxonomy (H1–H10)](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_hallucination_error_taxonomy.md)
- [Grounding Metrics Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_metrics_specification.md)
- [Grounding Metrics Engine](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_metrics.py)
- [Phase 8 Experiment Matrix (G1–G4)](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_experiment_matrix.md)
- [Phase 8 Grounding Experiment Harness](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_experiment.py)
- [Phase 8 Development Fixtures](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase8/grounding_fixtures.json)
- [Phase 8 Development Fixtures README](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase8/README.md)
- [Phase 8 Grounding Test Suite](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/tests/grounding_evaluation/)
- [Phase 8 Reproducibility Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_reproducibility.md)
- [Phase 8 Final Grounding Evaluation Report](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase8_grounding_evaluation_report.md)

---

## Artifact Index for Phase 7 (RAG vs. Non-RAG Experimental Evaluation)

- [Phase 7 RAG Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase7_rag_audit.md)
- [Controlled RAG vs. Non-RAG Experiment Contract](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase7_rag_nonrag_contract.md)
- [Phase 7 Experiment Matrix & Ablation Design](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase7_experiment_matrix.md)
- [Phase 7 Comparative Error Taxonomy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase7_rag_nonrag_error_taxonomy.md)
- [Phase 7 Reproducibility & Provenance Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase7_reproducibility.md)
- [Phase 7 Evaluation Methodology & Statistical Protocol](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase7_evaluation_methodology.md)
- [Phase 7 RAG vs. Non-RAG Report](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase7_rag_nonrag_report.md)
- [Non-RAG Experiment Runner (E5)](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/nonrag_experiment.py)
- [RAG Experiment Runner (E6/E7/E8)](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/rag_experiment.py)
- [Phase 7 Comparative Evaluation Harness](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/run_phase7_experiment.py)
- [Phase 7 Test Suite](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/tests/rag_evaluation/)

---

## Artifact Index for Phase 6 (Eligibility Reasoning)

- [Phase 6 Eligibility Reasoning Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase6_eligibility_reasoning_audit.md)
- [Canonical Eligibility Reasoning Contract](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/eligibility_reasoning_contract.md)
- [Eligibility Evidence Policy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/eligibility_evidence_policy.md)
- [Eligibility Uncertainty Policy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/eligibility_uncertainty_policy.md)
- [Phase 6 Eligibility Evaluation Methodology](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase6_eligibility_evaluation.md)
- [Eligibility Reasoning Error Taxonomy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/eligibility_reasoning_error_taxonomy.md)
- [Phase 6 Eligibility Reasoning Report](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase6_eligibility_reasoning_report.md)
- [Canonical Eligibility Schemas](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_schema.py)
- [Evidence-Grounded Reasoner](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_reasoner.py)
- [Deterministic Eligibility Aggregator](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_aggregator.py)
- [Deterministic Eligibility Validator](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/validate_eligibility.py)
- [Phase 6 Eligibility Test Suite](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/tests/eligibility/)

---

## Artifact Index for Phase 5 (Retrieval Engine)

- [Phase 5 Retrieval Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase5_retrieval_audit.md)
- [Canonical Retrieval Contract](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/retrieval_contract.md)
- [Retrieval Pydantic Schemas](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/retrieval_schema.py)
- [Modular Retrieval Engine & Algorithms](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/retrieval_engine.py)
- [Retrieval Evaluation Utilities](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/retrieval_evaluation.py)
- [Retrieval Error Taxonomy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/retrieval_error_taxonomy.md)
- [Phase 5 Retrieval Experiment Matrix](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase5_retrieval_experiment_matrix.md)
- [Phase 5 Retrieval Report](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase5_retrieval_report.md)
- [Phase 5 Retrieval Test Suite](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/tests/retrieval/)

---

## Artifact Index for Phase 4 (Patient Clinical Information Extraction)

- [Phase 4 Patient Pipeline Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase4_patient_pipeline_audit.md)
- [Canonical Patient Profile Schemas](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/patient_schema.py)
- [Patient Temporal Representation Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/patient_temporal_representation.md)
- [Patient Uncertainty & Negation Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/patient_uncertainty_specification.md)
- [Patient Information Provenance Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/patient_information_provenance.md)
- [Modular Patient Extractor Interface](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/patient_extractor.py)
- [Deterministic Patient Profile Validator](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/validate_patient_profile.py)
- [Patient Extraction Evaluation Design](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/patient_extraction_evaluation.md)
- [Patient Extraction Error Taxonomy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/patient_extraction_error_taxonomy.md)
- [Phase 4 Patient Information Report](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase4_patient_information_report.md)
- [Phase 4 Development Fixture README](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase4/README.md)
- [Phase 4 Patient Profile Development Fixture](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase4/patient_clinical_profile_fixture.json)
- [Phase 4 Extraction Contract Fixture](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase4/patient_extraction_contract.json)
- [Phase 4 Test Suite](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/tests/patient_information/)

---

## Artifact Index for Phase 3 (Clinical Trial Document Intelligence)

- [Phase 3 Document Pipeline Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase3_document_pipeline_audit.md)
- [Canonical Document Intelligence Schemas](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/document_schema.py)
- [Criterion Representation Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/criterion_representation_specification.md)
- [Document Provenance Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/document_provenance_specification.md)
- [Deterministic Section Normalizer](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/section_normalizer.py)
- [Deterministic Document Extraction Validator](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/validate_document_extraction.py)
- [Document Extraction Evaluation Design](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/document_extraction_evaluation.md)
- [Document Extraction Error Taxonomy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/document_extraction_error_taxonomy.md)
- [Phase 3 Document Intelligence Report](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase3_document_intelligence_report.md)
- [Phase 3 Development Fixture README](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase3/README.md)
- [Phase 3 Trial Document Development Fixture](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase3/trial_document_fixture.json)
- [Phase 3 Extraction Contract Fixture](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase3/document_extraction_contract.json)
- [Phase 3 Test Suite](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/tests/document_intelligence/)

---

## Artifact Index for Phase 2 (Dataset + Ground Truth)

- [Dataset Source Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/dataset_source_audit.md)
- [Dataset Card](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/dataset_card.md)
- [Dataset Statistics](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/dataset_statistics.md)
- [Phase 2 Dataset Report](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase2_dataset_report.md)
- [Dataset Reproduction Guide](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/README.md)
- [Dataset Master Manifest](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/manifests/dataset_manifest.json)
- [Dataset SHA-256 Checksums](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/manifests/checksums.sha256)
- [Canonical Dataset Schemas](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/dataset_schema.py)
- [Dataset Quality Validator](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/validate_dataset.py)
- [Synthetic Patient Generator](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/data_generation/generate_synthetic_patients.py)

---

## Artifact Index for Phase 1 (Research Problem & Evaluation Design)

- [Phase 1 Research Problem](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase1_research_problem.md)
- [Research Questions](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/research_questions.md)
- [Hypotheses](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/hypotheses.md)
- [Evaluation Methodology](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/evaluation_methodology.md)
- [Dataset Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/dataset_specification.md)
- [Ground Truth Schema](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/ground_truth_schema.md)
- [Metrics Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/metrics_specification.md)
- [Experiment Matrix](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/experiment_matrix.md)
- [Error Taxonomy](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/error_taxonomy.md)
- [Reproducibility Specification](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/reproducibility_specification.md)

---

## Artifact Index for Phase 0 (Current System Audit)

- [Phase 0 System Audit](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase0_system_audit.md)
- [Architecture Baseline](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/architecture_baseline.md)
- [AI Pipeline Baseline](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/ai_pipeline_baseline.md)
- [Data Pipeline Baseline](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/data_pipeline_baseline.md)
- [Evaluation Baseline](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/evaluation_baseline.md)
- [Security Baseline](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/security_baseline.md)
- [Capstone Gap Analysis](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/capstone_gap_analysis.md)
