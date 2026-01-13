"""
Marketing Research Agent - A deep agent for product research and development.
"""
from agent.core import create_agent, get_system_prompt
from agent.provider import get_llm_from_provider
from agent.config import AgentConfig

__all__ = ["create_agent", "get_system_prompt", "get_llm_from_provider", "AgentConfig"]
