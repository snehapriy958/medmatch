"""
Tests for Canonical Retrieval Schemas and Contracts.
Phase 5: Retrieval Engine.
"""

import pytest
from pydantic import ValidationError

from scripts.retrieval_schema import (
    CandidateTrialRecord,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
    RetrievalStrategy,
)


class TestRetrievalContracts:
    """Test suite for retrieval requests, results, and response contracts."""

    def test_retrieval_request_valid_instantiation(self):
        req = RetrievalRequest(
            request_id="REQ_001",
            tenant_id="HOSP_001",
            query_text="63yo male with Stage IV NSCLC, EGFR exon 19 deletion",
            top_k=10,
            retrieval_strategy=RetrievalStrategy.DENSE_BASELINE,
            experiment_id="E0",
        )
        assert req.request_id == "REQ_001"
        assert req.tenant_id == "HOSP_001"
        assert req.top_k == 10
        assert req.retrieval_strategy == RetrievalStrategy.DENSE_BASELINE

    def test_retrieval_request_empty_query_rejected(self):
        with pytest.raises(ValidationError):
            RetrievalRequest(
                request_id="REQ_EMPTY",
                query_text="",  # Invalid: empty string
            )

    def test_retrieval_request_top_k_bounds(self):
        with pytest.raises(ValidationError):
            RetrievalRequest(request_id="REQ_001", query_text="query", top_k=0)
        with pytest.raises(ValidationError):
            RetrievalRequest(request_id="REQ_001", query_text="query", top_k=101)

    def test_retrieval_result_provenance_and_metadata(self):
        res = RetrievalResult(
            trial_id="NCT02484404",
            criterion_id="CRIT_001",
            rank=1,
            score=0.885,
            raw_distance=0.115,
            retrieval_method="dense",
            source_reference="trial:NCT02484404",
            trial_title="Osimertinib in First-Line EGFR-Mutant NSCLC",
            metadata={"similarity": 0.885},
        )
        assert res.trial_id == "NCT02484404"
        assert res.rank == 1
        assert res.score == 0.885
        assert res.raw_distance == 0.115
        assert res.source_reference == "trial:NCT02484404"

    def test_retrieval_response_count_validation(self):
        res1 = RetrievalResult(
            trial_id="NCT01",
            rank=1,
            score=0.9,
            retrieval_method="dense",
        )
        res2 = RetrievalResult(
            trial_id="NCT02",
            rank=2,
            score=0.8,
            retrieval_method="dense",
        )
        response = RetrievalResponse(
            request_id="REQ_001",
            experiment_id="E0",
            retrieval_strategy=RetrievalStrategy.DENSE_BASELINE,
            total_candidates_evaluated=100,
            returned_count=2,
            results=[res1, res2],
            execution_time_ms=12.5,
        )
        assert response.returned_count == 2
        assert len(response.results) == 2
        assert response.execution_time_ms == 12.5

    def test_json_roundtrip_serialization(self):
        res = RetrievalResult(
            trial_id="NCT02484404",
            rank=1,
            score=0.95,
            retrieval_method="hybrid_rrf",
        )
        resp = RetrievalResponse(
            request_id="REQ_ROUNDTRIP",
            experiment_id="E3",
            retrieval_strategy=RetrievalStrategy.HYBRID_RRF,
            total_candidates_evaluated=50,
            returned_count=1,
            results=[res],
            execution_time_ms=5.2,
        )
        json_data = resp.model_dump_json()
        parsed = RetrievalResponse.model_validate_json(json_data)
        assert parsed.request_id == "REQ_ROUNDTRIP"
        assert parsed.results[0].trial_id == "NCT02484404"
        assert parsed.results[0].retrieval_method == "hybrid_rrf"
