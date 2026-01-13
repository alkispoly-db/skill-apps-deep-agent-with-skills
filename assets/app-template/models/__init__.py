"""
Models package - OpenAI-compatible Pydantic models.
"""

from .openai_schema import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ResponseMessage,
    ErrorResponse,
    ErrorDetail,
)

__all__ = [
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionChoice",
    "ResponseMessage",
    "ErrorResponse",
    "ErrorDetail",
]
