import json
import logging
from typing import Any, TypeVar

import httpx
from google.genai.errors import APIError, ClientError, ServerError
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel, ValidationError
from tenacity import (
    before_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config.llm import get_llm
from app.config.settings import settings
from app.exceptions.llm import (
    EmptyLLMResponseError,
    InvalidLLMResponseError,
    LLMCommunicationError,
    LLMConfigurationError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMTimeoutError,
)
from app.prompts.trial_extraction_prompt import TRIAL_EXTRACTION_PROMPT
from app.schemas.eligibility import EligibilityResponse
from app.schemas.trial_extraction import TrialExtraction


T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service responsible for interacting with the Gemini model.

    All LLM operations are centralized here so that requests use
    consistent error classification, retry behavior, JSON parsing,
    structured validation, and logging.
    """

    def __init__(self) -> None:
        self.client = get_llm()

    @staticmethod
    def _classify_llm_error(
        exc: Exception,
    ) -> LLMCommunicationError | LLMConfigurationError:
        """
        Convert provider exceptions into application-specific errors.

        Communication errors are transient and may be retried.
        Configuration/client errors are treated as permanent.
        """

        if isinstance(exc, TimeoutError):
            return LLMTimeoutError(
                str(exc)
            )

        if isinstance(exc, httpx.TimeoutException):
            return LLMTimeoutError(
                str(exc)
            )

        if isinstance(exc, httpx.HTTPError):
            return LLMCommunicationError(
                str(exc)
            )

        if isinstance(exc, ServerError):
            status_code = getattr(
                exc,
                "code",
                None,
            )

            if status_code == 503:
                return LLMServiceUnavailableError(
                    str(exc)
                )

            return LLMCommunicationError(
                str(exc)
            )

        if isinstance(exc, ClientError):
            status_code = getattr(
                exc,
                "code",
                None,
            )

            if status_code == 429:
                return LLMRateLimitError(
                    str(exc)
                )

            return LLMConfigurationError(
                str(exc)
            )

        if isinstance(exc, APIError):
            status_code = getattr(
                exc,
                "code",
                None,
            )

            if status_code == 429:
                return LLMRateLimitError(
                    str(exc)
                )

            if status_code == 503:
                return LLMServiceUnavailableError(
                    str(exc)
                )

            if (
                status_code is not None
                and status_code >= 500
            ):
                return LLMCommunicationError(
                    str(exc)
                )

            return LLMConfigurationError(
                str(exc)
            )

        return LLMCommunicationError(
            str(exc)
        )

    @staticmethod
    def _extract_response_text(
        response: Any,
    ) -> str:
        """
        Safely extract text from a Gemini response.

        Raises EmptyLLMResponseError if no usable response text exists.
        """

        response_text = getattr(
            response,
            "text",
            None,
        )

        if response_text is None:
            logger.error(
                "LLM response did not contain a text attribute."
            )

            raise EmptyLLMResponseError(
                "LLM response did not contain text."
            )

        if not isinstance(
            response_text,
            str,
        ):
            response_text = str(
                response_text
            )

        response_text = response_text.strip()

        if not response_text:
            logger.error(
                "LLM returned an empty response."
            )

            raise EmptyLLMResponseError(
                "LLM returned an empty response."
            )

        return response_text

    @retry(
        retry=retry_if_exception_type(
            (
                LLMCommunicationError,
                EmptyLLMResponseError,
                InvalidLLMResponseError,
            )
        ),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=8,
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
    def _generate_raw_json(
        self,
        prompt: str,
    ) -> Any:
        """
        Call Gemini and parse its response as JSON.

        Retries:
        - transient communication failures
        - empty responses
        - malformed JSON responses

        Permanent configuration failures are not retried.
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

        except (
            TimeoutError,
            httpx.HTTPError,
            APIError,
            ClientError,
            ServerError,
        ) as exc:
            classified_error = self._classify_llm_error(
                exc
            )

            logger.exception(
                "Gemini request failed. "
                "error_type=%s error=%s",
                classified_error.__class__.__name__,
                exc,
            )

            raise classified_error from exc

        response_text = self._extract_response_text(
            response
        )

        logger.info(
            "Gemini returned a response. "
            "response_length=%d",
            len(
                response_text
            ),
        )

        try:
            parsed_response = json.loads(
                response_text
            )

        except json.JSONDecodeError as exc:
            logger.error(
                "LLM returned invalid JSON. "
                "response_preview=%r",
                response_text[:500],
            )

            raise InvalidLLMResponseError(
                "LLM returned invalid JSON."
            ) from exc

        logger.info(
            "Gemini response was successfully parsed as JSON."
        )

        return parsed_response

    @retry(
        retry=retry_if_exception_type(
            (
                EmptyLLMResponseError,
                InvalidLLMResponseError,
                LLMCommunicationError,
            )
        ),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=8,
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
        Generate structured JSON from Gemini and validate it against
        the supplied Pydantic model.
        """

        data = self._generate_raw_json(
            prompt=prompt,
        )

        try:
            validated_response = (
                response_model.model_validate(
                    data
                )
            )

        except ValidationError as exc:
            logger.error(
                "LLM response validation failed. "
                "response_model=%s validation_errors=%s",
                response_model.__name__,
                exc.errors(),
            )

            raise InvalidLLMResponseError(
                "LLM returned an invalid structured response."
            ) from exc

        logger.info(
            "LLM structured response validated successfully. "
            "response_model=%s",
            response_model.__name__,
        )

        return validated_response

    def extract_trial_information(
        self,
        text: str,
    ) -> TrialExtraction:
        """
        Extract structured trial information from cleaned PDF text.
        """

        if not text or not text.strip():
            logger.error(
                "Trial extraction received empty source text."
            )

            raise ValueError(
                "Trial extraction requires non-empty text."
            )

        logger.info(
            "Starting clinical trial extraction. "
            "text_length=%d",
            len(
                text
            ),
        )

        prompt = TRIAL_EXTRACTION_PROMPT.format(
            text=text,
        )

        extraction = self._generate_json(
            prompt=prompt,
            response_model=TrialExtraction,
        )

        logger.info(
            "Clinical trial extraction completed successfully."
        )

        return extraction

    def evaluate_eligibility(
        self,
        prompt: str,
    ) -> list[EligibilityResponse]:
        """
        Evaluate patient eligibility using Gemini.

        Gemini must return one independent eligibility result for
        each evaluated clinical trial.
        """

        data = self._generate_raw_json(
            prompt=prompt,
        )

        if not isinstance(
            data,
            list,
        ):
            logger.error(
                "Gemini eligibility response must be a JSON array. "
                "actual_type=%s",
                type(
                    data
                ).__name__,
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

        results: list[
            EligibilityResponse
        ] = []

        for index, item in enumerate(
            data
        ):
            if not isinstance(
                item,
                dict,
            ):
                logger.error(
                    "Eligibility result at index %d "
                    "is not a JSON object. "
                    "actual_type=%s",
                    index,
                    type(
                        item
                    ).__name__,
                )

                raise InvalidLLMResponseError(
                    "LLM returned an invalid eligibility result."
                )

            try:
                result = (
                    EligibilityResponse.model_validate(
                        item
                    )
                )

            except ValidationError as exc:
                logger.error(
                    "Eligibility result validation failed "
                    "at index %d. errors=%s",
                    index,
                    exc.errors(),
                )

                raise InvalidLLMResponseError(
                    "LLM returned an invalid eligibility result."
                ) from exc

            if (
                len(
                    result.trial_ids_evaluated
                )
                != 1
            ):
                logger.error(
                    "Eligibility result at index %d contains "
                    "%d trial IDs instead of exactly one.",
                    index,
                    len(
                        result.trial_ids_evaluated
                    ),
                )

                raise InvalidLLMResponseError(
                    "Each eligibility result must correspond "
                    "to exactly one clinical trial."
                )

            results.append(
                result
            )

        logger.info(
            "Eligibility evaluation completed successfully. "
            "result_count=%d",
            len(
                results
            ),
        )

        return results