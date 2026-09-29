"""
Pydantic schemas for Phase 15 Evaluation & Performance Dashboard.

These models strictly define the contracts for read-only evaluation metrics,
performance benchmarks, clinical safety pipelines, and ablation results.
Every model explicitly distinguishes between:
- MEASURED
- OFFLINE EXPERIMENT
- SYNTHETIC / DEVELOPMENT FIXTURE
- CONFIGURATION RISK ONLY
- NOT MEASURED
"""

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


EvidenceType = Literal[
    "MEASURED",
    "OFFLINE EXPERIMENT",
    "SYNTHETIC / DEVELOPMENT FIXTURE",
    "CONFIGURATION RISK ONLY",
    "NOT MEASURED",
    "DERIVED",
]


# =============================================================================
# Performance Models (Phase 14.1 / Phase 14.2)
# =============================================================================

class FrozenPhase14Ref(BaseModel):
    commit: str = Field(description="Historical commit hash for frozen baseline.")
    candidate_trials: int = Field(description="Number of candidate trials in test workload.")
    total_criteria: int = Field(description="Total criteria across candidate trials.")
    criteria_loading_mean_ms: float = Field(description="Frozen criteria loading mean in ms (128.32).")
    local_pipeline_mean_ms: float = Field(description="Frozen local pipeline mean in ms (181.60).")
    criteria_loading_queries: int = Field(description="Sequential criteria queries emitted (5).")
    gemini_latency: str = Field(default="NOT MEASURED", description="Status of Gemini API measurement.")
    real_http_latency: str = Field(default="NOT MEASURED", description="Status of real HTTP socket measurement.")
    note: str = Field(description="Explanation of frozen historical status.")

    model_config = ConfigDict(extra="forbid")


class PrimaryQueryCount(BaseModel):
    headline: str
    baseline: int = Field(description="Sequential SQL queries (5).")
    optimized: int = Field(description="Batched set-based SQL queries (1).")
    reduction: int = Field(description="Absolute query reduction (4).")
    reduction_pct: float = Field(description="Query reduction percentage (80.0%).")

    model_config = ConfigDict(extra="forbid")


class LatencyStats(BaseModel):
    sample_count: int
    mean_ms: float
    stddev_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    throughput_items_per_sec: float

    model_config = ConfigDict(extra="forbid")


class LatencyComparison(BaseModel):
    baseline: LatencyStats
    optimized: LatencyStats
    absolute_reduction_ms: float
    percentage_improvement: float

    model_config = ConfigDict(extra="forbid")


class ControlledSameRunExperiment(BaseModel):
    workload: dict[str, Any]
    variance_explanation: str
    primary_query_count: PrimaryQueryCount
    secondary_orm_observation: str
    criteria_loading_latency_ms: LatencyComparison
    local_pipeline_latency_ms: LatencyComparison

    model_config = ConfigDict(extra="forbid")


class RealPostgresMeasurement(BaseModel):
    available: bool
    sequential_5_trials_mean_ms: float
    batched_5_trials_mean_ms: float
    real_db_reduction_ms: float
    real_db_pct_improvement: float

    model_config = ConfigDict(extra="forbid")


class VectorRetrievalScaling(BaseModel):
    corpus_size: int = Field(description="Number of vector rows scanned.")
    latency_ms: float = Field(description="Measured <=> cosine distance scan latency in ms.")
    search_type: str = Field(default="Sequential Scan (Unindexed pgvector)", description="Index access method.")

    model_config = ConfigDict(extra="forbid")


class CompletenessItem(BaseModel):
    benchmark: str
    status: EvidenceType
    scope: str

    model_config = ConfigDict(extra="forbid")


class EvaluationPerformanceResponse(BaseModel):
    phase: str = "14.2"
    optimization_id: str = "PERF-05-CRITERIA-N-PLUS-ONE"
    title: str = "Set-Based Criteria Loading Optimization & Performance Baseline"
    frozen_phase14_1_reference: FrozenPhase14Ref
    controlled_same_run_experiment: ControlledSameRunExperiment
    real_postgresql_measurement: RealPostgresMeasurement
    vector_retrieval_scaling: list[VectorRetrievalScaling]
    completeness_matrix: list[CompletenessItem]
    evidence_classification: dict[str, EvidenceType]
    unmeasured_components: list[str]

    model_config = ConfigDict(extra="forbid")


# =============================================================================
# Safety Models (Phase 12 / Phase 9)
# =============================================================================

class SafetyAblationItem(BaseModel):
    ablation_id: str
    name: str
    baseline_experiment: str
    treatment_experiment: str
    changed_gate: str
    primary_metric: str
    baseline_value: float
    treatment_value: float
    delta: float
    is_development_fixture_observation_only: bool
    clinical_claim_permitted: bool
    observation_summary: str

    model_config = ConfigDict(extra="forbid")


class ErrorInjectionSummary(BaseModel):
    total_injections: int = Field(description="Total adversarial scenarios tested (14).")
    prevented_count: int
    prevention_rate: float
    detected_count: int
    detection_rate: float
    mitigated_count: int
    mitigation_rate: float
    escalated_to_review_count: int
    human_review_routing_rate: float
    missed_count: int
    missed_injection_rate: float
    aggregate_interception_count: int
    aggregate_interception_rate: float

    model_config = ConfigDict(extra="forbid")


class SafetyPipelineSummary(BaseModel):
    s_e0_synthetic_unmitigated_unsafe_rate: float
    s_e4_synthetic_safety_pipeline_unsafe_rate: float
    s_e4_gate_pass_rate: float
    s_e4_hr_routing_recall: float
    s_e4_tenant_isolation_violation_rate: float
    error_injection: ErrorInjectionSummary

    model_config = ConfigDict(extra="forbid")


class ErrorScenarioItem(BaseModel):
    scenario_id: str
    name: str
    category: str
    target_gate: str
    detected: bool
    interception_mode: str
    details: str

    model_config = ConfigDict(extra="forbid")


class HumanReviewCategoryStat(BaseModel):
    category: str
    case_count: int
    expected_priority: str
    machine_decision_allowed: bool

    model_config = ConfigDict(extra="forbid")


class UncertaintyAndReviewSummary(BaseModel):
    evidence_classification: EvidenceType = "SYNTHETIC / DEVELOPMENT FIXTURE"
    total_cases: int
    routing_recall: float
    categories: list[HumanReviewCategoryStat]
    disclaimer: str

    model_config = ConfigDict(extra="forbid")


class EvaluationSafetyResponse(BaseModel):
    phase: str = "12.0"
    evidence_classification: EvidenceType = "SYNTHETIC / DEVELOPMENT FIXTURE"
    disclaimer: str
    summary: SafetyPipelineSummary
    safety_ablations: list[SafetyAblationItem]
    error_scenarios: list[ErrorScenarioItem]
    uncertainty_and_review: UncertaintyAndReviewSummary

    model_config = ConfigDict(extra="forbid")


# =============================================================================
# Ablation & Experiment Models (Phase 11)
# =============================================================================

class ExperimentSpecification(BaseModel):
    experiment_id: str
    description: str
    patient_representation: str
    retrieval_strategy: str
    top_k: int
    reasoning_mode: str

    model_config = ConfigDict(extra="forbid")


class ExperimentItem(BaseModel):
    experiment_id: str
    config: ExperimentSpecification
    dataset_classification: str
    sample_size: int
    retrieval_metrics: dict[str, float]
    eligibility_metrics: dict[str, Any]
    grounding_metrics: dict[str, float]
    uncertainty_metrics: dict[str, float]
    explainability_metrics: dict[str, float]

    model_config = ConfigDict(extra="forbid")


class AblationSpecification(BaseModel):
    ablation_id: str
    name: str
    hypothesis_tested: str
    baseline_experiment: str
    treatment_experiment: str
    changed_component: str
    unchanged_components: list[str]
    primary_metrics: list[str]
    sample_size: int
    interpretation_constraints: str

    model_config = ConfigDict(extra="forbid")


class AblationItem(BaseModel):
    ablation_id: str
    specification: AblationSpecification
    baseline_metrics: dict[str, float]
    treatment_metrics: dict[str, float]
    metric_deltas: dict[str, float]
    sample_size: int
    is_development_fixture_observation_only: bool
    empirical_superiority_claim_permitted: bool
    observation_summary: str

    model_config = ConfigDict(extra="forbid")


class EvaluationAblationsResponse(BaseModel):
    phase: str = "Phase 11: Evaluation & Ablation"
    evidence_classification: EvidenceType = "SYNTHETIC / DEVELOPMENT FIXTURE"
    sample_size: int = 6
    disclaimer: str
    verdict: str
    experiments: list[ExperimentItem]
    ablations: list[AblationItem]

    model_config = ConfigDict(extra="forbid")


# =============================================================================
# Overview Models
# =============================================================================

class CoveragePhaseItem(BaseModel):
    phase_id: str
    title: str
    evidence_classification: EvidenceType
    scope: str
    key_metric: str

    model_config = ConfigDict(extra="forbid")


class ExecutiveHighlight(BaseModel):
    title: str
    value: str
    unit: str
    evidence_classification: EvidenceType
    change_type: Literal["positive", "neutral", "informative"]
    description: str

    model_config = ConfigDict(extra="forbid")


class EvaluationOverviewResponse(BaseModel):
    title: str = "MedMatch V2 Research Evaluation & Performance Dashboard"
    evaluation_coverage: list[CoveragePhaseItem]
    highlights: list[ExecutiveHighlight]
    evidence_classification_summary: dict[str, EvidenceType]
    disclaimers: list[str]

    model_config = ConfigDict(extra="forbid")
