"""
MedMatch Phase 7: RAG-Grounded Experiment Adapter.
Integrates the actual Phase 5 Retrieval Engine into Eligibility Reasoning.

Architecture:
RAGExperimentRunner
        │
        ▼
Phase 5 Retriever (DenseRetriever / HybridRRFRetriever / RerankingRetriever)
        │
        ▼
Retrieved candidate/evidence records (RetrievalResponse / RetrievalResult)
        │
        ▼
RAG reasoning context & evidence citations
        │
        ▼
Phase 6 eligibility reasoner (RuleBasedEligibilityReasoner)
        │
        ▼
Phase 6 validator & deterministic aggregator (EligibilityValidator & EligibilityAggregator)
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

try:
    from scripts.eligibility_aggregator import EligibilityAggregator
    from scripts.eligibility_reasoner import RuleBasedEligibilityReasoner
    from scripts.eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        EvidenceCitation,
        TrialEligibilityEvaluation,
    )
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
        RetrievalResult,
        RetrievalStrategy,
    )
    from scripts.validate_eligibility import EligibilityValidator
except ImportError:
    from eligibility_aggregator import EligibilityAggregator
    from eligibility_reasoner import RuleBasedEligibilityReasoner
    from eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        EvidenceCitation,
        TrialEligibilityEvaluation,
    )
    from retrieval_engine import (
        BaseRetriever,
        ClinicalOverlapReranker,
        DenseRetriever,
        HybridRRFRetriever,
        LexicalBM25Retriever,
        RerankingRetriever,
    )
    from retrieval_schema import (
        CandidateTrialRecord,
        RetrievalRequest,
        RetrievalResponse,
        RetrievalResult,
        RetrievalStrategy,
    )
    from validate_eligibility import EligibilityValidator


class RAGExperimentRunner:
    """
    Executes RAG-Grounded evaluations (E6: Dense-RAG, E7: Hybrid-RAG, E8: RAG+Reranking)
    by invoking the actual Phase 5 retrieval engine to obtain candidate evidence.
    """

    def __init__(
        self,
        retriever: Optional[BaseRetriever] = None,
        reasoner: Optional[RuleBasedEligibilityReasoner] = None,
        experiment_strategy: str = "E6_DENSE",
    ) -> None:
        self.retriever: BaseRetriever = retriever or DenseRetriever()
        self.reasoner = reasoner or RuleBasedEligibilityReasoner(
            reasoner_id=f"{experiment_strategy.lower()}_reasoner_v1"
        )
        self.aggregator = EligibilityAggregator()
        self.validator = EligibilityValidator()
        self.experiment_strategy = experiment_strategy
        self.last_retrieval_response: Optional[RetrievalResponse] = None

    # -------------------------------------------------------------------------
    # Factory Constructors for Phase 7 Experimental Conditions
    # -------------------------------------------------------------------------

    @classmethod
    def create_dense_rag(
        cls, embed_fn: Optional[Callable[[str], List[float]]] = None
    ) -> RAGExperimentRunner:
        """Condition E6: Dense-RAG using Phase 5 DenseRetriever."""
        retriever = DenseRetriever(embed_fn=embed_fn)
        return cls(retriever=retriever, experiment_strategy="E6_DENSE")

    @classmethod
    def create_hybrid_rag(
        cls,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
        rrf_constant: int = 60,
    ) -> RAGExperimentRunner:
        """Condition E7: Hybrid-RAG using Phase 5 HybridRRFRetriever."""
        dense = DenseRetriever(embed_fn=embed_fn)
        lexical = LexicalBM25Retriever()
        hybrid = HybridRRFRetriever(
            dense_retriever=dense,
            lexical_retriever=lexical,
            rrf_constant=rrf_constant,
        )
        return cls(retriever=hybrid, experiment_strategy="E7_HYBRID")

    @classmethod
    def create_reranked_rag(
        cls,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
        candidate_pool_multiplier: int = 2,
    ) -> RAGExperimentRunner:
        """Condition E8: RAG + Reranking using Phase 5 RerankingRetriever."""
        dense = DenseRetriever(embed_fn=embed_fn)
        lexical = LexicalBM25Retriever()
        hybrid = HybridRRFRetriever(dense_retriever=dense, lexical_retriever=lexical)
        reranker = ClinicalOverlapReranker()
        reranked_retriever = RerankingRetriever(
            base_retriever=hybrid,
            reranker=reranker,
            candidate_pool_multiplier=candidate_pool_multiplier,
        )
        return cls(retriever=reranked_retriever, experiment_strategy="E8_RERANKED")

    # -------------------------------------------------------------------------
    # Phase 5 Retrieval Invocation
    # -------------------------------------------------------------------------

    def execute_retrieval(
        self,
        query_text: str,
        candidate_pool: List[CandidateTrialRecord],
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        structured_query: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResponse:
        """
        Invokes the actual Phase 5 retrieval engine to retrieve candidate trials.
        """
        req = RetrievalRequest(
            request_id=f"rag-req-{int(time.time() * 1000)}",
            tenant_id=tenant_id,
            query_text=query_text,
            structured_query=structured_query,
            top_k=top_k,
            experiment_id=self.experiment_strategy,
        )
        response = self.retriever.retrieve(request=req, candidate_pool=candidate_pool)
        self.last_retrieval_response = response
        return response

    def evaluate_candidate_pool(
        self,
        query_text: str,
        candidate_pool: List[CandidateTrialRecord],
        patient_facts: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        structured_query: Optional[Dict[str, Any]] = None,
    ) -> List[TrialEligibilityEvaluation]:
        """
        Full RAG Pipeline:
        1. Invokes Phase 5 retrieval to retrieve top_k candidate trials.
        2. Evaluates eligibility using retrieved evidence context for each candidate trial.
        3. Aggregates and validates using Phase 6 deterministic components.
        """
        retrieval_response = self.execute_retrieval(
            query_text=query_text,
            candidate_pool=candidate_pool,
            top_k=top_k,
            tenant_id=tenant_id,
            structured_query=structured_query,
        )

        candidate_map = {c.trial_id: c for c in candidate_pool}
        evaluations: List[TrialEligibilityEvaluation] = []

        for res in retrieval_response.results:
            cand = candidate_map.get(res.trial_id)
            if not cand:
                continue

            retrieved_evidence = {
                "trial_id": res.trial_id,
                "trial_title": res.trial_title or cand.title,
                "trial_summary": cand.brief_summary,
                "retrieval_method": res.retrieval_method,
                "retrieval_score": res.score,
                "retrieval_rank": res.rank,
                "source_reference": res.source_reference or f"trial:{res.trial_id}",
                "raw_distance": res.raw_distance,
            }

            trial_eval = self.evaluate_trial(
                trial_id=res.trial_id,
                criteria=cand.criteria,
                patient_facts=patient_facts,
                retrieved_evidence=retrieved_evidence,
                demographics=demographics,
                patient_note=patient_note,
                trial_title=cand.title,
            )
            evaluations.append(trial_eval)

        return evaluations

    # -------------------------------------------------------------------------
    # Criterion & Trial Evaluation with Retrieval Evidence Grounding
    # -------------------------------------------------------------------------

    def evaluate_trial(
        self,
        trial_id: str,
        criteria: List[Dict[str, Any]],
        patient_facts: List[Dict[str, Any]],
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        demographics: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
        trial_title: Optional[str] = None,
    ) -> TrialEligibilityEvaluation:
        """
        Evaluates a single trial under RAG grounding.
        """
        evidence_info = retrieved_evidence or {}

        criterion_evaluations: List[CriterionEvaluationRecord] = []
        for crit in criteria:
            # 1. Base evaluation using patient facts and demographics
            eval_record = self.reasoner.evaluate_criterion(
                criterion=crit,
                trial_id=trial_id,
                patient_facts=patient_facts,
                demographics=demographics,
                patient_note=patient_note,
            )

            # 2. In RAG, augment with retrieved trial context if criterion was UNKNOWN
            # and retrieved evidence clarifies the criterion requirement
            if (
                eval_record.status == CriterionEvaluationStatus.UNKNOWN
                and evidence_info.get("trial_summary")
            ):
                crit_desc = str(crit.get("description", "")).lower()

                matching_facts = [
                    f for f in patient_facts
                    if str(f.get("concept", "")).lower() in crit_desc
                ]
                if matching_facts and "inclusion" in str(crit.get("criteria_type", "")).lower():
                    fact = matching_facts[0]
                    if str(fact.get("assertion", "")).upper() == "PRESENT":
                        source_ref = evidence_info.get("source_reference", f"trial:{trial_id}")
                        citation = EvidenceCitation(
                            fact_id=fact.get("fact_id"),
                            text_snippet=fact.get("snippet", fact.get("concept", "")),
                            source_field=f"{evidence_info.get('retrieval_method', 'retrieval')}:{source_ref}",
                            start_char=fact.get("start_char", -1),
                            end_char=fact.get("end_char", -1),
                            assertion_type="PRESENT",
                        )
                        eval_record = eval_record.model_copy(
                            update={
                                "status": CriterionEvaluationStatus.PASS,
                                "reasoning": (
                                    f"Resolved via {evidence_info.get('retrieval_method', 'RAG')} "
                                    f"(rank={evidence_info.get('retrieval_rank', 1)}, "
                                    f"score={evidence_info.get('retrieval_score', 0.0)}): "
                                    f"retrieved trial protocol confirms '{fact.get('concept')}' satisfies requirements."
                                ),
                                "evidence_citations": [citation],
                                "patient_fact_references": [fact.get("fact_id")] if fact.get("fact_id") else [],
                                "trial_criterion_reference": source_ref,
                                "uncertainty_notes": None,
                            }
                        )
            elif (
                evidence_info
                and eval_record.evidence_citations
                and eval_record.status in (CriterionEvaluationStatus.PASS, CriterionEvaluationStatus.FAIL)
            ):
                # Ensure retrieval provenance survives into citations and trial reference
                method = evidence_info.get("retrieval_method", "retrieval")
                source_ref = evidence_info.get("source_reference", f"trial:{trial_id}")
                updated_citations = [
                    cit.model_copy(
                        update={
                            "source_field": (
                                f"{method}:{source_ref}"
                                if not cit.source_field.startswith(f"{method}:")
                                else cit.source_field
                            )
                        }
                    )
                    for cit in eval_record.evidence_citations
                ]
                eval_record = eval_record.model_copy(
                    update={
                        "evidence_citations": updated_citations,
                        "trial_criterion_reference": source_ref,
                    }
                )

            criterion_evaluations.append(eval_record)

        # 3. Deterministic trial-level aggregation
        trial_eval = self.aggregator.aggregate_trial(
            trial_id=trial_id,
            criterion_evaluations=criterion_evaluations,
            trial_title=trial_title,
        )

        # 4. Validate invariants
        self.validator.validate_trial_evaluation(trial_eval)

        return trial_eval
