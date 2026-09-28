"""
MedMatch Section Normalizer & Taxonomic Classifier.
Phase 3: Clinical Trial Document Intelligence.

Deterministic, rule-based detection and taxonomic normalization of common
clinical trial protocol sections, headings, and eligibility blocks.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

try:
    from scripts.document_schema import SectionType
except ImportError:
    from document_schema import SectionType


class SectionNormalizer:
    """
    Deterministic rule-based normalizer for clinical trial protocol sections.
    """

    # Compile case-insensitive regex patterns for known clinical trial protocol headings
    _PATTERNS: List[Tuple[SectionType, re.Pattern[str], float]] = [
        # Explicit Inclusion Criteria
        (
            SectionType.INCLUSION_CRITERIA,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?(?:subject\s+|patient\s+|key\s+)?inclusion\s+criteria(?:\s*[:\-])?", re.IGNORECASE),
            1.0,
        ),
        (
            SectionType.INCLUSION_CRITERIA,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?inclusion(?:\s*[:\-])?\s*$", re.IGNORECASE),
            0.95,
        ),
        # Explicit Exclusion Criteria
        (
            SectionType.EXCLUSION_CRITERIA,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?(?:subject\s+|patient\s+|key\s+)?exclusion\s+criteria(?:\s*[:\-])?", re.IGNORECASE),
            1.0,
        ),
        (
            SectionType.EXCLUSION_CRITERIA,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?exclusion(?:\s*[:\-])?\s*$", re.IGNORECASE),
            0.95,
        ),
        # Combined / General Eligibility
        (
            SectionType.ELIGIBILITY_CRITERIA,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?(?:patient\s+|key\s+)?eligibility(?:\s+criteria)?(?:\s*[:\-])?\s*$", re.IGNORECASE),
            0.95,
        ),
        (
            SectionType.ELIGIBILITY_CRITERIA,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?eligibility(?:\s*[:\-])?\s*$", re.IGNORECASE),
            0.90,
        ),
        # Study Population
        (
            SectionType.STUDY_POPULATION,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?(?:study|target|patient)\s+population(?:\s*[:\-])?", re.IGNORECASE),
            0.90,
        ),
        # Disease Characteristics
        (
            SectionType.DISEASE_CHARACTERISTICS,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?disease\s+characteristics(?:\s*[:\-])?", re.IGNORECASE),
            0.90,
        ),
        # Prior / Concurrent Therapy
        (
            SectionType.PRIOR_CONCURRENT_THERAPY,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?(?:prior|concurrent|prohibited)\s+(?:therapy|treatments|medications)(?:\s*[:\-])?", re.IGNORECASE),
            0.90,
        ),
        # Patient Characteristics
        (
            SectionType.PATIENT_CHARACTERISTICS,
            re.compile(r"^\s*(?:\d+[\.\)]\s*)?patient\s+characteristics(?:\s*[:\-])?", re.IGNORECASE),
            0.85,
        ),
    ]

    @classmethod
    def classify_heading(cls, heading: str) -> Tuple[SectionType, float]:
        """
        Classifies a raw heading string into a standardized SectionType with a confidence score.
        If no confident rule matches, returns (SectionType.UNKNOWN_AMBIGUOUS, 0.0).
        """
        if not heading or not heading.strip():
            return SectionType.UNKNOWN_AMBIGUOUS, 0.0

        clean_heading = heading.strip()

        for sec_type, pattern, conf in cls._PATTERNS:
            if pattern.search(clean_heading):
                return sec_type, conf

        return SectionType.UNKNOWN_AMBIGUOUS, 0.0

    @classmethod
    def segment_raw_eligibility_text(
        cls, raw_text: str
    ) -> List[Dict[str, Any]]:
        """
        Splits a raw eligibility narrative into segmented sections with detected headers.
        Preserves original heading, normalized type, start/end character offsets, and text.
        """
        if not raw_text or not raw_text.strip():
            return []

        # Find potential section header lines
        lines = raw_text.splitlines(keepends=True)
        sections: List[Dict[str, Any]] = []

        current_heading = "Header"
        current_type = SectionType.UNKNOWN_AMBIGUOUS
        current_conf = 0.5
        current_lines: List[str] = []
        char_offset = 0
        section_start_char = 0
        order = 1

        for line in lines:
            line_stripped = line.strip()
            detected_type, conf = cls.classify_heading(line_stripped)

            if detected_type != SectionType.UNKNOWN_AMBIGUOUS and conf >= 0.85:
                # If we were collecting a previous section, finish it
                if current_lines:
                    sec_text = "".join(current_lines).strip()
                    if sec_text:
                        sections.append({
                            "section_id": f"SEC_{order:03d}",
                            "section_type": current_type,
                            "heading": current_heading,
                            "text": sec_text,
                            "start_char": section_start_char,
                            "end_char": char_offset,
                            "source_order": order,
                            "confidence": current_conf,
                        })
                        order += 1

                current_heading = line_stripped
                current_type = detected_type
                current_conf = conf
                current_lines = []
                section_start_char = char_offset
            else:
                current_lines.append(line)

            char_offset += len(line)

        # Flush final section
        if current_lines:
            sec_text = "".join(current_lines).strip()
            if sec_text:
                sections.append({
                    "section_id": f"SEC_{order:03d}",
                    "section_type": current_type,
                    "heading": current_heading,
                    "text": sec_text,
                    "start_char": section_start_char,
                    "end_char": char_offset,
                    "source_order": order,
                    "confidence": current_conf,
                })

        return sections
