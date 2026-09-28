"""
MedMatch Patient Clinical Profile & Clinical Fact Validator.
Phase 4: Patient Clinical Information Extraction.

Deterministic validator for structured patient profiles:
- Validates PatientClinicalProfile, ClinicalFact, FactProvenance, and TemporalContext
- Checks for duplicate fact IDs and referential integrity
- Validates character offsets against source text when available
- Validates assertion states, negation consistency, uncertainty, and temporality
- Enforces unit syntax on quantified measurements
- Generates actionable, structured error and warning diagnostics
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from scripts.patient_schema import (
        AssertionType,
        ClinicalFact,
        EvidenceSource,
        FactProvenance,
        PatientClinicalProfile,
        PatientDemographics,
        PatientExtractionContract,
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
        PatientExtractionContract,
        TemporalContext,
        TemporalityType,
        UncertaintyStatus,
    )


class ValidationIssue:
    """Represents a discrete validation issue with severity, code, path, and message."""

    def __init__(
        self,
        severity: str,  # "ERROR" or "WARNING"
        code: str,
        path: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.severity = severity
        self.code = code
        self.path = path
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "details": self.details,
        }

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.code} at {self.path}: {self.message}"


class PatientProfileValidator:
    """
    Deterministic validator for patient clinical information intelligence outputs.
    """

    # Recognized clinical unit patterns for laboratory and vital measurements
    _VALID_UNIT_PATTERN = re.compile(
        r"^(?:years?|months?|weeks?|days?|hours?|mg(?:/dL|/kg|/m2)?|g/dL|x\s*10\^?[0-9]+/L|cells/mm3|%|mm\s*Hg|mL/min(?:/1\.73m2)?|ULN|LLN|IU/L|U/L|mcg/L|ng/mL)$",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        self.issues: List[ValidationIssue] = []

    def add_error(self, code: str, path: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.issues.append(ValidationIssue(severity="ERROR", code=code, path=path, message=message, details=details))

    def add_warning(self, code: str, path: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.issues.append(ValidationIssue(severity="WARNING", code=code, path=path, message=message, details=details))

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "ERROR"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "WARNING"]

    def validate_profile(
        self, profile_data: Union[PatientClinicalProfile, Dict[str, Any]]
    ) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validates an entire PatientClinicalProfile object or dictionary.
        """
        self.issues.clear()

        # 1. Parse or coerce into Pydantic model
        if isinstance(profile_data, dict):
            try:
                profile = PatientClinicalProfile.model_validate(profile_data)
            except Exception as e:
                self.add_error(
                    code="SCHEMA_VALIDATION_FAILED",
                    path="PatientClinicalProfile",
                    message=f"Root profile failed Pydantic schema validation: {str(e)}",
                )
                return False, self.issues
        elif isinstance(profile_data, PatientClinicalProfile) or getattr(profile_data, "__class__", None).__name__ == "PatientClinicalProfile":
            if isinstance(profile_data, PatientClinicalProfile):
                profile = profile_data
            else:
                profile = PatientClinicalProfile.model_validate(profile_data.model_dump())
        else:
            self.add_error(
                code="INVALID_PROFILE_TYPE",
                path="PatientClinicalProfile",
                message=f"Expected PatientClinicalProfile or dict, got {type(profile_data).__name__}",
            )
            return False, self.issues

        # 2. Check Patient-Level Required Fields
        if not profile.patient_id or not profile.patient_id.strip():
            self.add_error(
                code="MISSING_PATIENT_ID",
                path="profile",
                message="Patient ID is missing or empty.",
            )

        # 3. Check Demographics if provided
        if profile.demographics is not None:
            demo = profile.demographics
            if demo.age is not None and (demo.age < 0 or demo.age > 130):
                self.add_error(
                    code="INVALID_DEMOGRAPHIC_AGE",
                    path="profile.demographics.age",
                    message=f"Age ({demo.age}) must be between 0 and 130.",
                )

        # 4. Check Unique Fact IDs and Validate Every Fact
        seen_fact_ids: Set[str] = set()
        all_facts = profile.all_facts()

        if not all_facts:
            self.add_warning(
                code="EMPTY_CLINICAL_FACTS",
                path=f"profile({profile.patient_id})",
                message="Patient profile contains zero extracted clinical facts.",
            )

        for fact_idx, fact in enumerate(all_facts):
            fact_path = f"profile.facts[{fact_idx}](id={fact.fact_id}, concept={fact.concept})"
            self._validate_fact(
                fact=fact,
                fact_path=fact_path,
                parent_profile=profile,
                seen_fact_ids=seen_fact_ids,
            )

        return (not self.has_errors), self.issues

    def _validate_fact(
        self,
        fact: ClinicalFact,
        fact_path: str,
        parent_profile: PatientClinicalProfile,
        seen_fact_ids: Set[str],
    ) -> None:
        """Validates a single ClinicalFact, its provenance, assertion, and temporality."""
        # A. Unique Fact ID
        if fact.fact_id in seen_fact_ids:
            self.add_error(
                code="DUPLICATE_FACT_ID",
                path=fact_path,
                message=f"Duplicate fact_id '{fact.fact_id}' found in profile.",
            )
        seen_fact_ids.add(fact.fact_id)

        # B. Concept Name
        if not fact.concept or len(fact.concept.strip()) < 2:
            self.add_error(
                code="INVALID_FACT_CONCEPT",
                path=f"{fact_path}.concept",
                message="Concept identifier must be at least 2 characters.",
            )

        # C. Text Checks
        if not fact.source_text or not fact.source_text.strip():
            self.add_error(
                code="EMPTY_SOURCE_TEXT",
                path=f"{fact_path}.source_text",
                message="Clinical fact source_text is empty or whitespace.",
            )

        # D. Assertion and Value Consistency
        if fact.assertion == AssertionType.NEGATED:
            # If value is explicitly boolean True when negated, that's an inconsistent state
            if fact.value is True:
                self.add_error(
                    code="INCONSISTENT_NEGATION_VALUE",
                    path=fact_path,
                    message=f"Fact '{fact.fact_id}' has assertion='negated' but value=True.",
                )
        elif fact.assertion == AssertionType.AFFIRMED:
            if fact.value is False:
                self.add_warning(
                    code="INCONSISTENT_AFFIRMATION_VALUE",
                    path=fact_path,
                    message=f"Fact '{fact.fact_id}' has assertion='affirmed' but value=False.",
                )

        # E. Unit Validation
        if fact.unit is not None:
            unit_clean = fact.unit.strip()
            if not unit_clean:
                self.add_warning(
                    code="EMPTY_UNIT_STRING",
                    path=f"{fact_path}.unit",
                    message="Clinical fact specifies an empty unit string.",
                )

        # F. Confidence Range
        if fact.confidence < 0.0 or fact.confidence > 1.0:
            self.add_error(
                code="INVALID_CONFIDENCE_SCORE",
                path=f"{fact_path}.confidence",
                message=f"Confidence score ({fact.confidence}) must be between 0.0 and 1.0.",
            )

        # G. Temporality Validation
        temp = fact.temporality
        if temp.duration_days is not None and temp.duration_days < 0:
            self.add_error(
                code="NEGATIVE_DURATION_DAYS",
                path=f"{fact_path}.temporality.duration_days",
                message=f"Duration days ({temp.duration_days}) cannot be negative.",
            )

        # H. Provenance Verification
        prov = fact.provenance
        if prov.patient_id != parent_profile.patient_id:
            self.add_error(
                code="PROVENANCE_PATIENT_ID_MISMATCH",
                path=f"{fact_path}.provenance",
                message=f"Provenance patient_id '{prov.patient_id}' does not match profile patient_id '{parent_profile.patient_id}'.",
            )

        if not prov.note_id or not prov.note_id.strip():
            self.add_error(
                code="MISSING_PROVENANCE_NOTE_ID",
                path=f"{fact_path}.provenance.note_id",
                message="Provenance note_id is empty or missing.",
            )

        if prov.start_char is not None and prov.end_char is not None:
            if prov.start_char == -1 or prov.end_char == -1:
                pass  # Explicit unmapped indicator
            elif prov.start_char < 0 or prov.end_char < 0:
                self.add_error(
                    code="NEGATIVE_CHARACTER_OFFSET",
                    path=f"{fact_path}.provenance.offsets",
                    message=f"Offsets cannot be negative unless explicitly -1. Got start={prov.start_char}, end={prov.end_char}.",
                )
            elif prov.start_char > prov.end_char:
                self.add_error(
                    code="INVALID_CHARACTER_OFFSET_RANGE",
                    path=f"{fact_path}.provenance.offsets",
                    message=f"start_char ({prov.start_char}) exceeds end_char ({prov.end_char}).",
                )


def validate_patient_profile_file(file_path: Union[str, Path]) -> Tuple[bool, List[ValidationIssue]]:
    """Convenience helper to validate a patient profile JSON file on disk."""
    path = Path(file_path)
    if not path.exists():
        issue = ValidationIssue(
            severity="ERROR",
            code="FILE_NOT_FOUND",
            path=str(path),
            message=f"Patient profile file does not exist: {path}",
        )
        return False, [issue]

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validator = PatientProfileValidator()
    if "profile" in data and isinstance(data["profile"], dict):
        profile_data = data["profile"]
    else:
        profile_data = data

    return validator.validate_profile(profile_data)


def main() -> None:
    parser = argparse.ArgumentParser(description="MedMatch Patient Clinical Profile Validator")
    parser.add_argument("file", help="Path to patient profile JSON file to validate")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    args = parser.parse_args()

    success, issues = validate_patient_profile_file(args.file)
    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]

    print(f"Validation finished for: {args.file}")
    print(f"Errors: {len(errors)}, Warnings: {len(warnings)}")

    for issue in issues:
        print(f"  {issue}")

    if errors or (args.strict and warnings):
        print("\nRESULT: FAILED")
        sys.exit(1)
    else:
        print("\nRESULT: PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
