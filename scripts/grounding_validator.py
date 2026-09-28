"""
MedMatch Deterministic Grounding and Provenance Validator.
Phase 8: Grounding Evaluation & Faithfulness Auditing.

Performs deterministic verification of:
1. Citation and Provenance Validity:
   - Valid vs. Invalid source references
   - Nonexistent or misaligned evidence spans
   - Wrong trial or criterion references
   - Wrong patient-fact references
   - Mismatched retrieval provenance methods
2. Claim Support & Entailment:
   - Direct factual support (SUPPORTED)
   - Partial support (PARTIALLY_SUPPORTED)
   - Contradiction detection (CONTRADICTED)
   - Missing evidence acknowledgment (INSUFFICIENT_EVIDENCE)
   - Unsupported assertions and hallucinations (UNSUPPORTED -> H1-H10)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from scripts.claim_extractor import DeterministicClaimExtractor
    from scripts.eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        EvidenceCitation,
    )
    from scripts.grounding_schema import (
        CitationValidationRecord,
        ClaimType,
        ContradictionStatus,
        EvidenceSourceType,
        GroundingClaim,
        GroundingEvaluation,
        GroundingEvidence,
        HallucinationCategory,
        SupportStatus,
    )
except ImportError:
    from claim_extractor import DeterministicClaimExtractor
    from eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        EvidenceCitation,
    )
    from grounding_schema import (
        CitationValidationRecord,
        ClaimType,
        ContradictionStatus,
        EvidenceSourceType,
        GroundingClaim,
        GroundingEvaluation,
        GroundingEvidence,
        HallucinationCategory,
        SupportStatus,
    )


class GroundingValidator:
    """
    Deterministic validator auditing evidence grounding, provenance fidelity,
    and hallucination occurrences in clinical reasoning records.
    """

    VERSION = "1.0.0"

    def __init__(self, extractor: Optional[DeterministicClaimExtractor] = None) -> None:
        self.extractor = extractor or DeterministicClaimExtractor()

    # -------------------------------------------------------------------------
    # 1. Ground Evidence Ingestion
    # -------------------------------------------------------------------------

    @classmethod
    def compile_ground_evidence(
        cls,
        patient_facts: List[Dict[str, Any]],
        criteria: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
    ) -> List[GroundingEvidence]:
        """
        Transforms input records into canonical GroundingEvidence instances.
        """
        evidence_list: List[GroundingEvidence] = []

        # 1. Patient Facts
        for f in patient_facts:
            fid = str(f.get("fact_id", ""))
            concept = str(f.get("concept", ""))
            snippet = str(f.get("snippet", concept))
            assertion = str(f.get("assertion", "PRESENT")).upper()
            start_c = int(f.get("start_char", -1))
            end_c = int(f.get("end_char", -1))

            evidence_list.append(
                GroundingEvidence(
                    evidence_id=fid or f"fact-{len(evidence_list)}",
                    source_type=EvidenceSourceType.PATIENT_FACT,
                    source_id=fid,
                    text=snippet,
                    start_char=start_c,
                    end_char=end_c,
                    assertion=assertion,
                )
            )

        # 2. Demographics
        if demographics:
            for k, v in demographics.items():
                evidence_list.append(
                    GroundingEvidence(
                        evidence_id=f"demo-{k}",
                        source_type=EvidenceSourceType.PATIENT_DEMOGRAPHICS,
                        source_id=f"demo-{k}",
                        text=f"{k}: {v}",
                        assertion="PRESENT",
                    )
                )

        # 3. Criteria Definitions
        for c in criteria:
            cid = str(c.get("id") or c.get("criterion_id", ""))
            desc = str(c.get("description") or c.get("criterion_text", ""))
            evidence_list.append(
                GroundingEvidence(
                    evidence_id=cid or f"crit-{len(evidence_list)}",
                    source_type=EvidenceSourceType.TRIAL_CRITERION,
                    source_id=cid,
                    criterion_reference=cid,
                    text=desc,
                    assertion="PRESENT",
                )
            )

        # 4. Retrieved Protocol Evidence
        if retrieved_evidence:
            tid = str(retrieved_evidence.get("trial_id", "retrieved_trial"))
            summary = str(retrieved_evidence.get("trial_summary", ""))
            method = retrieved_evidence.get("retrieval_method")
            rank = retrieved_evidence.get("retrieval_rank")
            score = retrieved_evidence.get("retrieval_score")

            if summary:
                evidence_list.append(
                    GroundingEvidence(
                        evidence_id=f"retrieved-{tid}",
                        source_type=EvidenceSourceType.RETRIEVED_PROTOCOL,
                        source_id=tid,
                        document_reference=f"trial:{tid}",
                        text=summary,
                        retrieval_method=method,
                        retrieval_rank=rank,
                        retrieval_score=score,
                        assertion="PRESENT",
                    )
                )

        return evidence_list

    # -------------------------------------------------------------------------
    # 2. Citation and Provenance Validation
    # -------------------------------------------------------------------------

    @classmethod
    def validate_citations(
        cls,
        citations: List[EvidenceCitation],
        patient_facts: List[Dict[str, Any]],
        trial_id: str,
        criterion_id: str,
        patient_note: Optional[str] = None,
        retrieved_evidence: Optional[Dict[str, Any]] = None,
    ) -> List[CitationValidationRecord]:
        """
        Audits every cited piece of evidence for span correctness and reference validity.
        """
        records: List[CitationValidationRecord] = []
        fact_map = {str(f.get("fact_id")): f for f in patient_facts if f.get("fact_id")}
        retrieval_method = retrieved_evidence.get("retrieval_method") if retrieved_evidence else None

        for idx, cit in enumerate(citations):
            is_valid = True
            error_type: Optional[str] = None
            error_msg: Optional[str] = None

            # 1. Fact ID Existence
            if cit.fact_id:
                if cit.fact_id not in fact_map:
                    is_valid = False
                    error_type = "WRONG_PATIENT_FACT_REFERENCE"
                    error_msg = f"Cited fact_id '{cit.fact_id}' does not exist in patient facts"

            # 2. Span Alignment in Raw Note (if offsets != -1 and note provided)
            if is_valid and patient_note and cit.start_char >= 0 and cit.end_char > cit.start_char:
                if cit.end_char > len(patient_note):
                    is_valid = False
                    error_type = "NONEXISTENT_EVIDENCE_SPAN"
                    error_msg = f"Cited span [{cit.start_char}:{cit.end_char}] exceeds note length ({len(patient_note)})"
                else:
                    actual_span_text = patient_note[cit.start_char:cit.end_char]
                    if cit.text_snippet.strip().lower() not in actual_span_text.strip().lower():
                        is_valid = False
                        error_type = "NONEXISTENT_EVIDENCE_SPAN"
                        error_msg = f"Cited text '{cit.text_snippet}' does not match actual span '{actual_span_text}'"

            # 3. Source Reference Integrity
            if is_valid and cit.source_field:
                if ":" in cit.source_field:
                    prefix, target = cit.source_field.split(":", 1)
                    if prefix in {"dense", "hybrid_rrf", "hybrid_reranked"}:
                        # Check retrieval method consistency
                        if retrieval_method and prefix != retrieval_method:
                            is_valid = False
                            error_type = "MISMATCHED_RETRIEVAL_PROVENANCE"
                            error_msg = f"Citation retrieval method '{prefix}' conflicts with active method '{retrieval_method}'"
                        # Check target trial reference
                        if target.startswith("trial:") and not target.endswith(trial_id):
                            is_valid = False
                            error_type = "WRONG_TRIAL_REFERENCE"
                            error_msg = f"Citation references wrong trial target '{target}', expected trial:{trial_id}"
                elif cit.source_field != "patient_note":
                    # Non-standard source field without colon
                    if not cit.source_field.startswith("trial:"):
                        is_valid = False
                        error_type = "INVALID_SOURCE_REFERENCE"
                        error_msg = f"Unrecognized source reference format: '{cit.source_field}'"

            records.append(
                CitationValidationRecord(
                    citation_index=idx,
                    cited_fact_id=cit.fact_id,
                    cited_source_field=cit.source_field,
                    cited_snippet=cit.text_snippet,
                    cited_start_char=cit.start_char,
                    cited_end_char=cit.end_char,
                    is_valid=is_valid,
                    error_type=error_type,
                    error_message=error_msg,
                )
            )

        return records

    # -------------------------------------------------------------------------
    # 3. Claim Grounding Verification
    # -------------------------------------------------------------------------

    @classmethod
    def evaluate_claim_support(
        cls,
        claim: GroundingClaim,
        evidence_corpus: List[GroundingEvidence],
        demographics: Optional[Dict[str, Any]] = None,
    ) -> GroundingClaim:
        """
        Determines the SupportStatus and potential HallucinationCategory for an atomic claim.
        """
        claim_text_lower = claim.claim_text.lower()

        # Rule A: Inferred claims are intrinsically unsupported inferences
        if claim.claim_type == ClaimType.INFERRED_CLAIM:
            return claim.model_copy(
                update={
                    "support_status": SupportStatus.UNSUPPORTED,
                    "hallucination_category": HallucinationCategory.H5_UNSUPPORTED_CLINICAL_INFERENCE,
                    "rationale": "Claim makes speculative clinical inference without direct evidence entailment.",
                }
            )

        # Rule B: Explicit missingness / unknown statements
        missing_phrases = ["not documented", "cannot be determined", "status is unknown", "insufficient evidence", "no documented evidence"]
        if any(p in claim_text_lower for p in missing_phrases):
            return claim.model_copy(
                update={
                    "support_status": SupportStatus.INSUFFICIENT_EVIDENCE,
                    "confidence": 1.0,
                    "rationale": "Claim faithfully reports missing or unknown information.",
                }
            )

        # Rule C: Check for Contradictions with Negated Facts
        for ev in evidence_corpus:
            if ev.source_type == EvidenceSourceType.PATIENT_FACT and ev.assertion == "ABSENT":
                # If evidence says ABSENT (e.g. no brain metastases) and claim affirms concept
                ev_concept_lower = ev.text.lower()
                # Extract core nouns (skip "denies", "no", "negative for")
                clean_concept = re.sub(r"\b(?:no|denies|negative\s+for|without)\b", "", ev_concept_lower).strip()
                if clean_concept and clean_concept in claim_text_lower:
                    # Contradiction: patient fact was negated, but claim asserts presence
                    if not any(neg in claim_text_lower for neg in ["no", "denies", "negative", "without", "absent"]):
                        return claim.model_copy(
                            update={
                                "support_status": SupportStatus.CONTRADICTED,
                                "contradiction_status": ContradictionStatus.ASSERTION_CONFLICT,
                                "hallucination_category": HallucinationCategory.H6_CONTRADICTION_OF_SOURCE_EVIDENCE,
                                "supporting_evidence_ids": [ev.evidence_id],
                                "rationale": f"Claim affirms '{clean_concept}' which is documented as ABSENT in {ev.evidence_id}.",
                            }
                        )

        # Rule D: Numerical Values & Age Checks
        if claim.claim_type == ClaimType.NUMERICAL_VALUE and demographics:
            # Check age matching
            age_match = re.search(r"\bage\s*(?:is\s*)?(\d+)\b", claim_text_lower)
            if age_match:
                claimed_age = int(age_match.group(1))
                actual_age = int(demographics.get("age", -1))
                if actual_age > 0:
                    if claimed_age == actual_age:
                        return claim.model_copy(
                            update={
                                "support_status": SupportStatus.SUPPORTED,
                                "supporting_evidence_ids": ["demo-age"],
                                "rationale": f"Claimed age {claimed_age} matches documented age {actual_age}.",
                            }
                        )
                    else:
                        return claim.model_copy(
                            update={
                                "support_status": SupportStatus.CONTRADICTED,
                                "contradiction_status": ContradictionStatus.NUMERICAL_CONFLICT,
                                "hallucination_category": HallucinationCategory.H3_FABRICATED_NUMERICAL_VALUE,
                                "rationale": f"Claimed age {claimed_age} conflicts with documented age {actual_age}.",
                            }
                        )

        # Rule E: Direct Factual Entailment
        if claim.claim_type in (ClaimType.PATIENT_FACT, ClaimType.TEMPORAL_FACT, ClaimType.NUMERICAL_VALUE):
            relevant_corpus = [
                ev for ev in evidence_corpus
                if ev.source_type in (
                    EvidenceSourceType.PATIENT_FACT,
                    EvidenceSourceType.PATIENT_NOTE,
                    EvidenceSourceType.PATIENT_DEMOGRAPHICS,
                    EvidenceSourceType.RETRIEVED_PROTOCOL,
                )
            ]
        elif claim.claim_type == ClaimType.TRIAL_CRITERION:
            relevant_corpus = [
                ev for ev in evidence_corpus
                if ev.source_type in (EvidenceSourceType.TRIAL_CRITERION, EvidenceSourceType.RETRIEVED_PROTOCOL)
            ]
        else:
            relevant_corpus = evidence_corpus

        supporting_ids: List[str] = []
        is_partial = False
        partial_reason = ""

        # Aggregate all tokens present across all relevant evidence
        all_ev_tokens: Set[str] = set()
        for ev in relevant_corpus:
            all_ev_tokens.update(re.findall(r"\b[A-Za-z0-9]+\b", ev.text.lower()))

        # Non-clinical / common filler words
        filler_words = {
            "patient", "has", "confirmed", "and", "the", "with", "a", "an", "is", "in", "of",
            "to", "prior", "completed", "therapy", "treatment", "direct", "evidence", "found",
            "meets", "fails", "status", "history", "diagnosed", "documented", "presence",
            "absence", "negative", "positive", "denies", "any", "no", "not", "without", "shows"
        }

        claim_tokens = set(re.findall(r"\b[A-Za-z0-9]+\b", claim_text_lower))
        clinical_claim_tokens = {t for t in claim_tokens if t not in filler_words and len(t) > 2 and not t.isdigit()}

        for ev in relevant_corpus:
            ev_text_lower = ev.text.lower()
            ev_tokens = set(re.findall(r"\b[A-Za-z0-9]+\b", ev_text_lower))
            overlap = clinical_claim_tokens.intersection(ev_tokens)

            if len(overlap) >= 1:
                # Check if there are clinical claim tokens completely unmentioned in ANY relevant evidence
                unmentioned = [t for t in clinical_claim_tokens if t not in all_ev_tokens]
                if unmentioned:
                    is_partial = True
                    supporting_ids.append(ev.evidence_id)
                    partial_reason = f"Partially supported: matches {ev.evidence_id}, but terms {unmentioned} are unverified in record."
                else:
                    supporting_ids.append(ev.evidence_id)

        if is_partial and supporting_ids:
            return claim.model_copy(
                update={
                    "support_status": SupportStatus.PARTIALLY_SUPPORTED,
                    "supporting_evidence_ids": list(set(supporting_ids)),
                    "rationale": partial_reason,
                }
            )

        if supporting_ids:
            return claim.model_copy(
                update={
                    "support_status": SupportStatus.SUPPORTED,
                    "supporting_evidence_ids": list(set(supporting_ids)),
                    "rationale": f"Directly entailed by evidence items: {', '.join(set(supporting_ids))}.",
                }
            )

        # Rule F: Criterion claim check against criteria
        if claim.claim_type == ClaimType.TRIAL_CRITERION:
            for ev in evidence_corpus:
                if ev.source_type == EvidenceSourceType.TRIAL_CRITERION:
                    if any(t in ev.text.lower() for t in claim_text_lower.split() if len(t) > 3):
                        return claim.model_copy(
                            update={
                                "support_status": SupportStatus.SUPPORTED,
                                "supporting_evidence_ids": [ev.evidence_id],
                                "rationale": f"Matches trial criterion {ev.evidence_id}.",
                            }
                        )
            return claim.model_copy(
                update={
                    "support_status": SupportStatus.UNSUPPORTED,
                    "hallucination_category": HallucinationCategory.H2_FABRICATED_TRIAL_CRITERION,
                    "rationale": "Claimed trial requirement not found in registered criteria.",
                }
            )

        # Rule G: Eligibility Conclusion
        if claim.claim_type == ClaimType.ELIGIBILITY_CONCLUSION:
            # Conclusion is supported if intermediate reasoning has support
            return claim.model_copy(
                update={
                    "support_status": SupportStatus.PARTIALLY_SUPPORTED,
                    "rationale": "Eligibility conclusion depends on intermediate claim validity.",
                }
            )

        # Default: Unsupported Claim -> Map to appropriate category
        hallucination_cat = HallucinationCategory.H1_FABRICATED_PATIENT_FACT
        if claim.claim_type == ClaimType.NUMERICAL_VALUE:
            hallucination_cat = HallucinationCategory.H3_FABRICATED_NUMERICAL_VALUE
        elif claim.claim_type == ClaimType.TEMPORAL_FACT:
            hallucination_cat = HallucinationCategory.H4_FABRICATED_TEMPORAL_FACT

        return claim.model_copy(
            update={
                "support_status": SupportStatus.UNSUPPORTED,
                "hallucination_category": hallucination_cat,
                "rationale": "No entailing evidence found in patient facts or trial documents.",
            }
        )

    # -------------------------------------------------------------------------
    # 4. Master Evaluation Pipeline
    # -------------------------------------------------------------------------

    def evaluate_criterion_record(
        self,
        record: CriterionEvaluationRecord,
        patient_facts: List[Dict[str, Any]],
        criteria: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
    ) -> GroundingEvaluation:
        """
        Executes complete grounding and faithfulness evaluation on a CriterionEvaluationRecord.
        """
        # 1. Compile verified evidence
        evidence_corpus = self.compile_ground_evidence(
            patient_facts=patient_facts,
            criteria=criteria,
            demographics=demographics,
            retrieved_evidence=retrieved_evidence,
            patient_note=patient_note,
        )

        # 2. Extract atomic claims from reasoning
        raw_claims = self.extractor.extract_claims(
            reasoning_text=record.reasoning,
            criterion_id=record.criterion_id,
            trial_id=record.trial_id,
        )

        # 3. Evaluate each claim against evidence
        evaluated_claims: List[GroundingClaim] = []
        for cl in raw_claims:
            eval_cl = self.evaluate_claim_support(cl, evidence_corpus, demographics=demographics)
            evaluated_claims.append(eval_cl)

        # 4. Audit attached citations
        citation_records = self.validate_citations(
            citations=record.evidence_citations,
            patient_facts=patient_facts,
            trial_id=record.trial_id,
            criterion_id=record.criterion_id,
            patient_note=patient_note,
            retrieved_evidence=retrieved_evidence,
        )

        # 5. Check Conclusion Grounding ($H8 detection)
        has_underlying_failure = any(
            c.support_status in (SupportStatus.UNSUPPORTED, SupportStatus.CONTRADICTED)
            for c in evaluated_claims
            if c.claim_type != ClaimType.ELIGIBILITY_CONCLUSION
        )
        has_underlying_partial = any(
            c.support_status == SupportStatus.PARTIALLY_SUPPORTED
            for c in evaluated_claims
            if c.claim_type != ClaimType.ELIGIBILITY_CONCLUSION
        )

        for i, c in enumerate(evaluated_claims):
            if c.claim_type == ClaimType.ELIGIBILITY_CONCLUSION:
                if has_underlying_failure:
                    evaluated_claims[i] = c.model_copy(
                        update={
                            "support_status": SupportStatus.UNSUPPORTED,
                            "hallucination_category": HallucinationCategory.H8_UNSUPPORTED_ELIGIBILITY_CONCLUSION,
                            "rationale": "Eligibility conclusion is unsupported because underlying clinical assertions lack evidence.",
                        }
                    )
                elif has_underlying_partial:
                    evaluated_claims[i] = c.model_copy(
                        update={
                            "support_status": SupportStatus.PARTIALLY_SUPPORTED,
                            "rationale": "Eligibility conclusion is partially supported because underlying clinical propositions are partially supported.",
                        }
                    )
                else:
                    evaluated_claims[i] = c.model_copy(
                        update={
                            "support_status": SupportStatus.SUPPORTED,
                            "rationale": "Eligibility conclusion logically supported by verified underlying evidence.",
                        }
                    )

        supported_cnt = sum(1 for c in evaluated_claims if c.support_status == SupportStatus.SUPPORTED)
        partially_cnt = sum(1 for c in evaluated_claims if c.support_status == SupportStatus.PARTIALLY_SUPPORTED)
        unsupported_cnt = sum(1 for c in evaluated_claims if c.support_status == SupportStatus.UNSUPPORTED)
        contradicted_cnt = sum(1 for c in evaluated_claims if c.support_status == SupportStatus.CONTRADICTED)
        insufficient_cnt = sum(1 for c in evaluated_claims if c.support_status == SupportStatus.INSUFFICIENT_EVIDENCE)

        total_claims = len(evaluated_claims)

        # 6. Compute Metrics
        evaluable_claims = max(1, total_claims)
        csr = supported_cnt / float(evaluable_claims)
        ucr = unsupported_cnt / float(evaluable_claims)
        cr = contradicted_cnt / float(evaluable_claims)

        valid_citations = sum(1 for c in citation_records if c.is_valid)
        total_citations = len(citation_records)
        cvr = (valid_citations / float(total_citations)) if total_citations > 0 else 1.0

        claims_requiring_evidence = [
            c for c in evaluated_claims if c.claim_type in (ClaimType.PATIENT_FACT, ClaimType.NUMERICAL_VALUE, ClaimType.TEMPORAL_FACT)
        ]
        evidence_coverage = (
            sum(1 for c in claims_requiring_evidence if c.support_status == SupportStatus.SUPPORTED) / float(len(claims_requiring_evidence))
            if claims_requiring_evidence else 1.0
        )

        # Composite Grounding Score: weighted combination penalizing contradictions heavily
        grounding_score = max(
            0.0,
            round(csr * 0.6 + cvr * 0.2 + evidence_coverage * 0.2 - (cr * 0.8), 4)
        )

        hallucination_rate = round((unsupported_cnt + contradicted_cnt) / float(evaluable_claims), 4)
        has_hallucinations = (unsupported_cnt > 0) or (contradicted_cnt > 0) or (valid_citations < total_citations)
        is_faithful = (
            contradicted_cnt == 0
            and unsupported_cnt == 0
            and partially_cnt == 0
            and valid_citations == total_citations
        )

        return GroundingEvaluation(
            evaluation_id=f"ground-eval-{record.trial_id}-{record.criterion_id}",
            trial_id=record.trial_id,
            criterion_id=record.criterion_id,
            raw_reasoning_text=record.reasoning,
            claims=evaluated_claims,
            citations_audited=citation_records,
            total_claims=total_claims,
            supported_claim_count=supported_cnt,
            partially_supported_claim_count=partially_cnt,
            unsupported_claim_count=unsupported_cnt,
            contradicted_claim_count=contradicted_cnt,
            insufficient_evidence_count=insufficient_cnt,
            claim_support_rate=round(csr, 4),
            unsupported_claim_rate=round(ucr, 4),
            contradiction_rate=round(cr, 4),
            citation_validity_rate=round(cvr, 4),
            evidence_coverage=round(evidence_coverage, 4),
            grounding_score=grounding_score,
            hallucination_rate=hallucination_rate,
            has_hallucinations=has_hallucinations,
            is_faithful=is_faithful,
            evaluator_version=self.VERSION,
        )
