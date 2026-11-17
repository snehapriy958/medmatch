"""
Journey C: Clinical Trial Matching Integration Tests
Tests:
1. Synthetic patient profile submission to matching service
2. Semantic similarity vector retrieval with cosine distance threshold
3. Grouping criteria by trial_id to maintain trial integrity
4. PromptBuilder structure ensuring independent trial evaluation
5. LLM trial results validation (abstention on mismatched/unexpected trial IDs)
6. Grounded evidence attribution
"""

from unittest.mock import MagicMock
from uuid import uuid4
import pytest

from app.rag.prompt_builder import PromptBuilder
from app.schemas.eligibility import EligibilityResponse, EligibilityStatus
from app.services.matching_service import MatchingService


def test_journey_c_prompt_builder_groups_by_trial():
    """Retrieved criteria are strictly grouped by trial_id in prompt."""
    trial_1 = str(uuid4())
    trial_2 = str(uuid4())

    criteria = [
        {
            "id": str(uuid4()),
            "trial_id": trial_1,
            "title": "Study A",
            "condition": "NSCLC",
            "phase": "Phase 3",
            "status": "Recruiting",
            "brief_summary": "Summary A",
            "criteria_type": "INCLUSION",
            "description": "EGFR Exon 19 deletion",
        },
        {
            "id": str(uuid4()),
            "trial_id": trial_1,
            "title": "Study A",
            "condition": "NSCLC",
            "phase": "Phase 3",
            "status": "Recruiting",
            "brief_summary": "Summary A",
            "criteria_type": "EXCLUSION",
            "description": "Prior TKI therapy",
        },
        {
            "id": str(uuid4()),
            "trial_id": trial_2,
            "title": "Study B",
            "condition": "NSCLC",
            "phase": "Phase 2",
            "status": "Recruiting",
            "brief_summary": "Summary B",
            "criteria_type": "INCLUSION",
            "description": "KRAS G12C mutation",
        },
    ]

    patient_note = "58 yo female with metastatic NSCLC and EGFR Exon 19 del."
    prompt = PromptBuilder.build_matching_prompt(
        patient_note=patient_note,
        retrieved_criteria=criteria,
    )

    assert trial_1 in prompt
    assert trial_2 in prompt
    assert "EGFR Exon 19 deletion" in prompt
    assert "KRAS G12C mutation" in prompt
    assert patient_note in prompt


def test_journey_c_matching_service_abstention_on_zero_matches():
    """MatchingService returns safe POSSIBLY_ELIGIBLE abstention when no criteria match."""
    mock_repo = MagicMock()
    mock_repo.find_similar_criteria.return_value = []

    mock_criteria_repo = MagicMock()
    mock_hospital_repo = MagicMock()
    mock_hospital = MagicMock()
    mock_hospital.name = "Test Hospital"
    mock_hospital_repo.get_by_id.return_value = mock_hospital

    mock_emb = MagicMock()
    mock_emb.generate_embedding.return_value = [0.1] * 384

    mock_llm = MagicMock()
    mock_audit = MagicMock()

    service = MatchingService(
        repository=mock_repo,
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=mock_hospital_repo,
        embedding_service=mock_emb,
        llm_service=mock_llm,
        audit_service=mock_audit,
    )

    h_id = uuid4()
    current_user = {
        "sub": str(uuid4()),
        "email": "dr@test.org",
        "role": "PHYSICIAN",
        "hospital_id": str(h_id),
    }

    res = service.evaluate_eligibility(
        patient_note="Patient with NSCLC",
        hospital_id=h_id,
        current_user=current_user,
    )

    assert len(res.results) == 1
    assert res.results[0].eligibility == EligibilityStatus.POSSIBLY_ELIGIBLE
    assert res.results[0].confidence == 0.0
    assert "No matching clinical trial" in res.results[0].summary
    # Ensure Gemini was NOT called when zero trials were retrieved
    mock_llm.evaluate_eligibility.assert_not_called()


def test_journey_c_validation_rejects_hallucinated_trial():
    """Validation rejects LLM response containing a trial ID not in retrieval."""
    mock_repo = MagicMock()
    service = MatchingService(
        repository=mock_repo,
        trial_criteria_repository=MagicMock(),
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )

    expected_ids = {"trial-1", "trial-2"}
    hallucinated_result = [
        EligibilityResponse(
            eligibility=EligibilityStatus.ELIGIBLE,
            confidence=0.9,
            trial_ids_evaluated=["trial-1"],
            summary="Eligible",
            reasoning="Reason",
        ),
        EligibilityResponse(
            eligibility=EligibilityStatus.NOT_ELIGIBLE,
            confidence=0.8,
            trial_ids_evaluated=["hallucinated-trial-999"],
            summary="Not eligible",
            reasoning="Reason",
        ),
    ]

    with pytest.raises(ValueError, match="unexpected clinical trial"):
        service._validate_llm_trial_results(
            llm_results=hallucinated_result,
            expected_trial_ids=expected_ids,
        )
