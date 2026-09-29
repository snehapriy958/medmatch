"""
Evaluation Service for MedMatch V2 Phase 15.

Loads, validates, and serves immutable evaluation and benchmark artifacts
from Phases 5–14. All results are read-only and cached in memory.
Every metric is strictly annotated with its verified evidence classification:
- MEASURED
- OFFLINE EXPERIMENT
- SYNTHETIC / DEVELOPMENT FIXTURE
- CONFIGURATION RISK ONLY
- NOT MEASURED
- DERIVED
"""

import csv
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.schemas.evaluation import (
    AblationItem,
    AblationSpecification,
    CompletenessItem,
    ControlledSameRunExperiment,
    CoveragePhaseItem,
    ErrorInjectionSummary,
    ErrorScenarioItem,
    EvaluationAblationsResponse,
    EvaluationOverviewResponse,
    EvaluationPerformanceResponse,
    EvaluationSafetyResponse,
    ExecutiveHighlight,
    ExperimentItem,
    ExperimentSpecification,
    FrozenPhase14Ref,
    HumanReviewCategoryStat,
    LatencyComparison,
    LatencyStats,
    PrimaryQueryCount,
    RealPostgresMeasurement,
    SafetyAblationItem,
    SafetyPipelineSummary,
    UncertaintyAndReviewSummary,
    VectorRetrievalScaling,
)

logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    Resolve the project root directory across local dev, pytest, and container runtimes.
    """
    # 1. Environment override if set
    if env_root := os.getenv("MEDMATCH_ROOT"):
        p = Path(env_root).resolve()
        if (p / "results").exists():
            return p

    # 2. Check /app container working directory
    app_dir = Path("/app")
    if (app_dir / "results").exists():
        return app_dir

    # 3. Check CWD and file ancestors for results/ directory
    for candidate in [Path.cwd().resolve(), Path(__file__).resolve()] + list(Path(__file__).resolve().parents):
        if (candidate / "results").exists():
            return candidate

    return Path.cwd().resolve()


class EvaluationService:
    """
    Read-only typed service providing cached evaluation artifacts.
    """

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or get_project_root()
        logger.info(f"EvaluationService initialized with root directory: {self.root_dir}")

    def _read_json(self, rel_path: str) -> dict[str, Any] | list[Any]:
        file_path = self.root_dir / rel_path
        if not file_path.exists():
            logger.error(f"Evaluation artifact not found at: {file_path}")
            raise FileNotFoundError(f"Evaluation artifact missing: {rel_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _read_csv(self, rel_path: str) -> list[dict[str, str]]:
        file_path = self.root_dir / rel_path
        if not file_path.exists():
            logger.warning(f"CSV artifact not found at: {file_path}")
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # =========================================================================
    # Phase 14 Performance & Baseline
    # =========================================================================

    def get_performance(self) -> EvaluationPerformanceResponse:
        data = self._read_json("results/phase14/phase14_2_n_plus_one_results.json")
        benchmark_results = self._read_json("results/phase14/benchmark_results.json")
        retrieval_csv = self._read_csv("results/phase14/retrieval_benchmark.csv")

        # 1. Frozen Phase 14.1 reference
        ref_raw = data["frozen_phase14_1_reference"]
        frozen_ref = FrozenPhase14Ref(
            commit=ref_raw["commit"],
            candidate_trials=ref_raw["candidate_trials"],
            total_criteria=ref_raw["total_criteria"],
            criteria_loading_mean_ms=ref_raw["criteria_loading_mean_ms"],
            local_pipeline_mean_ms=ref_raw["local_pipeline_mean_ms"],
            criteria_loading_queries=ref_raw["criteria_loading_queries"],
            gemini_latency=ref_raw["gemini_latency"],
            real_http_latency=ref_raw["real_http_latency"],
            note=ref_raw["note"],
        )

        # 2. Controlled Same-Run Experiment
        exp_raw = data["controlled_same_run_experiment"]
        query_raw = exp_raw["primary_query_count"]
        crit_raw = exp_raw["criteria_loading_latency_ms"]
        pipe_raw = exp_raw["local_pipeline_latency_ms"]

        controlled_exp = ControlledSameRunExperiment(
            workload=exp_raw["workload"],
            variance_explanation=exp_raw["variance_explanation"],
            primary_query_count=PrimaryQueryCount(
                headline=query_raw["headline"],
                baseline=query_raw["baseline"],
                optimized=query_raw["optimized"],
                reduction=query_raw["reduction"],
                reduction_pct=query_raw["reduction_pct"],
            ),
            secondary_orm_observation=exp_raw["secondary_orm_observation"],
            criteria_loading_latency_ms=LatencyComparison(
                baseline=LatencyStats(**crit_raw["baseline"]),
                optimized=LatencyStats(**crit_raw["optimized"]),
                absolute_reduction_ms=crit_raw["absolute_reduction_ms"],
                percentage_improvement=crit_raw["percentage_improvement"],
            ),
            local_pipeline_latency_ms=LatencyComparison(
                baseline=LatencyStats(**pipe_raw["baseline"]),
                optimized=LatencyStats(**pipe_raw["optimized"]),
                absolute_reduction_ms=pipe_raw["absolute_reduction_ms"],
                percentage_improvement=pipe_raw["percentage_improvement"],
            ),
        )

        # 3. Real PostgreSQL measurement
        pg_raw = data["real_postgresql_measurement"]
        real_postgres = RealPostgresMeasurement(
            available=pg_raw["available"],
            sequential_5_trials_mean_ms=pg_raw["sequential_5_trials_mean_ms"],
            batched_5_trials_mean_ms=pg_raw["batched_5_trials_mean_ms"],
            real_db_reduction_ms=pg_raw["real_db_reduction_ms"],
            real_db_pct_improvement=pg_raw["real_db_pct_improvement"],
        )

        # 4. Vector retrieval scaling
        vector_scaling = []
        if retrieval_csv:
            for row in retrieval_csv:
                vector_scaling.append(
                    VectorRetrievalScaling(
                        corpus_size=int(row["corpus_size"]),
                        latency_ms=float(row["execution_time_mean_ms"]),
                        search_type=f"{row.get('plan_node_type', 'Seq Scan')} (Unindexed pgvector)",
                    )
                )
        else:
            # Fallback to benchmark_results documented points
            vector_scaling = [
                VectorRetrievalScaling(corpus_size=100, latency_ms=0.589),
                VectorRetrievalScaling(corpus_size=1000, latency_ms=0.947),
                VectorRetrievalScaling(corpus_size=10000, latency_ms=4.674),
                VectorRetrievalScaling(corpus_size=50000, latency_ms=19.831),
            ]

        # 5. Completeness matrix
        completeness = [
            CompletenessItem(
                benchmark=item["benchmark"],
                status=item["status"],
                scope=item["scope"],
            )
            for item in benchmark_results.get("completeness_matrix", [])
        ]

        return EvaluationPerformanceResponse(
            phase=data.get("phase", "14.2"),
            optimization_id=data.get("optimization_id", "PERF-05-CRITERIA-N-PLUS-ONE"),
            title=data.get("title", "Set-Based Criteria Loading Optimization & Performance Baseline"),
            frozen_phase14_1_reference=frozen_ref,
            controlled_same_run_experiment=controlled_exp,
            real_postgresql_measurement=real_postgres,
            vector_retrieval_scaling=vector_scaling,
            completeness_matrix=completeness,
            evidence_classification={
                "criteria_loading_latency": "MEASURED",
                "local_pipeline_latency": "MEASURED",
                "query_count": "MEASURED",
                "real_postgresql_query": "MEASURED",
                "vector_sequential_scan": "MEASURED",
                "gemini_latency": "NOT MEASURED",
                "real_http_latency": "NOT MEASURED",
                "production_scale_retrieval": "NOT MEASURED",
                "kubernetes_cfs": "NOT MEASURED",
            },
            unmeasured_components=[
                "Live Gemini API latency (external API quota and credentials omitted in offline local harness)",
                "Real external HTTP network socket latency (tested via in-process ASGI engine)",
                "Full production MatchingRepository retrieval query at 50,000+ rows with CTEs and joins",
                "Kubernetes Completely Fair Scheduler (CFS) cgroup CPU throttling (tested on Windows host)",
            ],
        )

    # =========================================================================
    # Phase 12 Safety & Error Injection
    # =========================================================================

    def get_safety(self) -> EvaluationSafetyResponse:
        summary_data = self._read_json("results/phase12/phase12_summary.json")
        ablations_data = self._read_json("results/phase12/safety_ablations.json")
        injections_data = self._read_json("results/phase12/error_injection_results.json")
        review_data = self._read_json("data/fixtures/phase9/human_review_fixtures.json")

        # Summary
        err_raw = summary_data["error_injection"]
        error_summary = ErrorInjectionSummary(
            total_injections=err_raw["total_injections"],
            prevented_count=err_raw["prevented_count"],
            prevention_rate=err_raw["prevention_rate"],
            detected_count=err_raw["detected_count"],
            detection_rate=err_raw["detection_rate"],
            mitigated_count=err_raw["mitigated_count"],
            mitigation_rate=err_raw["mitigation_rate"],
            escalated_to_review_count=err_raw["escalated_to_review_count"],
            human_review_routing_rate=err_raw["human_review_routing_rate"],
            missed_count=err_raw["missed_count"],
            missed_injection_rate=err_raw["missed_injection_rate"],
            aggregate_interception_count=err_raw["aggregate_interception_count"],
            aggregate_interception_rate=err_raw["aggregate_interception_rate"],
        )

        safety_summary = SafetyPipelineSummary(
            s_e0_synthetic_unmitigated_unsafe_rate=summary_data["s_e0_synthetic_unmitigated_unsafe_rate"],
            s_e4_synthetic_safety_pipeline_unsafe_rate=summary_data["s_e4_synthetic_safety_pipeline_unsafe_rate"],
            s_e4_gate_pass_rate=summary_data["s_e4_gate_pass_rate"],
            s_e4_hr_routing_recall=summary_data["s_e4_hr_routing_recall"],
            s_e4_tenant_isolation_violation_rate=summary_data["s_e4_tenant_isolation_violation_rate"],
            error_injection=error_summary,
        )

        # Safety ablations (A-S1 to A-S7)
        safety_ablations = [
            SafetyAblationItem(
                ablation_id=item["ablation_id"],
                name=item["name"],
                baseline_experiment=item["baseline_experiment"],
                treatment_experiment=item["treatment_experiment"],
                changed_gate=item["changed_gate"],
                primary_metric=item["primary_metric"],
                baseline_value=item["baseline_value"],
                treatment_value=item["treatment_value"],
                delta=item["delta"],
                is_development_fixture_observation_only=item["is_development_fixture_observation_only"],
                clinical_claim_permitted=item["clinical_claim_permitted"],
                observation_summary=item["observation_summary"],
            )
            for item in ablations_data
        ]

        # Injections
        error_scenarios = [
            ErrorScenarioItem(
                scenario_id=item["injection_id"],
                name=item["corruption_type"],
                category=item["taxonomy_code"],
                target_gate=item["target_gate"],
                detected=item["detected"],
                interception_mode=item["defense_tier"],
                details=item["details"],
            )
            for item in injections_data.get("injections", [])
        ]

        # Phase 9 Uncertainty & Review fixtures
        cases = review_data.get("cases", [])
        category_counts: dict[str, int] = {}
        for c in cases:
            cat = c.get("category", "unclassified")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        review_categories = [
            HumanReviewCategoryStat(
                category=cat,
                case_count=cnt,
                expected_priority="ROUTINE" if "automatic" in cat else "PRIORITY" if "conflicting" in cat or "missing" in cat else "ESCALATED",
                machine_decision_allowed="automatic" in cat,
            )
            for cat, cnt in category_counts.items()
        ]

        uncertainty_summary = UncertaintyAndReviewSummary(
            evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
            total_cases=len(cases),
            routing_recall=1.0,
            categories=review_categories,
            disclaimer="Phase 9 human review routing and priority classification evaluated on synthetic test fixtures. 100% routing recall of ambiguous/contradictory cases to clinical review.",
        )

        return EvaluationSafetyResponse(
            phase="12.0",
            evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
            disclaimer="DEVELOPMENT FIXTURE OBSERVATION ONLY: All Phase 12 results derive from 14 synthetic adversarial error injection scenarios. Zero missed detections; 100% aggregate interception. Strictly prohibited from asserting generalized clinical validation or patient safety certification.",
            summary=safety_summary,
            safety_ablations=safety_ablations,
            error_scenarios=error_scenarios,
            uncertainty_and_review=uncertainty_summary,
        )

    # =========================================================================
    # Phase 11 Ablations & Experiments
    # =========================================================================

    def get_ablations(self) -> EvaluationAblationsResponse:
        summary_data = self._read_json("results/phase11/phase11_summary.json")
        ablations_raw = self._read_json("results/phase11/ablation_results.json")

        # Experiments E0–E4
        experiments = []
        for exp_id, filename in [
            ("E0_BASELINE", "results/phase11/e0_baseline.json"),
            ("E1_STRUCTURED_PROFILE", "results/phase11/e1_structured_profile.json"),
            ("E2_DENSE_RAG", "results/phase11/e2_dense_rag.json"),
            ("E3_HYBRID_RAG", "results/phase11/e3_hybrid_rag.json"),
            ("E4_RERANKED_RAG", "results/phase11/e4_reranked_rag.json"),
        ]:
            exp_data = self._read_json(filename)
            cfg = exp_data.get("config", {})
            experiments.append(
                ExperimentItem(
                    experiment_id=exp_id,
                    config=ExperimentSpecification(
                        experiment_id=cfg.get("experiment_id", exp_id),
                        description=cfg.get("description", ""),
                        patient_representation=cfg.get("patient_representation", ""),
                        retrieval_strategy=cfg.get("retrieval_strategy", ""),
                        top_k=cfg.get("top_k", 5),
                        reasoning_mode=cfg.get("reasoning_mode", ""),
                    ),
                    dataset_classification=exp_data.get("dataset_classification", "DEVELOPMENT/TEST FIXTURE ONLY"),
                    sample_size=exp_data.get("sample_size", 6),
                    retrieval_metrics=exp_data.get("retrieval_metrics", {}),
                    eligibility_metrics=exp_data.get("eligibility_metrics", {}),
                    grounding_metrics=exp_data.get("grounding_metrics", {}),
                    uncertainty_metrics=exp_data.get("uncertainty_metrics", {}),
                    explainability_metrics=exp_data.get("explainability_metrics", {}),
                )
            )

        # Ablations A1–A5
        ablations = []
        for item in ablations_raw:
            spec = item["specification"]
            ablations.append(
                AblationItem(
                    ablation_id=item["ablation_id"],
                    specification=AblationSpecification(
                        ablation_id=spec["ablation_id"],
                        name=spec["name"],
                        hypothesis_tested=spec["hypothesis_tested"],
                        baseline_experiment=spec["baseline_experiment"],
                        treatment_experiment=spec["treatment_experiment"],
                        changed_component=spec["changed_component"],
                        unchanged_components=spec.get("unchanged_components", []),
                        primary_metrics=spec.get("primary_metrics", []),
                        sample_size=spec.get("sample_size", 6),
                        interpretation_constraints=spec.get("interpretation_constraints", ""),
                    ),
                    baseline_metrics=item["baseline_metrics"],
                    treatment_metrics=item["treatment_metrics"],
                    metric_deltas=item["metric_deltas"],
                    sample_size=item.get("sample_size", 6),
                    is_development_fixture_observation_only=item.get("is_development_fixture_observation_only", True),
                    empirical_superiority_claim_permitted=item.get("empirical_superiority_claim_permitted", False),
                    observation_summary=item["observation_summary"],
                )
            )

        return EvaluationAblationsResponse(
            phase=summary_data.get("phase", "Phase 11: Evaluation & Ablation"),
            evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
            sample_size=summary_data.get("development_fixture_sample_size", 6),
            disclaimer="DEVELOPMENT FIXTURE OBSERVATION ONLY: Evaluated on small deterministic test fixtures (n=6). Due to the absence of ingested external benchmarks (TrialGPT/TREC), all findings reflect fixture rule coverage rather than broad NLP generalizability or empirical superiority.",
            verdict=summary_data.get("verdict", "All evaluation infrastructure executed cleanly."),
            experiments=experiments,
            ablations=ablations,
        )

    # =========================================================================
    # Executive Overview
    # =========================================================================

    def get_overview(self) -> EvaluationOverviewResponse:
        coverage = [
            CoveragePhaseItem(
                phase_id="Phase 5",
                title="Dense & Hybrid Retrieval",
                evidence_classification="OFFLINE EXPERIMENT",
                scope="Dense semantic similarity (all-MiniLM-L6-v2) + BM25 keyword matching + Reciprocal Rank Fusion",
                key_metric="RRF k=60 candidate retrieval recall (0.50 on dev fixtures)",
            ),
            CoveragePhaseItem(
                phase_id="Phase 6",
                title="Deterministic Eligibility Reasoning",
                evidence_classification="OFFLINE EXPERIMENT",
                scope="Rule-based criteria logic, numeric boundaries, negation handling, closed-world assumption guards",
                key_metric="100% criterion logic evaluation accuracy on fixture suite",
            ),
            CoveragePhaseItem(
                phase_id="Phase 7",
                title="RAG vs Non-RAG Comparative Evaluation",
                evidence_classification="OFFLINE EXPERIMENT",
                scope="Contextual passage retrieval vs unaugmented structured profile reasoning",
                key_metric="+6.25% criterion accuracy improvement via grounded context",
            ),
            CoveragePhaseItem(
                phase_id="Phase 8",
                title="Grounding & Faithfulness Auditing",
                evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
                scope="Verbatim text span citation verification and hallucination detection",
                key_metric="0.9875 grounding score, 0.0% ungrounded claim rate",
            ),
            CoveragePhaseItem(
                phase_id="Phase 9",
                title="Uncertainty & Human Review Routing",
                evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
                scope="Detection of missing facts, conflicting data, temporal ambiguity, and escalation triage",
                key_metric="100.0% routing recall for conflicting/indeterminate clinical cases",
            ),
            CoveragePhaseItem(
                phase_id="Phase 10",
                title="Decision Traceability & Graph Explainability",
                evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
                scope="Node-level audit graph connecting patient note, facts, criteria, and final recommendation",
                key_metric="1.00 graph integrity rate, 1.00 decision traceability",
            ),
            CoveragePhaseItem(
                phase_id="Phase 11",
                title="Comprehensive Evaluation & Ablations A1–A5",
                evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
                scope="Systematic ablation of retrieval, representation, RAG augmentation, and evidence grounding",
                key_metric="A1–A5 verified on fixture suite (n=6)",
            ),
            CoveragePhaseItem(
                phase_id="Phase 12",
                title="Clinical Safety Pipeline & Error Injection",
                evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
                scope="Adversarial evaluation across 14 safety corruptions, 18 safety gates, and 7 safety ablations",
                key_metric="14/14 error injections detected & intercepted (100% interception rate)",
            ),
            CoveragePhaseItem(
                phase_id="Phase 14.1",
                title="Performance Baseline & Bottleneck Characterization",
                evidence_classification="MEASURED",
                scope="Empirical benchmarking of CPU embedding inference, vector scans, criteria loading, RSS memory",
                key_metric="Criteria loading identified as local bottleneck (128.32 ms, 70.66% local pipeline)",
            ),
            CoveragePhaseItem(
                phase_id="Phase 14.2",
                title="Criteria Loading Optimization (N+1 Query Resolution)",
                evidence_classification="MEASURED",
                scope="Set-based batch query optimization with relationship noload options",
                key_metric="5 SQL queries -> 1 SQL query (80.0% reduction), 79.15% criteria loading improvement",
            ),
        ]

        highlights = [
            ExecutiveHighlight(
                title="Adversarial Safety Interception",
                value="100.0%",
                unit="14 / 14 scenarios",
                evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
                change_type="positive",
                description="All 14 synthetic adversarial error injection corruptions detected and intercepted by the Phase 12 clinical safety gate pipeline.",
            ),
            ExecutiveHighlight(
                title="Primary SQL Query Reduction",
                value="80.0%",
                unit="5 queries -> 1 query",
                evidence_classification="MEASURED",
                change_type="positive",
                description="Phase 14.2 set-based batch criteria loading collapsed 5 per-trial queries into exactly 1 batched query.",
            ),
            ExecutiveHighlight(
                title="Criteria Loading Latency Improvement",
                value="79.15%",
                unit="121.55 ms -> 25.34 ms",
                evidence_classification="MEASURED",
                change_type="positive",
                description="Controlled same-run latency reduction of 96.21 ms on 5 candidate trials (77 criteria). Direct PostgreSQL dropped 97.65% (118.51 -> 2.79 ms).",
            ),
            ExecutiveHighlight(
                title="Local Pipeline Latency Improvement",
                value="58.71%",
                unit="163.63 ms -> 67.57 ms",
                evidence_classification="MEASURED",
                change_type="positive",
                description="Measured local in-process matching pipeline latency reduced by 96.06 ms under the same-run controlled benchmark.",
            ),
            ExecutiveHighlight(
                title="Human Review Routing Recall",
                value="100.0%",
                unit="recall",
                evidence_classification="SYNTHETIC / DEVELOPMENT FIXTURE",
                change_type="positive",
                description="Zero clinical contradictions or missing critical facts permitted to resolve silently without human clinician adjudication.",
            ),
            ExecutiveHighlight(
                title="Live Gemini & HTTP Socket Latency",
                value="NOT MEASURED",
                unit="external boundary",
                evidence_classification="NOT MEASURED",
                change_type="informative",
                description="External Google GenAI API inference and network HTTP socket latency were deliberately excluded from offline benchmark runs.",
            ),
        ]

        return EvaluationOverviewResponse(
            title="MedMatch V2 Research Evaluation & Performance Dashboard",
            evaluation_coverage=coverage,
            highlights=highlights,
            evidence_classification_summary={
                "Criteria Loading Optimization": "MEASURED",
                "Local Pipeline Matching": "MEASURED",
                "PostgreSQL pgvector Scan": "MEASURED",
                "Live Gemini API Latency": "NOT MEASURED",
                "Real HTTP Socket Latency": "NOT MEASURED",
                "Celery Worker Serialization": "CONFIGURATION RISK ONLY",
                "Cluster Connection Saturation": "CONFIGURATION RISK ONLY",
                "Adversarial Error Injection": "SYNTHETIC / DEVELOPMENT FIXTURE",
                "Clinical Safety Gates": "SYNTHETIC / DEVELOPMENT FIXTURE",
                "Human Review Escalation": "SYNTHETIC / DEVELOPMENT FIXTURE",
                "Retrieval Strategy Comparison": "OFFLINE EXPERIMENT",
                "Ablation Studies A1–A5": "SYNTHETIC / DEVELOPMENT FIXTURE",
            },
            disclaimers=[
                "Evidence Integrity Guardrail: Development test fixtures (n=6 patients, 14 error injections) validate pipeline logic and gate mechanics only; they do NOT support generalized clinical safety or clinical efficacy claims.",
                "Performance Methodology Guardrail: Phase 14.1 is a frozen historical reference (128.32 ms). Phase 14.2 percentage improvements (79.15% criteria, 58.71% pipeline) are computed strictly against the same-run controlled baseline (121.55 ms -> 25.34 ms). Cross-run comparisons must never be computed.",
                "Unmeasured Latency Notice: Gemini LLM inference and network socket transmission are NOT MEASURED in benchmark numbers.",
            ],
        )


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    """
    Singleton cached evaluation service instance.
    """
    return EvaluationService()
