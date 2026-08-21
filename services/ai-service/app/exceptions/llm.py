"""
Custom exceptions raised by the LLM service.
"""


class LLMError(Exception):
    """
    Base exception for all LLM-related failures.
    """


class LLMCommunicationError(LLMError):
    """
    Raised when communication with the language model fails.
    """


class EmptyLLMResponseError(LLMError):
    """
    Raised when the language model returns an empty response.
    """


class InvalidLLMResponseError(LLMError):
    """
    Raised when the language model returns invalid JSON.
    """