# MedMatch Capstone — Phase 8: Reproducibility & Audit Specification

**Document Version:** `1.0.0`  
**Phase:** 8 — Grounding Evaluation & Faithfulness Auditing  
**Date:** September 2026  
**Status:** Canonical Reproducibility Specification  

---

## 1. Reproducibility Manifest Contract

To eliminate hidden state, non-deterministic drift, or unrecorded dependencies, every Phase 8 execution must emit or adhere to the canonical reproducibility manifest:

```json
{
  "manifest_version": "1.0.0",
  "software_commit_sha": "c528894",
  "phase": 8,
  "component_versions": {
    "grounding_schema_version": "1.0.0",
    "claim_extractor_version": "1.0.0",
    "grounding_validator_version": "1.0.0",
    "metrics_engine_version": "1.0.0",
    "fixture_version": "1.0.0-dev"
  },
  "random_seed_policy": {
    "fixed_seed": 42,
    "temperature": 0.0,
    "stochasticity_permitted": false
  },
  "ordering_invariants": {
    "claim_ordering": "Verbatim ascending ordinal occurrence in reasoning text",
    "citation_ordering": "Preserved ordinal sequence in evidence_citations array",
    "criterion_evaluation_order": "Ascending criterion ID alphanumeric sort"
  },
  "provenance_handling_conventions": {
    "unlocatable_character_offsets": -1,
    "retrieval_prefix_format": "{retrieval_method}:{source_reference}",
    "missing_fact_id_representation": null
  },
  "benchmark_availability_status": {
    "validated_research_benchmark_ingested": false,
    "current_dataset_layer": "Layer A (Synthetic Development Fixture)",
    "empirical_claims_permitted": false
  }
}
```

---

## 2. Deterministic Execution Guarantees

1. **Deterministic Proposition Segmentation:**  
   `DeterministicClaimExtractor` uses pure Python regular expressions without stochastic sampling or external model calls. Repeated executions on the identical reasoning string yield bitwise identical claim lists.
2. **Deterministic Support Classification:**  
   `GroundingValidator` uses rule-based matching against explicit evidence dictionaries. No neural classifier or LLM prompt is invoked during validation.
3. **Floating Point Rounding Protocol:**  
   All metrics ($\text{CSR}, \text{UCR}, \text{CR}, \text{CVR}, \text{EC}, \text{GS}, \text{HR}$) are rounded to exactly 4 decimal places via standard half-to-even rounding (`round(x, 4)`).
4. **Deterministic Tie-Breaking:**  
   Sorting of candidates, claims, and criteria strictly breaks ties using canonical alphanumeric identifiers (`trial_id`, `criterion_id`, `claim_id`).

---

## 3. Provenance & Offset Invariants

- **Offsets:** Under no circumstances are missing start or end character positions fabricated. When a fact or criterion cannot be located to exact character indices in the raw note, `start_char = -1` and `end_char = -1` are preserved.
- **Retrieval Prefixes:** Retrieval provenance in citations must strictly follow the format:
  `{retrieval_method}:{source_reference}` (e.g. `dense:trial:NCT001`, `hybrid_rrf:trial:NCT001`, `hybrid_reranked:trial:NCT001`). Any mismatched prefix is flagged as an invalid citation ($H7$).

---

## 4. Benchmark Guardrail Statement

In strict adherence to capstone research integrity, **Phase 8 does NOT report empirical benchmark figures** because the external research benchmark (TrialGPT/TREC CT) has not yet been ingested. All tests and demonstrations use the synthetic 16-case fixture (`data/fixtures/phase8/grounding_fixtures.json`).
