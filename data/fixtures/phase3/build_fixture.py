"""
Builds the canonical Phase 3 development fixture JSON files deterministically
with exact character offset calculations and validation.
"""

import json
from pathlib import Path
import sys

# Ensure root is in path
root_dir = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "scripts"))
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
from validate_document_extraction import DocumentExtractionValidator

def generate_fixtures():
    trial_id = "NCT02484404"
    doc_id = "DOC_NCT02484404_PROTO_V1"
    doc_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # ==========================================
    # Section 1: Inclusion Criteria (Spans Page 1 - Page 2)
    # ==========================================
    sec1_id = "SEC_001"
    sec1_heading = "Inclusion Criteria"
    
    # Verbatim criterion strings
    crit1_text = "1. Histologically or cytologically confirmed non-small cell lung cancer (NSCLC) Stage IV."
    crit2_text = "2. Patient must be aged >= 18 years and have an ECOG performance status <= 1 at time of screening."
    crit3_text = "3. Absolute neutrophil count (ANC) >= 1.5 x 10^9/L."
    crit4_text = "4. Patient has adequate organ and marrow reserve in the opinion of the investigator."
    crit5_text = "5. Left ventricular ejection fraction (LVEF) >= 50% only in patients with prior cumulative doxorubicin exposure > 300 mg/m2; otherwise baseline cardiac evaluation not required."
    
    sec1_text = f"{crit1_text}\n{crit2_text}\n{crit3_text}\n{crit4_text}\n{crit5_text}"

    # Calculate offsets within sec1_text
    c1_start = sec1_text.find(crit1_text)
    c1_end = c1_start + len(crit1_text)

    c2_start = sec1_text.find(crit2_text)
    c2_end = c2_start + len(crit2_text)

    c3_start = sec1_text.find(crit3_text)
    c3_end = c3_start + len(crit3_text)

    c4_start = sec1_text.find(crit4_text)
    c4_end = c4_start + len(crit4_text)

    c5_start = sec1_text.find(crit5_text)
    c5_end = c5_start + len(crit5_text)

    criterion_1 = TrialCriterion(
        criterion_id="NCT02484404_INC_001",
        trial_id=trial_id,
        section_id=sec1_id,
        criterion_type=CriterionType.INCLUSION,
        domain=CriterionDomain.DIAGNOSIS_STAGE,
        raw_text=crit1_text,
        normalized_text="Histologically or cytologically confirmed non-small cell lung cancer (NSCLC) Stage IV",
        is_atomic=True,
        can_decompose=True,
        atomic_constraints=[
            AtomicConstraint(
                concept="non_small_cell_lung_cancer",
                operator=CriterionOperator.EQ,
                value="Stage IV",
            )
        ],
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=sec1_id,
            page_number=1,
            start_char=c1_start,
            end_char=c1_end,
            source_text=crit1_text,
        ),
        extraction_confidence=1.0,
    )

    criterion_2 = TrialCriterion(
        criterion_id="NCT02484404_INC_002",
        trial_id=trial_id,
        section_id=sec1_id,
        criterion_type=CriterionType.INCLUSION,
        domain=CriterionDomain.PERFORMANCE_STATUS,
        raw_text=crit2_text,
        normalized_text="Patient must be aged >= 18 years and have an ECOG performance status <= 1 at time of screening",
        is_atomic=False,
        can_decompose=True,
        compound_relation=LogicalRelation.AND,
        atomic_constraints=[
            AtomicConstraint(
                concept="age",
                operator=CriterionOperator.GTE,
                value=18,
                unit="years",
            ),
            AtomicConstraint(
                concept="ecog_performance_status",
                operator=CriterionOperator.LTE,
                value=1,
                temporal_anchor="at_screening",
            ),
        ],
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=sec1_id,
            page_number=1,
            start_char=c2_start,
            end_char=c2_end,
            source_text=crit2_text,
        ),
        extraction_confidence=0.98,
    )

    criterion_3 = TrialCriterion(
        criterion_id="NCT02484404_INC_003",
        trial_id=trial_id,
        section_id=sec1_id,
        criterion_type=CriterionType.INCLUSION,
        domain=CriterionDomain.LABORATORY_VALUES,
        raw_text=crit3_text,
        normalized_text="Absolute neutrophil count (ANC) >= 1.5 x 10^9/L",
        is_atomic=True,
        can_decompose=True,
        atomic_constraints=[
            AtomicConstraint(
                concept="absolute_neutrophil_count",
                operator=CriterionOperator.GTE,
                value=1.5,
                unit="x 10^9/L",
            )
        ],
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=sec1_id,
            page_number=1,
            start_char=c3_start,
            end_char=c3_end,
            source_text=crit3_text,
        ),
        extraction_confidence=1.0,
    )

    criterion_4 = TrialCriterion(
        criterion_id="NCT02484404_INC_004",
        trial_id=trial_id,
        section_id=sec1_id,
        criterion_type=CriterionType.AMBIGUOUS,
        domain=CriterionDomain.ORGAN_FUNCTION,
        raw_text=crit4_text,
        normalized_text="Patient has adequate organ and marrow reserve in the opinion of the investigator",
        is_atomic=True,
        can_decompose=True,
        atomic_constraints=[],  # Free text criterion without discrete atomic threshold
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=sec1_id,
            page_number=2,  # Spans into page 2
            start_char=c4_start,
            end_char=c4_end,
            source_text=crit4_text,
        ),
        extraction_confidence=0.85,
    )

    criterion_5 = TrialCriterion(
        criterion_id="NCT02484404_INC_005",
        trial_id=trial_id,
        section_id=sec1_id,
        criterion_type=CriterionType.INCLUSION,
        domain=CriterionDomain.ORGAN_FUNCTION,
        raw_text=crit5_text,
        normalized_text="Left ventricular ejection fraction (LVEF) >= 50% only in patients with prior cumulative doxorubicin exposure > 300 mg/m2; otherwise baseline cardiac evaluation not required",
        is_atomic=False,
        can_decompose=False,
        decomposition_block_reason="Conditional requirement with coupled dependent clauses; premature splitting would distort cardiac evaluation eligibility",
        atomic_constraints=[],
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=sec1_id,
            page_number=2,
            start_char=c5_start,
            end_char=c5_end,
            source_text=crit5_text,
        ),
        extraction_confidence=0.92,
    )

    section_1 = TrialSection(
        section_id=sec1_id,
        section_type=SectionType.INCLUSION_CRITERIA,
        heading=sec1_heading,
        text=sec1_text,
        page_start=1,
        page_end=2,
        source_order=1,
        confidence=1.0,
        criteria=[criterion_1, criterion_2, criterion_3, criterion_4, criterion_5],
    )

    # ==========================================
    # Section 2: Exclusion Criteria (Page 2)
    # ==========================================
    sec2_id = "SEC_002"
    sec2_heading = "Exclusion Criteria"

    crit6_text = "1. Known active central nervous system (CNS) metastases or untreated leptomeningeal disease."
    crit7_text = "2. No chemotherapy or radiotherapy within 28 days prior to Day 1 of study treatment."
    crit8_text = "3. Pregnant or lactating females, or females of childbearing potential not willing to use highly effective contraception."

    sec2_text = f"{crit6_text}\n{crit7_text}\n{crit8_text}"

    c6_start = sec2_text.find(crit6_text)
    c6_end = c6_start + len(crit6_text)

    c7_start = sec2_text.find(crit7_text)
    c7_end = c7_start + len(crit7_text)

    c8_start = sec2_text.find(crit8_text)
    c8_end = c8_start + len(crit8_text)

    criterion_6 = TrialCriterion(
        criterion_id="NCT02484404_EXC_001",
        trial_id=trial_id,
        section_id=sec2_id,
        criterion_type=CriterionType.EXCLUSION,
        domain=CriterionDomain.COMORBIDITIES,
        raw_text=crit6_text,
        normalized_text="Known active central nervous system (CNS) metastases or untreated leptomeningeal disease",
        is_atomic=True,
        can_decompose=True,
        atomic_constraints=[
            AtomicConstraint(
                concept="cns_metastases_or_leptomeningeal_disease",
                operator=CriterionOperator.EXISTS,
                value=True,
                is_negated=False,
            )
        ],
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=sec2_id,
            page_number=2,
            start_char=c6_start,
            end_char=c6_end,
            source_text=crit6_text,
        ),
        extraction_confidence=1.0,
    )

    criterion_7 = TrialCriterion(
        criterion_id="NCT02484404_EXC_002",
        trial_id=trial_id,
        section_id=sec2_id,
        criterion_type=CriterionType.EXCLUSION,
        domain=CriterionDomain.PRIOR_TREATMENT,
        raw_text=crit7_text,
        normalized_text="No chemotherapy or radiotherapy within 28 days prior to Day 1 of study treatment",
        is_atomic=True,
        can_decompose=True,
        atomic_constraints=[
            AtomicConstraint(
                concept="chemotherapy_or_radiotherapy",
                operator=CriterionOperator.EXISTS,
                value=True,
                temporal_window_days=28,
                temporal_anchor="prior_to_day_1",
                is_negated=True,
            )
        ],
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=sec2_id,
            page_number=2,
            start_char=c7_start,
            end_char=c7_end,
            source_text=crit7_text,
        ),
        extraction_confidence=0.99,
    )

    criterion_8 = TrialCriterion(
        criterion_id="NCT02484404_EXC_003",
        trial_id=trial_id,
        section_id=sec2_id,
        criterion_type=CriterionType.EXCLUSION,
        domain=CriterionDomain.ETHICAL_CONSENT,
        raw_text=crit8_text,
        normalized_text="Pregnant or lactating females, or females of childbearing potential not willing to use highly effective contraception",
        is_atomic=True,
        can_decompose=True,
        atomic_constraints=[
            AtomicConstraint(
                concept="pregnancy_or_lactation",
                operator=CriterionOperator.EXISTS,
                value=True,
                is_negated=False,
            )
        ],
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=sec2_id,
            page_number=2,
            start_char=c8_start,
            end_char=c8_end,
            source_text=crit8_text,
        ),
        extraction_confidence=0.99,
    )

    section_2 = TrialSection(
        section_id=sec2_id,
        section_type=SectionType.EXCLUSION_CRITERIA,
        heading=sec2_heading,
        text=sec2_text,
        page_start=2,
        page_end=2,
        source_order=2,
        confidence=1.0,
        criteria=[criterion_6, criterion_7, criterion_8],
    )

    # Document assembly
    doc = TrialDocument(
        document_id=doc_id,
        trial_id=trial_id,
        source_uri="protocols/NCT02484404_protocol.pdf",
        document_type="protocol_pdf",
        extraction_version="0.3.0",
        processing_timestamp="2026-09-28T12:00:00Z",
        document_hash=doc_hash,
        sections=[section_1, section_2],
    )

    # Build Document Extraction Contract
    all_criteria = section_1.criteria + section_2.criteria
    inc_count = sum(1 for c in all_criteria if c.criterion_type == CriterionType.INCLUSION)
    exc_count = sum(1 for c in all_criteria if c.criterion_type == CriterionType.EXCLUSION)
    amb_count = sum(1 for c in all_criteria if c.criterion_type == CriterionType.AMBIGUOUS)
    atomic_count = sum(1 for c in all_criteria if c.is_atomic)
    compound_count = sum(1 for c in all_criteria if not c.is_atomic)

    contract = DocumentExtractionContract(
        status="SUCCESS",
        document=doc,
        total_sections=len(doc.sections),
        total_criteria=len(all_criteria),
        inclusion_count=inc_count,
        exclusion_count=exc_count,
        ambiguous_count=amb_count,
        atomic_count=atomic_count,
        compound_count=compound_count,
        validation_passed=True,
        validation_messages=["Document extraction passed all structural and provenance verifications."],
    )

    # Validate with validator
    validator = DocumentExtractionValidator()
    is_valid, issues = validator.validate_document(doc)
    assert is_valid, f"Generated fixture failed validation: {[i.to_dict() for i in issues]}"

    out_dir = Path(__file__).resolve().parent
    doc_path = out_dir / "trial_document_fixture.json"
    contract_path = out_dir / "document_extraction_contract.json"

    with open(doc_path, "w", encoding="utf-8") as f:
        json.dump(doc.model_dump(), f, indent=2)

    with open(contract_path, "w", encoding="utf-8") as f:
        json.dump(contract.model_dump(), f, indent=2)

    print(f"Generated fixture successfully:\n  {doc_path}\n  {contract_path}")

if __name__ == "__main__":
    generate_fixtures()
