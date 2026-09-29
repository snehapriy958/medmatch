/**
 * TypeScript definitions for Phase 15 Evaluation & Performance Dashboard.
 * Matches backend schemas in app/schemas/evaluation.py exactly.
 */

export type EvidenceType =
  | "MEASURED"
  | "OFFLINE EXPERIMENT"
  | "SYNTHETIC / DEVELOPMENT FIXTURE"
  | "CONFIGURATION RISK ONLY"
  | "NOT MEASURED"
  | "DERIVED";

// ============================================================================
// Performance (Phase 14.1 & 14.2)
// ============================================================================

export interface FrozenPhase14Ref {
  commit: string;
  candidate_trials: number;
  total_criteria: number;
  criteria_loading_mean_ms: number;
  local_pipeline_mean_ms: number;
  criteria_loading_queries: number;
  gemini_latency: string;
  real_http_latency: string;
  note: string;
}

export interface PrimaryQueryCount {
  headline: string;
  baseline: number;
  optimized: number;
  reduction: number;
  reduction_pct: number;
}

export interface LatencyStats {
  sample_count: number;
  mean_ms: number;
  stddev_ms: number;
  min_ms: number;
  max_ms: number;
  p50_ms: number;
  p90_ms: number;
  p95_ms: number;
  p99_ms: number;
  throughput_items_per_sec: number;
}

export interface LatencyComparison {
  baseline: LatencyStats;
  optimized: LatencyStats;
  absolute_reduction_ms: number;
  percentage_improvement: number;
}

export interface ControlledSameRunExperiment {
  workload: {
    candidate_trials: number;
    total_criteria: number;
    iterations: number;
  };
  variance_explanation: string;
  primary_query_count: PrimaryQueryCount;
  secondary_orm_observation: string;
  criteria_loading_latency_ms: LatencyComparison;
  local_pipeline_latency_ms: LatencyComparison;
}

export interface RealPostgresMeasurement {
  available: boolean;
  sequential_5_trials_mean_ms: number;
  batched_5_trials_mean_ms: number;
  real_db_reduction_ms: number;
  real_db_pct_improvement: number;
}

export interface VectorRetrievalScaling {
  corpus_size: number;
  latency_ms: number;
  search_type: string;
}

export interface CompletenessItem {
  benchmark: string;
  status: EvidenceType;
  scope: string;
}

export interface EvaluationPerformanceResponse {
  phase: string;
  optimization_id: string;
  title: string;
  frozen_phase14_1_reference: FrozenPhase14Ref;
  controlled_same_run_experiment: ControlledSameRunExperiment;
  real_postgresql_measurement: RealPostgresMeasurement;
  vector_retrieval_scaling: VectorRetrievalScaling[];
  completeness_matrix: CompletenessItem[];
  evidence_classification: Record<string, EvidenceType>;
  unmeasured_components: string[];
}

// ============================================================================
// Safety (Phase 12 & 9)
// ============================================================================

export interface SafetyAblationItem {
  ablation_id: string;
  name: string;
  baseline_experiment: string;
  treatment_experiment: string;
  changed_gate: string;
  primary_metric: string;
  baseline_value: number;
  treatment_value: number;
  delta: number;
  is_development_fixture_observation_only: boolean;
  clinical_claim_permitted: boolean;
  observation_summary: string;
}

export interface ErrorInjectionSummary {
  total_injections: number;
  prevented_count: number;
  prevention_rate: number;
  detected_count: number;
  detection_rate: number;
  mitigated_count: number;
  mitigation_rate: number;
  escalated_to_review_count: number;
  human_review_routing_rate: number;
  missed_count: number;
  missed_injection_rate: number;
  aggregate_interception_count: number;
  aggregate_interception_rate: number;
}

export interface SafetyPipelineSummary {
  s_e0_synthetic_unmitigated_unsafe_rate: number;
  s_e4_synthetic_safety_pipeline_unsafe_rate: number;
  s_e4_gate_pass_rate: number;
  s_e4_hr_routing_recall: number;
  s_e4_tenant_isolation_violation_rate: number;
  error_injection: ErrorInjectionSummary;
}

export interface ErrorScenarioItem {
  scenario_id: string;
  name: string;
  category: string;
  target_gate: string;
  detected: boolean;
  interception_mode: string;
  details: string;
}

export interface HumanReviewCategoryStat {
  category: string;
  case_count: number;
  expected_priority: string;
  machine_decision_allowed: boolean;
}

export interface UncertaintyAndReviewSummary {
  evidence_classification: EvidenceType;
  total_cases: number;
  routing_recall: number;
  categories: HumanReviewCategoryStat[];
  disclaimer: string;
}

export interface EvaluationSafetyResponse {
  phase: string;
  evidence_classification: EvidenceType;
  disclaimer: string;
  summary: SafetyPipelineSummary;
  safety_ablations: SafetyAblationItem[];
  error_scenarios: ErrorScenarioItem[];
  uncertainty_and_review: UncertaintyAndReviewSummary;
}

// ============================================================================
// Ablations & Experiments (Phase 11)
// ============================================================================

export interface ExperimentSpecification {
  experiment_id: string;
  description: string;
  patient_representation: string;
  retrieval_strategy: string;
  top_k: number;
  reasoning_mode: string;
}

export interface ExperimentItem {
  experiment_id: string;
  config: ExperimentSpecification;
  dataset_classification: string;
  sample_size: number;
  retrieval_metrics: Record<string, number>;
  eligibility_metrics: {
    accuracy?: number;
    macro_precision?: number;
    macro_recall?: number;
    macro_f1?: number;
    per_class_f1?: Record<string, number>;
    trial_count?: number;
    criterion_count?: number;
    criterion_accuracy?: number;
    criterion_macro_f1?: number;
  };
  grounding_metrics: Record<string, number>;
  uncertainty_metrics: Record<string, number>;
  explainability_metrics: Record<string, number>;
}

export interface AblationSpecification {
  ablation_id: string;
  name: string;
  hypothesis_tested: string;
  baseline_experiment: string;
  treatment_experiment: string;
  changed_component: string;
  unchanged_components: string[];
  primary_metrics: string[];
  sample_size: number;
  interpretation_constraints: string;
}

export interface AblationItem {
  ablation_id: string;
  specification: AblationSpecification;
  baseline_metrics: Record<string, number>;
  treatment_metrics: Record<string, number>;
  metric_deltas: Record<string, number>;
  sample_size: number;
  is_development_fixture_observation_only: boolean;
  empirical_superiority_claim_permitted: boolean;
  observation_summary: string;
}

export interface EvaluationAblationsResponse {
  phase: string;
  evidence_classification: EvidenceType;
  sample_size: number;
  disclaimer: string;
  verdict: string;
  experiments: ExperimentItem[];
  ablations: AblationItem[];
}

// ============================================================================
// Overview
// ============================================================================

export interface CoveragePhaseItem {
  phase_id: string;
  title: string;
  evidence_classification: EvidenceType;
  scope: string;
  key_metric: string;
}

export interface ExecutiveHighlight {
  title: string;
  value: string;
  unit: string;
  evidence_classification: EvidenceType;
  change_type: "positive" | "neutral" | "informative";
  description: string;
}

export interface EvaluationOverviewResponse {
  title: string;
  evaluation_coverage: CoveragePhaseItem[];
  highlights: ExecutiveHighlight[];
  evidence_classification_summary: Record<string, EvidenceType>;
  disclaimers: string[];
}
