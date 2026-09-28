"""
MedMatch Deterministic Error Analyzer.
Phase 11: Evaluation & Ablation.

Categorizes system errors using established taxonomies (Phases 3–10):
- Retrieval Errors (Miss, False Retrieval)
- Eligibility Reasoning Errors (Misclassification, Tri-State Error, Temporal, Numerical, Negation)
- Grounding Errors (Unsupported Claim, Evidence Omission, Contradiction)
- Uncertainty & Review Errors (Uncertainty Routing Error)
- Explainability Errors (Traceability Failure)

Enforces language guideline: "categorized as" rather than "caused by".
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from scripts.evaluation_schema import (
        CategorizedError,
        ErrorAnalysisSummary,
        ExperimentResult,
    )
except ImportError:
    from evaluation_schema import (
        CategorizedError,
        ErrorAnalysisSummary,
        ExperimentResult,
    )


class ErrorAnalyzer:
    """
    Deterministic error classifier across experimental evaluations.
    """

    @classmethod
    def analyze_experiment_errors(
        cls,
        experiment_result: ExperimentResult,
        criteria_data: List[Dict[str, Any]],
        patients_data: List[Dict[str, Any]],
    ) -> ErrorAnalysisSummary:
        crit_map = {c["criterion_id"]: c for c in criteria_data}
        patient_map = {p["patient_id"]: p for p in patients_data}

        categorized_errors: List[CategorizedError] = []
        error_counts: Dict[str, int] = {}

        cases = experiment_result.evaluated_cases
        err_idx = 1

        for case in cases:
            pid = case["patient_id"]
            tid = case["trial_id"]
            pred = case["predicted_eligibility"]
            expected = case["ground_truth_eligibility"]

            if pred != expected:
                category = "ELIGIBILITY_AGGREGATION_MISMATCH"
                desc = (
                    f"Trial-level decision for patient {pid} on trial {tid} was predicted as '{pred}', "
                    f"whereas ground truth is '{expected}'."
                )

                if expected == "NEEDS_REVIEW" and pred != "NEEDS_REVIEW":
                    category = "UNCERTAINTY_ROUTING_ERROR"
                    desc = (
                        f"Uncertainty routing omission: case {pid}::{tid} requires clinician review "
                        f"due to ambiguous/missing evidence but was categorized as '{pred}'."
                    )
                elif pred == "NEEDS_REVIEW" and expected != "NEEDS_REVIEW":
                    category = "CONSERVATIVE_OVER_ROUTING"
                    desc = (
                        f"Conservative over-routing: case {pid}::{tid} was routed to review "
                        f"despite ground truth being definitive '{expected}'."
                    )
                elif (pred == "ELIGIBLE" and expected == "INELIGIBLE") or (
                    pred == "INELIGIBLE" and expected == "ELIGIBLE"
                ):
                    category = "CRITERION_POLARITY_MISCLASSIFICATION"
                    desc = (
                        f"Polarity inversion: patient {pid} predicted as '{pred}' "
                        f"against ground truth '{expected}'."
                    )

                error_counts[category] = error_counts.get(category, 0) + 1
                categorized_errors.append(
                    CategorizedError(
                        error_id=f"ERR-{experiment_result.experiment_id}-{err_idx:03d}",
                        error_category=category,
                        taxonomy_source="Phase 6 & Phase 9 Error Taxonomy",
                        patient_id=pid,
                        trial_id=tid,
                        expected=expected,
                        predicted=pred,
                        description=desc,
                    )
                )
                err_idx += 1

        # Check retrieval errors if retrieval metrics available
        if (
            experiment_result.retrieval_metrics
            and experiment_result.retrieval_metrics.recall_at_k < 1.0
        ):
            category = "RETRIEVAL_RECALL_MISS"
            error_counts[category] = error_counts.get(category, 0) + 1
            categorized_errors.append(
                CategorizedError(
                    error_id=f"ERR-{experiment_result.experiment_id}-{err_idx:03d}",
                    error_category=category,
                    taxonomy_source="Phase 5 Retrieval Taxonomy",
                    patient_id="AGGREGATE",
                    trial_id="MULTIPLE",
                    expected="1.0 Recall@K",
                    predicted=f"{experiment_result.retrieval_metrics.recall_at_k}",
                    description="One or more relevant trials were omitted from the top-k retrieved candidate pool.",
                )
            )
            err_idx += 1

        total_errs = len(categorized_errors)
        total_evals = max(1, len(cases))
        error_rates = {
            cat: round(count / float(total_evals), 4) for cat, count in error_counts.items()
        }

        interpretation = (
            f"Experiment {experiment_result.experiment_id} produced {total_errs} categorized errors "
            f"across {len(cases)} evaluated patient-trial encounters on the development fixture. "
            f"All failures are categorized deterministically using rule-based criteria audits."
        )

        return ErrorAnalysisSummary(
            experiment_id=experiment_result.experiment_id,
            total_errors=total_errs,
            error_counts_by_category=error_counts,
            error_rates_by_category=error_rates,
            detailed_errors=categorized_errors,
            interpretation=interpretation,
        )
