# MedMatch Capstone — Phase 8 Grounding & Hallucination Test Fixtures

**Fixture Version:** `1.0.0-dev`  
**Phase:** 8 — Grounding Evaluation & Faithfulness Auditing  
**Date:** September 2026  
**Status:** Synthetic Development Test Fixture  

---

> [!WARNING]
> **DEVELOPMENT TEST FIXTURES ONLY — NOT CLINICAL GROUND TRUTH**  
> The 16 test cases in `grounding_fixtures.json` are synthetic development fixtures constructed solely for automated software verification, schema validation, and unit testing of `scripts/grounding_validator.py`, `scripts/claim_extractor.py`, and `scripts/grounding_metrics.py`.  
> They do **NOT** represent clinical validation data, clinical benchmark results, or real-world patient records.

---

## Fixture Index (16 Test Cases)

| Index | Case ID | Description | Primary Target | Expected Faithfulness |
| :---: | :--- | :--- | :--- | :---: |
| **1** | `case-01-fully-supported` | Fully supported clinical reasoning | Factual entailment | **Faithful** |
| **2** | `case-02-partially-supported` | Partially supported reasoning | Qualifier unverified | Non-faithful |
| **3** | `case-03-unsupported-claim` | Unsupported clinical condition ($H1$) | Fabricated fact | Non-faithful |
| **4** | `case-04-contradicted-claim` | Contradiction of negated fact ($H6$) | Assertion conflict | Non-faithful |
| **5** | `case-05-missing-evidence` | Epistemic missingness handled correctly | Insufficient evidence | **Faithful** |
| **6** | `case-06-invalid-citation` | Citation pointing to nonexistent span ($H7$) | Offset drift | Non-faithful |
| **7** | `case-07-wrong-criterion-citation`| Citation referencing wrong trial ($H7$) | Provenance mismatch | Non-faithful |
| **8** | `case-08-fabricated-numerical` | Fabricated lab cutoff or score ($H3$) | Numerical conflict | Non-faithful |
| **9** | `case-09-fabricated-temporal` | Invented calendar date ($H4$) | Temporal fabrication | Non-faithful |
| **10** | `case-10-unsupported-certainty`| Overconfident reasoning on hedged fact ($H10$) | Certainty inflation | Non-faithful |
| **11** | `case-11-negated-fact-handled` | Explicit negation correctly yields INELIGIBLE/FAIL | Negation preservation | **Faithful** |
| **12** | `case-12-not-mentioned-handled`| Silence correctly yields UNKNOWN (not negated) | Missingness preservation | **Faithful** |
| **13** | `case-13-compound-mixed-support`| Compound justification with mixed support | Partial hallucination | Non-faithful |
| **14** | `case-14-multiple-evidence` | Reasoning grounded in multiple facts and demographics | Multi-source support | **Faithful** |
| **15** | `case-15-valid-retrieval-prov` | RAG evidence with valid retrieval provenance | Dense retrieval citations | **Faithful** |
| **16** | `case-16-invalid-retrieval-prov` | RAG citation with mismatched retrieval method ($H7$) | Method mismatch | Non-faithful |
