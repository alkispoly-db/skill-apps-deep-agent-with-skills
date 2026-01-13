"""
Chat completions endpoint - OpenAI-compatible API with deep agent integration.
"""
import uuid
import time
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends, Request

from models.openai_schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ResponseMessage,
    ChatMessage,
    ErrorResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_agent(request: Request) -> Any:
    """
    Get the shared agent instance from application state.

    Args:
        request: FastAPI request object

    Returns:
        The initialized agent instance

    Raises:
        RuntimeError: If agent is not initialized
    """
    if not hasattr(request.app.state, "agent"):
        raise RuntimeError(
            "Agent not initialized. Check application startup logs for errors."
        )

    return request.app.state.agent


def convert_openai_to_agent_messages(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    """
    Convert OpenAI message format to agent format.

    Filters out system messages (agent has its own system prompt) and
    unsupported message types (function, tool).

    Args:
        messages: OpenAI format messages

    Returns:
        Agent format messages (simplified)
    """
    agent_messages = []

    for msg in messages:
        # Skip system messages (agent has configured system prompt)
        if msg.role == "system":
            continue

        # Skip function/tool messages (not supported by agent)
        if msg.role in ["function", "tool"]:
            continue

        # Skip messages with no content
        if not msg.content:
            continue

        # Include user and assistant messages for conversation context
        if msg.role in ["user", "assistant"]:
            agent_messages.append({
                "role": msg.role,
                "content": msg.content
            })

    return agent_messages


def invoke_agent_safely(agent: Any, messages: List[Dict[str, str]]) -> str:
    """
    Invoke agent with error handling and response extraction.

    Args:
        agent: The agent instance
        messages: Agent format messages

    Returns:
        Agent's response content

    Raises:
        ValueError: If agent returns invalid response format
    """
    try:
        result = agent.invoke({"messages": messages})

        # Log the response structure for debugging
        logger.debug(f"Agent response structure: {type(result)}")
        logger.debug(f"Agent response keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")

        if not result or "messages" not in result:
            logger.error(f"Invalid response format. Result: {result}")
            raise ValueError("Agent returned invalid response format (missing 'messages')")

        if not result["messages"]:
            raise ValueError("Agent returned empty messages array")

        last_message = result["messages"][-1]
        logger.debug(f"Last message structure: {last_message}")

        # Handle both AIMessage objects and dict responses
        if hasattr(last_message, "content"):
            # AIMessage object
            return last_message.content
        elif isinstance(last_message, dict) and "content" in last_message:
            # Dict with content field
            return last_message["content"]
        else:
            logger.error(f"Unexpected message format: {type(last_message)}, {last_message}")
            raise ValueError(f"Agent response missing 'content' field. Message type: {type(last_message)}")

    except Exception as e:
        logger.error(f"Agent invocation failed: {e}", exc_info=True)
        raise


@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def create_chat_completion(
    request: ChatCompletionRequest,
    agent: Any = Depends(get_agent)
):
    """
    Create a chat completion using the deep agent (OpenAI-compatible endpoint).

    Integrates the marketing research agent with OpenAI-compatible API format.
    Converts between OpenAI message format and agent format, invokes the agent,
    and returns responses in OpenAI format.

    Args:
        request: Chat completion request with messages
        agent: The agent instance (injected dependency)

    Returns:
        ChatCompletionResponse in OpenAI format

    Raises:
        HTTPException: 400 if messages array is empty or invalid
        HTTPException: 500 for agent invocation errors
    """
    try:
        # Validate request
        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "message": "messages array cannot be empty",
                        "type": "invalid_request_error",
                        "param": "messages",
                        "code": "invalid_value",
                    }
                },
            )

        # Convert OpenAI messages to agent format
        agent_messages = convert_openai_to_agent_messages(request.messages)

        if not agent_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "message": "No valid user/assistant messages found after filtering",
                        "type": "invalid_request_error",
                        "param": "messages",
                        "code": "invalid_value",
                    }
                },
            )

        logger.info(f"Processing request with {len(agent_messages)} messages")

        # Invoke agent
        try:
            response_content = invoke_agent_safely(agent, agent_messages)
        except ValueError as e:
            # Agent returned invalid format
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "message": f"Agent returned invalid response: {str(e)}",
                        "type": "agent_error",
                        "code": "invalid_response",
                    }
                },
            )
        except Exception as e:
            # Agent invocation failed
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "message": f"Agent invocation failed: {str(e)}",
                        "type": "agent_error",
                        "code": "invocation_failed",
                    }
                },
            )

        # Generate unique completion ID
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"

        # Create OpenAI-compatible response
        response = ChatCompletionResponse(
            id=completion_id,
            object="chat.completion",
            created=int(time.time()),
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ResponseMessage(
                        role="assistant",
                        content=response_content
                    ),
                    finish_reason="stop",
                )
            ],
        )

        logger.info(f"Request completed successfully (id: {completion_id})")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": f"Unexpected error: {str(e)}",
                    "type": "internal_error",
                    "code": "server_error",
                }
            },
        )
