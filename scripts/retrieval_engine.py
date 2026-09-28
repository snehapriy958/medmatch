"""
MedMatch Modular Retrieval Engine & Experiment Implementations.
Phase 5: Retrieval Engine.

Implements research-grade retrieval strategies under a unified contract:
1. BaseRetriever (Abstract Interface)
2. DenseRetriever (E0/E1: Cosine similarity over dense embeddings)
3. LexicalBM25Retriever (E2: Okapi BM25 ranking over clinical trial text)
4. HybridRRFRetriever (E3: Reciprocal Rank Fusion combining dense + lexical)
5. RerankingRetriever (E4: Second-stage reranker over candidate pools)
"""

from __future__ import annotations

import abc
import math
import re
import time
from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    from scripts.retrieval_schema import (
        CandidateTrialRecord,
        RetrievalRequest,
        RetrievalResponse,
        RetrievalResult,
        RetrievalStrategy,
    )
except ImportError:
    from retrieval_schema import (
        CandidateTrialRecord,
        RetrievalRequest,
        RetrievalResponse,
        RetrievalResult,
        RetrievalStrategy,
    )


# ==========================================
# 1. Clinical Lexical Tokenizer & BM25 Index
# ==========================================

class ClinicalTokenizer:
    """
    Non-destructive clinical tokenizer preserving alphanumeric medical terms,
    gene variants (e.g., EGFR, T790M, L858R), Roman numerals (Stage IV),
    and clinical measurements.
    """
    _TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[\-_/][A-Za-z0-9]+)*")

    # Common English stopwords excluding clinically critical words like 'no', 'not', 'without'
    _STOPWORDS = {
        "a", "an", "the", "and", "or", "of", "to", "in", "is", "was", "for", "with", "by", "at",
        "from", "on", "as", "that", "this", "it", "are", "were", "be", "been", "have", "has", "had",
    }

    @classmethod
    def tokenize(cls, text: str, filter_stopwords: bool = True) -> List[str]:
        if not text:
            return []
        tokens = [t.lower() for t in cls._TOKEN_PATTERN.findall(text)]
        if filter_stopwords:
            tokens = [t for t in tokens if t not in cls._STOPWORDS and len(t) > 1]
        return tokens


class BM25Index:
    """
    In-memory Okapi BM25 index for clinical trial documents.
    Hyperparameters: k1=1.2, b=0.75.
    """

    def __init__(self, k1: float = 1.2, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lens: Dict[str, int] = {}
        self.doc_term_freqs: Dict[str, Counter[str]] = {}
        self.doc_freqs: Counter[str] = Counter()

    def index_documents(self, documents: Dict[str, str]) -> None:
        """Indexes doc_id -> text mapping."""
        self.corpus_size = len(documents)
        total_len = 0
        self.doc_lens.clear()
        self.doc_term_freqs.clear()
        self.doc_freqs.clear()

        for doc_id, text in documents.items():
            tokens = ClinicalTokenizer.tokenize(text)
            d_len = len(tokens)
            self.doc_lens[doc_id] = d_len
            total_len += d_len

            tf = Counter(tokens)
            self.doc_term_freqs[doc_id] = tf
            for term in tf:
                self.doc_freqs[term] += 1

        self.avg_doc_len = total_len / max(1, self.corpus_size)

    def score(self, query_tokens: List[str], doc_id: str) -> float:
        """Computes BM25 score for a document."""
        if doc_id not in self.doc_term_freqs:
            return 0.0

        score = 0.0
        tf_map = self.doc_term_freqs[doc_id]
        doc_len = self.doc_lens[doc_id]

        for term in query_tokens:
            if term not in tf_map:
                continue

            f = tf_map[term]
            df = self.doc_freqs[term]

            # Standard Lucene/BM25 IDF formula with smoothing
            idf = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

            # Term frequency saturation with document length normalization
            tf_norm = (f * (self.k1 + 1.0)) / (f + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len))))

            score += idf * tf_norm

        return score


# ==========================================
# 2. Base Retriever Interface
# ==========================================

class BaseRetriever(abc.ABC):
    """
    Abstract base retriever establishing the canonical retrieval interface.
    """

    @abc.abstractmethod
    def retrieve(
        self,
        request: RetrievalRequest,
        candidate_pool: List[CandidateTrialRecord],
    ) -> RetrievalResponse:
        """
        Executes candidate retrieval matching request parameters against candidate pool.
        """
        pass

    @staticmethod
    def filter_by_tenant(
        candidate_pool: List[CandidateTrialRecord], tenant_id: Optional[str]
    ) -> List[CandidateTrialRecord]:
        """Strict multi-tenant boundary filter."""
        if tenant_id is None:
            return candidate_pool
        return [c for c in candidate_pool if c.hospital_id == tenant_id or c.hospital_id is None]


# ==========================================
# 3. Dense Retriever (E0 / E1)
# ==========================================

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class DenseRetriever(BaseRetriever):
    """
    Dense vector retriever using cosine similarity over precomputed embeddings.
    """

    def __init__(self, embed_fn: Optional[Callable[[str], List[float]]] = None) -> None:
        self.embed_fn = embed_fn

    def retrieve(
        self,
        request: RetrievalRequest,
        candidate_pool: List[CandidateTrialRecord],
    ) -> RetrievalResponse:
        start_time = time.perf_counter()
        filtered_candidates = self.filter_by_tenant(candidate_pool, request.tenant_id)

        # Generate query vector if embedding function provided, otherwise look in structured_query
        query_vector: Optional[List[float]] = None
        if self.embed_fn is not None:
            query_vector = self.embed_fn(request.query_text)
        elif request.structured_query and "embedding" in request.structured_query:
            query_vector = request.structured_query["embedding"]

        scored_candidates: List[Tuple[float, float, str, CandidateTrialRecord]] = []

        for candidate in filtered_candidates:
            if candidate.embedding and query_vector:
                sim = cosine_similarity(query_vector, candidate.embedding)
                dist = 1.0 - sim
            else:
                sim = 0.0
                dist = 1.0

            scored_candidates.append((sim, dist, candidate.trial_id, candidate))

        # Sort descending by similarity, tie-break by trial_id ASC
        scored_candidates.sort(key=lambda x: (-x[0], x[2]))

        top_candidates = scored_candidates[:request.top_k]
        results: List[RetrievalResult] = []

        for rank_idx, (sim, dist, trial_id, cand) in enumerate(top_candidates, start=1):
            results.append(
                RetrievalResult(
                    trial_id=trial_id,
                    rank=rank_idx,
                    score=round(sim, 6),
                    raw_distance=round(dist, 6),
                    retrieval_method="dense",
                    trial_title=cand.title,
                    source_reference=f"trial:{trial_id}",
                    metadata={"similarity": sim, "distance": dist},
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RetrievalResponse(
            request_id=request.request_id,
            experiment_id=request.experiment_id,
            retrieval_strategy=request.retrieval_strategy,
            total_candidates_evaluated=len(filtered_candidates),
            returned_count=len(results),
            results=results,
            execution_time_ms=round(elapsed_ms, 3),
        )


# ==========================================
# 4. Lexical BM25 Retriever (E2)
# ==========================================

class LexicalBM25Retriever(BaseRetriever):
    """
    Lexical retriever using BM25 scoring over clinical trial text fields.
    """

    def retrieve(
        self,
        request: RetrievalRequest,
        candidate_pool: List[CandidateTrialRecord],
    ) -> RetrievalResponse:
        start_time = time.perf_counter()
        filtered_candidates = self.filter_by_tenant(candidate_pool, request.tenant_id)

        # Build corpus representation for each candidate trial
        docs: Dict[str, str] = {}
        trial_map: Dict[str, CandidateTrialRecord] = {}

        for cand in filtered_candidates:
            # Aggregate title, condition, summary, and criteria descriptions
            crit_texts = [str(c.get("description", "")) for c in cand.criteria]
            text = f"{cand.title} {cand.condition or ''} {cand.brief_summary or ''} {' '.join(crit_texts)}"
            docs[cand.trial_id] = text
            trial_map[cand.trial_id] = cand

        index = BM25Index()
        index.index_documents(docs)

        query_tokens = ClinicalTokenizer.tokenize(request.query_text)
        scored_candidates: List[Tuple[float, str, CandidateTrialRecord]] = []

        for trial_id, cand in trial_map.items():
            bm25_score = index.score(query_tokens, trial_id)
            scored_candidates.append((bm25_score, trial_id, cand))

        # Sort descending by BM25 score, tie-break by trial_id ASC
        scored_candidates.sort(key=lambda x: (-x[0], x[1]))

        top_candidates = scored_candidates[:request.top_k]
        results: List[RetrievalResult] = []

        for rank_idx, (b_score, trial_id, cand) in enumerate(top_candidates, start=1):
            results.append(
                RetrievalResult(
                    trial_id=trial_id,
                    rank=rank_idx,
                    score=round(b_score, 6),
                    retrieval_method="lexical_bm25",
                    trial_title=cand.title,
                    source_reference=f"trial:{trial_id}",
                    metadata={"bm25_score": b_score, "matched_terms": [t for t in query_tokens if t in index.doc_term_freqs.get(trial_id, {})]},
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RetrievalResponse(
            request_id=request.request_id,
            experiment_id=request.experiment_id,
            retrieval_strategy=request.retrieval_strategy,
            total_candidates_evaluated=len(filtered_candidates),
            returned_count=len(results),
            results=results,
            execution_time_ms=round(elapsed_ms, 3),
        )


# ==========================================
# 5. Hybrid RRF Retriever (E3)
# ==========================================

class HybridRRFRetriever(BaseRetriever):
    """
    Hybrid retriever combining dense vector rankings and lexical BM25 rankings
    using Reciprocal Rank Fusion (RRF):
    RRF_score(d) = sum_{m in M} 1 / (k_rrf + rank_m(d))
    """

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        lexical_retriever: LexicalBM25Retriever,
        rrf_constant: int = 60,
    ) -> None:
        self.dense_retriever = dense_retriever
        self.lexical_retriever = lexical_retriever
        self.rrf_constant = rrf_constant

    def retrieve(
        self,
        request: RetrievalRequest,
        candidate_pool: List[CandidateTrialRecord],
    ) -> RetrievalResponse:
        start_time = time.perf_counter()
        filtered_candidates = self.filter_by_tenant(candidate_pool, request.tenant_id)
        pool_size = max(request.top_k * 3, 50)

        # Execute component retrievals over broader candidate pool
        dense_req = request.model_copy(update={"top_k": pool_size, "retrieval_strategy": RetrievalStrategy.DENSE_BASELINE})
        lex_req = request.model_copy(update={"top_k": pool_size, "retrieval_strategy": RetrievalStrategy.LEXICAL_BM25})

        dense_resp = self.dense_retriever.retrieve(dense_req, filtered_candidates)
        lex_resp = self.lexical_retriever.retrieve(lex_req, filtered_candidates)

        # Compute RRF Scores
        trial_map = {c.trial_id: c for c in filtered_candidates}
        rrf_scores: Dict[str, float] = {}
        dense_ranks: Dict[str, int] = {}
        lex_ranks: Dict[str, int] = {}

        for res in dense_resp.results:
            dense_ranks[res.trial_id] = res.rank
            rrf_scores[res.trial_id] = rrf_scores.get(res.trial_id, 0.0) + (1.0 / (self.rrf_constant + res.rank))

        for res in lex_resp.results:
            lex_ranks[res.trial_id] = res.rank
            rrf_scores[res.trial_id] = rrf_scores.get(res.trial_id, 0.0) + (1.0 / (self.rrf_constant + res.rank))

        # Sort descending by RRF score, tie-break by trial_id ASC
        sorted_trials = sorted(rrf_scores.keys(), key=lambda tid: (-rrf_scores[tid], tid))
        top_trials = sorted_trials[:request.top_k]

        results: List[RetrievalResult] = []
        for rank_idx, tid in enumerate(top_trials, start=1):
            cand = trial_map.get(tid)
            title = cand.title if cand else "Unknown"
            results.append(
                RetrievalResult(
                    trial_id=tid,
                    rank=rank_idx,
                    score=round(rrf_scores[tid], 6),
                    retrieval_method="hybrid_rrf",
                    trial_title=title,
                    source_reference=f"trial:{tid}",
                    metadata={
                        "rrf_score": rrf_scores[tid],
                        "dense_rank": dense_ranks.get(tid, None),
                        "lexical_rank": lex_ranks.get(tid, None),
                        "rrf_constant": self.rrf_constant,
                    },
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RetrievalResponse(
            request_id=request.request_id,
            experiment_id=request.experiment_id,
            retrieval_strategy=RetrievalStrategy.HYBRID_RRF,
            total_candidates_evaluated=len(filtered_candidates),
            returned_count=len(results),
            results=results,
            execution_time_ms=round(elapsed_ms, 3),
        )


# ==========================================
# 6. Reranking Retriever (E4)
# ==========================================

class BaseReranker(abc.ABC):
    """
    Abstract interface for second-stage rerankers.
    Operates strictly on pre-retrieved candidate sets.
    """

    @abc.abstractmethod
    def rerank(
        self,
        query_text: str,
        candidates: List[RetrievalResult],
        trial_records: Dict[str, CandidateTrialRecord],
    ) -> List[RetrievalResult]:
        pass


class ClinicalOverlapReranker(BaseReranker):
    """
    Reference deterministic cross-encoder style reranker based on clinical concept overlap,
    biomarker match bonuses, and criteria precision scoring.
    """

    def rerank(
        self,
        query_text: str,
        candidates: List[RetrievalResult],
        trial_records: Dict[str, CandidateTrialRecord],
    ) -> List[RetrievalResult]:
        query_tokens = set(ClinicalTokenizer.tokenize(query_text))

        reranked: List[Tuple[float, str, RetrievalResult]] = []

        for cand_res in candidates:
            tid = cand_res.trial_id
            rec = trial_records.get(tid)
            if not rec:
                reranked.append((cand_res.score, tid, cand_res))
                continue

            # Compute clinical token overlap across trial fields
            trial_text = f"{rec.title} {rec.condition or ''} {rec.brief_summary or ''}"
            crit_texts = " ".join([str(c.get("description", "")) for c in rec.criteria])
            all_trial_tokens = set(ClinicalTokenizer.tokenize(f"{trial_text} {crit_texts}"))

            intersection = query_tokens.intersection(all_trial_tokens)
            overlap_ratio = len(intersection) / max(1, len(query_tokens))

            # Rerank score blends baseline score with token alignment
            rerank_score = cand_res.score * 0.5 + overlap_ratio * 0.5
            reranked.append((rerank_score, tid, cand_res))

        # Sort descending by rerank score, tie-break by trial_id ASC
        reranked.sort(key=lambda x: (-x[0], x[1]))

        results: List[RetrievalResult] = []
        for rank_idx, (r_score, tid, orig) in enumerate(reranked, start=1):
            updated_meta = dict(orig.metadata)
            updated_meta["original_rank"] = orig.rank
            updated_meta["rerank_score"] = round(r_score, 6)
            results.append(
                orig.model_copy(
                    update={
                        "rank": rank_idx,
                        "score": round(r_score, 6),
                        "retrieval_method": "hybrid_reranked",
                        "metadata": updated_meta,
                    }
                )
            )

        return results


class RerankingRetriever(BaseRetriever):
    """
    Two-stage retriever: retrieves top candidates using a base retriever,
    then applies a second-stage reranker.
    """

    def __init__(
        self,
        base_retriever: BaseRetriever,
        reranker: BaseReranker,
        candidate_pool_multiplier: int = 2,
    ) -> None:
        self.base_retriever = base_retriever
        self.reranker = reranker
        self.candidate_pool_multiplier = candidate_pool_multiplier

    def retrieve(
        self,
        request: RetrievalRequest,
        candidate_pool: List[CandidateTrialRecord],
    ) -> RetrievalResponse:
        start_time = time.perf_counter()
        pool_size = min(request.top_k * self.candidate_pool_multiplier, len(candidate_pool))

        # Step 1: Base retrieval
        sub_req = request.model_copy(update={"top_k": pool_size})
        base_resp = self.base_retriever.retrieve(sub_req, candidate_pool)

        # Step 2: Rerank
        trial_map = {c.trial_id: c for c in candidate_pool}
        reranked_results = self.reranker.rerank(request.query_text, base_resp.results, trial_map)

        # Final top-k truncation
        final_results = reranked_results[:request.top_k]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RetrievalResponse(
            request_id=request.request_id,
            experiment_id=request.experiment_id,
            retrieval_strategy=RetrievalStrategy.HYBRID_RERANKED,
            total_candidates_evaluated=base_resp.total_candidates_evaluated,
            returned_count=len(final_results),
            results=final_results,
            execution_time_ms=round(elapsed_ms, 3),
        )
