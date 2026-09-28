# Phase 9: Evidence Conflict Representation & Resolution Policy

## 1. Principles of Clinical Conflict Handling

In clinical trial matching, contradictory data is common across EHR records:
- Differing laboratory values over time.
- Discordant pathology reports versus clinical notes.
- Patient self-reports contradicting physician documentation.
- Positive versus negated assertions across encounters.

**The Golden Rule of MedMatch**:
> An automated system must NEVER arbitrarily select one conflicting data point over another to force an eligibility decision. If evidence is discordant and cannot be deterministically resolved by established temporal recency rules, the system must explicitly represent the conflict and defer the decision to human review.

---

## 2. Taxonomy of Clinical Conflicts

| Conflict Class | Description | Example | Default Resolution Path |
|:---|:---|:---|:---|
| **C1. Temporal Update** | Sequential measurements of a dynamic biomarker | HbA1c 8.2% (90 days ago) vs. 7.1% (14 days ago) | **Deterministically Resolvable** by recency rule if within valid protocol window |
| **C2. Inter-Document Discordance** | Discrepant findings in documents from same encounter or interval | Pathology reports "Invasive Ductal Carcinoma" while discharge summary notes "Lobular" | **Unresolvable automatically**; routes to `PENDING_REVIEW` |
| **C3. Assertion / Polarity Conflict** | One record affirms condition while another negates it | Note states "severe penicillin anaphylaxis"; intake notes "no drug allergies" | **Critical Safety Conflict**; routes to `ESCALATED` |
| **C4. Source Credibility Discordance** | Patient self-report conflicts with certified lab assay | Patient reports "normal kidney function" while serum creatinine is 2.8 mg/dL | **Prioritize certified laboratory** for physiological metrics, but flag self-report for review |
| **C5. Milestone Date Mismatch** | Discrepant dates for an anchor event | Note 1: "Resection Jan 2024"; Note 2: "Resection Nov 2023" | **Unresolvable automatically**; routes to `PENDING_REVIEW` |

---

## 3. Deterministic Resolution Policies

### 3.1 Temporal Recency Rule
A temporal conflict between measurement $M_{\text{old}}$ (timestamp $T_{\text{old}}$) and $M_{\text{new}}$ (timestamp $T_{\text{new}}$) may be deterministically resolved *without* human intervention **if and only if** all of the following conditions hold:
1. Both timestamps are valid absolute ISO dates.
2. $T_{\text{new}} > T_{\text{old}}$ with a non-zero interval.
3. The biomarker is clinically dynamic (e.g. serum creatinine, HbA1c, ANC, platelets, blood pressure).
4. $T_{\text{new}}$ falls strictly within the trial's mandatory screening window (e.g. within 28 days of screening).
5. There are no competing measurements on date $T_{\text{new}}$.

If all conditions hold, $M_{\text{new}}$ supersedes $M_{\text{old}}$, the status is marked `RESOLVED`, and an audit note documents the temporal supersession.

### 3.2 Unresolved Conflicts
If any of the above conditions fail:
- Status remains `CONFLICTING`.
- An `UncertaintyRecord` is generated with `conflict_details` containing both items.
- The case is routed to `PENDING_REVIEW` or `ESCALATED`.
- Automated `ELIGIBLE` is strictly blocked.
