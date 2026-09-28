"""
MedMatch Deterministic Claim Extractor for Grounding Evaluation.
Phase 8: Grounding Evaluation & Faithfulness Auditing.

Decomposes unstructured or semi-structured clinical reasoning justifications
into atomic, evaluable propositions classified by ClaimType:
1. PATIENT_FACT: assertions regarding patient conditions, biomarkers, history
2. TRIAL_CRITERION: statements describing trial requirements or protocol conditions
3. TEMPORAL_FACT: temporal markers, durations, dates, or time windows
4. NUMERICAL_VALUE: quantitative thresholds, lab values, scores, or ages
5. ELIGIBILITY_CONCLUSION: determinations of satisfaction, failure, or uncertainty
6. INFERRED_CLAIM: clinical inferences or speculations not directly observed

Preserves strict deterministic execution without relying on stochastic LLMs.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from scripts.grounding_schema import ClaimType, GroundingClaim
except ImportError:
    from grounding_schema import ClaimType, GroundingClaim


class DeterministicClaimExtractor:
    """
    Deterministic rule-based extractor that segments clinical reasoning text into
    atomic claims and classifies each into canonical ClaimType categories.
    """

    # Clause segmentation regex splitting on periods, semicolons, and structural transitions
    _SEGMENT_PATTERN = re.compile(r"(?<=[.;\n])\s+|(?<=[,])\s+(?=(?:patient|trial|criterion|resolved|meets|fails|requires|age)\b)", re.IGNORECASE)

    # Patterns for Conclusion claims
    _CONCLUSION_PATTERNS = [
        re.compile(r"\b(?:satisfies|meets|fails|meets requirement|fails criterion|criterion is met|ineligible|eligible|resolved via)\b", re.IGNORECASE),
        re.compile(r"\b(?:satisfies requirements|cannot be determined|status is unknown|insufficient evidence)\b", re.IGNORECASE),
    ]

    # Patterns for Temporal claims
    _TEMPORAL_PATTERNS = [
        re.compile(r"\b(?:within\s+(?:the\s+)?(?:past|last)\s+\d+\s+(?:months?|weeks?|years?|days?))\b", re.IGNORECASE),
        re.compile(r"\b(?:diagnosed\s+in\s+\d{4}|in\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})\b", re.IGNORECASE),
        re.compile(r"\b(?:prior\s+(?:to)?\s*(?:systemic|platinum|chemotherapy|treatment|therapy|surgery))\b", re.IGNORECASE),
        re.compile(r"\b(?:concurrent|history of|previously|recently|at presentation)\b", re.IGNORECASE),
    ]

    # Patterns for Numerical claims
    _NUMERICAL_PATTERNS = [
        re.compile(r"\b(?:age\s*(?:is\s*)?(?:[<>=]=?)?\s*\d+|\d+\s*(?:years?\s+old|y/?o))\b", re.IGNORECASE),
        re.compile(r"\b(?:ecog\s*(?:performance)?\s*(?:status|score)?\s*(?:of)?\s*\d+|kps\s*\d+)\b", re.IGNORECASE),
        re.compile(r"\b(?:\d+(?:\.\d+)?\s*(?:%|mg/dl|g/dl|mmol/l|u/l|cells/ul|ng/ml))\b", re.IGNORECASE),
        re.compile(r"\b(?:score\s*=\s*\d+(?:\.\d+)?|rank\s*=\s*\d+)\b", re.IGNORECASE),
        re.compile(r"[<>=]=?\s*\d+(?:\.\d+)?"),
    ]

    # Patterns for Trial Criterion claims
    _CRITERION_PATTERNS = [
        re.compile(r"\b(?:trial\s+requires|trial\s+protocol|criterion\s+requires|protocol\s+confirms)\b", re.IGNORECASE),
        re.compile(r"\b(?:requirement\s+['\"][^'\"]+['\"]|criterion:\s*['\"][^'\"]+['\"])\b", re.IGNORECASE),
    ]

    # Patterns for Inferred claims
    _INFERENCE_PATTERNS = [
        re.compile(r"\b(?:likely|suggests|presumed|suspected|assumed|implies|appears to be|extrapolated)\b", re.IGNORECASE),
    ]

    @classmethod
    def segment_reasoning(cls, reasoning_text: str) -> List[str]:
        """
        Segments a multi-sentence or compound reasoning paragraph into clean propositions.
        """
        if not reasoning_text or not reasoning_text.strip():
            return []

        raw_segments = cls._SEGMENT_PATTERN.split(reasoning_text.strip())
        cleaned_segments: List[str] = []

        for seg in raw_segments:
            seg_clean = seg.strip().rstrip(".;,")
            if len(seg_clean) > 3:
                cleaned_segments.append(seg_clean)

        return cleaned_segments

    @classmethod
    def classify_claim_type(cls, text: str) -> ClaimType:
        """
        Classifies an individual proposition into a ClaimType based on prioritized patterns.
        Order of evaluation ensures fine-grained typing:
        1. Inferred claims
        2. Eligibility conclusions
        3. Temporal claims
        4. Numerical claims
        5. Criterion claims
        6. Default to Patient factual claims
        """
        # 1. Speculative or inferred wording
        for pat in cls._INFERENCE_PATTERNS:
            if pat.search(text):
                return ClaimType.INFERRED_CLAIM

        # 2. Conclusions on satisfaction/failure
        for pat in cls._CONCLUSION_PATTERNS:
            if pat.search(text):
                return ClaimType.ELIGIBILITY_CONCLUSION

        # 3. Temporal markers or windows
        for pat in cls._TEMPORAL_PATTERNS:
            if pat.search(text):
                return ClaimType.TEMPORAL_FACT

        # 4. Numerical values / thresholds / scores
        for pat in cls._NUMERICAL_PATTERNS:
            if pat.search(text):
                return ClaimType.NUMERICAL_VALUE

        # 5. Trial protocol / criterion requirements
        for pat in cls._CRITERION_PATTERNS:
            if pat.search(text):
                return ClaimType.TRIAL_CRITERION

        # 6. Default factual statement
        return ClaimType.PATIENT_FACT

    @classmethod
    def extract_claims(
        cls,
        reasoning_text: str,
        criterion_id: Optional[str] = None,
        trial_id: Optional[str] = None,
    ) -> List[GroundingClaim]:
        """
        Decomposes a reasoning justification into atomic GroundingClaim models.
        """
        segments = cls.segment_reasoning(reasoning_text)
        claims: List[GroundingClaim] = []

        prefix = f"{criterion_id}-" if criterion_id else "claim-"

        for idx, seg in enumerate(segments, start=1):
            claim_id = f"{prefix}{idx:03d}"
            c_type = cls.classify_claim_type(seg)

            claim = GroundingClaim(
                claim_id=claim_id,
                claim_text=seg,
                claim_type=c_type,
                source_reference=f"trial:{trial_id}" if trial_id else None,
            )
            claims.append(claim)

        return claims
