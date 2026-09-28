# MedMatch Capstone — Evaluation Methodology & Task Formalization

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Mathematical Task Formalization

Let the clinical trial matching space be defined over a patient population $\mathcal{P}$ and a clinical trial registry $\mathcal{T}$.

### 1.1 Patient Representation ($P$)
A patient $P \in \mathcal{P}$ is characterized by:
$$P = \langle N_P, D_P, E_P \rangle$$
Where:
- $N_P \in \Sigma^*$ is the unstructured clinical encounter narrative (progress notes, discharge summaries, pathology reports).
- $D_P = \langle \text{age}, \text{sex}, \text{stage}, \text{histology}, \text{ecog} \rangle$ represents structured demographic and clinical staging attributes.
- $E_P = \{e_{P,1}, e_{P,2}, \dots, e_{P,m}\}$ is the set of explicit clinical evidence assertions (e.g., laboratory measurements, genetic alterations, prior lines of treatment), where each $e_{P,j} = \langle \text{entity}, \text{value}, \text{unit}, \text{status}, \text{span}, \tau \rangle$ with text span offset $\text{span} \subset N_P$ and temporal timestamp $\tau$.

### 1.2 Clinical Trial Representation ($T$) and Criteria ($C$)
A clinical trial protocol $T \in \mathcal{T}$ is characterized by:
$$T = \langle \text{NCT\_ID}, \text{Title}, \text{Summary}, \text{Phase}, \text{Conditions}, C_T \rangle$$
Where the eligibility criteria set $C_T$ is partitioned into two disjoint subsets:
$$C_T = C_{inc} \cup C_{exc}, \quad C_{inc} \cap C_{exc} = \emptyset$$
- $C_{inc} = \{c_1^{inc}, c_2^{inc}, \dots, c_m^{inc}\}$: Inclusion criteria defining mandatory conditions for enrollment.
- $C_{exc} = \{c_1^{exc}, c_2^{exc}, \dots, c_n^{exc}\}$: Exclusion criteria defining disqualifying conditions that prohibit enrollment.

Each criterion $c_i \in C_T$ is an atomic clinical rule $c_i = \langle \text{id}, \text{type}, \text{domain}, \text{text\_span}, \phi_i \rangle$, where $\phi_i$ represents the underlying clinical logical constraint.

---

## 2. Pipeline Subtasks

The matching process is decomposed into two distinct stages: Candidate Retrieval and Eligibility Determination.

### 2.1 Stage 1: Retrieval Task ($R_k$)
Given a patient record $P$ and trial registry $\mathcal{T}$, the retrieval function $R_k$ maps $P$ to an ordered candidate subset of top-$k$ relevant trials:
$$R_k(P, \mathcal{T}) = (T_{(1)}, T_{(2)}, \dots, T_{(k)}), \quad T_{(j)} \in \mathcal{T}, \quad k \ll |\mathcal{T}|$$
At the criterion-level, retrieval identifies the top-$k$ criteria across trials most pertinent to patient assertions:
$$R_k^{crit}(P, \bigcup_{T \in \mathcal{T}} C_T) = (c_{(1)}, c_{(2)}, \dots, c_{(k)})$$

### 2.2 Stage 2: Criterion-Level Evaluation Function ($g$)
For a candidate trial $T$ with criteria $C_T$, the criterion evaluation function $g$ evaluates patient $P$ against each individual criterion $c_i \in C_T$:
$$g(P, c_i) \to \langle y_i, \text{span}_P(c_i), \text{rationale}_i, \sigma_i \rangle$$
Where:
- $y_i \in \{\text{PASS}, \text{FAIL}, \text{UNKNOWN}\}$ is the tri-state criterion decision.
- $\text{span}_P(c_i) \subseteq N_P$ is the exact textual evidence span cited from the patient note (or $\emptyset$ if unmentioned).
- $\text{rationale}_i$ is the clinical justification.
- $\sigma_i \in [0, 1]$ is the model confidence score for the criterion evaluation.

### 2.3 Semantic Meaning of Criterion-Level Labels ($y_i$)

| Criterion Type | Evaluation ($y_i$) | Clinical Meaning | Example |
|---|---|---|---|
| **Inclusion** ($c \in C_{inc}$) | **PASS** | Patient explicitly satisfies the mandatory inclusion condition. | "Age $\ge 18$" and patient is 54. |
| **Inclusion** ($c \in C_{inc}$) | **FAIL** | Patient explicitly violates the mandatory inclusion condition. | "ECOG $\le 1$" and patient is ECOG 3. |
| **Inclusion** ($c \in C_{inc}$) | **UNKNOWN** | Patient record lacks sufficient data to confirm inclusion. | "Documented EGFR T790M mutation" but NGS pending. |
| **Exclusion** ($c \in C_{exc}$) | **PASS** | Patient does **not** have the disqualifying condition (cleared). | "No active brain metastases" and MRI negative. |
| **Exclusion** ($c \in C_{exc}$) | **FAIL** | Patient **has** the disqualifying condition (disqualified). | "Prior treatment with anti-PD-1" and patient received Nivolumab. |
| **Exclusion** ($c \in C_{exc}$) | **UNKNOWN** | Patient record lacks sufficient data to rule out exclusion. | "No history of autoimmune hepatitis" but liver history omitted. |

---

## 3. Formal Clinical Aggregation Logic ($\Lambda$)

The trial-level eligibility decision $Y \in \{\text{ELIGIBLE}, \text{INELIGIBLE}, \text{NEEDS\_REVIEW}\}$ is computed by applying a deterministic clinical aggregation operator $\Lambda$ over the multiset of criterion-level decisions:
$$Y = \Lambda(\{y_i\}_{i=1}^{|C_T|})$$

### 3.1 Mathematical Definition of Aggregation Rules

$$\Lambda(\{y_i\}) = \begin{cases} 
\text{INELIGIBLE} & \text{if } \exists c_i \in C_T \text{ s.t. } y_i = \text{FAIL} \\
\text{ELIGIBLE} & \text{if } \forall c_i \in C_T, y_i = \text{PASS} \\
\text{NEEDS\_REVIEW} & \text{if } (\forall c_i \in C_T, y_i \neq \text{FAIL}) \land (\exists c_j \in C_T \text{ s.t. } y_j = \text{UNKNOWN})
\end{cases}$$

### 3.2 Clinical Rationale for Aggregation
1. **Rule of Absolute Disqualification ($\text{INELIGIBLE}$):**  
   In clinical trial protocols, failing a single inclusion criterion or triggering a single exclusion criterion immediately disqualifies a patient from protocol enrollment, regardless of compliance on all other 30+ criteria. In our formalization, $y_i = \text{FAIL}$ on *any* criterion (whether failing an inclusion or hitting an exclusion) dictates $Y = \text{INELIGIBLE}$.
2. **Rule of Complete Compliance ($\text{ELIGIBLE}$):**  
   A patient can only be classified as definitely eligible if *every* protocol inclusion criterion is verified as present and *every* exclusion criterion is confirmed absent based on positive documented evidence.
3. **Rule of Conservative Uncertainty ($\text{NEEDS\_REVIEW}$):**  
   If an oncology patient violates no known criteria, but critical protocol requirements (e.g., organ function labs or molecular profiling) are absent from the encounter note, classifying the patient as `ELIGIBLE` is medically hazardous (false-positive enrollment risk), while classifying them as `INELIGIBLE` prematurely rejects a potentially life-saving trial. The system must assign `NEEDS_REVIEW` to prompt research staff to order the missing tests.

---

## 4. Systems Under Evaluation

The evaluation framework specifies three reference architectures for controlled comparative study:

### 4.1 System A: Baseline LLM-Only (Non-Retrieval)
- **Input:** Raw patient note $N_P$ concatenated with unindexed trial descriptions or tested zero-shot.
- **Mechanism:** Direct prompt querying LLM (e.g., Gemini 2.5 Flash) without database vector search or hybrid retrieval.
- **Purpose:** Establishes the performance floor and measures the extent to which LLMs rely on parametric knowledge or ungrounded heuristics.

### 4.2 System B: Current MedMatch Baseline (Phase 0 Implementation)
- **Input:** Raw clinical note string `patient_note: str`.
- **Retrieval:** Sequential pgvector cosine distance over 384-dimensional `sentence-transformers/all-MiniLM-L6-v2` trial summary embeddings (`top_k = 5`).
- **Reasoning:** Monolithic 966-line prompt (`app/prompts/trial_matching_prompt.py`) feeding raw note and retrieved trial blocks directly into Gemini 2.5 Flash (`temperature = 0.0`).
- **Output:** Pydantic `EligibilityEvaluationResponse` returned in-memory; no persistence; no character-level evidence verification.

### 4.3 Future System C: Modular Evidence-Grounded RAG (Target Architecture)
- **Input:** Structured patient profile $D_P, E_P$ combined with narrative $N_P$.
- **Retrieval:** Two-stage hybrid search (dense embeddings + sparse BM25) with reciprocal rank fusion (RRF) and cross-encoder reranking.
- **Decomposition:** Atomic criterion decomposition of trial protocols.
- **Reasoning:** Independent criterion-level verification ($g(P, c_i)$) with character-span extraction.
- **Aggregation:** Deterministic clinical aggregation rule $\Lambda(\{y_i\})$.
- **Status:** **Design specification only.** Implementation deferred to future phases.

---

## 5. End-to-End Evaluation Workflow Diagram

```text
+-----------------------------------------------------------------------------------+
|                            EVALUATION BENCHMARK PIPELINE                          |
+-----------------------------------------------------------------------------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
         [Patient Clinical Record P]             [Trial Protocol Corpus T]
         - Unstructured Narrative N_P            - Inclusion Criteria C_inc
         - Structured Attributes D_P             - Exclusion Criteria C_exc
                      |                                       |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |         STAGE 1: RETRIEVAL            |
                      |   R_k(P, T) -> Candidate Trials       |
                      +---------------------------------------+
                                          |
                        Evaluated via: Recall@K, MRR, nDCG@K
                                          |
                                          v
                      +---------------------------------------+
                      |    STAGE 2: CRITERION EVALUATION      |
                      |   g(P, c_i) -> {PASS, FAIL, UNKNOWN}  |
                      |   Evidence Spans: span_P, span_C      |
                      +---------------------------------------+
                                          |
                        Evaluated via: Criterion Macro-F1,
                                       Evidence Coverage,
                                       Unsupported Claim Rate
                                          |
                                          v
                      +---------------------------------------+
                      |    STAGE 3: CLINICAL AGGREGATION      |
                      |    Y = Lambda({y_i})                  |
                      |    Y in {ELIGIBLE, INELIGIBLE,        |
                      |          NEEDS_REVIEW}                |
                      +---------------------------------------+
                                          |
                        Evaluated via: Trial-Level Macro-F1,
                                       Expected Calibration Error,
                                       12-Factor Error Taxonomy
```
