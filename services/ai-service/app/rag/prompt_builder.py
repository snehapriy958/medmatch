from collections import defaultdict

from app.prompts.trial_matching_prompt import TRIAL_MATCHING_PROMPT


class PromptBuilder:
    """
    Builds deterministic prompts for clinical trial eligibility reasoning.

    Retrieved criteria are grouped by trial so that the LLM evaluates
    every clinical trial independently rather than mixing criteria from
    different trials.
    """

    @staticmethod
    def build_matching_prompt(
        patient_note: str,
        retrieved_criteria: list[dict],
    ) -> str:
        """
        Construct the prompt for evaluating a patient's eligibility
        against retrieved clinical trial criteria.

        The prompt preserves trial boundaries and includes the trial
        metadata required for independent eligibility evaluation.
        """

        if not retrieved_criteria:
            criteria_text = (
                "No condition-compatible trial criteria were retrieved."
            )

        else:
            trials: dict[object, list[dict]] = defaultdict(list)

            # -----------------------------------------------------
            # Group retrieved criteria by trial.
            # -----------------------------------------------------

            for criterion in retrieved_criteria:

                trial_id = criterion.get(
                    "trial_id"
                )

                if trial_id is None:
                    continue

                trials[trial_id].append(
                    criterion
                )

            # -----------------------------------------------------
            # Build one clearly separated section per trial.
            # -----------------------------------------------------

            sections: list[str] = []

            for trial_id, criteria in trials.items():

                if not criteria:
                    continue

                first = criteria[0]

                title = (
                    first.get("title")
                    or "Not provided"
                )

                condition = (
                    first.get("condition")
                    or "Not provided"
                )

                phase = (
                    first.get("phase")
                    or "Not provided"
                )

                status = (
                    first.get("status")
                    or "Not provided"
                )

                brief_summary = (
                    first.get("brief_summary")
                    or "Not provided"
                )

                section_lines = [
                    "================================",
                    "TRIAL INFORMATION",
                    "================================",
                    "",
                    f"Trial ID: {trial_id}",
                    f"Title: {title}",
                    f"Condition: {condition}",
                    f"Phase: {phase}",
                    f"Status: {status}",
                    "",
                    "Brief Summary:",
                    brief_summary,
                    "",
                    "ELIGIBILITY CRITERIA:",
                ]

                for criterion in criteria:

                    criteria_type = (
                        criterion.get(
                            "criteria_type"
                        )
                        or "Unknown"
                    )

                    description = (
                        criterion.get(
                            "description"
                        )
                        or "Not provided"
                    )

                    section_lines.extend(
                        [
                            "",
                            f"Criteria Type: {criteria_type}",
                            f"Requirement: {description}",
                        ]
                    )

                sections.append(
                    "\n".join(
                        section_lines
                    )
                )

            # -----------------------------------------------------
            # Defensive fallback if all retrieved records were
            # malformed and no usable trial IDs were available.
            # -----------------------------------------------------

            if sections:
                criteria_text = "\n\n".join(
                    sections
                )
            else:
                criteria_text = (
                    "No valid trial criteria were available "
                    "for evaluation."
                )

        return TRIAL_MATCHING_PROMPT.format(
            patient=patient_note.strip(),
            criteria=criteria_text.strip(),
        )