"""
Tests for Phase 11 Ablation Runner (A1–A5).
Phase 11: Evaluation & Ablation.
"""

import json
from pathlib import Path
from scripts.ablation_runner import AblationRunner
from scripts.evaluation_schema import ExperimentType
from scripts.experiment_runner import Phase11ExperimentRunner


class TestAblationRunner:
    """Verifies controlled ablation execution and guardrail adherence."""

    @classmethod
    def setup_class(cls):
        fixtures_dir = Path("data/fixtures")
        patients = json.loads((fixtures_dir / "patients.json").read_text(encoding="utf-8"))
        trials = json.loads((fixtures_dir / "trials.json").read_text(encoding="utf-8"))
        criteria = json.loads((fixtures_dir / "criteria.json").read_text(encoding="utf-8"))
        trial_labels = json.loads((fixtures_dir / "trial_labels.json").read_text(encoding="utf-8"))
        crit_labels = json.loads((fixtures_dir / "criterion_labels.json").read_text(encoding="utf-8"))

        runner = Phase11ExperimentRunner()
        cls.exp_results = {}
        for et in [
            ExperimentType.E0_BASELINE,
            ExperimentType.E1_STRUCTURED_PROFILE,
            ExperimentType.E2_DENSE_RAG,
            ExperimentType.E3_HYBRID_RAG,
            ExperimentType.E4_RERANKED_RAG,
        ]:
            cls.exp_results[et.value] = runner.run_experiment(
                exp_type=et,
                patients_data=patients,
                trials_data=trials,
                criteria_data=criteria,
                trial_labels_data=trial_labels,
                criterion_labels_data=crit_labels,
            )

    def test_all_five_ablations_executed(self):
        ablations = AblationRunner.run_ablations(self.exp_results)
        assert len(ablations) == 5
        ab_ids = [a.ablation_id for a in ablations]
        assert ab_ids == ["A1", "A2", "A3", "A4", "A5"]

    def test_ablation_guardrails_enforced(self):
        ablations = AblationRunner.run_ablations(self.exp_results)
        for ab in ablations:
            assert ab.is_development_fixture_observation_only is True
            assert ab.empirical_superiority_claim_permitted is False
            assert "DEVELOPMENT FIXTURE OBSERVATION ONLY" in ab.observation_summary
            assert len(ab.specification.unchanged_components) >= 3
            assert ab.sample_size == 6
