from google import genai
from app.config.settings import settings

_client = None


def get_llm():
    global _client

    if _client is None:
        _client = genai.Client(
            api_key=settings.GOOGLE_API_KEY
        )

    return _client