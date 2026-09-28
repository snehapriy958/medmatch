"""
MedMatch Controlled Ablation Runner.
Phase 11: Evaluation & Ablation.

Executes the five canonical ablations corresponding to Phase 1 hypotheses:
- A1: Dense Retrieval vs Hybrid Retrieval (E2 vs E3)
- A2: Hybrid Retrieval vs Hybrid + Reranking (E3 vs E4)
- A3: Raw Patient Representation vs Structured Patient Profile (E0 vs E1)
- A4: NON-RAG vs RAG (E1 vs E2)
- A5: Evidence-Grounded Reasoning vs Reasoning Without Retrieved Evidence (E2 vs E1)

Enforces:
1. Strict controlled-variable isolation
2. Explicit hypothesis and interpretation constraint recording
3. Development fixture observation designation (no empirical superiority claims permitted)
"""

from __future__ import annotations

from typing import Dict, List

try:
    from scripts.evaluation_schema import (
        AblationResult,
        AblationSpecification,
        ExperimentResult,
    )
except ImportError:
    from evaluation_schema import (
        AblationResult,
        AblationSpecification,
        ExperimentResult,
    )


class AblationRunner:
    """
    Executes controlled paired ablations across experiment results.
    """

    @classmethod
    def get_ablation_specifications(cls) -> Dict[str, AblationSpecification]:
        return {
            "A1": AblationSpecification(
                ablation_id="A1",
                name="Dense vs Hybrid Retrieval",
                hypothesis_tested="Hybrid RRF retrieval achieves higher candidate recall than dense-only retrieval by combining lexical and semantic signals.",
                baseline_experiment="E2_DENSE_RAG",
                treatment_experiment="E3_HYBRID_RAG",
                changed_component="Retrieval Method: DenseRetriever -> HybridRRFRetriever (BM25 + Dense)",
                unchanged_components=[
                    "Structured patient representation",
                    "Candidate pool",
                    "Top-K=5",
                    "Phase 6 eligibility reasoner",
                    "Deterministic aggregation",
                ],
                primary_metrics=["retrieval_mrr", "retrieval_recall_at_k", "macro_f1"],
                sample_size=6,
                interpretation_constraints="Development-fixture observation only. n=6 is statistically insufficient to infer generalized retrieval superiority.",
            ),
            "A2": AblationSpecification(
                ablation_id="A2",
                name="Hybrid Retrieval vs Hybrid + Reranking",
                hypothesis_tested="Second-stage clinical concept reranking improves precision and nDCG of top-ranked trial candidates.",
                baseline_experiment="E3_HYBRID_RAG",
                treatment_experiment="E4_RERANKED_RAG",
                changed_component="Second-stage reranking: None -> ClinicalOverlapReranker",
                unchanged_components=[
                    "Hybrid retrieval first-stage",
                    "Patient representation",
                    "Top-K=5",
                    "Eligibility reasoning engine",
                ],
                primary_metrics=["retrieval_precision_at_k", "retrieval_ndcg", "accuracy"],
                sample_size=6,
                interpretation_constraints="Development-fixture observation only. Multiplier=2 over n=6 cannot establish clinical ranking significance.",
            ),
            "A3": AblationSpecification(
                ablation_id="A3",
                name="Raw Patient Representation vs Structured Profile",
                hypothesis_tested="Structured clinical profiles (Phase 4) resolve explicit criteria more accurately and reduce UNKNOWN rates compared to raw text.",
                baseline_experiment="E0_BASELINE",
                treatment_experiment="E1_STRUCTURED_PROFILE",
                changed_component="Patient Representation: Raw clinical note -> PatientClinicalProfile",
                unchanged_components=[
                    "Dense retrieval",
                    "Non-RAG reasoning",
                    "Trial criteria definitions",
                    "Deterministic aggregation",
                ],
                primary_metrics=["macro_f1", "accuracy", "criterion_accuracy"],
                sample_size=6,
                interpretation_constraints="Development-fixture observation only. Measures fixture rule coverage rather than broad NLP generalizability.",
            ),
            "A4": AblationSpecification(
                ablation_id="A4",
                name="NON-RAG vs RAG",
                hypothesis_tested="Retrieval-augmented grounding allows criteria requiring protocol context to be resolved safely rather than defaulting to UNKNOWN.",
                baseline_experiment="E1_STRUCTURED_PROFILE",
                treatment_experiment="E2_DENSE_RAG",
                changed_component="Augmentation: Non-RAG -> Dense RAG with retrieved protocol passages",
                unchanged_components=[
                    "Structured patient profile",
                    "Dense retrieval method",
                    "Rule-based reasoning rules",
                    "Aggregation logic",
                ],
                primary_metrics=["macro_f1", "grounding_score", "claim_support_rate"],
                sample_size=6,
                interpretation_constraints="Development-fixture observation only. True RAG superiority must be tested on public external benchmarks (TrialGPT/TREC).",
            ),
            "A5": AblationSpecification(
                ablation_id="A5",
                name="Evidence-Grounded Reasoning vs Non-Retrieved Reasoning",
                hypothesis_tested="Evidence citations and graph grounding eliminate hallucination and increase decision traceability.",
                baseline_experiment="E1_STRUCTURED_PROFILE",
                treatment_experiment="E2_DENSE_RAG",
                changed_component="Evidence context: Absent -> Present with character-level citations",
                unchanged_components=[
                    "Patient facts",
                    "Demographics",
                    "Criterion definitions",
                    "Deterministic aggregation",
                ],
                primary_metrics=["evidence_coverage", "grounding_score", "citation_validity_rate"],
                sample_size=6,
                interpretation_constraints="Development-fixture observation only. Traceability metrics reflect schema adherence, not empirical clinical accuracy.",
            ),
        }

    @classmethod
    def run_ablations(
        cls, experiment_results: Dict[str, ExperimentResult]
    ) -> List[AblationResult]:
        specs = cls.get_ablation_specifications()
        results: List[AblationResult] = []

        for ab_id, spec in specs.items():
            base_exp = experiment_results.get(spec.baseline_experiment)
            treat_exp = experiment_results.get(spec.treatment_experiment)

            if not base_exp or not treat_exp:
                continue

            base_metrics: Dict[str, float] = {
                "accuracy": base_exp.eligibility_metrics.accuracy,
                "macro_f1": base_exp.eligibility_metrics.macro_f1,
                "criterion_accuracy": base_exp.eligibility_metrics.criterion_accuracy,
                "retrieval_mrr": base_exp.retrieval_metrics.mrr if base_exp.retrieval_metrics else 0.0,
                "retrieval_recall_at_k": base_exp.retrieval_metrics.recall_at_k if base_exp.retrieval_metrics else 0.0,
                "retrieval_precision_at_k": base_exp.retrieval_metrics.precision_at_k if base_exp.retrieval_metrics else 0.0,
                "retrieval_ndcg": base_exp.retrieval_metrics.ndcg if base_exp.retrieval_metrics else 0.0,
                "grounding_score": base_exp.grounding_metrics.grounding_score if base_exp.grounding_metrics else 0.0,
                "claim_support_rate": base_exp.grounding_metrics.claim_support_rate if base_exp.grounding_metrics else 0.0,
                "evidence_coverage": base_exp.grounding_metrics.evidence_coverage if base_exp.grounding_metrics else 0.0,
                "citation_validity_rate": base_exp.grounding_metrics.citation_validity_rate if base_exp.grounding_metrics else 0.0,
            }

            treat_metrics: Dict[str, float] = {
                "accuracy": treat_exp.eligibility_metrics.accuracy,
                "macro_f1": treat_exp.eligibility_metrics.macro_f1,
                "criterion_accuracy": treat_exp.eligibility_metrics.criterion_accuracy,
                "retrieval_mrr": treat_exp.retrieval_metrics.mrr if treat_exp.retrieval_metrics else 0.0,
                "retrieval_recall_at_k": treat_exp.retrieval_metrics.recall_at_k if treat_exp.retrieval_metrics else 0.0,
                "retrieval_precision_at_k": treat_exp.retrieval_metrics.precision_at_k if treat_exp.retrieval_metrics else 0.0,
                "retrieval_ndcg": treat_exp.retrieval_metrics.ndcg if treat_exp.retrieval_metrics else 0.0,
                "grounding_score": treat_exp.grounding_metrics.grounding_score if treat_exp.grounding_metrics else 0.0,
                "claim_support_rate": treat_exp.grounding_metrics.claim_support_rate if treat_exp.grounding_metrics else 0.0,
                "evidence_coverage": treat_exp.grounding_metrics.evidence_coverage if treat_exp.grounding_metrics else 0.0,
                "citation_validity_rate": treat_exp.grounding_metrics.citation_validity_rate if treat_exp.grounding_metrics else 0.0,
            }

            deltas: Dict[str, float] = {
                k: round(treat_metrics[k] - base_metrics[k], 4) for k in base_metrics
            }

            summary = (
                f"Ablation {ab_id} ({spec.name}): "
                f"Delta Macro-F1={deltas['macro_f1']}, Delta Accuracy={deltas['accuracy']}. "
                f"DEVELOPMENT FIXTURE OBSERVATION ONLY: no empirical superiority claimed due to small sample size (n={spec.sample_size})."
            )

            results.append(
                AblationResult(
                    ablation_id=ab_id,
                    specification=spec,
                    baseline_metrics=base_metrics,
                    treatment_metrics=treat_metrics,
                    metric_deltas=deltas,
                    sample_size=spec.sample_size,
                    is_development_fixture_observation_only=True,
                    empirical_superiority_claim_permitted=False,
                    observation_summary=summary,
                )
            )

        return results
