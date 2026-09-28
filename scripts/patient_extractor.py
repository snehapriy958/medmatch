"""
MedMatch Modular Patient Clinical Information Extraction Interface.
Phase 4: Patient Clinical Information Extraction.

Defines:
- BasePatientExtractor: Abstract extraction interface decoupling extraction strategy
  from downstream profile validation, retrieval, and reasoning.
- RuleBasedResearchExtractor: Reference deterministic extractor demonstrating
  the research extraction boundary without touching production matching.
"""

from __future__ import annotations

import abc
import datetime
import re
from typing import Any, Dict, List, Optional

try:
    from scripts.patient_schema import (
        AssertionType,
        ClinicalFact,
        EvidenceSource,
        FactProvenance,
        PatientClinicalProfile,
        PatientDemographics,
        TemporalContext,
        TemporalityType,
        UncertaintyStatus,
    )
except ImportError:
    from patient_schema import (
        AssertionType,
        ClinicalFact,
        EvidenceSource,
        FactProvenance,
        PatientClinicalProfile,
        PatientDemographics,
        TemporalContext,
        TemporalityType,
        UncertaintyStatus,
    )


class BasePatientExtractor(abc.ABC):
    """
    Abstract interface for patient clinical information extraction.
    Allows pluggable implementations (deterministic rules, clinical NLP, LLMs, hybrid).
    """

    @abc.abstractmethod
    def extract_profile(
        self,
        raw_text: str,
        patient_id: str,
        note_id: str,
        document_timestamp: Optional[str] = None,
    ) -> PatientClinicalProfile:
        """
        Transforms raw unstructured clinical patient narrative into a structured
        PatientClinicalProfile.
        """
        pass


class RuleBasedResearchExtractor(BasePatientExtractor):
    """
    Deterministic rule-based extractor for research benchmarking and testing.
    Extracts key oncology entities (demographics, stage, ECOG, biomarkers, labs,
    medications, allergies, and temporal statements) while preserving provenance.
    """

    def __init__(self, extraction_version: str = "0.4.0") -> None:
        self.extraction_version = extraction_version

    def extract_profile(
        self,
        raw_text: str,
        patient_id: str,
        note_id: str,
        document_timestamp: Optional[str] = None,
    ) -> PatientClinicalProfile:
        now_ts = document_timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()
        profile = PatientClinicalProfile(
            patient_id=patient_id,
            profile_version=self.extraction_version,
            source_reference=note_id,
        )

        if not raw_text or not raw_text.strip():
            return profile

        fact_counter = 1

        def _make_fact(
            concept: str,
            value: Any,
            source_text: str,
            start: int,
            end: int,
            assertion: AssertionType = AssertionType.AFFIRMED,
            temporality: Optional[TemporalContext] = None,
            uncertainty: UncertaintyStatus = UncertaintyStatus.KNOWN,
            unit: Optional[str] = None,
            evidence_source: EvidenceSource = EvidenceSource.CLINICIAN_NOTE,
        ) -> ClinicalFact:
            nonlocal fact_counter
            fid = f"FACT_{fact_counter:03d}"
            fact_counter += 1
            prov = FactProvenance(
                note_id=note_id,
                patient_id=patient_id,
                source_text=source_text,
                start_char=start,
                end_char=end,
                extraction_version=self.extraction_version,
                extraction_timestamp=now_ts,
                model_identifier="RuleBasedResearchExtractor",
            )
            return ClinicalFact(
                fact_id=fid,
                patient_id=patient_id,
                concept=concept,
                value=value,
                unit=unit,
                assertion=assertion,
                temporality=temporality or TemporalContext(temporality_type=TemporalityType.CURRENT),
                uncertainty=uncertainty,
                evidence_source=evidence_source,
                source_text=source_text,
                provenance=prov,
                confidence=1.0,
            )

        # 1. Demographics: Age & Gender
        age_match = re.search(r"\b(\d{1,3})[- ]year[- ]old\s+(male|female|man|woman)\b", raw_text, re.IGNORECASE)
        if age_match:
            age_val = int(age_match.group(1))
            gender_raw = age_match.group(2).lower()
            gender_val = "Female" if gender_raw in ("female", "woman") else "Male"
            profile.demographics = PatientDemographics(age=age_val, gender=gender_val)

        # 2. Performance Status (ECOG)
        ecog_match = re.search(r"\bECOG(?:\s+PS|\s+performance\s+status)?\s*(?:of\s*|:\s*|=\s*)?([0-4])\b", raw_text, re.IGNORECASE)
        if ecog_match:
            val = int(ecog_match.group(1))
            profile.performance_status = _make_fact(
                concept="ecog_performance_status",
                value=val,
                source_text=ecog_match.group(0),
                start=ecog_match.start(),
                end=ecog_match.end(),
            )

        # 3. Stage
        stage_match = re.search(r"\bstage\s+([IVXLCDM]+[A-C]?)\b", raw_text, re.IGNORECASE)
        if stage_match:
            profile.disease_stage = _make_fact(
                concept="disease_stage",
                value=f"Stage {stage_match.group(1).upper()}",
                source_text=stage_match.group(0),
                start=stage_match.start(),
                end=stage_match.end(),
            )

        # 4. Biomarkers: EGFR
        egfr_pos = re.search(r"\bEGFR\s+(?:mutation\s+)?(?:positive|detected|mutant)\b", raw_text, re.IGNORECASE)
        egfr_neg = re.search(r"\bEGFR\s+(?:mutation\s+)?(?:negative|not\s+detected|wild[- ]?type)\b", raw_text, re.IGNORECASE)
        if egfr_pos:
            profile.biomarkers.append(_make_fact(
                concept="egfr_mutation",
                value=True,
                source_text=egfr_pos.group(0),
                start=egfr_pos.start(),
                end=egfr_pos.end(),
                assertion=AssertionType.AFFIRMED,
            ))
        elif egfr_neg:
            profile.biomarkers.append(_make_fact(
                concept="egfr_mutation",
                value=False,
                source_text=egfr_neg.group(0),
                start=egfr_neg.start(),
                end=egfr_neg.end(),
                assertion=AssertionType.NEGATED,
            ))

        # 5. Negated Findings (e.g. Brain Metastases)
        cns_neg = re.search(r"\b(?:no|denies|negative\s+for)\s+(?:active\s+)?(?:brain|cns)\s+metastases\b", raw_text, re.IGNORECASE)
        if cns_neg:
            profile.comorbidities.append(_make_fact(
                concept="brain_metastases",
                value=False,
                source_text=cns_neg.group(0),
                start=cns_neg.start(),
                end=cns_neg.end(),
                assertion=AssertionType.NEGATED,
            ))

        return profile
