# Phase 9: Uncertainty & Human Review Metrics Specification

## 1. Overview

This document specifies the deterministic mathematical formulas, units of analysis, denominator constraints, and boundary edge cases for Phase 9 uncertainty and human review metrics.

These metrics evaluate the transparency, safety, and routing fidelity of the MedMatch decision support layer.

---

## 2. Mathematical Formulations

### 2.1 Uncertainty Rate ($UR$)
Measures the proportion of evaluated criteria impaired by unresolved uncertainty.
$$UR = \frac{N_{\text{criteria with unresolved uncertainty}}}{N_{\text{total criteria evaluated}}}$$
- **Numerator**: Distinct criterion references with `status != RESOLVED`.
- **Denominator**: Total eligibility criteria evaluated across all candidate trials.
- **Zero-denominator rule**: If $N_{\text{total criteria}} = 0$, $UR = 0.0$.

### 2.2 Missing Information Rate ($MIR$)
Measures frequency of criteria blocked by omitted patient facts (`NOT_MENTIONED`).
$$MIR = \frac{N_{\text{uncertainties with type MISSING\_PATIENT\_FACT}}}{N_{\text{total criteria evaluated}}}$$

### 2.3 Conflict Rate ($CR$)
Measures frequency of criteria affected by contradictory clinical evidence.
$$CR = \frac{N_{\text{uncertainties with type CONFLICTING}}}{N_{\text{total criteria evaluated}}}$$

### 2.4 Ambiguity Rate ($AR$)
Measures frequency of criteria affected by temporal or numerical ambiguity.
$$AR = \frac{N_{\text{uncertainties with type TEMPORAL\_AMBIGUITY or NUMERICAL\_AMBIGUITY}}}{N_{\text{total criteria evaluated}}}$$

### 2.5 Insufficient Evidence Rate ($IER$)
Measures frequency of criteria where evidence retrieval or extraction was insufficient.
$$IER = \frac{N_{\text{uncertainties with status INSUFFICIENT\_EVIDENCE}}}{N_{\text{total criteria evaluated}}}$$

### 2.6 Review Routing Rate ($RRR$)
Proportion of cases intercepted for human clinical review rather than decided autonomously.
$$RRR = \frac{N_{\text{cases routed to PENDING\_REVIEW, IN\_REVIEW, RESOLVED, or ESCALATED}}}{N_{\text{total cases evaluated}}}$$

### 2.7 Review Resolution Rate ($ResR$)
Proportion of queued human review cases that reach a formal clinical resolution.
$$ResR = \frac{N_{\text{cases with status RESOLVED}}}{N_{\text{total cases routed to review}}}$$
- **Zero-denominator rule**: If $N_{\text{routed}} = 0$, $ResR = 1.0$.

### 2.8 Escalation Rate ($ER$)
Proportion of cases requiring escalation to multidisciplinary review or principal investigators.
$$ER = \frac{N_{\text{cases with status ESCALATED}}}{N_{\text{total cases evaluated}}}$$

### 2.9 Appropriate Review Routing Rate ($ARRR$)
Measures agreement between deterministic routing output and ground-truth policy routing expectation.
$$ARRR = \frac{N_{\text{cases with correctly assigned routing status}}}{N_{\text{evaluable cases with expected routing}}}$$

### 2.10 Unsupported Automatic Decision Rate ($UADR$)
The rate at which the system permits an autonomous `ELIGIBLE` or `INELIGIBLE` verdict despite the presence of unresolved high or critical clinical uncertainties.
$$UADR = \frac{N_{\text{cases decided autonomously with unresolved HIGH/CRITICAL uncertainty}}}{N_{\text{total cases evaluated}}}$$
- **Critical Safety Guardrail**: A valid implementation **must strictly maintain** $UADR = 0.0$.

### 2.11 Evidence-Backed Resolution Rate ($EBRR$)
Proportion of resolved human reviews that cite at least one explicit evidence reference.
$$EBRR = \frac{N_{\text{resolved reviews with len(evidence\_references) } \ge 1}}{N_{\text{total resolved reviews}}}$$
- **Zero-denominator rule**: If $N_{\text{resolved}} = 0$, $EBRR = 1.0$.

---

## 3. Benchmark Disclaimer
All metrics defined herein are for development testing and architectural verification. In accordance with research roadmap guardrails, no empirical clinical performance or statistical superiority is claimed in Phase 9.
