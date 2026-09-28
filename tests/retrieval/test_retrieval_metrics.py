"""
Tests for Information Retrieval Evaluation Metrics.
Phase 5: Retrieval Engine.
"""

import pytest
from scripts.retrieval_evaluation import (
    dcg_at_k,
    evaluate_retrieval_benchmark,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestRetrievalMetrics:
    """Test suite for deterministic retrieval metrics: P@K, R@K, MRR, nDCG@K."""

    def test_precision_at_k_toy_example(self):
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc3", "doc9"}

        # Top 1: doc1 is relevant -> 1/1 = 1.0
        assert precision_at_k(retrieved, relevant, k=1) == 1.0
        # Top 3: doc1 and doc3 are relevant -> 2/3 ≈ 0.6667
        assert pytest.approx(precision_at_k(retrieved, relevant, k=3), 1e-4) == 2.0 / 3.0
        # Top 5: doc1 and doc3 are relevant -> 2/5 = 0.4
        assert precision_at_k(retrieved, relevant, k=5) == 0.4

    def test_recall_at_k_toy_example(self):
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc3", "doc9"}  # Total relevant = 3

        # Top 1: doc1 -> 1/3 ≈ 0.3333
        assert pytest.approx(recall_at_k(retrieved, relevant, k=1), 1e-4) == 1.0 / 3.0
        # Top 3: doc1, doc3 -> 2/3 ≈ 0.6667
        assert pytest.approx(recall_at_k(retrieved, relevant, k=3), 1e-4) == 2.0 / 3.0
        # Top 5: doc1, doc3 -> 2/3 (doc9 was never retrieved)
        assert pytest.approx(recall_at_k(retrieved, relevant, k=5), 1e-4) == 2.0 / 3.0

    def test_reciprocal_rank(self):
        relevant = {"doc_gold"}
        # Found at rank 1 -> 1/1 = 1.0
        assert reciprocal_rank(["doc_gold", "doc2"], relevant) == 1.0
        # Found at rank 2 -> 1/2 = 0.5
        assert reciprocal_rank(["doc1", "doc_gold"], relevant) == 0.5
        # Found at rank 4 -> 1/4 = 0.25
        assert reciprocal_rank(["doc1", "doc2", "doc3", "doc_gold"], relevant) == 0.25
        # Not found -> 0.0
        assert reciprocal_rank(["doc1", "doc2"], relevant) == 0.0

    def test_ndcg_at_k_graded_relevance(self):
        # Graded relevance: doc1=3, doc2=2, doc3=1, doc4=0
        qrels = {"doc1": 3.0, "doc2": 2.0, "doc3": 1.0, "doc4": 0.0}

        # Perfect ranking: ["doc1", "doc2", "doc3"] -> nDCG = 1.0
        perfect_run = ["doc1", "doc2", "doc3"]
        assert pytest.approx(ndcg_at_k(perfect_run, qrels, k=3), 1e-5) == 1.0

        # Sub-optimal ranking: ["doc3", "doc2", "doc1"] -> nDCG < 1.0
        reversed_run = ["doc3", "doc2", "doc1"]
        ndcg_rev = ndcg_at_k(reversed_run, qrels, k=3)
        assert 0.0 < ndcg_rev < 1.0

        # Completely irrelevant: ["doc4", "doc_unknown"] -> nDCG = 0.0
        irrelevant_run = ["doc4", "doc_unknown"]
        assert ndcg_at_k(irrelevant_run, qrels, k=2) == 0.0

    def test_evaluate_retrieval_benchmark_runner(self):
        run = {
            "Q1": ["d1", "d2", "d3"],
            "Q2": ["d2", "d1", "d4"],
        }
        qrels = {
            "Q1": {"d1": 1.0},
            "Q2": {"d1": 1.0},
        }
        metrics = evaluate_retrieval_benchmark(run, qrels, k_values=[1, 3])

        # Q1 has relevant d1 at rank 1 (RR=1.0)
        # Q2 has relevant d1 at rank 2 (RR=0.5)
        # Average MRR = (1.0 + 0.5) / 2 = 0.75
        assert metrics["mrr"] == 0.75
        assert metrics["recall@1"] == 0.5
        assert metrics["recall@3"] == 1.0

    def test_empty_and_edge_cases(self):
        assert precision_at_k([], {"d1"}, k=5) == 0.0
        assert recall_at_k([], {"d1"}, k=5) == 0.0
        assert reciprocal_rank([], {"d1"}) == 0.0
        assert ndcg_at_k([], {"d1": 1.0}, k=5) == 0.0
        assert evaluate_retrieval_benchmark({}, {}) == {}
