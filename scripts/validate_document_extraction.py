"""
MedMatch Clinical Trial Document Extraction Validator.
Phase 3: Clinical Trial Document Intelligence.

Deterministic validator for clinical trial document extraction results:
- Validates TrialDocument, TrialSection, and TrialCriterion instances
- Checks for duplicate IDs, orphan sections, and hierarchy integrity
- Validates character offsets against section texts when available
- Validates atomic constraints, operators, units, and decomposition rationales
- Enforces section-type vs criterion-type consistency
- Ensures valid free-text criteria are accepted without forcing over-normalization
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
    from scripts.document_schema import (
        AtomicConstraint,
        CriterionDomain,
        CriterionOperator,
        CriterionProvenance,
        CriterionType,
        DocumentExtractionContract,
        LogicalRelation,
        SectionType,
        TrialCriterion,
        TrialDocument,
        TrialSection,
    )
except ImportError:
    from document_schema import (
        AtomicConstraint,
        CriterionDomain,
        CriterionOperator,
        CriterionProvenance,
        CriterionType,
        DocumentExtractionContract,
        LogicalRelation,
        SectionType,
        TrialCriterion,
        TrialDocument,
        TrialSection,
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


class DocumentExtractionValidator:
    """
    Deterministic validator for clinical trial document intelligence outputs.
    """

    # Recognized clinical unit patterns for basic syntax checking
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

    def validate_document(self, doc_data: Union[TrialDocument, Dict[str, Any]]) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validates an entire TrialDocument object or dictionary.
        """
        self.issues.clear()

        # 1. Parse or coerce into Pydantic model
        if isinstance(doc_data, dict):
            try:
                document = TrialDocument.model_validate(doc_data)
            except Exception as e:
                self.add_error(
                    code="SCHEMA_VALIDATION_FAILED",
                    path="TrialDocument",
                    message=f"Root document failed Pydantic schema validation: {str(e)}",
                )
                return False, self.issues
        elif isinstance(doc_data, TrialDocument) or getattr(doc_data, "__class__", None).__name__ == "TrialDocument":
            if isinstance(doc_data, TrialDocument):
                document = doc_data
            else:
                document = TrialDocument.model_validate(doc_data.model_dump())
        else:
            self.add_error(
                code="INVALID_DOCUMENT_TYPE",
                path="TrialDocument",
                message=f"Expected TrialDocument or dict, got {type(doc_data).__name__}",
            )
            return False, self.issues

        # 2. Check Document-Level Required Fields
        if not document.trial_id or not document.trial_id.strip():
            self.add_error(
                code="MISSING_TRIAL_ID",
                path=f"document({document.document_id})",
                message="Trial ID is missing or empty.",
            )

        if not document.document_id or not document.document_id.strip():
            self.add_error(
                code="MISSING_DOCUMENT_ID",
                path="document",
                message="Document ID is missing or empty.",
            )

        if not document.document_hash or len(document.document_hash) < 16:
            self.add_error(
                code="INVALID_DOCUMENT_HASH",
                path=f"document({document.document_id}).document_hash",
                message="Document hash is missing or too short for a secure hash.",
            )

        # 3. Check Sections and Uniqueness
        seen_section_ids: Set[str] = set()
        seen_criterion_ids: Set[str] = set()

        if not document.sections:
            self.add_warning(
                code="EMPTY_SECTIONS",
                path=f"document({document.document_id}).sections",
                message="Document has no extracted sections.",
            )

        for sec_idx, section in enumerate(document.sections):
            sec_path = f"document.sections[{sec_idx}](id={section.section_id})"

            # Duplicate Section ID
            if section.section_id in seen_section_ids:
                self.add_error(
                    code="DUPLICATE_SECTION_ID",
                    path=sec_path,
                    message=f"Duplicate section_id '{section.section_id}' detected.",
                )
            seen_section_ids.add(section.section_id)

            # Orphan Section Check
            if not section.criteria:
                # Sections like STUDY_POPULATION or UNKNOWN_AMBIGUOUS might have no discrete criteria,
                # but eligibility sections with no criteria should be flagged as warnings
                if section.section_type in (SectionType.INCLUSION_CRITERIA, SectionType.EXCLUSION_CRITERIA, SectionType.ELIGIBILITY_CRITERIA):
                    self.add_warning(
                        code="ORPHAN_ELIGIBILITY_SECTION",
                        path=sec_path,
                        message=f"Section '{section.section_id}' has section_type '{section.section_type}' but contains no extracted criteria.",
                    )

            # Validate Section Page Range
            if section.page_start is not None and section.page_end is not None:
                if section.page_start > section.page_end:
                    self.add_error(
                        code="INVALID_SECTION_PAGE_RANGE",
                        path=f"{sec_path}.pages",
                        message=f"Section page_start ({section.page_start}) exceeds page_end ({section.page_end}).",
                    )

            # Validate Section Text
            if not section.text or not section.text.strip():
                self.add_error(
                    code="EMPTY_SECTION_TEXT",
                    path=f"{sec_path}.text",
                    message="Section text is empty or whitespace.",
                )

            # 4. Check Criteria within Section
            for crit_idx, crit in enumerate(section.criteria):
                crit_path = f"{sec_path}.criteria[{crit_idx}](id={crit.criterion_id})"
                self._validate_criterion(
                    crit=crit,
                    crit_path=crit_path,
                    parent_document=document,
                    parent_section=section,
                    seen_criterion_ids=seen_criterion_ids,
                )

        return (not self.has_errors), self.issues

    def _validate_criterion(
        self,
        crit: TrialCriterion,
        crit_path: str,
        parent_document: TrialDocument,
        parent_section: TrialSection,
        seen_criterion_ids: Set[str],
    ) -> None:
        """Validates a single TrialCriterion and its provenance and constraints."""
        # A. Unique Criterion ID
        if crit.criterion_id in seen_criterion_ids:
            self.add_error(
                code="DUPLICATE_CRITERION_ID",
                path=crit_path,
                message=f"Duplicate criterion_id '{crit.criterion_id}' found in document.",
            )
        seen_criterion_ids.add(crit.criterion_id)

        # B. Text Checks
        if not crit.raw_text or not crit.raw_text.strip():
            self.add_error(
                code="EMPTY_RAW_TEXT",
                path=f"{crit_path}.raw_text",
                message="Criterion raw_text is empty or whitespace.",
            )

        if not crit.normalized_text or not crit.normalized_text.strip():
            self.add_error(
                code="EMPTY_NORMALIZED_TEXT",
                path=f"{crit_path}.normalized_text",
                message="Criterion normalized_text is empty or whitespace.",
            )

        # C. Inconsistent Section vs Criterion Type
        if parent_section.section_type == SectionType.INCLUSION_CRITERIA and crit.criterion_type == CriterionType.EXCLUSION:
            self.add_warning(
                code="INCONSISTENT_SECTION_CRITERION_TYPE",
                path=crit_path,
                message=f"Criterion '{crit.criterion_id}' is marked as 'exclusion' inside an 'INCLUSION_CRITERIA' section.",
            )
        elif parent_section.section_type == SectionType.EXCLUSION_CRITERIA and crit.criterion_type == CriterionType.INCLUSION:
            self.add_warning(
                code="INCONSISTENT_SECTION_CRITERION_TYPE",
                path=crit_path,
                message=f"Criterion '{crit.criterion_id}' is marked as 'inclusion' inside an 'EXCLUSION_CRITERIA' section.",
            )

        # D. Atomicity and Decomposition Rules
        if not crit.can_decompose and not crit.decomposition_block_reason:
            self.add_error(
                code="MISSING_DECOMPOSITION_BLOCK_REASON",
                path=crit_path,
                message="Criterion has can_decompose=False but no decomposition_block_reason was provided.",
            )

        if crit.is_atomic and len(crit.atomic_constraints) > 1:
            self.add_warning(
                code="ATOMIC_CRITERION_MULTIPLE_CONSTRAINTS",
                path=crit_path,
                message=f"Criterion is marked is_atomic=True but contains {len(crit.atomic_constraints)} constraints.",
            )

        # E. Atomic Constraints Validation
        for c_idx, constraint in enumerate(crit.atomic_constraints):
            c_path = f"{crit_path}.atomic_constraints[{c_idx}]"
            self._validate_constraint(constraint, c_path)

        # F. Provenance and Character Offsets
        prov = crit.provenance
        if prov.trial_id != parent_document.trial_id:
            self.add_error(
                code="PROVENANCE_TRIAL_ID_MISMATCH",
                path=f"{crit_path}.provenance",
                message=f"Provenance trial_id '{prov.trial_id}' does not match document trial_id '{parent_document.trial_id}'.",
            )

        if prov.section_id != parent_section.section_id:
            self.add_error(
                code="PROVENANCE_SECTION_ID_MISMATCH",
                path=f"{crit_path}.provenance",
                message=f"Provenance section_id '{prov.section_id}' does not match parent section_id '{parent_section.section_id}'.",
            )

        if prov.document_id != parent_document.document_id:
            self.add_error(
                code="PROVENANCE_DOCUMENT_ID_MISMATCH",
                path=f"{crit_path}.provenance",
                message=f"Provenance document_id '{prov.document_id}' does not match document_id '{parent_document.document_id}'.",
            )

        # Character Offset Verification
        if prov.start_char is not None and prov.end_char is not None:
            # -1 is the recognized indicator for 'offsets not available from source extractor'
            if prov.start_char == -1 or prov.end_char == -1:
                pass  # Explicit unmapped indicator
            elif prov.start_char < 0 or prov.end_char < 0:
                self.add_error(
                    code="NEGATIVE_CHARACTER_OFFSET",
                    path=f"{crit_path}.provenance.offsets",
                    message=f"Offsets cannot be negative unless explicitly -1 (unknown). Got start={prov.start_char}, end={prov.end_char}.",
                )
            elif prov.start_char > prov.end_char:
                self.add_error(
                    code="INVALID_CHARACTER_OFFSET_RANGE",
                    path=f"{crit_path}.provenance.offsets",
                    message=f"start_char ({prov.start_char}) exceeds end_char ({prov.end_char}).",
                )
            else:
                # Check bounds within section text
                sec_len = len(parent_section.text)
                if prov.end_char > sec_len:
                    self.add_error(
                        code="OFFSET_EXCEEDS_SECTION_LENGTH",
                        path=f"{crit_path}.provenance.offsets",
                        message=f"end_char ({prov.end_char}) exceeds section text length ({sec_len}).",
                    )
                else:
                    # Check text slice match
                    extracted_slice = parent_section.text[prov.start_char:prov.end_char].strip()
                    source_text_clean = prov.source_text.strip()
                    # Allow minor whitespace variations, but core characters should match
                    slice_norm = " ".join(extracted_slice.split())
                    source_norm = " ".join(source_text_clean.split())
                    if slice_norm != source_norm:
                        self.add_warning(
                            code="OFFSET_TEXT_MISMATCH",
                            path=f"{crit_path}.provenance",
                            message="Text slice at offsets does not exactly match provenance source_text.",
                            details={"slice": slice_norm[:50], "source": source_norm[:50]},
                        )

    def _validate_constraint(self, constraint: AtomicConstraint, c_path: str) -> None:
        """Validates a single AtomicConstraint."""
        # Concept name length & format
        if not constraint.concept or len(constraint.concept.strip()) < 2:
            self.add_error(
                code="INVALID_CONSTRAINT_CONCEPT",
                path=f"{c_path}.concept",
                message="Constraint concept must be at least 2 characters.",
            )

        # Operator check
        if not isinstance(constraint.operator, CriterionOperator):
            try:
                CriterionOperator(str(constraint.operator))
            except ValueError:
                self.add_error(
                    code="UNSUPPORTED_OPERATOR",
                    path=f"{c_path}.operator",
                    message=f"Operator '{constraint.operator}' is not a valid CriterionOperator.",
                )

        # Value check
        if constraint.operator in (CriterionOperator.GTE, CriterionOperator.LTE, CriterionOperator.GT, CriterionOperator.LT):
            if not isinstance(constraint.value, (int, float)):
                self.add_error(
                    code="NON_NUMERIC_COMPARATOR_VALUE",
                    path=f"{c_path}.value",
                    message=f"Comparator '{constraint.operator}' requires numeric value, got '{type(constraint.value).__name__}'.",
                )

        # Between check
        if constraint.operator == CriterionOperator.BETWEEN:
            if not isinstance(constraint.value, (list, tuple)) or len(constraint.value) != 2:
                self.add_error(
                    code="INVALID_BETWEEN_VALUE",
                    path=f"{c_path}.value",
                    message="Operator 'between' requires a list or tuple of 2 boundary values [min, max].",
                )
            elif constraint.value[0] > constraint.value[1]:
                self.add_error(
                    code="INVALID_BETWEEN_RANGE",
                    path=f"{c_path}.value",
                    message=f"Lower bound ({constraint.value[0]}) exceeds upper bound ({constraint.value[1]}).",
                )

        # Unit validation
        if constraint.unit is not None:
            unit_clean = constraint.unit.strip()
            if not unit_clean:
                self.add_warning(
                    code="EMPTY_UNIT_STRING",
                    path=f"{c_path}.unit",
                    message="Constraint specifies an empty unit string.",
                )


def validate_extraction_file(file_path: Union[str, Path]) -> Tuple[bool, List[ValidationIssue]]:
    """Convenience helper to validate a JSON file on disk."""
    path = Path(file_path)
    if not path.exists():
        issue = ValidationIssue(
            severity="ERROR",
            code="FILE_NOT_FOUND",
            path=str(path),
            message=f"Extraction file does not exist: {path}",
        )
        return False, [issue]

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check if this is a DocumentExtractionContract or a TrialDocument
    validator = DocumentExtractionValidator()
    if "document" in data and isinstance(data["document"], dict):
        doc_data = data["document"]
    else:
        doc_data = data

    return validator.validate_document(doc_data)


def main() -> None:
    parser = argparse.ArgumentParser(description="MedMatch Document Extraction Validator")
    parser.add_argument("file", help="Path to trial document JSON file to validate")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    args = parser.parse_args()

    success, issues = validate_extraction_file(args.file)
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
