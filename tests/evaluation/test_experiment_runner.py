"""
Tests for Phase 11 Experiment Runner (E0–E4).
Phase 11: Evaluation & Ablation.
"""

import json
from pathlib import Path
from scripts.evaluation_schema import ExperimentType
from scripts.experiment_runner import Phase11ExperimentRunner


class TestExperimentRunner:
    """Verifies controlled execution of E0 through E4."""

    @classmethod
    def setup_class(cls):
        fixtures_dir = Path("data/fixtures")
        cls.patients = json.loads((fixtures_dir / "patients.json").read_text(encoding="utf-8"))
        cls.trials = json.loads((fixtures_dir / "trials.json").read_text(encoding="utf-8"))
        cls.criteria = json.loads((fixtures_dir / "criteria.json").read_text(encoding="utf-8"))
        cls.trial_labels = json.loads((fixtures_dir / "trial_labels.json").read_text(encoding="utf-8"))
        cls.crit_labels = json.loads((fixtures_dir / "criterion_labels.json").read_text(encoding="utf-8"))
        cls.runner = Phase11ExperimentRunner()

    def test_run_e0_baseline(self):
        res = self.runner.run_experiment(
            exp_type=ExperimentType.E0_BASELINE,
            patients_data=self.patients,
            trials_data=self.trials,
            criteria_data=self.criteria,
            trial_labels_data=self.trial_labels,
            criterion_labels_data=self.crit_labels,
        )
        assert res.experiment_id == "E0_BASELINE"
        assert res.sample_size == 6
        assert res.is_development_fixture_observation_only is True
        assert res.empirical_claim_permitted is False
        assert res.eligibility_metrics.trial_count == 6
        assert len(res.evaluated_cases) == 6

    def test_run_e1_structured_profile(self):
        res = self.runner.run_experiment(
            exp_type=ExperimentType.E1_STRUCTURED_PROFILE,
            patients_data=self.patients,
            trials_data=self.trials,
            criteria_data=self.criteria,
            trial_labels_data=self.trial_labels,
            criterion_labels_data=self.crit_labels,
        )
        assert res.experiment_id == "E1_STRUCTURED_PROFILE"
        assert res.config.patient_representation == "structured_profile"
        assert res.sample_size == 6

    def test_run_e2_dense_rag(self):
        res = self.runner.run_experiment(
            exp_type=ExperimentType.E2_DENSE_RAG,
            patients_data=self.patients,
            trials_data=self.trials,
            criteria_data=self.criteria,
            trial_labels_data=self.trial_labels,
            criterion_labels_data=self.crit_labels,
        )
        assert res.experiment_id == "E2_DENSE_RAG"
        assert res.config.retrieval_strategy == "dense"
        assert res.retrieval_metrics is not None

    def test_run_e3_hybrid_rag(self):
        res = self.runner.run_experiment(
            exp_type=ExperimentType.E3_HYBRID_RAG,
            patients_data=self.patients,
            trials_data=self.trials,
            criteria_data=self.criteria,
            trial_labels_data=self.trial_labels,
            criterion_labels_data=self.crit_labels,
        )
        assert res.experiment_id == "E3_HYBRID_RAG"
        assert res.config.retrieval_strategy == "hybrid_rrf"
        assert res.retrieval_metrics is not None

    def test_run_e4_reranked_rag(self):
        res = self.runner.run_experiment(
            exp_type=ExperimentType.E4_RERANKED_RAG,
            patients_data=self.patients,
            trials_data=self.trials,
            criteria_data=self.criteria,
            trial_labels_data=self.trial_labels,
            criterion_labels_data=self.crit_labels,
        )
        assert res.experiment_id == "E4_RERANKED_RAG"
        assert res.config.retrieval_strategy == "hybrid_reranked"
        assert res.retrieval_metrics is not None
