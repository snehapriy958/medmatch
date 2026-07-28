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

        if not retrieved_criteria:
            criteria_text = "No relevant trial criteria were retrieved."
        else:
            sections = []

            for index, criterion in enumerate(
                retrieved_criteria,
                start=1,
            ):
                sections.append(
                    (
                        f"==============================\n"
                        f"Retrieved Criterion #{index}\n"
                        f"==============================\n"
                        f"Trial ID: {criterion.get('trial_id', 'Unknown')}\n"
                        f"Title: {criterion.get('title', 'Unknown')}\n"
                        f"Condition: {criterion.get('condition', 'Unknown')}\n"
                        f"Phase: {criterion.get('phase', 'Unknown')}\n"
                        f"Status: {criterion.get('status', 'Unknown')}\n"
                        f"Summary: {criterion.get('brief_summary', 'Not Available')}\n\n"
                        f"Criterion Type: {criterion.get('criteria_type', 'Unknown')}\n"
                        f"Criterion: {criterion.get('description', '')}\n"
                    )
                )

            criteria_text = "\n".join(sections)

        return TRIAL_MATCHING_PROMPT.format(
            patient=patient_note.strip(),
            criteria=criteria_text.strip(),
        )