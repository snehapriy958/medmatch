"""
MedMatch Synthetic Patient & Ground Truth Generator.
Phase 2: Dataset + Ground Truth.

Generates controlled, rule-derived synthetic patient records and corresponding
criterion-level and trial-level ground truth from explicit clinical trial protocols.

Scenarios Generated:
1. Scenario A — Clearly Eligible (Positive Control)
2. Scenario B — Clearly Ineligible (Disqualification Control)
3. Scenario C — Missing Information (Uncertainty Control -> NEEDS_REVIEW)
4. Scenario D — Conflicting Evidence (Contradiction Control -> NEEDS_REVIEW)
5. Scenario E — Boundary Conditions (Numerical Threshold Cutoff)
6. Scenario F — Temporal Conditions (Washout Interval Arithmetic)

WARNING: Generated profiles are programmatic stress-test artifacts.
They must NEVER be represented as real-world clinical evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure scripts directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataset_schema import (
    AnnotationSource,
    CanonicalCriterion,
    CanonicalPatient,
    CanonicalTrial,
    CriterionDomain,
    CriterionEvidence,
    CriterionGroundTruth,
    CriterionType,
    CriterionVerdict,
    LabValue,
    PatientEvidence,
    TrialEligibilityVerdict,
    TrialGroundTruth,
    compute_trial_eligibility,
    summarize_criterion_verdicts,
)


def get_reference_oncology_trials() -> List[CanonicalTrial]:
    """Returns curated reference clinical trial protocols based on ClinicalTrials.gov."""
    return [
        CanonicalTrial(
            trial_id="NCT02484404",
            source="clinicaltrials.gov",
            source_id="NCT02484404",
            title="Study of Osimertinib in Patients With Advanced Non-Small Cell Lung Cancer",
            condition=["Non-Small Cell Lung Cancer (NSCLC)"],
            intervention=["Osimertinib 80mg oral daily"],
            phase="Phase 3",
            eligibility_text=(
                "Inclusion Criteria:\n"
                "1. Histologically confirmed locally advanced or metastatic NSCLC (Stage IV).\n"
                "2. Documented EGFR sensitizing mutation (Exon 19 deletion or L858R).\n"
                "3. Age >= 18 years.\n"
                "4. ECOG performance status 0 or 1.\n"
                "5. Adequate hematologic function: Absolute Neutrophil Count (ANC) >= 1.5 x 10^9/L, "
                "Platelet count >= 100 x 10^9/L.\n\n"
                "Exclusion Criteria:\n"
                "1. Prior treatment with third-generation EGFR-TKI.\n"
                "2. Untreated or symptomatic central nervous system (CNS) metastases.\n"
                "3. Cytotoxic chemotherapy completed within 28 days prior to Day 1.\n"
                "4. Major surgical procedure within 14 days prior to screening.\n"
            ),
            criteria=[
                CanonicalCriterion(
                    criterion_id="NCT02484404_INC_01",
                    trial_id="NCT02484404",
                    criterion_type=CriterionType.INCLUSION,
                    domain=CriterionDomain.DIAGNOSIS_STAGE,
                    source_text="Histologically confirmed locally advanced or metastatic NSCLC (Stage IV).",
                ),
                CanonicalCriterion(
                    criterion_id="NCT02484404_INC_02",
                    trial_id="NCT02484404",
                    criterion_type=CriterionType.INCLUSION,
                    domain=CriterionDomain.BIOMARKER_GENOMICS,
                    source_text="Documented EGFR sensitizing mutation (Exon 19 deletion or L858R).",
                ),
                CanonicalCriterion(
                    criterion_id="NCT02484404_INC_03",
                    trial_id="NCT02484404",
                    criterion_type=CriterionType.INCLUSION,
                    domain=CriterionDomain.AGE,
                    source_text="Age >= 18 years.",
                ),
                CanonicalCriterion(
                    criterion_id="NCT02484404_INC_04",
                    trial_id="NCT02484404",
                    criterion_type=CriterionType.INCLUSION,
                    domain=CriterionDomain.PERFORMANCE_STATUS,
                    source_text="ECOG performance status 0 or 1.",
                ),
                CanonicalCriterion(
                    criterion_id="NCT02484404_INC_05",
                    trial_id="NCT02484404",
                    criterion_type=CriterionType.INCLUSION,
                    domain=CriterionDomain.LABORATORY_VALUES,
                    source_text="Adequate hematologic function: Platelet count >= 100 x 10^9/L.",
                ),
                CanonicalCriterion(
                    criterion_id="NCT02484404_EXC_01",
                    trial_id="NCT02484404",
                    criterion_type=CriterionType.EXCLUSION,
                    domain=CriterionDomain.PRIOR_TREATMENT,
                    source_text="Prior treatment with third-generation EGFR-TKI.",
                ),
                CanonicalCriterion(
                    criterion_id="NCT02484404_EXC_02",
                    trial_id="NCT02484404",
                    criterion_type=CriterionType.EXCLUSION,
                    domain=CriterionDomain.COMORBIDITIES,
                    source_text="Untreated or symptomatic central nervous system (CNS) metastases.",
                ),
                CanonicalCriterion(
                    criterion_id="NCT02484404_EXC_03",
                    trial_id="NCT02484404",
                    criterion_type=CriterionType.EXCLUSION,
                    domain=CriterionDomain.PRIOR_TREATMENT,
                    source_text="Cytotoxic chemotherapy completed within 28 days prior to Day 1.",
                ),
            ],
        )
    ]


def generate_scenario_patients(
    trial: CanonicalTrial, seed: int = 42
) -> List[Tuple[CanonicalPatient, List[CriterionGroundTruth], TrialGroundTruth]]:
    """Generates the 6 controlled scenario patient cases for a given trial."""
    cases = []

    # -------------------------------------------------------------
    # Case 1: Scenario A — Clearly Eligible (Positive Control)
    # -------------------------------------------------------------
    p1_note = (
        "CLINICAL ONCOLOGY NOTE\n"
        "Patient ID: SYN_P001 | Encounter Date: 2026-09-15\n"
        "History of Present Illness: 62-year-old female presenting for trial evaluation. "
        "Pathology confirms Stage IV lung adenocarcinoma with pleural metastases. "
        "Next-generation sequencing reveals EGFR Exon 19 deletion (p.E746_A750del). "
        "Physical Exam & Labs: ECOG performance status is 0. Ambulatory and active. "
        "Complete Blood Count shows Platelet count: 185 x 10^9/L (normal range 150-450). "
        "Prior Treatments: Received first-line carboplatin/pemetrexed which was completed 45 days ago. "
        "Has never received osimertinib or any third-generation EGFR TKI. "
        "Neuro/Imaging: Brain MRI from 2026-09-01 shows no evidence of intracranial metastases."
    )
    p1 = CanonicalPatient(
        patient_id="SYN_P001",
        source="synthetic",
        age=62,
        sex="female",
        diagnoses=["Non-Small Cell Lung Cancer (Adenocarcinoma)"],
        stage="Stage IV",
        biomarkers={"EGFR": "Exon 19 deletion"},
        medications=["Ondansetron PRN"],
        comorbidities=["Hypertension"],
        laboratory_values=[LabValue(test_name="Platelets", value=185.0, unit="x 10^9/L")],
        prior_treatments=["Carboplatin/Pemetrexed (completed 45 days ago)"],
        ecog_performance_status=0,
        clinical_note=p1_note,
    )
    p1_crit_verdicts = [
        (trial.criteria[0], CriterionVerdict.PASS, "Stage IV lung adenocarcinoma with pleural metastases."),
        (trial.criteria[1], CriterionVerdict.PASS, "EGFR Exon 19 deletion (p.E746_A750del)."),
        (trial.criteria[2], CriterionVerdict.PASS, "62-year-old female"),
        (trial.criteria[3], CriterionVerdict.PASS, "ECOG performance status is 0."),
        (trial.criteria[4], CriterionVerdict.PASS, "Platelet count: 185 x 10^9/L"),
        (trial.criteria[5], CriterionVerdict.PASS, "Has never received osimertinib or any third-generation EGFR TKI."),
        (trial.criteria[6], CriterionVerdict.PASS, "Brain MRI from 2026-09-01 shows no evidence of intracranial metastases."),
        (trial.criteria[7], CriterionVerdict.PASS, "carboplatin/pemetrexed which was completed 45 days ago"),
    ]
    p1_cgts = [
        CriterionGroundTruth(
            patient_id=p1.patient_id,
            trial_id=trial.trial_id,
            criterion_id=crit.criterion_id,
            criterion_type=crit.criterion_type,
            ground_truth=verd,
            patient_evidence=PatientEvidence(
                text=ev_txt,
                start_char=p1_note.find(ev_txt),
                end_char=p1_note.find(ev_txt) + len(ev_txt) if ev_txt in p1_note else -1,
                source_section="Clinical Narrative",
            ),
            criterion_evidence=CriterionEvidence(text=crit.source_text),
            annotation_source=AnnotationSource.SYNTHETIC,
            annotator_id=f"generator_seed_{seed}",
            annotation_notes="Scenario A: Clearly Eligible positive control",
        )
        for crit, verd, ev_txt in p1_crit_verdicts
    ]
    p1_tgt = TrialGroundTruth(
        patient_id=p1.patient_id,
        trial_id=trial.trial_id,
        eligibility=compute_trial_eligibility([cg.ground_truth for cg in p1_cgts]),
        criterion_summary=summarize_criterion_verdicts([cg.ground_truth for cg in p1_cgts]),
        evidence=["Patient satisfies all inclusion criteria and exhibits no exclusion conditions."],
        annotation_source=AnnotationSource.SYNTHETIC,
        annotator_id=f"generator_seed_{seed}",
        annotation_notes="Scenario A: Clearly Eligible",
    )
    cases.append((p1, p1_cgts, p1_tgt))

    # -------------------------------------------------------------
    # Case 2: Scenario B — Clearly Ineligible (Disqualification Control)
    # -------------------------------------------------------------
    p2_note = (
        "CLINICAL ONCOLOGY NOTE\n"
        "Patient ID: SYN_P002 | Encounter Date: 2026-09-15\n"
        "History: 58-year-old male with confirmed Stage IV NSCLC. "
        "Molecular testing shows KRAS G12C mutation; EGFR testing is wild-type. "
        "Exam: ECOG performance status 3 (bedbound > 50% of waking hours). "
        "Labs: Platelets 140 x 10^9/L. "
        "Prior Therapies: None. No prior TKI. "
        "Brain MRI: Negative for CNS lesions."
    )
    p2 = CanonicalPatient(
        patient_id="SYN_P002",
        source="synthetic",
        age=58,
        sex="male",
        diagnoses=["Non-Small Cell Lung Cancer"],
        stage="Stage IV",
        biomarkers={"KRAS": "G12C", "EGFR": "Wild-type"},
        laboratory_values=[LabValue(test_name="Platelets", value=140.0, unit="x 10^9/L")],
        ecog_performance_status=3,
        clinical_note=p2_note,
    )
    p2_crit_verdicts = [
        (trial.criteria[0], CriterionVerdict.PASS, "Stage IV NSCLC."),
        (trial.criteria[1], CriterionVerdict.FAIL, "EGFR testing is wild-type."),  # Violates EGFR inclusion
        (trial.criteria[2], CriterionVerdict.PASS, "58-year-old male"),
        (trial.criteria[3], CriterionVerdict.FAIL, "ECOG performance status 3 (bedbound > 50% of waking hours)."),  # Violates ECOG
        (trial.criteria[4], CriterionVerdict.PASS, "Platelets 140 x 10^9/L."),
        (trial.criteria[5], CriterionVerdict.PASS, "No prior TKI."),
        (trial.criteria[6], CriterionVerdict.PASS, "Brain MRI: Negative for CNS lesions."),
        (trial.criteria[7], CriterionVerdict.PASS, "Prior Therapies: None."),
    ]
    p2_cgts = [
        CriterionGroundTruth(
            patient_id=p2.patient_id,
            trial_id=trial.trial_id,
            criterion_id=crit.criterion_id,
            criterion_type=crit.criterion_type,
            ground_truth=verd,
            patient_evidence=PatientEvidence(
                text=ev_txt,
                start_char=p2_note.find(ev_txt),
                end_char=p2_note.find(ev_txt) + len(ev_txt) if ev_txt in p2_note else -1,
                source_section="Clinical Narrative",
            ),
            criterion_evidence=CriterionEvidence(text=crit.source_text),
            annotation_source=AnnotationSource.SYNTHETIC,
            annotator_id=f"generator_seed_{seed}",
            annotation_notes="Scenario B: Clearly Ineligible (EGFR wild-type and ECOG 3)",
        )
        for crit, verd, ev_txt in p2_crit_verdicts
    ]
    p2_tgt = TrialGroundTruth(
        patient_id=p2.patient_id,
        trial_id=trial.trial_id,
        eligibility=compute_trial_eligibility([cg.ground_truth for cg in p2_cgts]),
        criterion_summary=summarize_criterion_verdicts([cg.ground_truth for cg in p2_cgts]),
        evidence=["Patient fails EGFR mutation inclusion and ECOG performance status inclusion."],
        annotation_source=AnnotationSource.SYNTHETIC,
        annotator_id=f"generator_seed_{seed}",
        annotation_notes="Scenario B: Clearly Ineligible",
    )
    cases.append((p2, p2_cgts, p2_tgt))

    # -------------------------------------------------------------
    # Case 3: Scenario C — Missing Information (Uncertainty Control -> NEEDS_REVIEW)
    # -------------------------------------------------------------
    p3_note = (
        "CLINICAL ONCOLOGY NOTE\n"
        "Patient ID: SYN_P003 | Encounter Date: 2026-09-15\n"
        "History: 65-year-old female with advanced lung cancer. CT scan shows multiple pulmonary nodules. "
        "ECOG performance status is 1. "
        "Next-generation sequencing panel has been ordered and is currently pending results. "
        "Platelet count is 210 x 10^9/L. No prior EGFR targeted therapies. "
        "No headaches or neurologic symptoms."
    )
    p3 = CanonicalPatient(
        patient_id="SYN_P003",
        source="synthetic",
        age=65,
        sex="female",
        diagnoses=["Advanced Lung Cancer"],
        biomarkers={"EGFR": "Pending"},
        laboratory_values=[LabValue(test_name="Platelets", value=210.0, unit="x 10^9/L")],
        ecog_performance_status=1,
        clinical_note=p3_note,
    )
    p3_crit_verdicts = [
        (trial.criteria[0], CriterionVerdict.PASS, "advanced lung cancer. CT scan shows multiple pulmonary nodules."),
        (trial.criteria[1], CriterionVerdict.UNKNOWN, ""),  # Missing EGFR result -> UNKNOWN
        (trial.criteria[2], CriterionVerdict.PASS, "65-year-old female"),
        (trial.criteria[3], CriterionVerdict.PASS, "ECOG performance status is 1."),
        (trial.criteria[4], CriterionVerdict.PASS, "Platelet count is 210 x 10^9/L."),
        (trial.criteria[5], CriterionVerdict.PASS, "No prior EGFR targeted therapies."),
        (trial.criteria[6], CriterionVerdict.UNKNOWN, ""),  # Brain MRI not performed/recorded -> UNKNOWN
        (trial.criteria[7], CriterionVerdict.PASS, "No prior EGFR targeted therapies."),
    ]
    p3_cgts = [
        CriterionGroundTruth(
            patient_id=p3.patient_id,
            trial_id=trial.trial_id,
            criterion_id=crit.criterion_id,
            criterion_type=crit.criterion_type,
            ground_truth=verd,
            patient_evidence=PatientEvidence(
                text=ev_txt,
                start_char=p3_note.find(ev_txt) if ev_txt else -1,
                end_char=p3_note.find(ev_txt) + len(ev_txt) if ev_txt else -1,
                source_section="Clinical Narrative" if ev_txt else "None",
            ),
            criterion_evidence=CriterionEvidence(text=crit.source_text),
            annotation_source=AnnotationSource.SYNTHETIC,
            annotator_id=f"generator_seed_{seed}",
            annotation_notes="Scenario C: Missing EGFR status and missing brain imaging",
        )
        for crit, verd, ev_txt in p3_crit_verdicts
    ]
    p3_tgt = TrialGroundTruth(
        patient_id=p3.patient_id,
        trial_id=trial.trial_id,
        eligibility=compute_trial_eligibility([cg.ground_truth for cg in p3_cgts]),
        criterion_summary=summarize_criterion_verdicts([cg.ground_truth for cg in p3_cgts]),
        evidence=["EGFR molecular status pending; brain MRI not documented. Clinical review required."],
        annotation_source=AnnotationSource.SYNTHETIC,
        annotator_id=f"generator_seed_{seed}",
        annotation_notes="Scenario C: Missing Information (NEEDS_REVIEW)",
    )
    cases.append((p3, p3_cgts, p3_tgt))

    # -------------------------------------------------------------
    # Case 4: Scenario D — Conflicting Evidence (Contradiction Control)
    # -------------------------------------------------------------
    p4_note = (
        "CLINICAL ONCOLOGY NOTE\n"
        "Patient ID: SYN_P004 | Encounter Date: 2026-09-15\n"
        "History: 70-year-old male with Stage IV NSCLC.\n"
        "PATHOLOGY REPORT (Outside facility, 2026-08-10): Molecular panel positive for EGFR L858R point mutation.\n"
        "ONCOLOGY PROGRESS NOTE (Current clinic, 2026-09-15): Liquid biopsy NGS reported as EGFR negative/wild-type. "
        "Discrepancy noted between tissue and cfDNA; repeat tissue biopsy requested.\n"
        "Exam: ECOG 1. Platelets: 155 x 10^9/L. No prior third-gen TKI. Brain MRI unremarkable."
    )
    p4 = CanonicalPatient(
        patient_id="SYN_P004",
        source="synthetic",
        age=70,
        sex="male",
        diagnoses=["Stage IV NSCLC"],
        stage="Stage IV",
        biomarkers={"EGFR": "Conflicting (Tissue positive L858R vs Liquid negative)"},
        laboratory_values=[LabValue(test_name="Platelets", value=155.0, unit="x 10^9/L")],
        ecog_performance_status=1,
        clinical_note=p4_note,
    )
    p4_crit_verdicts = [
        (trial.criteria[0], CriterionVerdict.PASS, "Stage IV NSCLC."),
        (trial.criteria[1], CriterionVerdict.UNKNOWN, ""),  # Conflicting -> Must be UNKNOWN / Flagged
        (trial.criteria[2], CriterionVerdict.PASS, "70-year-old male"),
        (trial.criteria[3], CriterionVerdict.PASS, "ECOG 1."),
        (trial.criteria[4], CriterionVerdict.PASS, "Platelets: 155 x 10^9/L."),
        (trial.criteria[5], CriterionVerdict.PASS, "No prior third-gen TKI."),
        (trial.criteria[6], CriterionVerdict.PASS, "Brain MRI unremarkable."),
        (trial.criteria[7], CriterionVerdict.PASS, "No prior third-gen TKI."),
    ]
    p4_cgts = [
        CriterionGroundTruth(
            patient_id=p4.patient_id,
            trial_id=trial.trial_id,
            criterion_id=crit.criterion_id,
            criterion_type=crit.criterion_type,
            ground_truth=verd,
            patient_evidence=PatientEvidence(
                text=ev_txt,
                start_char=p4_note.find(ev_txt) if ev_txt else -1,
                end_char=p4_note.find(ev_txt) + len(ev_txt) if ev_txt else -1,
                source_section="Clinical Narrative" if ev_txt else "None",
            ),
            criterion_evidence=CriterionEvidence(text=crit.source_text),
            annotation_source=AnnotationSource.SYNTHETIC,
            annotator_id=f"generator_seed_{seed}",
            annotation_notes="Scenario D: Conflicting tissue vs liquid biopsy EGFR status",
        )
        for crit, verd, ev_txt in p4_crit_verdicts
    ]
    p4_tgt = TrialGroundTruth(
        patient_id=p4.patient_id,
        trial_id=trial.trial_id,
        eligibility=compute_trial_eligibility([cg.ground_truth for cg in p4_cgts]),
        criterion_summary=summarize_criterion_verdicts([cg.ground_truth for cg in p4_cgts]),
        evidence=["Contradictory EGFR biomarker findings require clinical pathologist adjudication."],
        annotation_source=AnnotationSource.SYNTHETIC,
        annotator_id=f"generator_seed_{seed}",
        annotation_notes="Scenario D: Conflicting Evidence (NEEDS_REVIEW)",
    )
    cases.append((p4, p4_cgts, p4_tgt))

    # -------------------------------------------------------------
    # Case 5: Scenario E — Boundary Condition (Platelet Cutoff at 99 vs 100)
    # -------------------------------------------------------------
    p5_note = (
        "CLINICAL ONCOLOGY NOTE\n"
        "Patient ID: SYN_P005 | Encounter Date: 2026-09-15\n"
        "History: 54-year-old female with metastatic Stage IV NSCLC, documented EGFR Exon 19 deletion. "
        "ECOG performance status is 1. "
        "Routine laboratory evaluation reveals Platelet count: 99 x 10^9/L (mild thrombocytopenia). "
        "Prior treatments: Chemotherapy finished 60 days ago. No prior osimertinib. "
        "Brain MRI: Clear."
    )
    p5 = CanonicalPatient(
        patient_id="SYN_P005",
        source="synthetic",
        age=54,
        sex="female",
        diagnoses=["Metastatic Non-Small Cell Lung Cancer"],
        stage="Stage IV",
        biomarkers={"EGFR": "Exon 19 deletion"},
        laboratory_values=[LabValue(test_name="Platelets", value=99.0, unit="x 10^9/L")],
        ecog_performance_status=1,
        clinical_note=p5_note,
    )
    p5_crit_verdicts = [
        (trial.criteria[0], CriterionVerdict.PASS, "metastatic Stage IV NSCLC"),
        (trial.criteria[1], CriterionVerdict.PASS, "EGFR Exon 19 deletion."),
        (trial.criteria[2], CriterionVerdict.PASS, "54-year-old female"),
        (trial.criteria[3], CriterionVerdict.PASS, "ECOG performance status is 1."),
        (trial.criteria[4], CriterionVerdict.FAIL, "Platelet count: 99 x 10^9/L"),  # 99 < 100 -> FAIL
        (trial.criteria[5], CriterionVerdict.PASS, "No prior osimertinib."),
        (trial.criteria[6], CriterionVerdict.PASS, "Brain MRI: Clear."),
        (trial.criteria[7], CriterionVerdict.PASS, "Chemotherapy finished 60 days ago."),
    ]
    p5_cgts = [
        CriterionGroundTruth(
            patient_id=p5.patient_id,
            trial_id=trial.trial_id,
            criterion_id=crit.criterion_id,
            criterion_type=crit.criterion_type,
            ground_truth=verd,
            patient_evidence=PatientEvidence(
                text=ev_txt,
                start_char=p5_note.find(ev_txt),
                end_char=p5_note.find(ev_txt) + len(ev_txt) if ev_txt in p5_note else -1,
                source_section="Clinical Narrative",
            ),
            criterion_evidence=CriterionEvidence(text=crit.source_text),
            annotation_source=AnnotationSource.SYNTHETIC,
            annotator_id=f"generator_seed_{seed}",
            annotation_notes="Scenario E: Numerical Boundary (Platelets 99 vs >= 100 cutoff)",
        )
        for crit, verd, ev_txt in p5_crit_verdicts
    ]
    p5_tgt = TrialGroundTruth(
        patient_id=p5.patient_id,
        trial_id=trial.trial_id,
        eligibility=compute_trial_eligibility([cg.ground_truth for cg in p5_cgts]),
        criterion_summary=summarize_criterion_verdicts([cg.ground_truth for cg in p5_cgts]),
        evidence=["Platelet count 99 x 10^9/L fails protocol lower boundary of >= 100 x 10^9/L."],
        annotation_source=AnnotationSource.SYNTHETIC,
        annotator_id=f"generator_seed_{seed}",
        annotation_notes="Scenario E: Numerical Boundary (INELIGIBLE)",
    )
    cases.append((p5, p5_cgts, p5_tgt))

    # -------------------------------------------------------------
    # Case 6: Scenario F — Temporal Condition (Washout Interval: 27 vs 28 days)
    # -------------------------------------------------------------
    p6_note = (
        "CLINICAL ONCOLOGY NOTE\n"
        "Patient ID: SYN_P006 | Encounter Date: 2026-09-15\n"
        "History: 61-year-old male with Stage IV NSCLC, EGFR L858R mutation positive. "
        "ECOG performance status is 0. Platelets: 205 x 10^9/L. "
        "Brain MRI: Clear. "
        "Treatment History: Completed Carboplatin/Paclitaxel chemotherapy exactly 27 days prior to today. "
        "Patient is eager to start trial therapy immediately."
    )
    p6 = CanonicalPatient(
        patient_id="SYN_P006",
        source="synthetic",
        age=61,
        sex="male",
        diagnoses=["Stage IV NSCLC"],
        stage="Stage IV",
        biomarkers={"EGFR": "L858R"},
        laboratory_values=[LabValue(test_name="Platelets", value=205.0, unit="x 10^9/L")],
        prior_treatments=["Carboplatin/Paclitaxel (completed 27 days ago)"],
        ecog_performance_status=0,
        clinical_note=p6_note,
    )
    p6_crit_verdicts = [
        (trial.criteria[0], CriterionVerdict.PASS, "Stage IV NSCLC"),
        (trial.criteria[1], CriterionVerdict.PASS, "EGFR L858R mutation positive."),
        (trial.criteria[2], CriterionVerdict.PASS, "61-year-old male"),
        (trial.criteria[3], CriterionVerdict.PASS, "ECOG performance status is 0."),
        (trial.criteria[4], CriterionVerdict.PASS, "Platelets: 205 x 10^9/L."),
        (trial.criteria[5], CriterionVerdict.PASS, "Treatment History: Completed Carboplatin/Paclitaxel"),
        (trial.criteria[6], CriterionVerdict.PASS, "Brain MRI: Clear."),
        (trial.criteria[7], CriterionVerdict.FAIL, "Completed Carboplatin/Paclitaxel chemotherapy exactly 27 days prior to today."),  # 27 < 28 days -> triggers exclusion
    ]
    p6_cgts = [
        CriterionGroundTruth(
            patient_id=p6.patient_id,
            trial_id=trial.trial_id,
            criterion_id=crit.criterion_id,
            criterion_type=crit.criterion_type,
            ground_truth=verd,
            patient_evidence=PatientEvidence(
                text=ev_txt,
                start_char=p6_note.find(ev_txt),
                end_char=p6_note.find(ev_txt) + len(ev_txt) if ev_txt in p6_note else -1,
                source_section="Clinical Narrative",
            ),
            criterion_evidence=CriterionEvidence(text=crit.source_text),
            annotation_source=AnnotationSource.SYNTHETIC,
            annotator_id=f"generator_seed_{seed}",
            annotation_notes="Scenario F: Temporal Washout (Chemotherapy 27 days vs >= 28 days required)",
        )
        for crit, verd, ev_txt in p6_crit_verdicts
    ]
    p6_tgt = TrialGroundTruth(
        patient_id=p6.patient_id,
        trial_id=trial.trial_id,
        eligibility=compute_trial_eligibility([cg.ground_truth for cg in p6_cgts]),
        criterion_summary=summarize_criterion_verdicts([cg.ground_truth for cg in p6_cgts]),
        evidence=["Chemotherapy completed 27 days ago; violates protocol 28-day washout window."],
        annotation_source=AnnotationSource.SYNTHETIC,
        annotator_id=f"generator_seed_{seed}",
        annotation_notes="Scenario F: Temporal Condition (INELIGIBLE)",
    )
    cases.append((p6, p6_cgts, p6_tgt))

    return cases


def generate_and_save_fixtures(output_dir: Path, seed: int = 42) -> None:
    """Generates synthetic dataset fixtures and saves them as canonical JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    trials = get_reference_oncology_trials()
    all_patients = []
    all_criterion_labels = []
    all_trial_labels = []

    for trial in trials:
        cases = generate_scenario_patients(trial, seed=seed)
        for patient, crit_labels, trial_label in cases:
            all_patients.append(patient)
            all_criterion_labels.extend(crit_labels)
            all_trial_labels.append(trial_label)

    # Save canonical files
    (output_dir / "trials.json").write_text(
        json.dumps([t.model_dump(mode="json") for t in trials], indent=2), encoding="utf-8"
    )
    (output_dir / "patients.json").write_text(
        json.dumps([p.model_dump(mode="json") for p in all_patients], indent=2), encoding="utf-8"
    )
    (output_dir / "criteria.json").write_text(
        json.dumps([c.model_dump(mode="json") for t in trials for c in t.criteria], indent=2),
        encoding="utf-8",
    )
    (output_dir / "criterion_labels.json").write_text(
        json.dumps([cl.model_dump(mode="json") for cl in all_criterion_labels], indent=2),
        encoding="utf-8",
    )
    (output_dir / "trial_labels.json").write_text(
        json.dumps([tl.model_dump(mode="json") for tl in all_trial_labels], indent=2),
        encoding="utf-8",
    )

    print(
        f"Successfully generated fixtures in {output_dir}: "
        f"{len(trials)} trials, {len(all_patients)} patients, "
        f"{len(all_criterion_labels)} criterion labels, {len(all_trial_labels)} trial labels."
    )


def main():
    parser = argparse.ArgumentParser(description="MedMatch Synthetic Patient Generator")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/fixtures"),
        help="Directory to save generated JSON fixtures",
    )
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    args = parser.parse_args()

    generate_and_save_fixtures(args.output_dir, seed=args.seed)


if __name__ == "__main__":
    main()
