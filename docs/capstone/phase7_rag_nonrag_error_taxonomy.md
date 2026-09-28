# MedMatch Capstone — Phase 7: RAG vs. Non-RAG Comparative Error Taxonomy

**Document Version:** `1.0.0`  
**Phase:** 7 — RAG vs. Non-RAG Experimental Evaluation  
**Date:** September 2026  
**Status:** Canonical Error Taxonomy  

---

## 1. Scope & Diagnostic Architecture

This taxonomy defines and formalizes error classes that arise specifically during **comparative RAG vs. Non-RAG evaluations**. It maps every error to its root-cause architectural subsystem:
1. **Retrieval Subsystem** (Phase 5)
2. **Reasoning Subsystem** (Phase 6)
3. **Evidence Grounding Subsystem**
4. **Aggregation Subsystem**
5. **Data Quality / Source EHR Subsystem**

```text
+----------------------------------------------------------------------------------------------------+
|                                    COMPARATIVE ERROR ATTRIBUTION                                   |
+----------------------------------------------------------------------------------------------------+
                                                  |
         +----------------+---------------+-------+--------+----------------+
         |                |               |                |                |
         v                v               v                v                v
   [Retrieval]       [Reasoning]     [Grounding]     [Aggregation]    [Data Quality]
   - Omission        - Negation      - Hallucinated  - Invariant      - Incomplete EHR
   - False Positive  - Temporal        Citation        Violation      - Contradictory
   - Irrelevant      - Numerical     - Provenance    - Count            EHR records
     Passage         - Compound        Loss            Mismatch
```

---

## 2. Canonical Comparative Error Catalog

| Error ID | Error Name | Architectural Source | Condition Affected | Clinical Definition & Comparative Scenario |
| :---: | :--- | :---: | :---: | :--- |
| **ERR-P7-01** | **Retrieval Omission** | Retrieval | RAG Only | Relevant candidate trial or critical criterion was missed by Stage 1 search, causing downstream false negative. |
| **ERR-P7-02** | **Retrieval False Positive** | Retrieval | RAG Only | Irrelevant candidate trial retrieved due to superficial embedding overlap, forcing unnecessary evaluation. |
| **ERR-P7-03** | **Irrelevant Evidence Injection** | Retrieval / Context | RAG Only | Retrieved passage contains distracting or irrelevant protocol text that confuses the reasoning model. |
| **ERR-P7-04** | **Evidence Conflict** | Data Quality | Both | Patient record contains contradictory statements (e.g. Note A: "diabetes", Note B: "no diabetes"). |
| **ERR-P7-05** | **Reasoning Error with Correct Evidence** | Reasoning | Both | Grounded evidence is completely provided and accurate, but model misclassifies criterion outcome. |
| **ERR-P7-06** | **Hallucinated Fact / Evidence** | Reasoning / LLM | Non-RAG (High), RAG (Low) | Model invents clinical findings, measurements, or dates not documented in patient chart. |
| **ERR-P7-07** | **Unsupported PASS** | Grounding | Both | Model emits `PASS` without citing a valid snippet or `fact_id`. Caught and demoted by validator. |
| **ERR-P7-08** | **Unsupported FAIL** | Grounding | Both | Model emits `FAIL` without citing supporting evidence of violation. Caught and demoted by validator. |
| **ERR-P7-09** | **UNKNOWN Inflation** | Reasoning | Non-RAG (High) | Baseline Non-RAG fails to resolve criteria that could easily be answered if retrieved protocol context was provided. |
| **ERR-P7-10** | **Criterion Misinterpretation** | Reasoning | Both | System misinterprets clinical nuance of criterion (e.g. confusing adjuvant vs neoadjuvant therapy). |
| **ERR-P7-11** | **Temporal Reasoning Error** | Reasoning | Both | Miscalculating durations or recency windows (e.g. treating surgery 60 days ago as "within 30 days"). |
| **ERR-P7-12** | **Numerical Threshold Error** | Reasoning | Both | Mathematical miscalculation across operators ($<, \le, >, \ge$) or boundary values. |
| **ERR-P7-13** | **Negation Inversion Error** | Reasoning | Both | Negated phrase parsed as affirmative (e.g. "no history of stroke" parsed as stroke present). |
| **ERR-P7-14** | **Compound Logic Error** | Reasoning | Both | Misinterpreting Boolean operators ($A \land B$ vs. $A \lor B$). |
| **ERR-P7-15** | **Aggregation Invariant Error** | Aggregation | Both | Trial status inconsistent with criterion counts (prevented by deterministic aggregator). |
| **ERR-P7-16** | **Schema Validation Failure** | Schema / Parser | Both | LLM output cannot be parsed into canonical Pydantic models. Triggers safe abstention. |
| **ERR-P7-17** | **Evidence Provenance Loss** | Grounding | Both | Evaluation cites a snippet but omits character offsets or foreign key links to patient profile. |

---

## 3. Comparative Diagnostics: Expected Error Shifts (E5 vs. E6)

| Metric / Error Behavior | E5: Non-RAG Baseline | E6: RAG-Grounded System | Root-Cause Explanation |
| :--- | :---: | :---: | :--- |
| **Hallucination Rate (`ERR-P7-06`)** | High (without grounding) | Low (constrained by evidence) | RAG conditions the generator on explicit retrieved evidence passages. |
| **UNKNOWN Inflation (`ERR-P7-09`)** | High | Low | Retrieval provides missing protocol definitions, resolving ambiguities. |
| **Retrieval Noise (`ERR-P7-02`, `03`)** | Zero (no retrieval) | Non-zero | E5 has no retrieval noise; RAG must handle distracting retrieved passages. |
| **Evidence Grounding Rate** | Lower | Near 100% | RAG pipeline natively extracts and cites retrieved text spans. |
| **Aggregation Errors (`ERR-P7-15`)** | Zero (shared code) | Zero (shared code) | Both use identical deterministic Phase 6 aggregation code. |
