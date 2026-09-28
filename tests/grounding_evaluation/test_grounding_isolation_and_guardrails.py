"""
Tests for Grounding Isolation, Production Protection, and Benchmark Guardrails.
Phase 8: Grounding Evaluation & Faithfulness Auditing.
"""

import os
import subprocess
import pytest

from scripts.grounding_experiment import GroundingExperimentHarness
from scripts.nonrag_experiment import InformationLeakageError, NonRAGExperimentRunner


class TestGroundingIsolationAndGuardrails:
    """Verifies strict production isolation, anti-leakage guards, and benchmark guardrails."""

    def test_g1_nonrag_grounding_strictly_withholds_retrieval(self):
        """G1 evaluation executes without retrieval and has zero retrieval context."""
        harness = GroundingExperimentHarness()
        criteria = [{"id": "c1", "criteria_type": "INCLUSION", "description": "Metastatic NSCLC"}]
        facts = [
            {
                "fact_id": "f1",
                "concept": "metastatic NSCLC",
                "assertion": "PRESENT",
                "snippet": "metastatic NSCLC",
                "start_char": 0,
                "end_char": 16,
            }
        ]

        result = harness.run_g1_nonrag_grounding(
            trial_id="TRIAL-G1",
            criteria=criteria,
            patient_facts=facts,
            demographics={"age": 55},
        )

        assert result["condition"] == "G1_NONRAG"
        trial_eval = result["trial_evaluation"]
        assert trial_eval.total_criteria_evaluated == 1
        # In Non-RAG, no citation or record may have retrieval method
        for crit in trial_eval.criterion_evaluations:
            for cit in crit.evidence_citations:
                assert not cit.source_field.startswith("dense:")
                assert not cit.source_field.startswith("hybrid_rrf:")
                assert not cit.source_field.startswith("hybrid_reranked:")

    def test_g1_rejects_retrieval_leakage(self):
        """NonRAG runner in G1 raises InformationLeakageError if retrieval metadata is present."""
        runner = NonRAGExperimentRunner()
        leaky_input = {
            "retrieved_evidence": {"source": "dense", "score": 0.85},
            "criteria": [{"id": "c1", "description": "Age >= 18"}],
        }
        with pytest.raises(InformationLeakageError):
            runner.assert_no_retrieval_leakage(leaky_input)

    def test_benchmark_guardrail_prevents_unvalidated_claims(self):
        """Guardrail confirms external benchmark is not ingested."""
        harness = GroundingExperimentHarness()
        assert harness.check_research_benchmark_available(data_dir="data") is False

    def test_production_services_untouched_and_unimporting(self):
        """Zero Phase 8 modules are imported in services/ and services/ has zero git diff."""
        # 1. Check git diff on services/
        diff = subprocess.run(
            ["git", "diff", "--stat", "--", "services/"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert diff.stdout.strip() == "", f"Production files modified:\n{diff.stdout}"

        # 2. Check no imports of Phase 8 modules
        forbidden = [
            "grounding_schema",
            "claim_extractor",
            "grounding_validator",
            "grounding_metrics",
            "grounding_experiment",
        ]
        services_dir = os.path.join("services", "ai-service", "app")
        for root, _, files in os.walk(services_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        for term in forbidden:
                            assert term not in content, (
                                f"Production file '{full_path}' imports Phase 8 module '{term}'!"
                            )
