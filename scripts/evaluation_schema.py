"""
MedMatch Canonical Evaluation & Experiment Schemas.
Phase 11: Evaluation & Ablation.

Defines strongly-typed Pydantic contracts for:
1. BenchmarkAvailabilityRecord & DatasetValidationSummary
2. ExperimentConfig, ExperimentType, ExecutionStatus
3. EvaluationMetrics (Retrieval, Eligibility, Grounding, Uncertainty, Explainability)
4. AblationSpecification & AblationResult
5. ErrorAnalysisRecord & CategorizedError
6. StatisticalComparisonRecord
7. Phase11EvaluationManifest & Summary
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExperimentType(str, Enum):
    E0_BASELINE = "E0_BASELINE"
    E1_STRUCTURED_PROFILE = "E1_STRUCTURED_PROFILE"
    E2_DENSE_RAG = "E2_DENSE_RAG"
    E3_HYBRID_RAG = "E3_HYBRID_RAG"
    E4_RERANKED_RAG = "E4_RERANKED_RAG"


class BenchmarkClassification(str, Enum):
    DEVELOPMENT_FIXTURE = "DEVELOPMENT_FIXTURE"
    RESEARCH_BENCHMARK = "RESEARCH_BENCHMARK"
    STRESS_TEST_FIXTURE = "STRESS_TEST_FIXTURE"


class BenchmarkAvailabilityRecord(BaseModel):
    benchmark_name: str
    official_reference: str
    physical_files_exist: bool
    record_count: int = 0
    ingestion_status: str
    classification: BenchmarkClassification
    licensing: str
    can_support_generalizable_claims: bool = False
    limitation_notes: str


class DatasetValidationSummary(BaseModel):
    dataset_name: str
    version: str
    classification: str
    total_patients: int
    total_trials: int
    total_criteria: int
    total_patient_trial_pairs: int
    total_criterion_labels: int
    criterion_label_distribution: Dict[str, int]
    trial_label_distribution: Dict[str, int]
    unknown_missing_distribution: Dict[str, int]
    split_sizes: Dict[str, int]
    patient_leakage_detected: bool
    duplicate_record_count: int
    invalid_record_count: int
    is_valid: bool
    validation_timestamp: str


class ExperimentConfig(BaseModel):
    experiment_id: str
    experiment_type: ExperimentType
    description: str
    dataset_version: str
    patient_representation: str  # "raw_clinical_note" vs "structured_profile"
    retrieval_strategy: Optional[str] = None  # None, "dense", "hybrid_rrf", "hybrid_reranked"
    top_k: int = 5
    bm25_k1: float = 1.2
    bm25_b: float = 0.75
    rrf_constant: int = 60
    reranker_multiplier: int = 2
    random_seed: int = 42
    reasoning_mode: str = "deterministic_rule_based"
    anti_leakage_enforced: bool = True
    ground_truth_isolated: bool = True


class RetrievalMetrics(BaseModel):
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    total_queries: int = 0


class EligibilityMetrics(BaseModel):
    accuracy: float = 0.0
    macro_precision: float = 0.0
    macro_recall: float = 0.0
    macro_f1: float = 0.0
    per_class_f1: Dict[str, float] = Field(default_factory=dict)
    trial_count: int = 0
    criterion_count: int = 0
    criterion_accuracy: float = 0.0
    criterion_macro_f1: float = 0.0


class GroundingMetricsSummary(BaseModel):
    claim_support_rate: float = 0.0
    unsupported_claim_rate: float = 0.0
    contradiction_rate: float = 0.0
    citation_validity_rate: float = 0.0
    evidence_coverage: float = 0.0
    grounding_score: float = 0.0
    hallucination_rate: float = 0.0


class UncertaintyMetricsSummary(BaseModel):
    uncertainty_rate: float = 0.0
    review_routing_rate: float = 0.0
    unresolved_uncertainty_rate: float = 0.0
    total_evaluations: int = 0


class ExplainabilityMetricsSummary(BaseModel):
    evidence_coverage: float = 0.0
    decision_traceability_rate: float = 0.0
    criterion_traceability_rate: float = 0.0
    provenance_validity_rate: float = 0.0
    explanation_support_rate: float = 0.0
    unsupported_claim_rate: float = 0.0
    contradiction_disclosure_rate: float = 0.0
    graph_integrity_rate: float = 0.0


class ExperimentResult(BaseModel):
    experiment_id: str
    experiment_type: ExperimentType
    config: ExperimentConfig
    dataset_classification: str
    sample_size: int
    retrieval_metrics: Optional[RetrievalMetrics] = None
    eligibility_metrics: EligibilityMetrics
    grounding_metrics: Optional[GroundingMetricsSummary] = None
    uncertainty_metrics: Optional[UncertaintyMetricsSummary] = None
    explainability_metrics: Optional[ExplainabilityMetricsSummary] = None
    execution_time_seconds: float
    evaluated_cases: List[Dict[str, Any]] = Field(default_factory=list)
    is_development_fixture_observation_only: bool = True
    empirical_claim_permitted: bool = False


class AblationSpecification(BaseModel):
    ablation_id: str
    name: str
    hypothesis_tested: str
    baseline_experiment: str
    treatment_experiment: str
    changed_component: str
    unchanged_components: List[str]
    primary_metrics: List[str]
    sample_size: int
    interpretation_constraints: str


class AblationResult(BaseModel):
    ablation_id: str
    specification: AblationSpecification
    baseline_metrics: Dict[str, float]
    treatment_metrics: Dict[str, float]
    metric_deltas: Dict[str, float]
    sample_size: int
    is_development_fixture_observation_only: bool = True
    empirical_superiority_claim_permitted: bool = False
    observation_summary: str


class CategorizedError(BaseModel):
    error_id: str
    error_category: str
    taxonomy_source: str
    patient_id: str
    trial_id: str
    criterion_id: Optional[str] = None
    expected: Any
    predicted: Any
    description: str


class ErrorAnalysisSummary(BaseModel):
    experiment_id: str
    total_errors: int
    error_counts_by_category: Dict[str, int]
    error_rates_by_category: Dict[str, float]
    detailed_errors: List[CategorizedError]
    interpretation: str


class StatisticalComparisonRecord(BaseModel):
    comparison_name: str
    system_a: str
    system_b: str
    metric_name: str
    sample_size: int
    is_paired: bool
    test_method_attempted: str
    p_value: Optional[float] = None
    confidence_interval_95: Optional[List[float]] = None
    statistically_significant: bool = False
    justification_for_inference: str
    inference_permitted: bool = False


class Phase11EvaluationManifest(BaseModel):
    phase: str = "Phase 11: Evaluation & Ablation"
    generated_at: str
    git_commit_sha: str = "59e3f2f"
    random_seed: int = 42
    environment_info: Dict[str, str]
    benchmark_availability: List[BenchmarkAvailabilityRecord]
    dataset_validation: DatasetValidationSummary
    experiments_executed: List[str]
    ablations_executed: List[str]
    statistical_checks_executed: List[str]
    empirical_benchmark_available: bool = False
    generalizable_claims_asserted: bool = False
    summary_verdict: str
