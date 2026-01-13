"""
OpenAI-compatible Pydantic models for chat completions API.

This module defines simplified request/response models that are compatible
with OpenAI's Chat Completions API format.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Message in a chat conversation."""

    role: Literal["system", "user", "assistant", "function", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None

    model_config = {"extra": "allow"}


class ChatCompletionRequest(BaseModel):
    """Simplified OpenAI chat completion request - accepts only messages."""

    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")

    model_config = {"extra": "forbid"}


class ResponseMessage(BaseModel):
    """Assistant response message."""

    role: Literal["assistant"] = "assistant"
    content: str


class ChatCompletionChoice(BaseModel):
    """Individual completion choice."""

    index: int
    message: ResponseMessage
    finish_reason: Literal["stop", "length", "content_filter", "tool_calls"]


class ChatCompletionResponse(BaseModel):
    """
    Simplified OpenAI chat completion response.

    Returns only: id, object, created, choices
    """

    id: str = Field(..., description="Unique completion ID")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(..., description="Unix timestamp of completion creation")
    choices: List[ChatCompletionChoice]


class ErrorDetail(BaseModel):
    """OpenAI error detail format."""

    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """OpenAI error response wrapper."""

    error: ErrorDetail
