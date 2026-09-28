# MedMatch Capstone — Metrics Specification

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Overview of Metric Hierarchy

Evaluation in MedMatch operates across four complementary dimensions:
1. **Retrieval Metrics:** Did the system surface the correct trials and protocol criteria?
2. **Criterion-Level Classification Metrics:** Did the system evaluate individual medical constraints correctly?
3. **Trial-Level Classification Metrics:** Was the overall eligibility determination accurate and calibrated?
4. **Grounding & Provenance Metrics:** Are decisions backed by verbatim, non-hallucinated patient evidence?

```text
+---------------------------------------------------------------------------------+
|                               METRIC TAXONOMY                                   |
+---------------------------------------------------------------------------------+
| Dimension         | Key Metrics                                                |
|-------------------+-------------------------------------------------------------|
| Retrieval         | Recall@{1,3,5,10,20}, Precision@K, MRR, nDCG@{5,10}         |
| Criterion-Level   | Criterion Accuracy, Macro-F1, Per-class (PASS/FAIL/UNKNOWN) |
| Trial-Level       | 3-Class Macro-F1, Binary F1, Confusion Matrix, ECE          |
| Grounding         | Evidence Coverage, Grounded Decision Rate, Unsupported Rate |
| Uncertainty       | Selective Risk-Coverage AUC, Needs-Review Precision/Recall  |
+---------------------------------------------------------------------------------+
```

---

## 2. Stage 1: Retrieval Evaluation Metrics

Let $Q$ be the set of evaluation queries (patient profiles), and for each query $q \in Q$, let $\mathcal{T}_{rel}(q)$ be the ground-truth set of relevant trials (or criteria), and $\mathcal{R}_K(q) = (r_1, r_2, \dots, r_K)$ be the top-$K$ ranked items returned by the retrieval system.

### 2.1 Definition of Relevance
- **Binary Relevance (Recall@K / Precision@K):** A trial $T$ is considered *relevant* if the patient has a clinically verified ground-truth annotation for $T$ (i.e., $T$ addresses the patient's histological condition and stage, regardless of whether the patient is ultimately eligible or ineligible).
- **Graded Relevance (nDCG@K):**
  - $\text{rel} = 2$: Eligible trial ($\text{ELIGIBLE}$).
  - $\text{rel} = 1$: Relevant disease/stage trial, but patient is disqualified or incomplete ($\text{INELIGIBLE}$ or $\text{NEEDS\_REVIEW}$).
  - $\text{rel} = 0$: Mismatched disease condition, inappropriate phase, or irrelevant trial.

### 2.2 Recall@K ($K \in \{1, 3, 5, 10, 20\}$)
$$\text{Recall@}K(q) = \frac{|\mathcal{T}_{rel}(q) \cap \mathcal{R}_K(q)|}{|\mathcal{T}_{rel}(q)|}, \quad \text{Recall@}K = \frac{1}{|Q|} \sum_{q \in Q} \text{Recall@}K(q)$$
Measures whether the retrieval pipeline surfaces relevant protocol options within the top $K$ candidate window.

### 2.3 Precision@K
$$\text{Precision@}K(q) = \frac{|\mathcal{T}_{rel}(q) \cap \mathcal{R}_K(q)|}{K}, \quad \text{Precision@}K = \frac{1}{|Q|} \sum_{q \in Q} \text{Precision@}K(q)$$

### 2.4 Mean Reciprocal Rank (MRR)
$$\text{MRR} = \frac{1}{|Q|} \sum_{q \in Q} \frac{1}{\text{rank}_1(q)}$$
Where $\text{rank}_1(q)$ is the rank position of the *first* relevant trial returned for query $q$ (or $\infty$ if no relevant trial is retrieved in top $K$).

### 2.5 Normalized Discounted Cumulative Gain (nDCG@K)
$$\text{DCG@}K(q) = \sum_{i=1}^K \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}, \quad \text{nDCG@}K(q) = \frac{\text{DCG@}K(q)}{\text{IDCG@}K(q)}$$
Where $\text{IDCG@}K(q)$ is the ideal DCG obtained by sorting items by true relevance in descending order.

---

## 3. Stage 2: Criterion-Level Metrics

Criterion-level metrics evaluate the atomic decision function $g(P, c_i) \to y_i \in \{\text{PASS}, \text{FAIL}, \text{UNKNOWN}\}$.

### 3.1 Criterion Accuracy
$$\text{Accuracy}_{\text{crit}} = \frac{\sum_{i=1}^M \mathbb{I}(\hat{y}_i = y_i^*)}{M}$$
Where $M$ is the total number of evaluated patient-criterion pairs across the benchmark corpus.

### 3.2 Criterion Macro-$F_1$ and Per-Class Scores
$$\text{Macro-}F_{1,\text{crit}} = \frac{F_{1,\text{PASS}} + F_{1,\text{FAIL}} + F_{1,\text{UNKNOWN}}}{3}$$
For each class $c \in \{\text{PASS}, \text{FAIL}, \text{UNKNOWN}\}$:
$$\text{Precision}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}, \quad \text{Recall}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}, \quad F_{1,c} = \frac{2 \cdot \text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

### 3.3 Error Attribution Breakdown
Criterion-level evaluation enables precise pinpointing of where system failure occurs:
$$\text{Total Errors} = E_{\text{retrieval}} + E_{\text{parsing}} + E_{\text{interpretation}} + E_{\text{evidence}} + E_{\text{aggregation}}$$

---

## 4. Stage 3: Trial-Level Eligibility Classification Metrics

Evaluates final protocol enrollment determinations $\hat{Y} \in \{\text{ELIGIBLE}, \text{INELIGIBLE}, \text{NEEDS\_REVIEW}\}$.

### 4.1 Primary 3-Class Evaluation
The primary benchmark metric is **Macro-Averaged $F_1$**:
$$\text{Macro-}F_1 = \frac{1}{3} \left( F_{1,\text{ELIGIBLE}} + F_{1,\text{INELIGIBLE}} + F_{1,\text{NEEDS\_REVIEW}} \right)$$

Full evaluation produces a $3 \times 3$ confusion matrix:
```text
                       Predicted
                   ELIG     INELIG   REVIEW
Actual  ELIG     [ TP_e     FN_e->i  FN_e->r ]
        INELIG   [ FP_i->e  TP_i     FN_i->r ]
        REVIEW   [ FP_r->e  FP_r->i  TP_r    ]
```

### 4.2 Clinical Safety Focus: False Positive Rate for Eligibility ($FPR_{\text{elig}}$)
In clinical trials, falsely classifying an ineligible patient as eligible ($\text{INELIGIBLE} \to \text{ELIGIBLE}$) risks toxic exposure or protocol violations:
$$FPR_{\text{elig}} = \frac{\text{Count}(\text{Actual} = \text{INELIGIBLE} \land \text{Predicted} = \text{ELIGIBLE})}{\text{Total Actual INELIGIBLE}}$$

### 4.3 Secondary Binary Projection Evaluation
For comparison with binary classification literature:
$$\text{Binary Decision}: \hat{Y}_{\text{bin}} = \begin{cases} 
\text{ELIGIBLE} & \text{if } \hat{Y} = \text{ELIGIBLE} \\ 
\text{NOT\_ELIGIBLE} & \text{if } \hat{Y} \in \{\text{INELIGIBLE}, \text{NEEDS\_REVIEW}\} 
\end{cases}$$
> **Clinical Rationale:** Patients flagged as `NEEDS_REVIEW` cannot be immediately enrolled without additional testing, making them practically `NOT_ELIGIBLE` at the time of screening.

---

## 5. Grounding, Provenance & Hallucination Metrics

These metrics quantify whether reasoning is anchored in real text spans rather than parametric hallucination.

### 5.1 Evidence Coverage ($EC$)
Percentage of evaluated criteria where the system identified and cited a specific supporting text span from the patient narrative:
$$EC = \frac{\sum_{i=1}^M \mathbb{I}(\text{has\_span}(\hat{e}_{P,i}))}{M} \times 100\%$$

### 5.2 Grounded Decision Rate ($GDR$)
The proportion of trial decisions for which 100% of non-unknown criteria are supported by verified substrings from the patient narrative:
$$GDR = \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}\left( \forall c_i \text{ with } \hat{y}_i \neq \text{UNKNOWN}, \, \hat{\text{span}}_i \subseteq N_P \right)$$

### 5.3 Unsupported Claim Rate ($UCR$)
The fraction of generated clinical claims that cannot be traced to any factual substring in the patient note:
$$UCR = \frac{\text{Count}(\text{Clinical claims asserted by LLM with no textual match})}{\text{Total clinical claims asserted by LLM}}$$

### 5.4 Evidence-Criterion Consistency ($ECC$)
Evaluated on a randomly sampled expert-audited subset ($n=100$ decisions):
$$ECC = \frac{\text{Count}(\text{Citing spans that clinically validate the criterion verdict})}{\text{Total cited spans audited}}$$

---

## 6. Uncertainty & Calibration Metrics

### 6.1 Expected Calibration Error (ECE)
Groups predictions into $B=10$ confidence bins $I_b = (\frac{b-1}{B}, \frac{b}{B}]$:
$$\text{ECE} = \sum_{b=1}^B \frac{|I_b|}{N} \left| \text{acc}(I_b) - \text{conf}(I_b) \right|$$
Where $\text{acc}(I_b)$ is the empirical accuracy of predictions in bin $b$, and $\text{conf}(I_b)$ is the mean predicted confidence.

### 6.2 Selective Classification Risk-Coverage Curve
Measures error rate as a function of the coverage threshold $\theta$ (retaining only decisions with confidence $\ge \theta$ and deferring others to human review as `NEEDS_REVIEW`). Computes Area Under the Risk-Coverage Curve (AURC).
