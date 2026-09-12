from app.rag.prompt_builder import PromptBuilder


def test_build_matching_prompt_includes_patient_note():
    patient_note = (
        "54-year-old male with Stage II colon cancer."
    )

    prompt = (
        PromptBuilder.build_matching_prompt(
            patient_note=patient_note,
            retrieved_criteria=[],
        )
    )

    assert patient_note in prompt


def test_build_matching_prompt_handles_empty_criteria():
    patient_note = (
        "54-year-old male with colon cancer."
    )

    prompt = (
        PromptBuilder.build_matching_prompt(
            patient_note=patient_note,
            retrieved_criteria=[],
        )
    )

    assert (
        "No condition-compatible trial criteria were retrieved."
        in prompt
    )


def test_build_matching_prompt_groups_criteria_by_trial():
    patient_note = (
        "Patient with Stage II colon cancer."
    )

    trial_id = "11111111-1111-1111-1111-111111111111"

    retrieved_criteria = [
        {
            "trial_id": trial_id,
            "title": "Colon Cancer Trial",
            "condition": "Colon Cancer",
            "phase": "Phase II",
            "status": "Recruiting",
            "brief_summary": "Clinical trial summary.",
            "criteria_type": "Inclusion",
            "description": "Patient must have colon cancer.",
        },
        {
            "trial_id": trial_id,
            "title": "Colon Cancer Trial",
            "condition": "Colon Cancer",
            "phase": "Phase II",
            "status": "Recruiting",
            "brief_summary": "Clinical trial summary.",
            "criteria_type": "Exclusion",
            "description": "No severe liver disease.",
        },
    ]

    prompt = (
        PromptBuilder.build_matching_prompt(
            patient_note=patient_note,
            retrieved_criteria=retrieved_criteria,
        )
    )

    assert f"Trial ID: {trial_id}" in prompt

    assert (
        "Patient must have colon cancer."
        in prompt
    )

    assert (
        "No severe liver disease."
        in prompt
    )


def test_build_matching_prompt_keeps_trials_separated():
    patient_note = (
        "Patient with cancer."
    )

    trial_one = (
        "11111111-1111-1111-1111-111111111111"
    )

    trial_two = (
        "22222222-2222-2222-2222-222222222222"
    )

    retrieved_criteria = [
        {
            "trial_id": trial_one,
            "title": "Trial One",
            "condition": "Condition One",
            "phase": "Phase I",
            "status": "Recruiting",
            "brief_summary": "First trial.",
            "criteria_type": "Inclusion",
            "description": "Requirement one.",
        },
        {
            "trial_id": trial_two,
            "title": "Trial Two",
            "condition": "Condition Two",
            "phase": "Phase II",
            "status": "Recruiting",
            "brief_summary": "Second trial.",
            "criteria_type": "Inclusion",
            "description": "Requirement two.",
        },
    ]

    prompt = (
        PromptBuilder.build_matching_prompt(
            patient_note=patient_note,
            retrieved_criteria=retrieved_criteria,
        )
    )

    assert f"Trial ID: {trial_one}" in prompt
    assert f"Trial ID: {trial_two}" in prompt

    assert "Requirement one." in prompt
    assert "Requirement two." in prompt


def test_build_matching_prompt_handles_missing_trial_id():
    patient_note = (
        "Patient with cancer."
    )

    retrieved_criteria = [
        {
            "title": "Malformed Trial",
            "criteria_type": "Inclusion",
            "description": "Requirement.",
        }
    ]

    prompt = (
        PromptBuilder.build_matching_prompt(
            patient_note=patient_note,
            retrieved_criteria=retrieved_criteria,
        )
    )

    assert (
        "No valid trial criteria were available "
        "for evaluation."
        in prompt
    )