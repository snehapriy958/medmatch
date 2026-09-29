import unittest
from unittest.mock import MagicMock, patch

import httpx
from google.genai.types import GenerateContentConfig, HttpOptions

from app.config.settings import settings
import app.config.llm as llm_module
from app.exceptions.llm import LLMCommunicationError, LLMTimeoutError
from app.services.llm_service import LLMService


class TestLLMTimeout(unittest.TestCase):
    def test_get_llm_configures_timeout(self):
        """Verify that get_llm passes settings.LLM_TIMEOUT_SECONDS * 1000 to genai.Client."""
        original_client = llm_module._client
        try:
            llm_module._client = None
            with patch.object(settings, "GOOGLE_API_KEY", "fake-api-key"):
                with patch("app.config.llm.genai.Client") as mock_client_cls:
                    mock_client = MagicMock()
                    mock_client_cls.return_value = mock_client

                    llm_module.get_llm()

                    mock_client_cls.assert_called_once()
                    _, kwargs = mock_client_cls.call_args
                    self.assertIn("http_options", kwargs)
                    http_options = kwargs["http_options"]
                    self.assertIsInstance(http_options, HttpOptions)
                    self.assertEqual(
                        http_options.timeout,
                        settings.LLM_TIMEOUT_SECONDS * 1000,
                    )
        finally:
            llm_module._client = original_client

    def test_real_client_retains_timeout_and_applies_to_requests(self):
        """
        Verify with a real genai.Client instance that the timeout is retained
        in client._api_client._http_options and applied to built requests.
        Fails if the timeout configuration disappears.
        """
        original_client = llm_module._client
        try:
            llm_module._client = None
            with patch.object(settings, "GOOGLE_API_KEY", "test-verification-key"):
                real_client = llm_module.get_llm()

                # Verify client-level storage
                api_client = real_client._api_client
                read_only_opts = api_client.get_read_only_http_options()
                self.assertIsNotNone(read_only_opts)
                self.assertEqual(
                    read_only_opts.get("timeout"),
                    settings.LLM_TIMEOUT_SECONDS * 1000,
                )

                # Verify actual request build sets timeout and X-Server-Timeout header
                built_request = api_client._build_request(
                    "post",
                    "models/gemini-2.5-flash:generateContent",
                    {},
                )
                self.assertEqual(
                    built_request.timeout,
                    float(settings.LLM_TIMEOUT_SECONDS),
                )
                self.assertEqual(
                    built_request.headers.get("X-Server-Timeout"),
                    str(settings.LLM_TIMEOUT_SECONDS),
                )
        finally:
            llm_module._client = original_client

    def test_generate_raw_json_passes_timeout_to_generate_content(self):
        """Verify that _generate_raw_json passes HttpOptions with configured timeout to generate_content."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"status": "ok"}'
        mock_client.models.generate_content.return_value = mock_response

        with patch("app.services.llm_service.get_llm", return_value=mock_client):
            service = LLMService()
            result = service._generate_raw_json("Test prompt")

            self.assertEqual(result, {"status": "ok"})
            mock_client.models.generate_content.assert_called_once()
            _, kwargs = mock_client.models.generate_content.call_args
            config = kwargs.get("config")
            self.assertIsInstance(config, GenerateContentConfig)
            self.assertIsNotNone(config.http_options)
            self.assertEqual(
                config.http_options.timeout,
                settings.LLM_TIMEOUT_SECONDS * 1000,
            )

    def test_generate_raw_json_raises_llm_timeout_error_on_read_timeout(self):
        """Verify that a read timeout from the HTTP client is mapped to LLMTimeoutError."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = httpx.ReadTimeout("Socket timeout")

        with patch("app.services.llm_service.get_llm", return_value=mock_client):
            service = LLMService()
            with self.assertRaises(LLMTimeoutError):
                service._generate_raw_json("Test prompt")

    def test_classify_llm_error_handles_timeout_exceptions(self):
        """Verify that TimeoutError and httpx.TimeoutException are classified as LLMTimeoutError."""
        exc1 = TimeoutError("Request timed out after 60 seconds")
        classified1 = LLMService._classify_llm_error(exc1)
        self.assertIsInstance(classified1, LLMTimeoutError)
        self.assertIsInstance(classified1, LLMCommunicationError)

        exc2 = httpx.ReadTimeout("Read timed out on socket")
        classified2 = LLMService._classify_llm_error(exc2)
        self.assertIsInstance(classified2, LLMTimeoutError)
        self.assertIsInstance(classified2, LLMCommunicationError)


if __name__ == "__main__":
    unittest.main()
