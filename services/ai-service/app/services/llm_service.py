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
                "Communication with Gemini failed."
            )

            raise LLMCommunicationError(
                "Failed to communicate with the language model."
            ) from exc

        if not response.text:
            logger.error(
                "LLM returned an empty response."
            )

            raise EmptyLLMResponseError(
                "LLM returned an empty response."
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

        return response_model.model_validate(data)

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
    ) -> EligibilityResponse:
        """
        Evaluate patient eligibility using the supplied prompt.
        """

        return self._generate_json(
            prompt=prompt,
            response_model=EligibilityResponse,
        )