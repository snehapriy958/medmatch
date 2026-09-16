from google import genai

from app.config.settings import settings


_client: genai.Client | None = None


def get_llm() -> genai.Client:
    """
    Return the shared Gemini client.

    The API key is validated before creating the client so that a
    configuration problem fails with a clear startup/runtime error
    instead of producing an अस्पष्ट Gemini authentication failure.
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
    )

    return _client