"""
MedMatch Evidence-Grounded Eligibility Reasoner.
Phase 6: Eligibility Reasoning.

Implements rule-based, symbolic, and evidence-grounded reasoning over:
1. Patient clinical facts (from PatientClinicalProfile or extracted facts)
2. Clinical trial eligibility criteria (inclusion & exclusion)
3. Explicit negation, assertion, and uncertainty states
4. Numerical thresholds and unit compatibility
5. Temporal constraints (durations, recency, historical status)
6. Compound criteria (AND / OR)
7. Explicit detection and handling of conflicting evidence

Strict Epistemic Principle:
- Absence of evidence is NEVER evidence of absence.
- Missing or ambiguous evidence yields UNKNOWN.
- Contradictory evidence yields UNKNOWN with explicit conflict justification.
- Every PASS or FAIL must cite grounded evidence.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from scripts.eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        CriterionType,
        EvidenceCitation,
    )
except ImportError:
    from eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        CriterionType,
        EvidenceCitation,
    )


class RuleBasedEligibilityReasoner:
    """
    Deterministic research-grade eligibility reasoner operating strictly on
    structured patient facts, demographics, and clinical trial criteria.
    """

    def __init__(self, reasoner_id: str = "rule_based_research_reasoner_v1") -> None:
        self.reasoner_id = reasoner_id

    # -------------------------------------------------------------------------
    # Numerical & Threshold Helper Functions
    # -------------------------------------------------------------------------

    _NUMERICAL_REGEX = re.compile(
        r"(?:(age|creatinine|ecog|platelets?|ejection fraction|alt|ast|bilirubin|wbc|hemoglobin)\s*([><=]=?|<|>|=)\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%^0-9]+)?)",
        re.IGNORECASE,
    )

    @classmethod
    def parse_numerical_threshold(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Extracts numerical constraint: parameter, operator, value, unit.
        """
        match = cls._NUMERICAL_REGEX.search(text)
        if not match:
            return None
        param = match.group(1).lower()
        op = match.group(2)
        val = float(match.group(3))
        unit = match.group(4) if match.group(4) else ""
        return {"parameter": param, "operator": op, "value": val, "unit": unit}

    @classmethod
    def evaluate_numerical_comparison(
        cls, patient_val: float, operator: str, threshold: float
    ) -> bool:
        """Evaluates comparison between patient value and threshold."""
        if operator in (">=", "=>"):
            return patient_val >= threshold
        elif operator in ("<=", "=<"):
            return patient_val <= threshold
        elif operator == ">":
            return patient_val > threshold
        elif operator == "<":
            return patient_val < threshold
        elif operator in ("==", "="):
            return patient_val == threshold
        elif operator == "!=":
            return patient_val != threshold
        return False

    # -------------------------------------------------------------------------
    # Core Criterion Evaluation
    # -------------------------------------------------------------------------

    def evaluate_criterion(
        self,
        criterion: Dict[str, Any],
        trial_id: str,
        patient_facts: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
    ) -> CriterionEvaluationRecord:
        """
        Evaluates a single criterion against patient facts and demographics.
        """
        cid = criterion.get("id") or criterion.get("criterion_id") or "UNKNOWN_CRITERION"
        ctype_str = criterion.get("criteria_type") or criterion.get("criterion_type") or "INCLUSION"
        ctype = (
            CriterionType.EXCLUSION
            if "EXCLUSION" in str(ctype_str).upper()
            else CriterionType.INCLUSION
        )
        ctext = criterion.get("description") or criterion.get("criterion_text") or ""

        # 1. Check for Compound Logic (AND / OR)
        compound_res = self._check_compound_criteria(
            criterion, trial_id, ctype, ctext, patient_facts, demographics, patient_note
        )
        if compound_res is not None:
            return compound_res

        # 2. Check for Numerical Thresholds (e.g. age, creatinine, ECOG)
        num_res = self._check_numerical_criteria(
            cid, trial_id, ctype, ctext, patient_facts, demographics, patient_note
        )
        if num_res is not None:
            return num_res

        # 3. Check for Clinical Concept / Condition Matching with Negation & Conflicts
        concept_res = self._check_concept_and_negation(
            cid, trial_id, ctype, ctext, patient_facts, patient_note
        )
        return concept_res

    # -------------------------------------------------------------------------
    # Compound Criteria Evaluation (AND / OR)
    # -------------------------------------------------------------------------

    def _check_compound_criteria(
        self,
        criterion: Dict[str, Any],
        trial_id: str,
        ctype: CriterionType,
        ctext: str,
        patient_facts: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]],
        patient_note: Optional[str],
    ) -> Optional[CriterionEvaluationRecord]:
        cid = criterion.get("id") or criterion.get("criterion_id") or "UNKNOWN_CRITERION"

        # Check explicit sub-criteria in dictionary if present
        sub_criteria = criterion.get("sub_criteria") or []
        compound_op = criterion.get("compound_operator")  # "AND" or "OR"

        # Alternatively, detect simple natural language compound patterns "X AND Y", "A OR B"
        if not sub_criteria:
            if " AND " in ctext and not self._NUMERICAL_REGEX.search(ctext):
                parts = [p.strip() for p in ctext.split(" AND ") if p.strip()]
                if len(parts) >= 2:
                    sub_criteria = [{"id": f"{cid}_sub_{i}", "criterion_text": p, "criterion_type": ctype} for i, p in enumerate(parts)]
                    compound_op = "AND"
            elif " OR " in ctext and not self._NUMERICAL_REGEX.search(ctext):
                parts = [p.strip() for p in ctext.split(" OR ") if p.strip()]
                if len(parts) >= 2:
                    sub_criteria = [{"id": f"{cid}_sub_{i}", "criterion_text": p, "criterion_type": ctype} for i, p in enumerate(parts)]
                    compound_op = "OR"

        if not sub_criteria or not compound_op:
            return None

        # Recursively evaluate sub-criteria
        sub_evals: List[CriterionEvaluationRecord] = []
        for sub_c in sub_criteria:
            sub_res = self.evaluate_criterion(
                criterion=sub_c,
                trial_id=trial_id,
                patient_facts=patient_facts,
                demographics=demographics,
                patient_note=patient_note,
            )
            sub_evals.append(sub_res)

        all_citations: List[EvidenceCitation] = []
        all_fact_refs: List[str] = []
        for s in sub_evals:
            all_citations.extend(s.evidence_citations)
            all_fact_refs.extend(s.patient_fact_references)

        if compound_op == "AND":
            # AND: If any FAIL -> FAIL. Else if any UNKNOWN -> UNKNOWN. Else all PASS -> PASS.
            if any(s.status == CriterionEvaluationStatus.FAIL for s in sub_evals):
                status = CriterionEvaluationStatus.FAIL
                reasoning = f"Compound AND condition failed: {[s.reasoning for s in sub_evals if s.status == CriterionEvaluationStatus.FAIL]}"
            elif any(s.status == CriterionEvaluationStatus.UNKNOWN for s in sub_evals):
                status = CriterionEvaluationStatus.UNKNOWN
                reasoning = f"Compound AND condition has unknown components: {[s.reasoning for s in sub_evals if s.status == CriterionEvaluationStatus.UNKNOWN]}"
            else:
                status = CriterionEvaluationStatus.PASS
                reasoning = "All components of compound AND condition satisfied."
        else:  # OR
            # OR: If any PASS -> PASS. Else if all FAIL -> FAIL. Else if any UNKNOWN -> UNKNOWN.
            if any(s.status == CriterionEvaluationStatus.PASS for s in sub_evals):
                status = CriterionEvaluationStatus.PASS
                reasoning = f"Compound OR condition satisfied by: {[s.reasoning for s in sub_evals if s.status == CriterionEvaluationStatus.PASS]}"
            elif all(s.status == CriterionEvaluationStatus.FAIL for s in sub_evals):
                status = CriterionEvaluationStatus.FAIL
                reasoning = "All alternative branches of compound OR condition failed."
            else:
                status = CriterionEvaluationStatus.UNKNOWN
                reasoning = "Compound OR condition cannot be satisfied due to missing/unknown branches."

        # Filter out empty evidence if UNKNOWN
        citations_to_keep = all_citations if status != CriterionEvaluationStatus.UNKNOWN else []
        fact_refs_to_keep = all_fact_refs if status != CriterionEvaluationStatus.UNKNOWN else []

        if status in (CriterionEvaluationStatus.PASS, CriterionEvaluationStatus.FAIL) and not citations_to_keep and not fact_refs_to_keep:
            # Fallback citation
            citations_to_keep.append(
                EvidenceCitation(text_snippet=ctext[:100], source_field="compound_criterion")
            )

        return CriterionEvaluationRecord(
            criterion_id=cid,
            trial_id=trial_id,
            criterion_type=ctype,
            criterion_text=ctext,
            status=status,
            reasoning=reasoning,
            evidence_citations=citations_to_keep,
            patient_fact_references=fact_refs_to_keep,
            evaluator=self.reasoner_id,
        )

    # -------------------------------------------------------------------------
    # Numerical Criteria Evaluation
    # -------------------------------------------------------------------------

    def _check_numerical_criteria(
        self,
        cid: str,
        trial_id: str,
        ctype: CriterionType,
        ctext: str,
        patient_facts: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]],
        patient_note: Optional[str],
    ) -> Optional[CriterionEvaluationRecord]:
        thresh_info = self.parse_numerical_threshold(ctext)
        if not thresh_info:
            return None

        param = thresh_info["parameter"]
        op = thresh_info["operator"]
        thresh_val = thresh_info["value"]
        thresh_unit = thresh_info["unit"]

        # Check demographic age
        if param == "age":
            if not demographics or "age" not in demographics or demographics["age"] is None:
                return CriterionEvaluationRecord(
                    criterion_id=cid,
                    trial_id=trial_id,
                    criterion_type=ctype,
                    criterion_text=ctext,
                    status=CriterionEvaluationStatus.UNKNOWN,
                    reasoning="Patient age is missing from demographics.",
                    uncertainty_notes="Age not documented.",
                    numerical_threshold=f"age {op} {thresh_val}",
                    evaluator=self.reasoner_id,
                )

            patient_age = float(demographics["age"])
            satisfies = self.evaluate_numerical_comparison(patient_age, op, thresh_val)

            # Inclusion: satisfies -> PASS, violates -> FAIL
            # Exclusion: satisfies -> FAIL (triggered), violates -> PASS (cleared)
            if ctype == CriterionType.INCLUSION:
                status = CriterionEvaluationStatus.PASS if satisfies else CriterionEvaluationStatus.FAIL
            else:
                status = CriterionEvaluationStatus.FAIL if satisfies else CriterionEvaluationStatus.PASS

            citation = EvidenceCitation(
                text_snippet=f"Age: {patient_age}",
                source_field="demographics",
            )
            reasoning = (
                f"Patient age ({patient_age}) {'satisfies' if satisfies else 'violates'} "
                f"criterion requirement '{param} {op} {thresh_val}'."
            )
            return CriterionEvaluationRecord(
                criterion_id=cid,
                trial_id=trial_id,
                criterion_type=ctype,
                criterion_text=ctext,
                status=status,
                reasoning=reasoning,
                evidence_citations=[citation],
                numerical_threshold=f"age {op} {thresh_val}",
                evaluator=self.reasoner_id,
            )

        # Check quantitative lab facts or performance status (ECOG, creatinine, etc.)
        matched_fact: Optional[Dict[str, Any]] = None
        for fact in patient_facts:
            concept = str(fact.get("concept", "")).lower()
            if param in concept:
                matched_fact = fact
                break

        if not matched_fact or matched_fact.get("value") is None:
            return CriterionEvaluationRecord(
                criterion_id=cid,
                trial_id=trial_id,
                criterion_type=ctype,
                criterion_text=ctext,
                status=CriterionEvaluationStatus.UNKNOWN,
                reasoning=f"Required laboratory/clinical measurement '{param}' is not documented in patient facts.",
                uncertainty_notes=f"Missing measurement for {param}.",
                numerical_threshold=f"{param} {op} {thresh_val} {thresh_unit}".strip(),
                evaluator=self.reasoner_id,
            )

        try:
            patient_num = float(matched_fact["value"])
        except (ValueError, TypeError):
            return CriterionEvaluationRecord(
                criterion_id=cid,
                trial_id=trial_id,
                criterion_type=ctype,
                criterion_text=ctext,
                status=CriterionEvaluationStatus.UNKNOWN,
                reasoning=f"Patient measurement value '{matched_fact.get('value')}' cannot be parsed as a float.",
                uncertainty_notes="Non-numeric measurement.",
                evaluator=self.reasoner_id,
            )

        # Unit mismatch check if threshold has an explicit unit
        fact_unit = str(matched_fact.get("unit") or "").lower().strip()
        thresh_unit_clean = thresh_unit.lower().strip()
        if thresh_unit_clean and fact_unit and thresh_unit_clean != fact_unit:
            # Report unit mismatch as UNKNOWN to prevent erroneous comparison
            return CriterionEvaluationRecord(
                criterion_id=cid,
                trial_id=trial_id,
                criterion_type=ctype,
                criterion_text=ctext,
                status=CriterionEvaluationStatus.UNKNOWN,
                reasoning=(
                    f"Unit mismatch: criterion specifies '{thresh_unit}', "
                    f"but patient fact documents '{matched_fact.get('unit')}'."
                ),
                uncertainty_notes="Unit mismatch requires clinical conversion.",
                evaluator=self.reasoner_id,
            )

        satisfies = self.evaluate_numerical_comparison(patient_num, op, thresh_val)

        if ctype == CriterionType.INCLUSION:
            status = CriterionEvaluationStatus.PASS if satisfies else CriterionEvaluationStatus.FAIL
        else:
            status = CriterionEvaluationStatus.FAIL if satisfies else CriterionEvaluationStatus.PASS

        fid = matched_fact.get("fact_id")
        citation = EvidenceCitation(
            fact_id=fid,
            text_snippet=f"{param}: {patient_num} {matched_fact.get('unit', '')}".strip(),
            source_field="patient_facts",
            start_char=matched_fact.get("start_char", -1),
            end_char=matched_fact.get("end_char", -1),
        )

        reasoning = (
            f"Patient measurement '{param}' = {patient_num} {matched_fact.get('unit', '')} "
            f"{'satisfies' if satisfies else 'violates'} threshold '{param} {op} {thresh_val}'."
        )

        return CriterionEvaluationRecord(
            criterion_id=cid,
            trial_id=trial_id,
            criterion_type=ctype,
            criterion_text=ctext,
            status=status,
            reasoning=reasoning,
            evidence_citations=[citation],
            patient_fact_references=[fid] if fid else [],
            numerical_threshold=f"{param} {op} {thresh_val}",
            evaluator=self.reasoner_id,
        )

    # -------------------------------------------------------------------------
    # Concept Matching, Negation, Temporal & Conflict Checking
    # -------------------------------------------------------------------------

    def _check_concept_and_negation(
        self,
        cid: str,
        trial_id: str,
        ctype: CriterionType,
        ctext: str,
        patient_facts: List[Dict[str, Any]],
        patient_note: Optional[str],
    ) -> CriterionEvaluationRecord:
        """
        Evaluates qualitative conditions with explicit assertion tracking and conflict detection.
        """
        ctext_lower = ctext.lower()

        # Find all patient facts that match the criterion concept
        matching_facts: List[Dict[str, Any]] = []
        for fact in patient_facts:
            concept = str(fact.get("concept", "")).lower()
            if not concept:
                continue
            # Substring match or word match
            if concept in ctext_lower or any(word in ctext_lower for word in concept.split() if len(word) > 3):
                matching_facts.append(fact)

        # If zero facts match: Missing information -> UNKNOWN
        if not matching_facts:
            return CriterionEvaluationRecord(
                criterion_id=cid,
                trial_id=trial_id,
                criterion_type=ctype,
                criterion_text=ctext,
                status=CriterionEvaluationStatus.UNKNOWN,
                reasoning=(
                    f"Criterion concept not mentioned in patient profile. "
                    "Silence cannot be treated as absence."
                ),
                uncertainty_notes="Concept not mentioned in available clinical evidence.",
                evaluator=self.reasoner_id,
            )

        # Check for Conflicting Evidence (both PRESENT and ABSENT for the same concept)
        assertions = {str(f.get("assertion", "")).upper() for f in matching_facts}
        if "PRESENT" in assertions and "ABSENT" in assertions:
            return CriterionEvaluationRecord(
                criterion_id=cid,
                trial_id=trial_id,
                criterion_type=ctype,
                criterion_text=ctext,
                status=CriterionEvaluationStatus.UNKNOWN,
                reasoning=(
                    "Conflicting clinical evidence detected: patient profile contains both "
                    "PRESENT and ABSENT assertions for this concept. Requires manual clinical reconciliation."
                ),
                uncertainty_notes="Contradictory evidence in patient records.",
                evaluator=self.reasoner_id,
            )

        # Check for Uncertainty/Possible assertions
        if "POSSIBLE" in assertions or "UNCERTAIN" in assertions:
            return CriterionEvaluationRecord(
                criterion_id=cid,
                trial_id=trial_id,
                criterion_type=ctype,
                criterion_text=ctext,
                status=CriterionEvaluationStatus.UNKNOWN,
                reasoning=(
                    "Evidence is documented as POSSIBLE / suspected, but not confirmed. "
                    "Cannot definitively establish eligibility."
                ),
                uncertainty_notes="Unconfirmed or suspected finding.",
                evaluator=self.reasoner_id,
            )

        # Representative fact (first matching fact)
        primary_fact = matching_facts[0]
        assertion = str(primary_fact.get("assertion", "PRESENT")).upper()
        fid = primary_fact.get("fact_id")

        # Temporal constraint check
        temporal_res = self._check_temporal_compatibility(ctext_lower, primary_fact)
        if temporal_res is not None:
            # If temporal check returned UNKNOWN or FAIL
            status, temp_reason = temporal_res
            if status == CriterionEvaluationStatus.UNKNOWN:
                return CriterionEvaluationRecord(
                    criterion_id=cid,
                    trial_id=trial_id,
                    criterion_type=ctype,
                    criterion_text=ctext,
                    status=CriterionEvaluationStatus.UNKNOWN,
                    reasoning=temp_reason,
                    uncertainty_notes="Temporal constraint could not be verified.",
                    evaluator=self.reasoner_id,
                )
            elif status == CriterionEvaluationStatus.FAIL:
                citation = EvidenceCitation(
                    fact_id=fid,
                    text_snippet=str(primary_fact.get("snippet", primary_fact.get("concept", ""))),
                    source_field="patient_facts",
                    start_char=primary_fact.get("start_char", -1),
                    end_char=primary_fact.get("end_char", -1),
                    assertion_type=assertion,
                )
                return CriterionEvaluationRecord(
                    criterion_id=cid,
                    trial_id=trial_id,
                    criterion_type=ctype,
                    criterion_text=ctext,
                    status=CriterionEvaluationStatus.FAIL,
                    reasoning=temp_reason,
                    evidence_citations=[citation],
                    patient_fact_references=[fid] if fid else [],
                    evaluator=self.reasoner_id,
                )

        # Determine PASS / FAIL based on assertion and criterion type
        # INCLUSION:
        # - PRESENT -> PASS
        # - ABSENT -> FAIL
        # EXCLUSION:
        # - PRESENT -> FAIL (exclusion triggered)
        # - ABSENT -> PASS (exclusion confirmed satisfied/absent)
        if ctype == CriterionType.INCLUSION:
            if assertion == "PRESENT":
                status = CriterionEvaluationStatus.PASS
                reasoning = (
                    f"Patient is confirmed to have required condition '{primary_fact.get('concept')}'. "
                    f"Inclusion criterion satisfied."
                )
            elif assertion == "ABSENT":
                status = CriterionEvaluationStatus.FAIL
                reasoning = (
                    f"Patient is explicitly documented as NOT having '{primary_fact.get('concept')}'. "
                    f"Required inclusion criterion failed."
                )
            else:
                status = CriterionEvaluationStatus.UNKNOWN
                reasoning = f"Uncertain assertion state: {assertion}."
        else:  # EXCLUSION
            if assertion == "PRESENT":
                status = CriterionEvaluationStatus.FAIL
                reasoning = (
                    f"Patient is confirmed to have excluded condition '{primary_fact.get('concept')}'. "
                    f"Exclusion criterion triggered."
                )
            elif assertion == "ABSENT":
                status = CriterionEvaluationStatus.PASS
                reasoning = (
                    f"Patient is explicitly documented as free of excluded condition '{primary_fact.get('concept')}'. "
                    f"Exclusion criterion passed."
                )
            else:
                status = CriterionEvaluationStatus.UNKNOWN
                reasoning = f"Uncertain assertion state: {assertion}."

        citation = EvidenceCitation(
            fact_id=fid,
            text_snippet=str(primary_fact.get("snippet", primary_fact.get("concept", ""))),
            source_field="patient_facts",
            start_char=primary_fact.get("start_char", -1),
            end_char=primary_fact.get("end_char", -1),
            assertion_type=assertion,
        )

        return CriterionEvaluationRecord(
            criterion_id=cid,
            trial_id=trial_id,
            criterion_type=ctype,
            criterion_text=ctext,
            status=status,
            reasoning=reasoning,
            evidence_citations=[citation],
            patient_fact_references=[fid] if fid else [],
            is_negated=(assertion == "ABSENT"),
            evaluator=self.reasoner_id,
        )

    # -------------------------------------------------------------------------
    # Temporal Helper
    # -------------------------------------------------------------------------

    def _check_temporal_compatibility(
        self, ctext_lower: str, fact: Dict[str, Any]
    ) -> Optional[Tuple[CriterionEvaluationStatus, str]]:
        """
        Checks whether temporal window in criterion matches fact temporality.
        Returns None if no temporal constraint in criterion or compatibility holds.
        Returns (UNKNOWN, reason) or (FAIL, reason) if violated or unverifiable.
        """
        temporal = fact.get("temporal") or {}
        is_current = fact.get("is_current")

        # Criterion requires 'prior history' or 'history of'
        if "history of" in ctext_lower or "prior history" in ctext_lower:
            # If fact is explicitly marked as current only and cannot be verified as history
            # In clinical medicine, a current disease implies history, but for acute events (e.g. prior MI),
            # check temporality
            pass

        # Criterion requires 'current' or 'active'
        if "currently" in ctext_lower or "active" in ctext_lower:
            if is_current is False:
                return (
                    CriterionEvaluationStatus.FAIL,
                    "Condition is documented as historical / resolved, but criterion requires active/current status.",
                )
            elif is_current is None:
                return (
                    CriterionEvaluationStatus.UNKNOWN,
                    "Criterion requires active/current disease status, but temporality is not documented as current.",
                )

        # Criterion specifies a recency window (e.g., 'within 30 days', 'within 6 months')
        match_days = re.search(r"within\s+([0-9]+)\s+days?", ctext_lower)
        if match_days:
            max_days = int(match_days.group(1))
            duration_days = temporal.get("duration_days")
            if duration_days is None:
                return (
                    CriterionEvaluationStatus.UNKNOWN,
                    f"Criterion specifies occurrence within {max_days} days, but patient temporal duration is unknown.",
                )
            if duration_days > max_days:
                return (
                    CriterionEvaluationStatus.FAIL,
                    f"Event occurred {duration_days} days ago, exceeding the allowable {max_days} day window.",
                )

        return None
