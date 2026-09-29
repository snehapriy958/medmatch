from google import genai
from google.genai import types

from app.config.settings import settings


_client: genai.Client | None = None


def get_llm() -> genai.Client:
    """
    Return the shared Gemini client configured with an explicit timeout.

    The API key is validated before creating the client so that a
    configuration problem fails with a clear startup/runtime error
    instead of producing an ambiguous Gemini authentication failure.
    """

    global _client

    if _client is not None:
        return _client

    if not settings.GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY is not configured. "
            "Set GOOGLE_API_KEY before starting the AI service."
        )

    _client = genai.Client(
        api_key=settings.GOOGLE_API_KEY,
        http_options=types.HttpOptions(
            timeout=settings.LLM_TIMEOUT_SECONDS * 1000,
        ),
    )

    return _client
