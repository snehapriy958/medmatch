"""
Tests for Retrieval Algorithms: Dense, Lexical BM25, Hybrid RRF, and Reranking.
Phase 5: Retrieval Engine.
"""

import pytest
from scripts.retrieval_engine import (
    BM25Index,
    ClinicalTokenizer,
    ClinicalOverlapReranker,
    DenseRetriever,
    HybridRRFRetriever,
    LexicalBM25Retriever,
    RerankingRetriever,
    cosine_similarity,
)
from scripts.retrieval_schema import (
    CandidateTrialRecord,
    RetrievalRequest,
    RetrievalStrategy,
)


def _make_candidate_pool() -> list[CandidateTrialRecord]:
    """Controlled toy candidate pool for deterministic testing."""
    return [
        CandidateTrialRecord(
            trial_id="NCT001",
            title="First-Line Osimertinib in Advanced EGFR-Mutant NSCLC",
            condition="Non-Small Cell Lung Cancer",
            brief_summary="Study evaluating osimertinib for patients with Stage IV NSCLC harboring EGFR mutations.",
            criteria=[{"description": "Documented EGFR exon 19 deletion or L858R mutation."}],
            embedding=[0.9, 0.1, 0.0],
        ),
        CandidateTrialRecord(
            trial_id="NCT002",
            title="Pembrolizumab Monotherapy in Advanced Melanoma",
            condition="Cutaneous Melanoma",
            brief_summary="Phase 3 trial of anti-PD1 therapy in metastatic melanoma.",
            criteria=[{"description": "Histologically confirmed metastatic melanoma."}],
            embedding=[0.1, 0.9, 0.0],
        ),
        CandidateTrialRecord(
            trial_id="NCT003",
            title="Sotorasib in KRAS G12C Advanced Solid Tumors",
            condition="Solid Tumors",
            brief_summary="Targeted therapy for KRAS G12C mutated non-small cell lung cancer.",
            criteria=[{"description": "Confirmed KRAS G12C mutation on genomic testing."}],
            embedding=[0.6, 0.4, 0.0],
        ),
    ]


class TestRetrievalAlgorithms:
    """Test suite for dense, lexical, hybrid, and reranking retrieval engines."""

    def test_clinical_tokenizer_preserves_medical_terms(self):
        text = "Patient with Stage-IV NSCLC and EGFR-T790M mutation, received chemo 28-days ago."
        tokens = ClinicalTokenizer.tokenize(text)
        assert "stage-iv" in tokens
        assert "nsclc" in tokens
        assert "egfr-t790m" in tokens
        assert "28-days" in tokens

    def test_cosine_similarity_calculation(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        assert pytest.approx(cosine_similarity(v1, v2), 1e-5) == 1.0
        assert pytest.approx(cosine_similarity(v1, v3), 1e-5) == 0.0

    def test_dense_retriever_ranking_and_tie_breaking(self):
        pool = _make_candidate_pool()
        retriever = DenseRetriever()
        req = RetrievalRequest(
            request_id="REQ_DENSE",
            query_text="EGFR mutant lung cancer",
            structured_query={"embedding": [0.9, 0.1, 0.0]},
            top_k=2,
            retrieval_strategy=RetrievalStrategy.DENSE_BASELINE,
        )
        resp = retriever.retrieve(req, pool)

        assert resp.returned_count == 2
        assert resp.results[0].trial_id == "NCT001"
        assert resp.results[0].rank == 1
        assert resp.results[0].score > resp.results[1].score

    def test_lexical_bm25_retriever(self):
        pool = _make_candidate_pool()
        retriever = LexicalBM25Retriever()
        req = RetrievalRequest(
            request_id="REQ_LEX",
            query_text="melanoma pembrolizumab metastatic",
            top_k=2,
            retrieval_strategy=RetrievalStrategy.LEXICAL_BM25,
        )
        resp = retriever.retrieve(req, pool)

        assert resp.returned_count == 2
        # NCT002 is the melanoma trial and should rank 1st
        assert resp.results[0].trial_id == "NCT002"
        assert resp.results[0].score > 0.0

    def test_hybrid_rrf_combines_dense_and_lexical(self):
        pool = _make_candidate_pool()
        dense_ret = DenseRetriever()
        lex_ret = LexicalBM25Retriever()
        hybrid_ret = HybridRRFRetriever(dense_ret, lex_ret, rrf_constant=60)

        req = RetrievalRequest(
            request_id="REQ_HYBRID",
            query_text="Osimertinib EGFR NSCLC",
            structured_query={"embedding": [0.9, 0.1, 0.0]},
            top_k=3,
            retrieval_strategy=RetrievalStrategy.HYBRID_RRF,
        )
        resp = hybrid_ret.retrieve(req, pool)

        assert resp.returned_count == 3
        # NCT001 ranks 1 in both dense and lexical, so it must be top RRF
        top = resp.results[0]
        assert top.trial_id == "NCT001"
        assert top.retrieval_method == "hybrid_rrf"
        # RRF formula check: 1/(60 + 1) + 1/(60 + 1) = 2/61 ≈ 0.032787
        expected_rrf = (1.0 / 61.0) + (1.0 / 61.0)
        assert pytest.approx(top.score, 1e-4) == expected_rrf

    def test_reranking_retriever_operates_on_candidate_pool(self):
        pool = _make_candidate_pool()
        dense_ret = DenseRetriever()
        reranker = ClinicalOverlapReranker()
        retriever = RerankingRetriever(dense_ret, reranker, candidate_pool_multiplier=2)

        req = RetrievalRequest(
            request_id="REQ_RERANK",
            query_text="Sotorasib KRAS G12C mutation",
            structured_query={"embedding": [0.6, 0.4, 0.0]},
            top_k=2,
            retrieval_strategy=RetrievalStrategy.HYBRID_RERANKED,
        )
        resp = retriever.retrieve(req, pool)

        assert resp.returned_count == 2
        assert resp.results[0].trial_id == "NCT003"
        assert resp.results[0].retrieval_method == "hybrid_reranked"
        assert "rerank_score" in resp.results[0].metadata

    def test_deterministic_retrieval_ordering(self):
        """Identical query and candidate pool must return identical ranked results."""
        pool = _make_candidate_pool()
        retriever = LexicalBM25Retriever()
        req = RetrievalRequest(
            request_id="REQ_DET",
            query_text="lung cancer trial",
            top_k=3,
            retrieval_strategy=RetrievalStrategy.LEXICAL_BM25,
        )
        resp1 = retriever.retrieve(req, pool)
        resp2 = retriever.retrieve(req, pool)

        assert [r.trial_id for r in resp1.results] == [r.trial_id for r in resp2.results]
        assert [r.score for r in resp1.results] == [r.score for r in resp2.results]
