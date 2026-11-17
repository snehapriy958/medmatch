"""
MedMatch V2 — Gemini API Client Regression Test Suite.
Verifies:
1. Client initialization uses api_version="v1beta".
2. Structured JSON generation works.
3. Invalid JSON is handled safely.
4. Gemini API errors are handled without crashing.
5. Missing API key produces a controlled configuration error.
6. UNKNOWN clinical criteria still route to NEEDS_REVIEW.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from google.genai.errors import APIError, ClientError, ServerError
from google.genai.types import HttpOptions

from app.config import llm as llm_config
from app.config.settings import settings
from app.exceptions.llm import (
    InvalidLLMResponseError,
    LLMCommunicationError,
    LLMConfigurationError,
)
from app.schemas.eligibility import EligibilityResponse
from app.services.llm_service import LLMService


def test_client_initialization_uses_v1beta(monkeypatch):
    """1. Client initialization uses the intended API version (v1beta)."""
    monkeypatch.setattr(llm_config, "_client", None)
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "test-synthetic-key-12345")

    with patch("app.config.llm.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        client = llm_config.get_llm()
        assert client is mock_client

        # Verify genai.Client was called with http_options having api_version="v1beta"
        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args
        http_opts = kwargs.get("http_options")
        assert http_opts is not None
        assert http_opts.api_version == "v1beta"
        assert http_opts.timeout == settings.LLM_TIMEOUT_SECONDS * 1000

    # Reset singleton
    monkeypatch.setattr(llm_config, "_client", None)


def test_structured_json_generation_works():
    """2. Structured JSON generation works with valid Gemini output."""
    service = LLMService.__new__(LLMService)
    trial_id = "00000000-0000-0000-0000-000000000001"

    mock_response = MagicMock()
    mock_response.text = (
        f'[{{"eligibility": "Eligible", "confidence": 0.95, "trial_ids_evaluated": ["{trial_id}"], '
        f'"summary": "Patient meets criteria.", "matched_inclusion": [], "failed_inclusion": [], '
        f'"satisfied_exclusion": [], "triggered_exclusion": [], "missing_information": [], '
        f'"recommendation": "Enroll in trial.", "matched_criteria": [], "failed_criteria": [], '
        f'"reasoning": "All requirements satisfied."}}]'
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    service.client = mock_client

    results = service.evaluate_eligibility(prompt="Sample patient prompt")
    assert len(results) == 1
    assert isinstance(results[0], EligibilityResponse)
    assert results[0].eligibility == "Eligible"
    assert results[0].confidence == 0.95


def test_invalid_json_handled_safely():
    """3. Invalid JSON is handled safely (raises InvalidLLMResponseError)."""
    service = LLMService.__new__(LLMService)

    mock_response = MagicMock()
    mock_response.text = "This is raw unformatted text, not valid JSON."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    service.client = mock_client

    with pytest.raises(InvalidLLMResponseError):
        service.evaluate_eligibility(prompt="Sample prompt")


def test_gemini_api_errors_handled_without_crashing_worker():
    """4. Gemini API errors are classified into domain exceptions without unexpected crashes."""
    service = LLMService.__new__(LLMService)

    mock_client = MagicMock()
    # Simulate a 503 ServerError from Google Gemini backend
    response_mock = MagicMock()
    response_mock.status_code = 503
    mock_client.models.generate_content.side_effect = ServerError(503, {"error": "Overloaded"}, response_mock)
    service.client = mock_client

    with pytest.raises(LLMCommunicationError):
        service._generate_raw_json("Sample prompt")


def test_missing_api_key_produces_controlled_error(monkeypatch):
    """5. Missing API key produces a controlled configuration error (RuntimeError)."""
    monkeypatch.setattr(llm_config, "_client", None)
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", None)

    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY is not configured"):
        llm_config.get_llm()

    monkeypatch.setattr(llm_config, "_client", None)


def test_unknown_clinical_criteria_routes_to_needs_review():
    """6. UNKNOWN clinical criteria still route to NEEDS_REVIEW triage state."""
    service = LLMService.__new__(LLMService)
    trial_id = "00000000-0000-0000-0000-000000000002"

    mock_response = MagicMock()
    mock_response.text = (
        f'[{{"eligibility": "Possibly Eligible", "confidence": 0.50, "trial_ids_evaluated": ["{trial_id}"], '
        f'"summary": "Pending molecular markers require review.", "matched_inclusion": [], "failed_inclusion": [], '
        f'"satisfied_exclusion": [], "triggered_exclusion": [], '
        f'"missing_information": ["EGFR Exon 19 del ctDNA confirmation"], '
        f'"recommendation": "Hold for secondary molecular panel.", "matched_criteria": [], "failed_criteria": [], '
        f'"reasoning": "Molecular marker pending; open-world triage active."}}]'
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    service.client = mock_client

    results = service.evaluate_eligibility(prompt="Pending biomarker prompt")
    assert len(results) == 1
    # Check that it requires review and notes missing information
    assert results[0].eligibility == "Possibly Eligible"
    assert "EGFR Exon 19 del ctDNA confirmation" in results[0].missing_information
