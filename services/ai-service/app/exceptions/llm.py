"""
Custom exceptions raised by the LLM service.

These exceptions allow the application to distinguish between
transient provider failures, permanent configuration failures,
timeouts, rate limits, and invalid model responses.

Only transient communication failures should be retried.
"""


class LLMError(Exception):
    """
    Base exception for all LLM-related failures.
    """


class LLMCommunicationError(LLMError):
    """
    Raised when communication with the language model fails due to
    a transient provider or network error.

    Examples:
    - Temporary provider outage
    - HTTP 5xx response
    - Network connectivity failure
    """


class LLMTimeoutError(LLMCommunicationError):
    """
    Raised when the language model request exceeds the configured
    timeout.

    This is treated as a transient communication failure and may
    be retried.
    """


class LLMRateLimitError(LLMCommunicationError):
    """
    Raised when the language model provider rejects a request because
    of a temporary rate limit or quota limit.

    This is treated as a transient communication failure and may
    be retried with exponential backoff.
    """


class LLMServiceUnavailableError(LLMCommunicationError):
    """
    Raised when the language model provider is temporarily unavailable.

    This is treated as a transient communication failure and may
    be retried.
    """


class LLMConfigurationError(LLMError):
    """
    Raised when the LLM client, API key, model configuration, or
    provider configuration is invalid.

    Configuration errors should not be retried automatically.
    """


class EmptyLLMResponseError(LLMError):
    """
    Raised when the language model returns an empty response.
    """


class InvalidLLMResponseError(LLMError):
    """
    Raised when the language model returns invalid JSON or a response
    that does not conform to the expected structured schema.
    """