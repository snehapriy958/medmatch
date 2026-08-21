from app.prompts.trial_matching_prompt import TRIAL_MATCHING_PROMPT
from collections import defaultdict

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
        against retrieved clinical trial criteria.
        """

        if not retrieved_criteria:
            criteria_text = "No relevant trial criteria were retrieved."

        else:

            trials = defaultdict(list)


            for criterion in retrieved_criteria:
                trials[criterion["trial_id"]].append(
                    criterion
                )


            sections = []


            for trial_id, criteria in trials.items():

                first = criteria[0]

                section = (
                    f"""
            ================================
            TRIAL INFORMATION
            ================================

            Trial ID:
            {trial_id}

            Title:
            {first.get('title')}

            Condition:
            {first.get('condition')}

            Phase:
            {first.get('phase')}

            Status:
            {first.get('status')}


            CRITERIA:

            """
                )


                for criterion in criteria:

                    section += (
                        f"""
            Type:
            {criterion.get('criteria_type')}

            Requirement:
            {criterion.get('description')}

            """
                    )


                sections.append(section)


            criteria_text = "\n".join(sections)


        return TRIAL_MATCHING_PROMPT.format(
            patient=patient_note.strip(),
            criteria=criteria_text.strip(),
        )