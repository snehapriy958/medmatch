"""
Tests for Phase 11 Production Isolation & Empirical Benchmark Guardrails.
Phase 11: Evaluation & Ablation.
"""

import os
from pathlib import Path
from scripts.run_phase11_pipeline import audit_benchmarks


class TestPhase11Isolation:
    """Verifies that Phase 11 remains strictly isolated from production services."""

    def test_production_services_have_no_phase11_imports(self):
        services_dir = Path("services/ai-service")
        forbidden_terms = [
            "evaluation_schema",
            "dataset_validator_extended",
            "evaluation_metrics",
            "experiment_runner",
            "ablation_runner",
            "error_analyzer",
            "statistical_analyzer",
            "run_phase11_pipeline",
        ]

        for py_path in services_dir.rglob("*.py"):
            if ".venv" in py_path.parts:
                continue
            text = py_path.read_text(encoding="utf-8")
            for term in forbidden_terms:
                assert term not in text, f"Found forbidden import '{term}' in production file {py_path}"

    def test_benchmark_guardrail_prevents_generalizable_claims(self):
        records = audit_benchmarks(Path("data"))
        for rec in records:
            assert rec.can_support_generalizable_claims is False
            if rec.benchmark_name != "MedMatch Development Test Fixture":
                assert "NOT YET INGESTED" in rec.ingestion_status
