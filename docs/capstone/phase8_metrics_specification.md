# MedMatch Capstone — Phase 8: Grounding & Faithfulness Metrics Specification

**Document Version:** `1.0.0`  
**Phase:** 8 — Grounding Evaluation & Faithfulness Auditing  
**Date:** September 2026  
**Status:** Canonical Metrics Specification  
**Component:** `scripts/grounding_metrics.py`  

---

## 1. Overview & Evaluation Principles

To move beyond qualitative inspections of LLM reasoning, the **Phase 8 Metrics Specification** defines pure, deterministic mathematical functions measuring claim support, evidence coverage, citation validity, and hallucination rates.

In strict compliance with capstone research guardrails:
- All denominators are formally specified with defined edge-case handling.
- Metrics are bounded in $[0.0, 1.0]$.
- **No empirical scores or benchmark rankings are reported in this specification** until a validated research benchmark is ingested.

---

## 2. Primary Grounding Metrics

Let $C = \{c_1, c_2, \dots, c_m\}$ denote the set of atomic claims extracted from a clinical reasoning text.  
Let $S, P, U, X, I \subseteq C$ partition $C$ into sets of claims that are:
- $S$: `SUPPORTED`
- $P$: `PARTIALLY_SUPPORTED`
- $U$: `UNSUPPORTED`
- $X$: `CONTRADICTED`
- $I$: `INSUFFICIENT_EVIDENCE`

Let $K = |C| = |S| + |P| + |U| + |X| + |I|$.

---

### 2.1 Claim Support Rate (CSR)
Measures the proportion of propositions in the reasoning that are fully entailed by verified evidence:

$$\text{CSR} = \begin{cases} 
1.0 & \text{if } K = 0 \\
\frac{|S|}{K} & \text{if } K > 0 
\end{cases}$$

- **Relaxed Variant ($\text{CSR}_{\text{relaxed}}$):**  
  Awards half-credit for partially supported claims:
  $$\text{CSR}_{\text{relaxed}} = \frac{|S| + 0.5 \cdot |P|}{K}$$
- **Range:** $[0.0, 1.0]$. Higher is better.

---

### 2.2 Unsupported Claim Rate (UCR)
Measures the frequency of undocumented assertions or speculative inferences:

$$\text{UCR} = \begin{cases} 
0.0 & \text{if } K = 0 \\
\frac{|U|}{K} & \text{if } K > 0 
\end{cases}$$

- **Range:** $[0.0, 1.0]$. Lower is better.

---

### 2.3 Contradiction Rate (CR)
Measures the frequency of propositions that directly conflict with verified source evidence:

$$\text{CR} = \begin{cases} 
0.0 & \text{if } K = 0 \\
\frac{|X|}{K} & \text{if } K > 0 
\end{cases}$$

- **Range:** $[0.0, 1.0]$. Lower is better. Any non-zero $\text{CR}$ indicates an overt failure of factual alignment.

---

### 2.4 Citation Validity Rate (CVR)
Let $\Gamma = \{\gamma_1, \gamma_2, \dots, \gamma_v\}$ denote the set of citations attached to the reasoning.  
Let $\Gamma_{\text{valid}} \subseteq \Gamma$ denote citations that satisfy all existence, span-matching, and retrieval-provenance checks.

$$\text{CVR} = \begin{cases} 
1.0 & \text{if } |\Gamma| = 0 \\
\frac{|\Gamma_{\text{valid}}|}{|\Gamma|} & \text{if } |\Gamma| > 0 
\end{cases}$$

- **Range:** $[0.0, 1.0]$. Higher is better. A value $< 1.0$ indicates corrupted provenance, offset drift, or spurious fact citations.

---

### 2.5 Evidence Coverage (EC)
Let $C_{\text{fact}} \subseteq C$ denote factual propositions that require empirical evidence (patient conditions, numerical values, temporal milestones), excluding self-evident logical connectors or meta-conclusions:

$$\text{EC} = \begin{cases} 
1.0 & \text{if } |C_{\text{fact}}| = 0 \\
\frac{|S \cap C_{\text{fact}}|}{|C_{\text{fact}}|} & \text{if } |C_{\text{fact}}| > 0 
\end{cases}$$

- **Range:** $[0.0, 1.0]$. Higher is better.

---

### 2.6 Hallucination Rate (HR)
Measures the total fraction of claims that constitute either ungrounded assertions ($U$) or overt contradictions ($X$):

$$\text{HR} = \begin{cases} 
0.0 & \text{if } K = 0 \\
\frac{|U| + |X|}{K} & \text{if } K > 0 
\end{cases}$$

- **Range:** $[0.0, 1.0]$. Lower is better.

---

### 2.7 Composite Grounding Score (GS)
A unified holistic score balancing positive support and citation validity while heavily penalizing factual contradictions:

$$\text{GS} = \max\left(0.0, \; w_1 \cdot \text{CSR} + w_2 \cdot \text{CVR} + w_3 \cdot \text{EC} - w_4 \cdot \text{CR}\right)$$

- **Standard Canonical Weights:**
  - $w_1 = 0.50$ (Claim support)
  - $w_2 = 0.25$ (Citation validity)
  - $w_3 = 0.25$ (Evidence coverage)
  - $w_4 = 1.00$ (Contradiction penalty)
- **Range:** $[0.0, 1.0]$. Higher is better. If $\text{CR} \ge 1.0$, $\text{GS}$ drops immediately to $0.0$.

---

## 3. Edge-Case & Denominator Policy

| Edge-Case Scenario | Denominator | Metric Value Assigned | Justification |
| :--- | :---: | :---: | :--- |
| **Empty Reasoning ($K = 0$)** | $0$ | $\text{CSR}=1.0, \text{UCR}=0.0, \text{CR}=0.0, \text{HR}=0.0$ | Vacuously true; no false claims made. |
| **No Citations Attached ($|\Gamma| = 0$)** | $0$ | $\text{CVR}=1.0$ | No citations exist to fail audit. |
| **Reasoning Expresses Uncertainty ($I = C$)** | $K$ | $\text{CSR}=0.0, \text{UCR}=0.0, \text{CR}=0.0, \text{HR}=0.0$ | Epistemic abstention; no ungrounded assertion. |
| **Contradicted Claim Present ($|X| > 0$)** | $K$ | $\text{CR} > 0.0 \implies \text{is\_faithful} = \text{False}$ | Immediate forfeiture of faithfulness. |
| **Partially Supported Claim ($P$)** | $K$ | Counted in $K$, excluded from strict $S$ | Prevents false overconfidence. |

---

## 4. Benchmark Guardrail Statement

The mathematical formulas above are implemented in [`scripts/grounding_metrics.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/grounding_metrics.py). In strict compliance with capstone guidelines, **no empirical performance claims, macro-averages on un-ingested clinical datasets, or comparative RAG-vs-NON-RAG percentages are asserted** in this document.
