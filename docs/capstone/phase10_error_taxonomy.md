# Phase 10: Explainability & Evidence Graph Error Taxonomy (X1–X14)

## 1. Overview

Phase 10 formalizes 14 distinct failure categories covering structural graph violations, provenance corruptions, explanation unfaithfulness, and audit omissions.

---

## 2. Taxonomic Error Matrix

| Error Code | Error Category | Invariant Violated | Operational Definition | Detection Mechanism |
|:---|:---|:---|:---|:---|
| **X1** | Missing Evidence Link | **G2** | A criterion evaluation is marked `PASS` or `FAIL` without an incoming `SUPPORTS` or `CONTRADICTS` edge. | Validator identifies status in `(PASS, FAIL)` with zero incoming evidence edges. |
| **X2** | Invalid Provenance | **G3** | Evidence fragment has inconsistent character offsets (`start_char > end_char`) or missing source document. | Validator checks offset boundary condition on all `NodeProvenance` records. |
| **X3** | Dangling Graph Reference | **G9** | An edge references a `source_id` or `target_id` that does not exist in `graph.nodes`. | Graph validator scans all edges against node index keys. |
| **X4** | Duplicate Node/Edge ID | **G11** | Multiple nodes or edges share the same identifier within a single EvidenceGraph instance. | Validator detects collision when indexing node/edge identifiers. |
| **X5** | Incorrect Criterion Linkage | **G1** | A `CRITERION_EVALUATION` is not linked to a `TRIAL_CRITERION` via `EVALUATED_BY`. | Validator inspects incoming evaluation edges on evaluation nodes. |
| **X6** | Incorrect Decision Linkage | **G4** | An `ELIGIBILITY_DECISION` lacks incoming `CONTRIBUTES_TO` edges from contributing criterion evaluations. | Validator checks incoming contribution edges on decision nodes. |
| **X7** | Lost Uncertainty Linkage | **G5** | An `UNCERTAINTY` node is orphaned without an incoming `HAS_UNCERTAINTY` edge from an evaluation or fact. | Validator verifies parent linkage on all uncertainty nodes. |
| **X8** | Lost Review Linkage | **G6, G7** | A `REVIEW` node lacks an incoming `TRIGGERS` edge, or a `REVIEW_RESOLUTION` lacks an incoming `RESOLVED_BY` edge. | Validator verifies review workflow edge connectivity. |
| **X9** | Unsupported Explanation Claim | Guardrail 9 | An explanation claim asserts a factual proposition whose referenced nodes do not exist in the graph. | Explanation validator checks every `claim.referenced_node_ids` against graph. |
| **X10** | Contradictory Evidence Omitted | Guardrail 4 | An evaluation has contradictory evidence in the graph, but the explanation fails to cite or surface it. | Validator compares graph `CONTRADICTS` edges against explanation references. |
| **X11** | Machine Decision Overwritten | **G8** | A human review resolution omits or mutates the `original_machine_output` audit snapshot. | Validator checks presence of immutable machine output dictionary in resolution. |
| **X12** | Explanation Alters Decision | Guardrail 5 | An explanation asserts a verdict that contradicts the graph target node's recorded status. | Validator verifies `explanation.decision_reference == target_node.status`. |
| **X13** | Fabricated Source Location | **G10** | Provenance records use arbitrary negative offsets $< -1$ or fake coordinates. | Validator flags negative offsets other than `-1`. |
| **X14** | Graph Serialization Corruption | **G12** | Serializing to JSON and deserializing fails or mutates the node/edge count or properties. | Validator executes round-trip test and compares reconstructed entity counts. |
