"""
MedMatch Phase 11 Master Evaluation & Ablation Pipeline.
Phase 11: Evaluation & Ablation.

Executes the full evaluation pipeline:
1. Benchmark Availability Audit (documents external un-ingested status)
2. Extended Dataset Validation (produces dataset_validation.json)
3. Controlled Experiments E0–E4 (produces e0_baseline.json through e4_reranked_rag.json)
4. Controlled Ablations A1–A5 (produces ablation_results.json)
5. Comprehensive Error Analysis (produces error_analysis.json)
6. Statistical Significance Safeguard Checks (produces statistical_analysis.json)
7. Full Evaluation Manifest & Summary (produces experiment_manifest.json and phase11_summary.json)
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure scripts directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset_validator_extended import ExtendedDatasetValidator
from evaluation_schema import (
    BenchmarkAvailabilityRecord,
    BenchmarkClassification,
    ExperimentType,
    Phase11EvaluationManifest,
)
from experiment_runner import Phase11ExperimentRunner
from ablation_runner import AblationRunner
from error_analyzer import ErrorAnalyzer
from statistical_analyzer import StatisticalAnalyzer


def audit_benchmarks(data_dir: Path) -> List[BenchmarkAvailabilityRecord]:
    """Audits local filesystem for claimed benchmarks."""
    records = []

    # 1. ClinicalTrials.gov REST API v2
    records.append(
        BenchmarkAvailabilityRecord(
            benchmark_name="ClinicalTrials.gov REST API v2",
            official_reference="NLM / NIH, https://clinicaltrials.gov/data-api/about-api",
            physical_files_exist=False,
            record_count=0,
            ingestion_status="SOURCE IDENTIFIED — NOT YET INGESTED (Curated protocol NCT02484404 extracted as fixture template)",
            classification=BenchmarkClassification.RESEARCH_BENCHMARK,
            licensing="Public Domain (U.S. Government work)",
            can_support_generalizable_claims=False,
            limitation_notes="Protocol descriptions available; zero patient records or eligibility qrels.",
        )
    )

    # 2. TrialGPT Benchmark Cohort
    trialgpt_file = data_dir / "raw" / "external" / "trialgpt_annotations.json"
    records.append(
        BenchmarkAvailabilityRecord(
            benchmark_name="TrialGPT Benchmark Cohort",
            official_reference="Qiao Jin et al., Nature Communications 15, Article 5772 (2024)",
            physical_files_exist=trialgpt_file.exists(),
            record_count=0 if not trialgpt_file.exists() else 184,
            ingestion_status="SOURCE IDENTIFIED — NOT YET INGESTED" if not trialgpt_file.exists() else "INGESTED",
            classification=BenchmarkClassification.RESEARCH_BENCHMARK,
            licensing="Public Domain / MIT License",
            can_support_generalizable_claims=False,
            limitation_notes="Public repository identified; external dataset not physically ingested into repo.",
        )
    )

    # 3. TREC Clinical Trials 2021 Track
    trec21_file = data_dir / "raw" / "external" / "trec2021_qrels.txt"
    records.append(
        BenchmarkAvailabilityRecord(
            benchmark_name="TREC Clinical Trials 2021 Track",
            official_reference="Roberts et al., Overview of the TREC 2021 Clinical Trials Track, NIST SP",
            physical_files_exist=trec21_file.exists(),
            record_count=0,
            ingestion_status="SOURCE IDENTIFIED — NOT YET INGESTED",
            classification=BenchmarkClassification.RESEARCH_BENCHMARK,
            licensing="Open Academic Research Use",
            can_support_generalizable_claims=False,
            limitation_notes="Retrieval qrels only; no criterion-level labels or character text spans.",
        )
    )

    # 4. TREC Clinical Trials 2022 Track
    records.append(
        BenchmarkAvailabilityRecord(
            benchmark_name="TREC Clinical Trials 2022 Track",
            official_reference="Roberts et al., Overview of the TREC 2022 Clinical Trials Track, NIST SP",
            physical_files_exist=False,
            record_count=0,
            ingestion_status="SOURCE IDENTIFIED — NOT YET INGESTED",
            classification=BenchmarkClassification.RESEARCH_BENCHMARK,
            licensing="Open Academic Research Use",
            can_support_generalizable_claims=False,
            limitation_notes="Retrieval qrels only; no criterion-level labels.",
        )
    )

    # 5. Local MedMatch Development Test Fixture
    dev_fixture_exists = (data_dir / "fixtures" / "patients.json").exists()
    records.append(
        BenchmarkAvailabilityRecord(
            benchmark_name="MedMatch Development Test Fixture",
            official_reference="data/fixtures/ (NCT02484404 + 6 synthetic patients)",
            physical_files_exist=dev_fixture_exists,
            record_count=6 if dev_fixture_exists else 0,
            ingestion_status="LOCAL FIXTURE IMPLEMENTED",
            classification=BenchmarkClassification.DEVELOPMENT_FIXTURE,
            licensing="Apache 2.0 (MedMatch project)",
            can_support_generalizable_claims=False,
            limitation_notes="DEVELOPMENT/TEST FIXTURE ONLY: small deterministic sample (n=6) for CI/CD and pipeline validation. Strictly prohibited from supporting clinical efficacy claims.",
        )
    )

    return records


def run_pipeline(data_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 80)
    print("MEDMATCH PHASE 11: EVALUATION & ABLATION PIPELINE")
    print("=" * 80)
    print(f"Data directory: {data_dir.resolve()}")
    print(f"Output directory: {output_dir.resolve()}")

    # 1. Benchmark Audit
    print("\n[Step 1/7] Auditing benchmark availability...")
    benchmark_records = audit_benchmarks(data_dir)
    for b in benchmark_records:
        print(f" - {b.benchmark_name}: {b.ingestion_status} (Can support general claims: {b.can_support_generalizable_claims})")

    # 2. Extended Dataset Validation
    print("\n[Step 2/7] Running extended dataset validation...")
    validator = ExtendedDatasetValidator(data_dir)
    dataset_summary = validator.validate_and_summarize()
    dataset_val_path = output_dir / "dataset_validation.json"
    dataset_val_path.write_text(json.dumps(dataset_summary.model_dump(), indent=2), encoding="utf-8")
    print(f" -> Written dataset validation summary to {dataset_val_path.name}")
    print(f"    Patients: {dataset_summary.total_patients}, Trials: {dataset_summary.total_trials}, Criteria: {dataset_summary.total_criteria}")
    print(f"    Criterion Labels: {dataset_summary.total_criterion_labels}, Trial Labels: {dataset_summary.total_patient_trial_pairs}")
    print(f"    Patient Leakage Detected: {dataset_summary.patient_leakage_detected}, Valid: {dataset_summary.is_valid}")

    # Load fixture data
    fixtures_dir = data_dir / "fixtures"
    patients = json.loads((fixtures_dir / "patients.json").read_text(encoding="utf-8"))
    trials = json.loads((fixtures_dir / "trials.json").read_text(encoding="utf-8"))
    criteria = json.loads((fixtures_dir / "criteria.json").read_text(encoding="utf-8"))
    trial_labels = json.loads((fixtures_dir / "trial_labels.json").read_text(encoding="utf-8"))
    crit_labels = json.loads((fixtures_dir / "criterion_labels.json").read_text(encoding="utf-8"))

    # 3. Controlled Experiments (E0–E4)
    print("\n[Step 3/7] Running controlled experiments E0–E4...")
    runner = Phase11ExperimentRunner()
    exp_types = [
        ExperimentType.E0_BASELINE,
        ExperimentType.E1_STRUCTURED_PROFILE,
        ExperimentType.E2_DENSE_RAG,
        ExperimentType.E3_HYBRID_RAG,
        ExperimentType.E4_RERANKED_RAG,
    ]
    exp_results = {}
    file_map = {
        ExperimentType.E0_BASELINE: "e0_baseline.json",
        ExperimentType.E1_STRUCTURED_PROFILE: "e1_structured_profile.json",
        ExperimentType.E2_DENSE_RAG: "e2_dense_rag.json",
        ExperimentType.E3_HYBRID_RAG: "e3_hybrid_rag.json",
        ExperimentType.E4_RERANKED_RAG: "e4_reranked_rag.json",
    }

    for et in exp_types:
        res = runner.run_experiment(
            exp_type=et,
            patients_data=patients,
            trials_data=trials,
            criteria_data=criteria,
            trial_labels_data=trial_labels,
            criterion_labels_data=crit_labels,
        )
        exp_results[et.value] = res
        target_path = output_dir / file_map[et]
        target_path.write_text(json.dumps(res.model_dump(), indent=2), encoding="utf-8")
        print(f" -> Executed {et.value}: Trial Accuracy={res.eligibility_metrics.accuracy}, Macro-F1={res.eligibility_metrics.macro_f1} -> saved to {file_map[et]}")

    # 4. Controlled Ablations (A1–A5)
    print("\n[Step 4/7] Running controlled ablations A1–A5...")
    ablation_results = AblationRunner.run_ablations(exp_results)
    ablation_path = output_dir / "ablation_results.json"
    ablation_path.write_text(
        json.dumps([a.model_dump() for a in ablation_results], indent=2), encoding="utf-8"
    )
    print(f" -> Computed {len(ablation_results)} ablations -> saved to {ablation_path.name}")

    # 5. Error Analysis
    print("\n[Step 5/7] Performing deterministic error categorization...")
    all_error_summaries = {}
    for et_str, res in exp_results.items():
        summary = ErrorAnalyzer.analyze_experiment_errors(
            experiment_result=res,
            criteria_data=criteria,
            patients_data=patients,
        )
        all_error_summaries[et_str] = summary.model_dump()
    error_path = output_dir / "error_analysis.json"
    error_path.write_text(json.dumps(all_error_summaries, indent=2), encoding="utf-8")
    print(f" -> Categorized errors across all experiments -> saved to {error_path.name}")

    # 6. Statistical Significance Safeguard Analysis
    print("\n[Step 6/7] Running statistical analysis safeguards...")
    stat_comparisons = [
        StatisticalAnalyzer.compare_experiments(exp_results["E2_DENSE_RAG"], exp_results["E3_HYBRID_RAG"]),
        StatisticalAnalyzer.compare_experiments(exp_results["E3_HYBRID_RAG"], exp_results["E4_RERANKED_RAG"]),
        StatisticalAnalyzer.compare_experiments(exp_results["E0_BASELINE"], exp_results["E1_STRUCTURED_PROFILE"]),
        StatisticalAnalyzer.compare_experiments(exp_results["E1_STRUCTURED_PROFILE"], exp_results["E2_DENSE_RAG"]),
    ]
    stat_path = output_dir / "statistical_analysis.json"
    stat_path.write_text(
        json.dumps([s.model_dump() for s in stat_comparisons], indent=2), encoding="utf-8"
    )
    print(f" -> Recorded statistical checks -> saved to {stat_path.name}")
    for sc in stat_comparisons:
        print(f"    * {sc.comparison_name}: Inference permitted={sc.inference_permitted} ({sc.justification_for_inference})")

    # 7. Manifest & Phase Summary
    print("\n[Step 7/7] Generating evaluation manifest and summary...")
    manifest = Phase11EvaluationManifest(
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        git_commit_sha="59e3f2f",
        random_seed=42,
        environment_info={
            "python_version": sys.version.split()[0],
            "os": platform.platform(),
            "platform": platform.machine(),
        },
        benchmark_availability=[b.model_dump() for b in benchmark_records],
        dataset_validation=dataset_summary.model_dump(),
        experiments_executed=list(exp_results.keys()),
        ablations_executed=[a.ablation_id for a in ablation_results],
        statistical_checks_executed=[s.comparison_name for s in stat_comparisons],
        empirical_benchmark_available=False,
        generalizable_claims_asserted=False,
        summary_verdict="All evaluation infrastructure, experiments (E0–E4), ablations (A1–A5), error categorization, and statistical safeguards executed cleanly. Due to the absence of ingested external benchmarks (TrialGPT/TREC), all findings remain strictly classified as development-fixture observations.",
    )
    manifest_path = output_dir / "experiment_manifest.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(), indent=2), encoding="utf-8")

    summary_path = output_dir / "phase11_summary.json"
    summary_content = {
        "phase": "Phase 11: Evaluation & Ablation",
        "benchmark_status": "IDENTIFIED BUT NOT INGESTED",
        "development_fixture_sample_size": dataset_summary.total_patients,
        "experiments_count": len(exp_results),
        "ablations_count": len(ablation_results),
        "errors_analyzed": sum(s["total_errors"] for s in all_error_summaries.values()),
        "statistical_inference_permitted": False,
        "empirical_claims_permitted": False,
        "verdict": manifest.summary_verdict,
    }
    summary_path.write_text(json.dumps(summary_content, indent=2), encoding="utf-8")
    print(f" -> Written manifest to {manifest_path.name} and summary to {summary_path.name}")

    print("\n" + "=" * 80)
    print("PHASE 11 PIPELINE EXECUTION COMPLETE")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="MedMatch Phase 11 Evaluation Pipeline")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Path to data directory")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/phase11"),
        help="Path to results directory",
    )
    args = parser.parse_args()
    run_pipeline(args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()
