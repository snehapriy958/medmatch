"""
MedMatch Retrieval Evaluation & Information Retrieval Metrics.
Phase 5: Retrieval Engine.

Implements deterministic evaluation metrics:
- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (nDCG@K) for graded relevance
- Multi-query benchmark evaluation runner
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Set, Union


def precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int,
) -> float:
    """
    Computes Precision@K:
    Precision@K = |{retrieved_{1..K}} ∩ relevant| / K
    """
    if k <= 0:
        raise ValueError("k must be greater than 0")
    if not retrieved_ids or not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    num_hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return num_hits / float(k)


def recall_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int,
) -> float:
    """
    Computes Recall@K:
    Recall@K = |{retrieved_{1..K}} ∩ relevant| / |relevant|
    """
    if k <= 0:
        raise ValueError("k must be greater than 0")
    if not relevant_ids:
        return 0.0
    if not retrieved_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    num_hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return num_hits / float(len(relevant_ids))


def reciprocal_rank(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
) -> float:
    """
    Computes Reciprocal Rank (RR):
    RR = 1 / rank_first_relevant (1-based rank), or 0.0 if not found.
    """
    if not retrieved_ids or not relevant_ids:
        return 0.0

    for idx, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / float(idx)

    return 0.0


def dcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Dict[str, float],
    k: int,
) -> float:
    """
    Computes Discounted Cumulative Gain at K (DCG@K):
    DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log2(i + 1)
    """
    if k <= 0:
        raise ValueError("k must be greater than 0")
    if not retrieved_ids or not relevance_scores:
        return 0.0

    top_k = retrieved_ids[:k]
    dcg = 0.0

    for idx, doc_id in enumerate(top_k, start=1):
        rel = relevance_scores.get(doc_id, 0.0)
        if rel > 0.0:
            gain = (2.0 ** rel) - 1.0
            discount = math.log2(idx + 1)
            dcg += gain / discount

    return dcg


def ndcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Dict[str, float],
    k: int,
) -> float:
    """
    Computes Normalized Discounted Cumulative Gain at K (nDCG@K):
    nDCG@K = DCG@K / IDCG@K
    """
    if k <= 0:
        raise ValueError("k must be greater than 0")
    if not relevance_scores:
        return 0.0

    actual_dcg = dcg_at_k(retrieved_ids, relevance_scores, k)
    if actual_dcg == 0.0:
        return 0.0

    # Calculate Ideal DCG (sort relevance scores descending)
    ideal_relevances = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = 0.0
    for idx, rel in enumerate(ideal_relevances, start=1):
        if rel > 0.0:
            gain = (2.0 ** rel) - 1.0
            discount = math.log2(idx + 1)
            idcg += gain / discount

    if idcg == 0.0:
        return 0.0

    return actual_dcg / idcg


def evaluate_retrieval_benchmark(
    run_results: Dict[str, List[str]],
    ground_truth_qrels: Dict[str, Dict[str, float]],
    k_values: List[int] = [1, 5, 10, 20],
) -> Dict[str, float]:
    """
    Evaluates a full retrieval run across multiple queries against ground-truth qrels.

    Parameters:
    - run_results: query_id -> ranked list of retrieved doc_ids
    - ground_truth_qrels: query_id -> (doc_id -> relevance_grade)
    - k_values: list of cutoff thresholds (e.g., [1, 5, 10, 20])

    Returns:
    - Dict of averaged metrics: P@1, P@5, R@1, R@5, MRR, nDCG@5, etc.
    """
    if not run_results:
        return {}

    num_queries = len(run_results)
    metrics: Dict[str, float] = {}

    # Initialize accumulators
    for k in k_values:
        metrics[f"precision@{k}"] = 0.0
        metrics[f"recall@{k}"] = 0.0
        metrics[f"ndcg@{k}"] = 0.0
    metrics["mrr"] = 0.0

    for qid, retrieved in run_results.items():
        qrels = ground_truth_qrels.get(qid, {})
        # Binary relevant set (relevance > 0.0)
        binary_relevant = {did for did, rel in qrels.items() if rel > 0.0}

        metrics["mrr"] += reciprocal_rank(retrieved, binary_relevant)

        for k in k_values:
            metrics[f"precision@{k}"] += precision_at_k(retrieved, binary_relevant, k)
            metrics[f"recall@{k}"] += recall_at_k(retrieved, binary_relevant, k)
            metrics[f"ndcg@{k}"] += ndcg_at_k(retrieved, qrels, k)

    # Compute averages across all queries in run
    averaged_metrics: Dict[str, float] = {}
    for key, val in metrics.items():
        averaged_metrics[key] = round(val / float(max(1, num_queries)), 4)

    return averaged_metrics
