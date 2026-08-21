import json
import logging
from typing import TypeVar

from google.genai.types import GenerateContentConfig
from pydantic import BaseModel
from tenacity import (
    before_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

T = TypeVar("T", bound=BaseModel)

from app.config.llm import get_llm
from app.config.settings import settings
from app.exceptions.llm import (
    EmptyLLMResponseError,
    InvalidLLMResponseError,
    LLMCommunicationError,
)
from app.prompts.trial_extraction_prompt import TRIAL_EXTRACTION_PROMPT
from app.schemas.eligibility import EligibilityResponse
from app.schemas.trial_extraction import TrialExtraction

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service responsible for interacting with the Gemini model.
    """

    def __init__(self) -> None:
        self.client = get_llm()

    @retry(
        retry=retry_if_exception_type(LLMCommunicationError),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=4,
        ),
        stop=stop_after_attempt(3),
        before=before_log(
            logger,
            logging.INFO,
        ),
        before_sleep=before_sleep_log(
            logger,
            logging.WARNING,
        ),
        reraise=True,
    )
    def _generate_json(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        """
        Generate a structured JSON response from Gemini and
        validate it against the supplied Pydantic model.
        """

        try:
            response = self.client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )

        except Exception as exc:
            logger.exception(
                "Communication with Gemini failed: %s",
                exc,
            )

            raise LLMCommunicationError(
                str(exc)
            ) from exc

        if not response.text:
            logger.error(
                "LLM returned an empty response."
            )

            raise EmptyLLMResponseError(
                "LLM returned an empty response."
            )

        logger.info(
            "Gemini raw response: %s",
            response.text,
        )

        try:
            data = json.loads(response.text)

        except json.JSONDecodeError as exc:
            logger.error(
                "Invalid JSON returned by LLM: %s",
                response.text,
            )

            raise InvalidLLMResponseError(
                "LLM returned invalid JSON."
            ) from exc

        try:
            return response_model.model_validate(data)

        except Exception as exc:
            logger.exception(
                "LLM response validation failed: %s",
                data,
            )

            raise InvalidLLMResponseError(
                "LLM returned an invalid structured response."
            ) from exc

    def extract_trial_information(
        self,
        text: str,
    ) -> TrialExtraction:
        """
        Extract structured trial information from cleaned PDF text.
        """

        prompt = TRIAL_EXTRACTION_PROMPT.format(
            text=text,
        )

        return self._generate_json(
            prompt=prompt,
            response_model=TrialExtraction,
        )

    def evaluate_eligibility(
        self,
        prompt: str,
    ) -> list[EligibilityResponse]:
        """
        Evaluate patient eligibility using Gemini.

        Gemini is expected to return one independent
        EligibilityResponse object for every evaluated trial.

        Expected JSON format:

        [
            {
                "eligibility": "...",
                "confidence": 0.0,
                "trial_ids_evaluated": ["trial-id-1"],
                ...
            },
            {
                "eligibility": "...",
                "confidence": 0.0,
                "trial_ids_evaluated": ["trial-id-2"],
                ...
            }
        ]
        """

        try:
            response = self.client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )

        except Exception as exc:
            logger.exception(
                "Communication with Gemini failed: %s",
                exc,
            )

            raise LLMCommunicationError(
                str(exc)
            ) from exc

        if not response.text:
            logger.error(
                "LLM returned an empty response."
            )

            raise EmptyLLMResponseError(
                "LLM returned an empty response."
            )

        logger.info(
            "Gemini raw response: %s",
            response.text,
        )

        # ---------------------------------------------------------
        # Parse JSON
        # ---------------------------------------------------------

        try:
            data = json.loads(response.text)

        except json.JSONDecodeError as exc:
            logger.error(
                "Invalid JSON returned by LLM: %s",
                response.text,
            )

            raise InvalidLLMResponseError(
                "LLM returned invalid JSON."
            ) from exc

        # ---------------------------------------------------------
        # Gemini must return an array because each trial must be
        # evaluated independently.
        # ---------------------------------------------------------

        if not isinstance(data, list):

            logger.error(
                "Gemini eligibility response must be a JSON array: %r",
                data,
            )

            raise InvalidLLMResponseError(
                "LLM returned an invalid eligibility response. "
                "Expected a JSON array containing one result per trial."
            )

        if not data:

            logger.error(
                "Gemini returned an empty eligibility response array."
            )

            raise InvalidLLMResponseError(
                "LLM returned no eligibility evaluations."
            )

        # ---------------------------------------------------------
        # Validate every independent trial evaluation.
        # ---------------------------------------------------------

        results: list[EligibilityResponse] = []

        for index, item in enumerate(data):

            if not isinstance(item, dict):

                logger.error(
                    "Gemini eligibility result at index %d is not an object: %r",
                    index,
                    item,
                )

                raise InvalidLLMResponseError(
                    "LLM returned an invalid eligibility result."
                )

            try:

                result = EligibilityResponse.model_validate(
                    item
                )

            except Exception as exc:

                logger.exception(
                    "Gemini eligibility result validation failed "
                    "at index %d: %s",
                    index,
                    item,
                )

                raise InvalidLLMResponseError(
                    "LLM returned an invalid eligibility result."
                ) from exc

            # -----------------------------------------------------
            # Every result must identify exactly one trial.
            # -----------------------------------------------------

            if len(result.trial_ids_evaluated) != 1:

                logger.error(
                    "Eligibility result at index %d contains "
                    "%d trial IDs instead of exactly one: %s",
                    index,
                    len(result.trial_ids_evaluated),
                    result.trial_ids_evaluated,
                )

                raise InvalidLLMResponseError(
                    "Each eligibility result must correspond "
                    "to exactly one clinical trial."
                )

            results.append(result)

        return results