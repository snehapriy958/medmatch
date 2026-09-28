"""
Tests for Multi-Tenant Isolation during Candidate Retrieval.
Phase 5: Retrieval Engine.
"""

import pytest
from scripts.retrieval_engine import DenseRetriever, LexicalBM25Retriever
from scripts.retrieval_schema import (
    CandidateTrialRecord,
    RetrievalRequest,
    RetrievalStrategy,
)


def _make_multi_tenant_pool() -> list[CandidateTrialRecord]:
    return [
        CandidateTrialRecord(
            trial_id="TRIAL_HOSP_A_1",
            hospital_id="HOSP_A",
            title="Trial at Hospital A for NSCLC",
            condition="NSCLC",
            brief_summary="Summary A",
            embedding=[0.9, 0.1, 0.0],
        ),
        CandidateTrialRecord(
            trial_id="TRIAL_HOSP_B_1",
            hospital_id="HOSP_B",
            title="Trial at Hospital B with exact query keyword NSCLC EGFR",
            condition="NSCLC",
            brief_summary="Summary B",
            embedding=[0.95, 0.05, 0.0],  # Closer vector!
        ),
    ]


class TestTenantIsolation:
    """Test suite for tenant filtering and cross-tenant data leakage prevention."""

    def test_dense_retrieval_enforces_tenant_boundary(self):
        pool = _make_multi_tenant_pool()
        retriever = DenseRetriever()
        req = RetrievalRequest(
            request_id="REQ_TENANT_A",
            tenant_id="HOSP_A",  # Tenant A
            query_text="NSCLC trial",
            structured_query={"embedding": [0.9, 0.1, 0.0]},
            top_k=5,
            retrieval_strategy=RetrievalStrategy.DENSE_BASELINE,
        )
        resp = retriever.retrieve(req, pool)

        # Must only return TRIAL_HOSP_A_1; TRIAL_HOSP_B_1 must NOT leak
        assert resp.returned_count == 1
        assert resp.results[0].trial_id == "TRIAL_HOSP_A_1"
        assert all(r.trial_id != "TRIAL_HOSP_B_1" for r in resp.results)

    def test_lexical_retrieval_enforces_tenant_boundary(self):
        pool = _make_multi_tenant_pool()
        retriever = LexicalBM25Retriever()
        req = RetrievalRequest(
            request_id="REQ_TENANT_A_LEX",
            tenant_id="HOSP_A",  # Tenant A
            query_text="EGFR NSCLC",
            top_k=5,
            retrieval_strategy=RetrievalStrategy.LEXICAL_BM25,
        )
        resp = retriever.retrieve(req, pool)

        # Even though HOSPITAL_B has exact keyword match, it must be excluded
        assert resp.returned_count == 1
        assert resp.results[0].trial_id == "TRIAL_HOSP_A_1"
        assert all(r.trial_id != "TRIAL_HOSP_B_1" for r in resp.results)
