# MedMatch Capstone — Atomic Criterion Representation Specification

> **Status:** Phase 3 Research Specification  
> **Phase:** 3 — Clinical Trial Document Intelligence  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Document Intelligence & Extraction Engine

---

## 1. Definition and Philosophy of Atomicity

In clinical trial protocols, eligibility criteria are frequently drafted as dense, compound sentences spanning multiple medical domains. For example:
> *"Patients must be aged $\ge 18$ years, have an ECOG performance status of 0 or 1, and demonstrate adequate bone marrow reserve defined as ANC $\ge 1.5 \times 10^9/\text{L}$ and platelets $\ge 100 \times 10^9/\text{L}$."*

In the baseline MedMatch pipeline (Phase 0), this sentence is preserved as a **single monolithic string**. If a patient has an ANC of $1.2 \times 10^9/\text{L}$, the entire compound criterion is evaluated as `FAIL` or `INELIGIBLE` without explicitly recording whether the patient met the age, ECOG, or platelet requirements.

### 1.1 Atomic Criterion Definition
In MedMatch, an **atomic criterion** is formally defined as:
> **A single, semantically indivisible clinical constraint evaluating a single clinical variable, laboratory threshold, historical event, or biomarker status that can be verified independently against patient medical records without altering the truth value of other protocol rules.**

When decomposed, the example above produces four independent atomic criteria:
1. `NCT02484404_INC_01A`: Concept: `age`, Operator: `>=`, Value: `18`, Unit: `years`
2. `NCT02484404_INC_01B`: Concept: `ecog_performance_status`, Operator: `<=`, Value: `1`
3. `NCT02484404_INC_01C`: Concept: `absolute_neutrophil_count`, Operator: `>=`, Value: `1.5`, Unit: `x 10^9/L`
4. `NCT02484404_INC_01D`: Concept: `platelet_count`, Operator: `>=`, Value: `100.0`, Unit: `x 10^9/L`

---

## 2. Structured Data Model (`AtomicConstraint`)

Each atomic criterion encapsulates one or more strongly typed constraints:

```text
+---------------------------------------------------------------------------------+
|                            ATOMIC CONSTRAINT STRUCTURE                          |
+----------------------+----------------------+-----------------------------------+
| Field                | Type                 | Description / Examples            |
+----------------------+----------------------+-----------------------------------+
| concept              | str                  | Normalized entity: "platelet_count"|
| operator             | CriterionOperator    | >=, <=, ==, !=, in, between, exists|
| value                | Union[num, str, list]| Threshold: 100.0, "Exon 19 del"   |
| unit                 | Optional[str]        | "x 10^9/L", "mg/dL", "days"       |
| temporal_window_days | Optional[int]        | Washout period: 28 days           |
| temporal_anchor      | Optional[str]        | "prior_to_day_1", "prior_to_screen"|
| is_negated           | bool                 | True for negated clinical rules   |
+----------------------+----------------------+-----------------------------------+
```

---

## 3. When Automatic Decomposition MUST NOT Occur (Non-Decomposable Rules)

While decomposing independent conjunctions ("A and B and C") improves matching resolution, **naive syntactic splitting of dependent clinical clauses destroys protocol logic and introduces hazardous matching errors**.

The MedMatch document intelligence engine enforces an explicit `can_decompose: bool` flag with mandatory `decomposition_block_reason: str`. Automatic decomposition is strictly prohibited in the following five clinical categories:

### Case 1: Complex Dependent Exception Clauses
- **Protocol Text:** *"Active autoimmune disease requiring systemic treatment, EXCEPT vitiligo, resolved childhood asthma, or type 1 diabetes on stable insulin."*
- **Why Decomposition Fails:** Splitting at the comma or "except" creates an orphan rule ("vitiligo, resolved childhood asthma") that appears to be an inclusion requirement or an unconditional exclusion. The exception modifies the primary condition conditionally.
- **Representation:** Preserved as single criterion with `can_decompose = False`, `compound_relation = "EXCEPTION"`.

### Case 2: Subjective Clinical Discretion
- **Protocol Text:** *"Any severe or uncontrolled medical condition that, in the opinion of the investigator, would compromise patient safety or protocol compliance."*
- **Why Decomposition Fails:** Contains no objective numerical threshold or discrete ontology term. It represents human clinical judgment and cannot be separated into atomic variables.
- **Representation:** Preserved with `criterion_type = "ambiguous"`, `can_decompose = False`.

### Case 3: Non-Separable Clinical Formulae & Alternative Ratio Cutoffs
- **Protocol Text:** *"Adequate renal function defined as serum creatinine $\le 1.5 \times \text{ULN}$ OR calculated creatinine clearance $\ge 50\text{ mL/min}$ by Cockcroft-Gault formula."*
- **Why Decomposition Fails:** This is a disjunctive equivalence ($A \lor B$). If split into two isolated rules, an evaluator requiring all inclusion rules to pass would falsely disqualify a patient who fails serum creatinine but passes Cockcroft-Gault clearance.
- **Representation:** Preserved as single compound criterion with `compound_relation = "OR"`.

### Case 4: Chronologically Interdependent Therapies
- **Protocol Text:** *"Prior taxane therapy permitted ONLY IF disease recurrence occurred $\ge 6$ months following completion of adjuvant therapy."*
- **Why Decomposition Fails:** The permission of therapy A is conditioned on the elapsed duration before event B. Splitting "prior taxane therapy" from "recurrence $\ge 6$ months" creates conflicting inclusion/exclusion assertions.
- **Representation:** Preserved with `can_decompose = False`, `compound_relation = "DEPENDENT_CLAUSE"`.

### Case 5: Multi-System Holistic Syndromes
- **Protocol Text:** *"Clinically significant cardiovascular disease within 6 months, including myocardial infarction, severe angina, or NYHA Class III/IV congestive heart failure."*
- **Why Decomposition Fails:** The examples are non-exhaustive instances of a broad clinical concept bounded by a shared 6-month temporal window.
- **Representation:** Preserved as domain `comorbidities` with `temporal_window_days = 180`.

---

## 4. Normalization and Operator Mapping

| Textual Pattern in Protocol | Normalized Operator | Value Representation | Example Clinical Context |
|---|:---:|---|---|
| "at least", "$\ge$", "minimum of", "greater than or equal to" | `>=` | Float or Integer | `ANC >= 1.5 x 10^9/L` |
| "no more than", "$\le$", "maximum of", "less than or equal to" | `<=` | Float or Integer | `ECOG <= 1` |
| "strictly greater than", ">" | `>` | Float or Integer | `LVEF > 50%` |
| "strictly less than", "<" | `<` | Float or Integer | `Total Bilirubin < 1.5 x ULN` |
| "documented", "confirmed", "positive for" | `==` or `exists` | String / Boolean | `EGFR == "Exon 19 del"` |
| "no history of", "absence of", "negative for" | `not_exists` or `!=` | String / Boolean | `Brain_Metastases == False` |
| "within X days", "completed $\ge$ X days prior" | `>=` with temporal anchor | Integer (days) | `Washout >= 28 days` |
| "between X and Y" | `between` | `[X, Y]` list | `Age between [18, 75]` |
