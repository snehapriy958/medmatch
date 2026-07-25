from app.prompts.trial_matching_prompt import TRIAL_MATCHING_PROMPT


class PromptBuilder:
    """
    Builds prompts for clinical trial eligibility reasoning.
    """

    @staticmethod
    def build_matching_prompt(
        patient_note: str,
        retrieved_criteria: list[dict],
    ) -> str:
        """
        Construct the prompt for evaluating a patient's eligibility
        against the retrieved clinical trial criteria.
        """

        criteria_text = "\n\n".join(
            (
                f"Trial ID: {criterion.get('trial_id', 'Unknown')}\n"
                f"Criteria Type: {criterion.get('criteria_type', 'Unknown')}\n"
                f"Description: {criterion.get('description', '')}"
            )
            for criterion in retrieved_criteria
        )

        return TRIAL_MATCHING_PROMPT.format(
            patient=patient_note.strip(),
            criteria=criteria_text.strip(),
        )