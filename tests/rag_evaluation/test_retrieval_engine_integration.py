"""
MedMatch Phase 7: Comprehensive Phase 5 Retrieval Engine Integration Tests.

Validates the 15 required integration checkpoints:
1. E6 invokes actual DenseRetriever
2. E7 invokes actual HybridRRFRetriever
3. E8 invokes actual RerankingRetriever if implemented
4. E5 never invokes retrieval
5. E5 receives no retrieval output
6. E6 receives actual DenseRetriever output
7. E7 receives actual HybridRRFRetriever output
8. retrieval provenance survives into RAG evidence citations
9. same patient/criterion input is used across conditions
10. Phase 6 reasoner is identical across conditions
11. Phase 6 aggregator is identical across conditions
12. Phase 6 validator is identical across conditions
13. deterministic execution remains deterministic
14. benchmark guardrail still prevents empirical results without research benchmark
15. production services remain untouched
"""

import os
import subprocess
import pytest
from unittest.mock import MagicMock, patch

from scripts.eligibility_aggregator import EligibilityAggregator
from scripts.eligibility_reasoner import RuleBasedEligibilityReasoner
from scripts.eligibility_schema import (
    CriterionEvaluationStatus,
    TrialEligibilityEvaluation,
    TrialEligibilityStatus,
)
from scripts.nonrag_experiment import InformationLeakageError, NonRAGExperimentRunner
from scripts.rag_experiment import RAGExperimentRunner
from scripts.retrieval_engine import (
    BaseRetriever,
    ClinicalOverlapReranker,
    DenseRetriever,
    HybridRRFRetriever,
    LexicalBM25Retriever,
    RerankingRetriever,
)
from scripts.retrieval_schema import (
    CandidateTrialRecord,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
)
from scripts.run_phase7_experiment import Phase7ExperimentHarness
from scripts.validate_eligibility import EligibilityValidator


@pytest.fixture
def sample_candidates():
    """Provides representative candidate trials for retrieval testing."""
    return [
        CandidateTrialRecord(
            trial_id="NCT001",
            title="Phase 3 Study of Osimertinib in EGFR-Mutated NSCLC",
            condition="Non-Small Cell Lung Cancer",
            phase="Phase 3",
            brief_summary="Evaluating osimertinib in patients with locally advanced or metastatic EGFR T790M NSCLC.",
            criteria=[
                {
                    "id": "c1",
                    "criteria_type": "INCLUSION",
                    "description": "Histologically confirmed metastatic non-small cell lung cancer",
                },
                {
                    "id": "c2",
                    "criteria_type": "INCLUSION",
                    "description": "Documented EGFR T790M mutation",
                },
            ],
            embedding=[0.1] * 384,
        ),
        CandidateTrialRecord(
            trial_id="NCT002",
            title="Pembrolizumab in Advanced Melanoma",
            condition="Melanoma",
            phase="Phase 2",
            brief_summary="Study of pembrolizumab monotherapy in patients with unresectable stage IV melanoma.",
            criteria=[
                {
                    "id": "c3",
                    "criteria_type": "INCLUSION",
                    "description": "Unresectable stage IV metastatic melanoma",
                }
            ],
            embedding=[0.0] * 384,
        ),
    ]


@pytest.fixture
def sample_patient_facts():
    return [
        {
            "fact_id": "f_nsclc_01",
            "concept": "non-small cell lung cancer",
            "assertion": "PRESENT",
            "snippet": "Patient has stage IV metastatic non-small cell lung cancer",
            "start_char": 10,
            "end_char": 66,
        },
        {
            "fact_id": "f_egfr_02",
            "concept": "EGFR T790M mutation",
            "assertion": "PRESENT",
            "snippet": "Molecular testing shows EGFR T790M positive",
            "start_char": 80,
            "end_char": 123,
        },
    ]


class TestPhase5RetrievalEngineIntegration:
    """Rigorous verification of Phase 5 retrieval integration into Phase 7."""

    def test_1_e6_invokes_actual_dense_retriever(self, sample_candidates):
        """1. E6 invokes actual DenseRetriever."""
        runner = RAGExperimentRunner.create_dense_rag(embed_fn=lambda q: [0.1] * 384)
        assert isinstance(runner.retriever, DenseRetriever)
        assert runner.experiment_strategy == "E6_DENSE"

        with patch.object(runner.retriever, "retrieve", wraps=runner.retriever.retrieve) as spy_retrieve:
            resp = runner.execute_retrieval(
                query_text="NSCLC EGFR",
                candidate_pool=sample_candidates,
                top_k=2,
            )
            assert spy_retrieve.call_count == 1
            call_args = spy_retrieve.call_args
            req = call_args[1]["request"] if "request" in call_args[1] else call_args[0][0]
            assert isinstance(req, RetrievalRequest)
            assert req.query_text == "NSCLC EGFR"
            assert isinstance(resp, RetrievalResponse)
            assert resp.results[0].retrieval_method == "dense"

    def test_2_e7_invokes_actual_hybrid_rrf_retriever(self, sample_candidates):
        """2. E7 invokes actual HybridRRFRetriever."""
        runner = RAGExperimentRunner.create_hybrid_rag(embed_fn=lambda q: [0.1] * 384)
        assert isinstance(runner.retriever, HybridRRFRetriever)
        assert isinstance(runner.retriever.dense_retriever, DenseRetriever)
        assert isinstance(runner.retriever.lexical_retriever, LexicalBM25Retriever)
        assert runner.experiment_strategy == "E7_HYBRID"

        with patch.object(runner.retriever, "retrieve", wraps=runner.retriever.retrieve) as spy_retrieve:
            resp = runner.execute_retrieval(
                query_text="osimertinib EGFR lung",
                candidate_pool=sample_candidates,
                top_k=2,
            )
            assert spy_retrieve.call_count == 1
            assert isinstance(resp, RetrievalResponse)
            assert resp.retrieval_strategy == RetrievalStrategy.HYBRID_RRF
            assert resp.results[0].retrieval_method == "hybrid_rrf"

    def test_3_e8_invokes_actual_reranking_retriever(self, sample_candidates):
        """3. E8 invokes actual RerankingRetriever."""
        runner = RAGExperimentRunner.create_reranked_rag(embed_fn=lambda q: [0.1] * 384)
        assert isinstance(runner.retriever, RerankingRetriever)
        assert isinstance(runner.retriever.reranker, ClinicalOverlapReranker)
        assert runner.experiment_strategy == "E8_RERANKED"

        with patch.object(runner.retriever, "retrieve", wraps=runner.retriever.retrieve) as spy_retrieve:
            resp = runner.execute_retrieval(
                query_text="osimertinib EGFR mutation",
                candidate_pool=sample_candidates,
                top_k=2,
            )
            assert spy_retrieve.call_count == 1
            assert isinstance(resp, RetrievalResponse)
            assert resp.retrieval_strategy == RetrievalStrategy.HYBRID_RERANKED
            assert resp.results[0].retrieval_method == "hybrid_reranked"
            assert "rerank_score" in resp.results[0].metadata

    def test_4_e5_never_invokes_retrieval(self, sample_patient_facts):
        """4. E5 never invokes retrieval."""
        nonrag = NonRAGExperimentRunner()
        assert not hasattr(nonrag, "retriever")
        criteria = [{"id": "c1", "criteria_type": "INCLUSION", "description": "Metastatic melanoma"}]

        # Ensure no BaseRetriever instance or subclass is called during E5 evaluation
        with patch.object(BaseRetriever, "retrieve", autospec=True) as mock_retrieve:
            eval_res = nonrag.evaluate_trial(
                trial_id="TRIAL-TEST",
                criteria=criteria,
                patient_facts=sample_patient_facts,
            )
            assert mock_retrieve.call_count == 0
            assert isinstance(eval_res, TrialEligibilityEvaluation)

    def test_5_e5_receives_no_retrieval_output(self):
        """5. E5 receives no retrieval output."""
        nonrag = NonRAGExperimentRunner()
        leaky_input = {
            "retrieved_evidence": {"source": "dense_retrieval", "score": 0.99},
            "criteria": [{"id": "c1", "description": "Age >= 18"}],
        }
        with pytest.raises(InformationLeakageError) as exc_info:
            nonrag.assert_no_retrieval_leakage(leaky_input)
        assert "retrieved_evidence" in str(exc_info.value)

        # Confirm evaluation outputs have no retrieval fields
        clean_eval = nonrag.evaluate_trial(
            trial_id="TRIAL-CLEAN",
            criteria=[{"id": "c1", "criteria_type": "INCLUSION", "description": "Age >= 18"}],
            patient_facts=[],
            demographics={"age": 25},
        )
        for c in clean_eval.criterion_evaluations:
            assert c.trial_criterion_reference is None
            for cit in c.evidence_citations:
                assert not cit.source_field.startswith("dense:")
                assert not cit.source_field.startswith("hybrid_rrf:")
                assert not cit.source_field.startswith("hybrid_reranked:")

    def test_6_e6_receives_actual_dense_retriever_output(self, sample_candidates, sample_patient_facts):
        """6. E6 receives actual DenseRetriever output."""
        runner = RAGExperimentRunner.create_dense_rag(embed_fn=lambda q: [0.1] * 384)
        evals = runner.evaluate_candidate_pool(
            query_text="Osimertinib EGFR NSCLC",
            candidate_pool=sample_candidates,
            patient_facts=sample_patient_facts,
            top_k=2,
        )
        assert len(evals) == 2
        assert runner.last_retrieval_response is not None
        assert runner.last_retrieval_response.results[0].retrieval_method == "dense"
        assert evals[0].trial_id == "NCT001"

    def test_7_e7_receives_actual_hybrid_rrf_retriever_output(self, sample_candidates, sample_patient_facts):
        """7. E7 receives actual HybridRRFRetriever output."""
        runner = RAGExperimentRunner.create_hybrid_rag(embed_fn=lambda q: [0.1] * 384)
        evals = runner.evaluate_candidate_pool(
            query_text="osimertinib EGFR lung",
            candidate_pool=sample_candidates,
            patient_facts=sample_patient_facts,
            top_k=2,
        )
        assert len(evals) == 2
        assert runner.last_retrieval_response is not None
        assert runner.last_retrieval_response.results[0].retrieval_method == "hybrid_rrf"
        assert "rrf_score" in runner.last_retrieval_response.results[0].metadata

    def test_8_retrieval_provenance_survives_into_rag_evidence_citations(
        self, sample_candidates, sample_patient_facts
    ):
        """8. Retrieval provenance survives into RAG evidence citations."""
        runner = RAGExperimentRunner.create_dense_rag(embed_fn=lambda q: [0.1] * 384)
        evals = runner.evaluate_candidate_pool(
            query_text="Osimertinib EGFR NSCLC",
            candidate_pool=sample_candidates,
            patient_facts=sample_patient_facts,
            top_k=1,
        )
        nct001_eval = evals[0]
        assert nct001_eval.trial_id == "NCT001"
        assert nct001_eval.passed_count >= 1

        passed_crit = [c for c in nct001_eval.criterion_evaluations if c.status == CriterionEvaluationStatus.PASS][0]
        assert len(passed_crit.evidence_citations) > 0
        citation = passed_crit.evidence_citations[0]
        # Provenance contains retrieval method and trial reference
        assert "dense:trial:NCT001" in citation.source_field
        assert passed_crit.trial_criterion_reference == "trial:NCT001"
        assert citation.start_char != -999  # Valid offset or -1 convention

    def test_9_same_patient_criterion_input_is_used_across_conditions(self, sample_patient_facts):
        """9. Same patient/criterion input is used across conditions."""
        criteria = [{"id": "c1", "criteria_type": "INCLUSION", "description": "Metastatic melanoma"}]
        harness = Phase7ExperimentHarness()

        comparison = harness.run_case_comparison(
            trial_id="TRIAL-COMP-01",
            criteria=criteria,
            patient_facts=sample_patient_facts,
            retrieved_evidence={"trial_summary": "Melanoma trial summary", "retrieval_method": "dense"},
        )
        nonrag_eval = comparison["nonrag_evaluation"]
        rag_eval = comparison["rag_evaluation"]

        assert nonrag_eval.trial_id == rag_eval.trial_id == "TRIAL-COMP-01"
        assert nonrag_eval.total_criteria_evaluated == rag_eval.total_criteria_evaluated == 1
        assert nonrag_eval.criterion_evaluations[0].criterion_id == rag_eval.criterion_evaluations[0].criterion_id == "c1"
        assert nonrag_eval.criterion_evaluations[0].criterion_text == rag_eval.criterion_evaluations[0].criterion_text

    def test_10_phase6_reasoner_is_identical_across_conditions(self):
        """10. Phase 6 reasoner is identical across conditions."""
        nonrag = NonRAGExperimentRunner()
        rag = RAGExperimentRunner.create_dense_rag()
        assert isinstance(nonrag.reasoner, RuleBasedEligibilityReasoner)
        assert isinstance(rag.reasoner, RuleBasedEligibilityReasoner)
        assert type(nonrag.reasoner) is type(rag.reasoner)

    def test_11_phase6_aggregator_is_identical_across_conditions(self):
        """11. Phase 6 aggregator is identical across conditions."""
        nonrag = NonRAGExperimentRunner()
        rag = RAGExperimentRunner.create_dense_rag()
        assert isinstance(nonrag.aggregator, EligibilityAggregator)
        assert isinstance(rag.aggregator, EligibilityAggregator)
        assert type(nonrag.aggregator) is type(rag.aggregator)

    def test_12_phase6_validator_is_identical_across_conditions(self):
        """12. Phase 6 validator is identical across conditions."""
        nonrag = NonRAGExperimentRunner()
        rag = RAGExperimentRunner.create_dense_rag()
        assert isinstance(nonrag.validator, EligibilityValidator)
        assert isinstance(rag.validator, EligibilityValidator)
        assert type(nonrag.validator) is type(rag.validator)

    def test_13_deterministic_execution_remains_deterministic(
        self, sample_candidates, sample_patient_facts
    ):
        """13. Deterministic execution remains deterministic across runs."""
        harness = Phase7ExperimentHarness()
        run1 = harness.run_corpus_retrieval_comparison(
            query_text="EGFR NSCLC lung cancer",
            candidate_pool=sample_candidates,
            patient_facts=sample_patient_facts,
            top_k=2,
            embed_fn=lambda q: [0.1] * 384,
        )
        run2 = harness.run_corpus_retrieval_comparison(
            query_text="EGFR NSCLC lung cancer",
            candidate_pool=sample_candidates,
            patient_facts=sample_patient_facts,
            top_k=2,
            embed_fn=lambda q: [0.1] * 384,
        )

        assert len(run1["e6_dense_evaluations"]) == len(run2["e6_dense_evaluations"])
        assert len(run1["e7_hybrid_evaluations"]) == len(run2["e7_hybrid_evaluations"])
        assert len(run1["e8_reranked_evaluations"]) == len(run2["e8_reranked_evaluations"])

        for e1, e2 in zip(run1["e6_dense_evaluations"], run2["e6_dense_evaluations"]):
            assert e1.trial_id == e2.trial_id
            assert e1.status == e2.status
            assert e1.passed_count == e2.passed_count

    def test_14_benchmark_guardrail_still_prevents_empirical_results_without_research_benchmark(self):
        """14. Benchmark guardrail prevents empirical results without research benchmark."""
        harness = Phase7ExperimentHarness()
        # Verify guardrail returns False when raw research benchmark is un-ingested
        assert harness.check_research_benchmark_available(data_dir="data") is False

    def test_15_production_services_remain_untouched(self):
        """15. Production services remain untouched and contain no Phase 7 imports."""
        # 1. Check services directory has no git modifications
        git_diff = subprocess.run(
            ["git", "diff", "--stat", "services/"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert git_diff.stdout.strip() == "", f"Production files modified:\n{git_diff.stdout}"

        # 2. Check no production files import Phase 7 experiment modules
        forbidden = ["rag_experiment", "nonrag_experiment", "run_phase7_experiment"]
        services_dir = os.path.join("services", "ai-service", "app")
        for root, _, files in os.walk(services_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        for term in forbidden:
                            assert term not in content, (
                                f"Production file '{full_path}' contains forbidden import '{term}'!"
                            )
