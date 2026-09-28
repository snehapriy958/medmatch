# Phase 10: Explainability & Evidence Graph Metrics Specification

## 1. Overview & Formal Notation

Phase 10 defines eight quantitative metrics evaluating graph integrity, provenance validity, and explanation faithfulness:

1. **Evidence Coverage (EC)**
2. **Decision Traceability Rate (DTR)**
3. **Criterion Traceability Rate (CTR)**
4. **Provenance Validity Rate (PVR)**
5. **Explanation Support Rate (ESR)**
6. **Unsupported Explanation Claim Rate (UECR)**
7. **Contradiction Disclosure Rate (CDR)**
8. **Graph Integrity Rate (GIR)**

---

## 2. Mathematical Definitions & Safeguards

### 2.1 Evidence Coverage (EC)
Fraction of evaluated criteria that are grounded in at least one verified evidence item (patient fact or source fragment).

$$\text{EC} = \frac{|\{e \in \mathcal{E}_{\text{crit}} \mid \text{deg}_{\text{in}}^{\text{SUPPORTS}}(e) + \text{deg}_{\text{in}}^{\text{CONTRADICTS}}(e) \ge 1\}|}{|\mathcal{E}_{\text{crit}}|}$$

- **Zero-denominator safeguard**: If $|\mathcal{E}_{\text{crit}}| = 0$, $\text{EC} = 1.0$.

### 2.2 Decision Traceability Rate (DTR)
Fraction of trial-level decisions connected by an unbroken path from all contributing criterion evaluations.

$$\text{DTR} = \frac{|\{d \in \mathcal{D}_{\text{trial}} \mid \text{deg}_{\text{in}}^{\text{CONTRIBUTES\_TO}}(d) \ge 1\}|}{|\mathcal{D}_{\text{trial}}|}$$

- **Zero-denominator safeguard**: If $|\mathcal{D}_{\text{trial}}| = 0$, $\text{DTR} = 1.0$.

### 2.3 Criterion Traceability Rate (CTR)
Fraction of criterion evaluations that trace back to a defined trial protocol criterion.

$$\text{CTR} = \frac{|\{e \in \mathcal{E}_{\text{crit}} \mid \text{deg}_{\text{in}}^{\text{EVALUATED\_BY}}(e) \ge 1\}|}{|\mathcal{E}_{\text{crit}}|}$$

- **Zero-denominator safeguard**: If $|\mathcal{E}_{\text{crit}}| = 0$, $\text{CTR} = 1.0$.

### 2.4 Provenance Validity Rate (PVR)
Fraction of evidence-bearing nodes possessing valid, non-fabricated provenance coordinates.

$$\text{PVR} = \frac{|\{v \in \mathcal{V}_{\text{evidence}} \mid \text{IsValidProvenance}(v)\}|}{|\mathcal{V}_{\text{evidence}}|}$$

- Valid provenance requires: `source_id` is present, offsets $\ge -1$, and $start \le end$ when offsets are locatable.
- **Zero-denominator safeguard**: If $|\mathcal{V}_{\text{evidence}}| = 0$, $\text{PVR} = 1.0$.

### 2.5 Explanation Support Rate (ESR)
Fraction of explanation claims whose cited entities strictly resolve within the EvidenceGraph.

$$\text{ESR} = \frac{|\{c \in \mathcal{C}_{\text{claims}} \mid \forall v \in \text{Refs}(c), v \in \mathcal{V}_{\text{graph}}\}|}{|\mathcal{C}_{\text{claims}}|}$$

- **Zero-denominator safeguard**: If $|\mathcal{C}_{\text{claims}}| = 0$, $\text{ESR} = 1.0$.

### 2.6 Unsupported Explanation Claim Rate (UECR)
Fraction of explanation claims lacking graph backing. Complement of ESR.

$$\text{UECR} = 1.0 - \text{ESR} = \frac{|\{c \in \mathcal{C}_{\text{claims}} \mid \exists v \in \text{Refs}(c), v \notin \mathcal{V}_{\text{graph}}\}|}{|\mathcal{C}_{\text{claims}}|}$$

- **Zero-denominator safeguard**: If $|\mathcal{C}_{\text{claims}}| = 0$, $\text{UECR} = 0.0$.

### 2.7 Contradiction Disclosure Rate (CDR)
Fraction of criterion evaluations containing graph contradictions that are surfaced in the explanation.

$$\text{CDR} = \frac{|\{e \in \mathcal{E}_{\text{contra}} \mid \text{DisclosedInExplanation}(e)\}|}{|\mathcal{E}_{\text{contra}}|}$$

- **Zero-denominator safeguard**: If $|\mathcal{E}_{\text{contra}}| = 0$, $\text{CDR} = 1.0$.

### 2.8 Graph Integrity Rate (GIR)
Fraction of EvidenceGraphs satisfying all twelve invariants G1–G12 without error.

$$\text{GIR} = \frac{|\{g \in \mathcal{G} \mid \text{ValidateGraph}(g).\text{is\_valid} = \text{True}\}|}{|\mathcal{G}|}$$

- **Zero-denominator safeguard**: If $|\mathcal{G}| = 0$, $\text{GIR} = 0.0$.
